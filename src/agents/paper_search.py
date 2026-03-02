"""Paper Search Agent - 自主决策循环 Agent：意图理解 + 自适应搜索 + 深读迭代 + LLM 排序."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote

from loguru import logger
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent
from src.core.llm_client import LLMClient
from src.core.search_client import ExternalSearchResult, SearchManager


# --- Data Models ---


class SmartSearchInput(BaseModel):
    """智能搜索输入."""

    query: str
    providers: list[str] | None = None
    max_results: int = 20
    language_hint: str = "auto"


class RankedPaper(BaseModel):
    """排序后的论文结果."""

    title: str = ""
    authors: str = ""
    year: str = ""
    venue: str = ""
    doi: str = ""
    url: str = ""
    abstract: str = ""
    source: str = ""
    relevance_score: float = 0.0
    relevance_reason: str = ""


class SmartSearchOutput(BaseModel):
    """智能搜索输出."""

    query: str = ""
    interpreted_intent: str = ""
    generated_keywords: list[str] = Field(default_factory=list)
    results: list[RankedPaper] = Field(default_factory=list)
    total_candidates: int = 0
    providers_used: list[str] = Field(default_factory=list)
    # T-86 新增字段（向后兼容）
    iterations_used: int = 1
    search_log: list[str] = Field(default_factory=list)
    domain_detected: str = ""
    quality_score: float = 0.0
    # T-87: 中文数据库快捷链接
    chinese_db_links: list[dict[str, str]] = Field(default_factory=list)


# --- Internal State ---

_DOMAIN_PROVIDERS: dict[str, list[str]] = {
    "medical": ["pubmed", "semantic_scholar", "crossref"],
    "biomedical": ["pubmed", "biorxiv", "semantic_scholar", "crossref"],
    "biology": ["pubmed", "biorxiv", "semantic_scholar", "crossref"],
    "neuroscience": ["pubmed", "semantic_scholar", "crossref"],
    "chemistry": ["pubmed", "semantic_scholar", "openalex", "crossref"],
    "computer_science": ["arxiv", "semantic_scholar", "openalex", "crossref"],
    "ai": ["arxiv", "semantic_scholar", "openalex", "crossref"],
    "machine_learning": ["arxiv", "semantic_scholar", "crossref"],
    "physics": ["arxiv", "openalex", "crossref"],
    "mathematics": ["arxiv", "openalex", "crossref"],
    "general": ["semantic_scholar", "openalex", "arxiv", "pubmed", "crossref"],
}

_MAX_ITERATIONS = 4
_TIMEOUT_SECONDS = 100  # API 120s - 20s buffer

# --- T-87: 中文数据库快捷链接 ---

_CHINESE_DB_LINKS: list[dict[str, str]] = [
    {
        "name": "中国知网 (CNKI)",
        "url_template": "https://search.cnki.com.cn/Search/Result?content={query}",
    },
    {
        "name": "万方数据",
        "url_template": "https://s.wanfangdata.com.cn/paper?q={query}",
    },
    {
        "name": "百度学术",
        "url_template": "https://xueshu.baidu.com/s?wd={query}",
    },
]


def _contains_chinese(text: str) -> bool:
    """检测文本是否包含中文字符."""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _build_chinese_db_links(query: str) -> list[dict[str, str]]:
    """为中文查询生成知网/万方/百度学术的快捷搜索链接."""
    encoded = quote(query)
    return [
        {"name": item["name"], "url": item["url_template"].format(query=encoded)}
        for item in _CHINESE_DB_LINKS
    ]


@dataclass
class _AgentLoopState:
    """跨迭代的 Agent 状态."""

    query: str = ""
    intent: str = ""
    domain: str = "general"
    all_keywords: list[str] = field(default_factory=list)
    candidates: list[ExternalSearchResult] = field(default_factory=list)
    seen_titles: set[str] = field(default_factory=set)
    search_log: list[str] = field(default_factory=list)
    providers_override: list[str] | None = None
    iteration: int = 0
    start_time: float = 0.0


class _AgentDecision(BaseModel):
    """Agent 单轮决策."""

    action: str = "stop"  # search | refine_keywords | deep_read | stop
    reason: str = ""
    new_keywords: list[str] = Field(default_factory=list)
    paper_indices: list[int] = Field(default_factory=list)  # for deep_read
    quality_assessment: float = 0.0  # 0-1, 当前结果质量


# --- Agent ---


class PaperSearchAgent(BaseAgent):
    """智能论文搜索 Agent：自主决策循环 — 理解意图 → 迭代搜索 → 深读 → 排序."""

    agent_type: str = "paper_search"

    def __init__(
        self,
        llm_client: LLMClient,
        search_manager: SearchManager | None = None,
        **kwargs: Any,
    ):
        super().__init__(llm_client, **kwargs)
        self._search_manager = search_manager or SearchManager()

    def process(self, input_data: SmartSearchInput) -> SmartSearchOutput:
        """执行 Agent 决策循环."""
        state = _AgentLoopState(
            query=input_data.query,
            providers_override=input_data.providers,
            start_time=time.time(),
        )

        # Phase 0: 意图理解 + 关键词 + 领域检测
        self._understand_query(state)
        state.search_log.append(
            f"[Phase 0] Intent: {state.intent} | Domain: {state.domain} | Keywords: {state.all_keywords}"
        )

        # 自适应 Provider 选择
        resolved_providers = self._resolve_providers(state)
        state.search_log.append(f"[Phase 0] Providers: {resolved_providers}")

        # 首轮搜索
        self._execute_search(state, state.all_keywords, resolved_providers, input_data.max_results)
        state.iteration = 1
        state.search_log.append(
            f"[Iter 1] Search with {len(state.all_keywords)} keywords → {len(state.candidates)} candidates"
        )

        # Agent 决策循环 (最多 _MAX_ITERATIONS 轮)
        last_quality = 0.0
        while state.iteration < _MAX_ITERATIONS:
            # 超时检查
            elapsed = time.time() - state.start_time
            if elapsed > _TIMEOUT_SECONDS:
                state.search_log.append(f"[Iter {state.iteration}] Timeout ({elapsed:.0f}s), stopping")
                break

            decision = self._decide_next_action(state, input_data.max_results)
            last_quality = decision.quality_assessment
            state.search_log.append(
                f"[Iter {state.iteration + 1}] Decision: {decision.action} | Quality: {decision.quality_assessment:.2f} | Reason: {decision.reason}"
            )

            if decision.action == "stop":
                break
            elif decision.action == "search":
                if decision.new_keywords:
                    state.all_keywords.extend(decision.new_keywords)
                    self._execute_search(state, decision.new_keywords, resolved_providers, input_data.max_results)
            elif decision.action == "refine_keywords":
                if decision.new_keywords:
                    state.all_keywords.extend(decision.new_keywords)
                    self._execute_search(state, decision.new_keywords, resolved_providers, input_data.max_results)
            elif decision.action == "deep_read":
                new_terms = self._execute_deep_read(state, decision.paper_indices)
                if new_terms:
                    state.all_keywords.extend(new_terms)
                    self._execute_search(state, new_terms, resolved_providers, input_data.max_results)

            state.iteration += 1
            state.search_log.append(
                f"[Iter {state.iteration}] Total candidates: {len(state.candidates)}"
            )

        iterations_used = state.iteration

        # 最终排序
        ranked = self._filter_and_rank(input_data.query, state.intent, state.candidates)
        ranked = ranked[: input_data.max_results]

        providers_used = list({c.source for c in state.candidates})

        # 去重关键词
        unique_keywords = list(dict.fromkeys(state.all_keywords))

        # T-87: 中文查询时生成快捷链接
        chinese_db_links: list[dict[str, str]] = []
        if _contains_chinese(input_data.query):
            chinese_db_links = _build_chinese_db_links(input_data.query)

        return SmartSearchOutput(
            query=input_data.query,
            interpreted_intent=state.intent,
            generated_keywords=unique_keywords,
            results=ranked,
            total_candidates=len(state.candidates),
            providers_used=providers_used,
            iterations_used=iterations_used,
            search_log=state.search_log,
            domain_detected=state.domain,
            quality_score=last_quality,
            chinese_db_links=chinese_db_links,
        )

    # --- Phase 0: 意图理解 ---

    def _understand_query(self, state: _AgentLoopState) -> None:
        """LLM 理解用户意图、检测领域、生成关键词."""
        prompt = (
            "## Phase 0: Intent Understanding, Domain Detection & Keyword Generation\n\n"
            f"User query: {state.query}\n\n"
            "Tasks:\n"
            "1. Understand the user's research intent\n"
            "2. Detect the research domain (choose from: medical, biomedical, biology, neuroscience, "
            "chemistry, computer_science, ai, machine_learning, physics, mathematics, general)\n"
            "3. Generate 4-8 English search keywords/phrases for academic paper search\n\n"
            "Respond in JSON:\n"
            '{"interpreted_intent": "...", "research_domain": "...", "keywords": ["...", ...]}'
        )
        try:
            result = self._call_llm_json(prompt)
            state.intent = result.get("interpreted_intent", state.query)
            state.domain = result.get("research_domain", "general")
            state.all_keywords = result.get("keywords", [state.query])
            if not state.all_keywords:
                state.all_keywords = [state.query]
        except Exception as e:
            logger.warning(f"[paper_search] Phase 0 failed: {e}, using raw query")
            state.intent = state.query
            state.domain = "general"
            state.all_keywords = [state.query]

    # --- Provider 选择 ---

    def _resolve_providers(self, state: _AgentLoopState) -> list[str] | None:
        """根据用户指定或领域自动选择 Provider."""
        if state.providers_override:
            return state.providers_override
        domain_providers = _DOMAIN_PROVIDERS.get(state.domain, _DOMAIN_PROVIDERS["general"])
        # 过滤出实际可用的 Provider
        available = {p.name for p in self._search_manager.available_providers}
        resolved = [p for p in domain_providers if p in available]
        return resolved if resolved else None  # None = use all available

    # --- 搜索执行 ---

    def _execute_search(
        self,
        state: _AgentLoopState,
        keywords: list[str],
        providers: list[str] | None,
        max_results: int,
    ) -> None:
        """执行搜索并合并到 state，自动去重."""
        max_per_keyword = max(3, max_results // max(len(keywords), 1))
        for kw in keywords:
            try:
                results = self._search_manager.search(
                    kw, max_results=max_per_keyword, provider_names=providers
                )
                for r in results:
                    title_key = r.title.lower().strip()
                    if title_key and title_key not in state.seen_titles:
                        state.seen_titles.add(title_key)
                        state.candidates.append(r)
            except Exception as e:
                logger.warning(f"[paper_search] Search failed for '{kw}': {e}")

    # --- Agent 决策 ---

    def _decide_next_action(self, state: _AgentLoopState, target_count: int) -> _AgentDecision:
        """LLM 评估当前结果质量并决定下一步动作."""
        # 构建当前候选摘要
        sample_size = min(len(state.candidates), 15)
        sample_papers = []
        for i, c in enumerate(state.candidates[:sample_size]):
            sample_papers.append({
                "index": i,
                "title": c.title,
                "year": c.year,
                "abstract": c.abstract[:200] if c.abstract else "",
            })

        prompt = (
            "## Agent Decision: Evaluate & Choose Next Action\n\n"
            f"Original query: {state.query}\n"
            f"Interpreted intent: {state.intent}\n"
            f"Research domain: {state.domain}\n"
            f"Keywords used so far: {state.all_keywords}\n"
            f"Current candidate count: {len(state.candidates)}\n"
            f"Target result count: {target_count}\n"
            f"Iteration: {state.iteration + 1} / {_MAX_ITERATIONS}\n\n"
            f"Sample of current candidates ({sample_size} shown):\n"
            f"{json.dumps(sample_papers, ensure_ascii=False, indent=1)}\n\n"
            "Evaluate the current results and decide the next action.\n"
            "Actions:\n"
            '- "search": Search with new keywords (provide new_keywords)\n'
            '- "refine_keywords": Current keywords are too broad/narrow, try refined ones (provide new_keywords)\n'
            '- "deep_read": Read abstracts of promising papers to extract new terms (provide paper_indices)\n'
            '- "stop": Results are sufficient, stop searching\n\n'
            "Consider:\n"
            "- Do we have enough relevant papers (>= target_count candidates)?\n"
            "- Are the papers actually relevant to the query?\n"
            "- Could different keywords or terminology find better results?\n"
            "- Would reading abstracts reveal field-specific terminology we missed?\n\n"
            "Respond in JSON:\n"
            "{\n"
            '  "action": "search|refine_keywords|deep_read|stop",\n'
            '  "reason": "why this action",\n'
            '  "quality_assessment": 0.0-1.0,\n'
            '  "new_keywords": ["...", ...],\n'
            '  "paper_indices": [0, 1, ...]\n'
            "}"
        )
        try:
            result = self._call_llm_json(prompt)
            return _AgentDecision(
                action=result.get("action", "stop"),
                reason=result.get("reason", ""),
                new_keywords=result.get("new_keywords", []),
                paper_indices=result.get("paper_indices", []),
                quality_assessment=float(result.get("quality_assessment", 0.5)),
            )
        except Exception as e:
            logger.warning(f"[paper_search] Decision failed: {e}, stopping")
            return _AgentDecision(action="stop", reason=f"Decision LLM error: {e}", quality_assessment=0.5)

    # --- 深读 ---

    def _execute_deep_read(self, state: _AgentLoopState, paper_indices: list[int]) -> list[str]:
        """深读指定论文的摘要，提取新的搜索术语."""
        abstracts = []
        for idx in paper_indices:
            if 0 <= idx < len(state.candidates):
                c = state.candidates[idx]
                if c.abstract:
                    abstracts.append(f"[{idx}] {c.title}: {c.abstract[:500]}")

        if not abstracts:
            return []

        sep = "\n---\n"
        abstracts_text = sep.join(abstracts)
        prompt = (
            "## Deep Read: Extract New Search Terms\n\n"
            f"Original query: {state.query}\n"
            f"Intent: {state.intent}\n"
            f"Keywords already used: {state.all_keywords}\n\n"
            f"Paper abstracts to analyze:\n{abstracts_text}\n\n"
            "Extract 2-4 NEW English search keywords/phrases from these abstracts that could help "
            "find more relevant papers. Focus on:\n"
            "- Field-specific terminology not yet in our keyword list\n"
            "- Related methods, techniques, or concepts\n"
            "- Canonical names for the research area\n\n"
            'Respond in JSON: {"new_terms": ["...", ...]}'
        )
        try:
            result = self._call_llm_json(prompt)
            new_terms = result.get("new_terms", [])
            if new_terms:
                state.search_log.append(f"[Deep Read] Extracted terms: {new_terms}")
            return new_terms
        except Exception as e:
            logger.warning(f"[paper_search] Deep read failed: {e}")
            return []

    # --- 排序（保留原逻辑）---

    def _filter_and_rank(
        self,
        query: str,
        intent: str,
        candidates: list[ExternalSearchResult],
    ) -> list[RankedPaper]:
        """LLM 筛选候选论文并评分排序."""
        if not candidates:
            return []

        paper_list = []
        for i, c in enumerate(candidates):
            paper_list.append({
                "index": i,
                "title": c.title,
                "authors": c.authors[:100],
                "year": c.year,
                "venue": c.venue,
                "abstract": c.abstract[:300],
            })

        prompt = (
            "## Final Phase: Paper Filtering & Ranking\n\n"
            f"User query: {query}\n"
            f"Interpreted intent: {intent}\n\n"
            f"Candidate papers ({len(paper_list)} total):\n"
            f"{json.dumps(paper_list, ensure_ascii=False, indent=1)}\n\n"
            "Evaluate and rank these papers. Only include papers with relevance_score >= 0.3. "
            "Respond in JSON with key: ranked_papers (list of {{index, relevance_score, relevance_reason}})."
        )

        try:
            result = self._call_llm_json(prompt)
            ranked_items = result.get("ranked_papers", [])
        except Exception as e:
            logger.warning(f"[paper_search] Ranking failed: {e}, returning all with default score")
            return [
                RankedPaper(
                    **c.model_dump(),
                    relevance_score=0.5,
                    relevance_reason="LLM ranking unavailable",
                )
                for c in candidates
            ]

        ranked_papers: list[RankedPaper] = []
        for item in ranked_items:
            idx = item.get("index", -1)
            if 0 <= idx < len(candidates):
                c = candidates[idx]
                ranked_papers.append(
                    RankedPaper(
                        **c.model_dump(),
                        relevance_score=float(item.get("relevance_score", 0.5)),
                        relevance_reason=item.get("relevance_reason", ""),
                    )
                )

        ranked_papers.sort(key=lambda p: p.relevance_score, reverse=True)
        return ranked_papers
