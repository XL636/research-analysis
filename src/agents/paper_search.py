"""Paper Search Agent - 智能论文搜索：意图理解 + 关键词生成 + 多源搜索 + LLM 排序."""

from __future__ import annotations

import json
from typing import Any

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


# --- Agent ---


class PaperSearchAgent(BaseAgent):
    """智能论文搜索 Agent：理解意图 → 生成关键词 → 多源搜索 → LLM 筛选排序."""

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
        """执行智能搜索三步流程."""
        # Step 1: 理解意图 + 生成关键词
        intent, keywords = self._understand_and_generate_keywords(input_data.query)
        logger.info(f"[paper_search] Intent: {intent}")
        logger.info(f"[paper_search] Keywords ({len(keywords)}): {keywords}")

        # Step 2: 多关键词多源搜索 + 去重
        candidates = self._search_with_keywords(
            keywords,
            providers=input_data.providers,
            max_per_keyword=max(3, input_data.max_results // len(keywords)) if keywords else 5,
        )
        logger.info(f"[paper_search] Candidates after dedup: {len(candidates)}")

        # Step 3: LLM 筛选排序
        ranked = self._filter_and_rank(input_data.query, intent, candidates)
        # 截取到 max_results
        ranked = ranked[: input_data.max_results]

        providers_used = list({c.source for c in candidates})

        return SmartSearchOutput(
            query=input_data.query,
            interpreted_intent=intent,
            generated_keywords=keywords,
            results=ranked,
            total_candidates=len(candidates),
            providers_used=providers_used,
        )

    def _understand_and_generate_keywords(self, query: str) -> tuple[str, list[str]]:
        """LLM 理解用户意图并生成英文搜索关键词."""
        prompt = (
            "## Phase 1: Intent Understanding & Keyword Generation\n\n"
            f"User query: {query}\n\n"
            "Analyze the query and generate 4-8 English search keywords. "
            "Respond in JSON with keys: interpreted_intent, research_domain, keywords."
        )
        try:
            result = self._call_llm_json(prompt)
            intent = result.get("interpreted_intent", query)
            keywords = result.get("keywords", [])
            if not keywords:
                # Fallback: use query as-is
                keywords = [query]
            return intent, keywords
        except Exception as e:
            logger.warning(f"[paper_search] Keyword generation failed: {e}, using raw query")
            return query, [query]

    def _search_with_keywords(
        self,
        keywords: list[str],
        providers: list[str] | None = None,
        max_per_keyword: int = 5,
    ) -> list[ExternalSearchResult]:
        """用多个关键词搜索多个源，合并去重."""
        all_results: list[ExternalSearchResult] = []
        seen_titles: set[str] = set()

        for kw in keywords:
            try:
                results = self._search_manager.search(
                    kw, max_results=max_per_keyword, provider_names=providers
                )
                for r in results:
                    title_key = r.title.lower().strip()
                    if title_key and title_key not in seen_titles:
                        seen_titles.add(title_key)
                        all_results.append(r)
            except Exception as e:
                logger.warning(f"[paper_search] Search failed for '{kw}': {e}")

        return all_results

    def _filter_and_rank(
        self,
        query: str,
        intent: str,
        candidates: list[ExternalSearchResult],
    ) -> list[RankedPaper]:
        """LLM 筛选候选论文并评分排序."""
        if not candidates:
            return []

        # 构建候选论文列表供 LLM 评估
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
            "## Phase 2: Paper Filtering & Ranking\n\n"
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
            # Fallback: 返回全部候选，默认评分
            return [
                RankedPaper(
                    **c.model_dump(),
                    relevance_score=0.5,
                    relevance_reason="LLM ranking unavailable",
                )
                for c in candidates
            ]

        # 按 LLM 返回排序组装结果
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

        # 按评分降序排序
        ranked_papers.sort(key=lambda p: p.relevance_score, reverse=True)
        return ranked_papers
