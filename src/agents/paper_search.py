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
    "economics": ["openalex", "crossref", "semantic_scholar"],
    "finance": ["openalex", "crossref", "semantic_scholar"],
    "business": ["openalex", "crossref", "semantic_scholar"],
    "management": ["openalex", "crossref", "semantic_scholar"],
    "social_science": ["openalex", "crossref", "semantic_scholar"],
    "psychology": ["pubmed", "openalex", "crossref", "semantic_scholar"],
    "education": ["openalex", "crossref", "semantic_scholar"],
    "law": ["openalex", "crossref", "semantic_scholar"],
    "environmental": ["openalex", "crossref", "semantic_scholar", "pubmed"],
    "engineering": ["arxiv", "openalex", "crossref", "semantic_scholar"],
    "general": ["semantic_scholar", "openalex", "arxiv", "pubmed", "crossref"],
}

_MAX_ITERATIONS = 3
_TIMEOUT_SECONDS = 60  # 留 60s 给最终排序 LLM 调用 + 网络延迟，前端 120s 超时

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


# --- 无 LLM Fallback: 中文学术术语 → 英文关键词 ---

# 术语词典：中文片段 → (英文关键词列表, 领域标签)
# 匹配采用最长子串优先
_ACADEMIC_TERM_MAP: list[tuple[str, list[str], str]] = [
    # --- 经济学 / 金融 / 商业 ---
    ("代理理论", ["agency theory"], "economics"),
    ("代理成本", ["agency cost"], "economics"),
    ("代理经济", ["agency economics", "agency theory"], "economics"),
    ("代理商业", ["agency business", "agency theory"], "business"),
    ("代理问题", ["agency problem", "principal-agent problem"], "economics"),
    ("委托代理", ["principal-agent", "agency theory"], "economics"),
    ("资本市场", ["capital market"], "finance"),
    ("股票市场", ["stock market", "equity market"], "finance"),
    ("市场反应", ["market reaction", "market response"], "finance"),
    ("资产定价", ["asset pricing"], "finance"),
    ("公司治理", ["corporate governance"], "finance"),
    ("信息不对称", ["information asymmetry", "asymmetric information"], "economics"),
    ("道德风险", ["moral hazard"], "economics"),
    ("逆向选择", ["adverse selection"], "economics"),
    ("行为金融", ["behavioral finance"], "finance"),
    ("风险管理", ["risk management"], "finance"),
    ("投资组合", ["portfolio", "portfolio management"], "finance"),
    ("金融市场", ["financial market"], "finance"),
    ("货币政策", ["monetary policy"], "economics"),
    ("财政政策", ["fiscal policy"], "economics"),
    ("宏观经济", ["macroeconomics"], "economics"),
    ("微观经济", ["microeconomics"], "economics"),
    ("博弈论", ["game theory"], "economics"),
    ("供应链", ["supply chain"], "business"),
    ("创新", ["innovation"], "business"),
    ("企业家精神", ["entrepreneurship"], "business"),
    ("并购", ["mergers and acquisitions", "M&A"], "finance"),
    ("IPO", ["initial public offering", "IPO"], "finance"),
    ("会计", ["accounting"], "business"),
    ("审计", ["auditing"], "business"),
    ("盈余管理", ["earnings management"], "finance"),
    ("股利", ["dividend"], "finance"),
    ("ESG", ["ESG", "environmental social governance"], "finance"),
    ("可持续发展", ["sustainable development", "sustainability"], "environmental"),
    ("碳排放", ["carbon emission"], "environmental"),
    ("绿色金融", ["green finance"], "finance"),
    # --- 管理学 ---
    ("组织行为", ["organizational behavior"], "management"),
    ("人力资源", ["human resource management"], "management"),
    ("战略管理", ["strategic management"], "management"),
    ("领导力", ["leadership"], "management"),
    ("知识管理", ["knowledge management"], "management"),
    ("项目管理", ["project management"], "management"),
    # --- 计算机 / AI ---
    ("机器学习", ["machine learning"], "machine_learning"),
    ("深度学习", ["deep learning"], "ai"),
    ("自然语言处理", ["natural language processing", "NLP"], "ai"),
    ("计算机视觉", ["computer vision"], "ai"),
    ("大语言模型", ["large language model", "LLM"], "ai"),
    ("人工智能", ["artificial intelligence"], "ai"),
    ("强化学习", ["reinforcement learning"], "ai"),
    ("神经网络", ["neural network"], "ai"),
    ("推荐系统", ["recommendation system", "recommender system"], "computer_science"),
    ("区块链", ["blockchain"], "computer_science"),
    ("数据挖掘", ["data mining"], "computer_science"),
    ("知识图谱", ["knowledge graph"], "computer_science"),
    # --- 医学 / 生物 ---
    ("基因编辑", ["gene editing", "CRISPR"], "biomedical"),
    ("蛋白质", ["protein"], "biology"),
    ("药物", ["drug", "pharmaceutical"], "medical"),
    ("临床试验", ["clinical trial"], "medical"),
    ("流行病", ["epidemic", "epidemiology"], "medical"),
    ("免疫", ["immunology", "immune"], "medical"),
    ("癌症", ["cancer", "oncology"], "medical"),
    # --- 教育 / 心理 / 社科 ---
    ("教育", ["education"], "education"),
    ("心理", ["psychology", "psychological"], "psychology"),
    ("认知", ["cognition", "cognitive"], "psychology"),
    ("社会", ["social", "society"], "social_science"),
    ("政策", ["policy"], "social_science"),
    # --- 通用学术词 ---
    ("实证研究", ["empirical study", "empirical research"], ""),
    ("实验", ["experiment", "experimental"], ""),
    ("综述", ["review", "survey"], ""),
    ("元分析", ["meta-analysis"], ""),
    ("回归分析", ["regression analysis"], ""),
    ("因果", ["causality", "causal"], ""),
    ("影响", ["impact", "effect"], ""),
    ("关系", ["relationship", "relation"], ""),
    ("机制", ["mechanism"], ""),
    ("模型", ["model"], ""),
    ("效率", ["efficiency"], ""),
    ("绩效", ["performance"], ""),
]

# 按中文术语长度降序排序（最长匹配优先）
_ACADEMIC_TERM_MAP.sort(key=lambda x: len(x[0]), reverse=True)


def _fallback_translate_and_detect(query: str) -> tuple[list[str], str, str]:
    """无 LLM 时的 fallback：基于术语词典将中文查询翻译为英文关键词 + 检测领域.

    Uses overlapping scan (not greedy consume) so "资本市场反应" matches both
    "资本市场" → capital market AND "市场反应" → market reaction.

    Returns:
        (english_keywords, detected_domain, interpreted_intent)
    """
    if not _contains_chinese(query):
        return [query], "general", query

    keywords: list[str] = []
    domain_votes: dict[str, int] = {}
    matched_cn: list[str] = []

    # 非消耗式扫描：在原始 query 上匹配所有术语（允许重叠）
    for cn_term, en_terms, domain in _ACADEMIC_TERM_MAP:
        if cn_term in query:
            keywords.extend(en_terms)
            matched_cn.append(cn_term)
            if domain:
                domain_votes[domain] = domain_votes.get(domain, 0) + 1

    # 领域投票
    detected_domain = "general"
    if domain_votes:
        detected_domain = max(domain_votes, key=lambda k: domain_votes[k])

    # 生成组合短语：取每个匹配术语的首选英文词做组合
    if len(matched_cn) >= 2:
        term_groups: list[str] = []
        seen_terms: set[str] = set()
        for cn_term, en_terms, _ in _ACADEMIC_TERM_MAP:
            if cn_term in matched_cn and en_terms[0] not in seen_terms:
                term_groups.append(en_terms[0])
                seen_terms.add(en_terms[0])
        if len(term_groups) >= 2:
            combined = " ".join(term_groups[:3])
            keywords.insert(0, combined)

    # 去重并保序
    seen: set[str] = set()
    unique_keywords: list[str] = []
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen:
            seen.add(kw_lower)
            unique_keywords.append(kw)

    if not unique_keywords:
        logger.warning(f"[paper_search] Fallback: no terms matched for '{query}', using raw query")
        unique_keywords = [query]

    intent = f"Research on {', '.join(unique_keywords[:3])}" if unique_keywords else query

    logger.info(
        f"[paper_search] Fallback translate: '{query}' → keywords={unique_keywords}, domain={detected_domain}"
    )

    return unique_keywords, detected_domain, intent


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
        available_domains = ", ".join(sorted(_DOMAIN_PROVIDERS.keys()))
        prompt = (
            "## Phase 0: Intent Understanding, Domain Detection & Keyword Generation\n\n"
            f"User query: {state.query}\n\n"
            "Tasks:\n"
            "1. Understand the user's research intent\n"
            f"2. Detect the research domain (choose from: {available_domains})\n"
            "3. Generate 4-8 English search keywords/phrases for academic paper search\n"
            "   - If the query is in Chinese, translate it to English academic terms\n"
            "   - Include both broad and specific keywords\n"
            "   - Include canonical terminology for the research area\n\n"
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
            logger.warning(f"[paper_search] Phase 0 LLM failed: {e}, using fallback translator")
            # Fallback: 用术语词典翻译中文 → 英文
            keywords, domain, intent = _fallback_translate_and_detect(state.query)
            state.intent = intent
            state.domain = domain
            state.all_keywords = keywords

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
            logger.warning(f"[paper_search] Ranking failed: {e}, using keyword-based fallback ranking")
            return self._fallback_rank(query, intent, candidates)

        ranked_papers: list[RankedPaper] = []
        for item in ranked_items:
            idx = item.get("index", -1)
            if 0 <= idx < len(candidates):
                c = candidates[idx]
                # 安全解析 relevance_score（LLM 可能返回字符串而非数字）
                raw_score = item.get("relevance_score", 0.5)
                try:
                    score = float(raw_score)
                except (ValueError, TypeError):
                    score = 0.5
                ranked_papers.append(
                    RankedPaper(
                        **c.model_dump(),
                        relevance_score=score,
                        relevance_reason=str(item.get("relevance_reason", "")),
                    )
                )

        ranked_papers.sort(key=lambda p: p.relevance_score, reverse=True)
        return ranked_papers

    # --- Fallback 排序（无 LLM）---

    @staticmethod
    def _fallback_rank(
        query: str,
        intent: str,
        candidates: list[ExternalSearchResult],
    ) -> list[RankedPaper]:
        """基于关键词匹配的 fallback 排序，无需 LLM."""
        # 提取搜索关键词（从 intent 和 query 中）
        if _contains_chinese(query):
            _, _, intent_text = _fallback_translate_and_detect(query)
        else:
            intent_text = intent or query

        # 构建关键词集合（小写，去停用词）
        stop_words = {"the", "a", "an", "of", "in", "on", "and", "or", "for", "to", "with", "is", "are", "research"}
        raw_terms = re.split(r"[\s,;]+", intent_text.lower().replace("research on ", ""))
        search_terms = {t for t in raw_terms if t and t not in stop_words and len(t) > 1}

        ranked: list[RankedPaper] = []
        for c in candidates:
            text = f"{c.title} {c.abstract}".lower()
            if not text.strip():
                continue

            # 计算关键词命中率
            hits = sum(1 for term in search_terms if term in text)
            term_score = hits / max(len(search_terms), 1)

            # 标题命中额外加权（标题相关性更高）
            title_lower = c.title.lower()
            title_hits = sum(1 for term in search_terms if term in title_lower)
            title_bonus = title_hits * 0.1

            # 有摘要的论文稍微加分
            abstract_bonus = 0.05 if c.abstract else 0.0

            score = min(term_score + title_bonus + abstract_bonus, 1.0)

            # 生成简短的匹配说明
            matched = [t for t in search_terms if t in text]
            reason = f"Keywords matched: {', '.join(sorted(matched)[:5])}" if matched else "Low keyword overlap"

            ranked.append(
                RankedPaper(
                    **c.model_dump(),
                    relevance_score=round(score, 3),
                    relevance_reason=reason,
                )
            )

        ranked.sort(key=lambda p: p.relevance_score, reverse=True)
        return ranked
