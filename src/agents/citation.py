"""CitationAgent - 从知识库和 LLM 收集论文引用."""

from __future__ import annotations

from typing import Any

from loguru import logger

from src.agents.base import BaseAgent
from src.core.paper_models import CitationRef, PaperProject


class CitationAgent(BaseAgent):
    """引用收集 Agent."""

    agent_type = "citation"

    def _default_system_prompt(self) -> str:
        return "You are an academic citation management assistant. Output JSON only."

    def process(self, input_data: Any) -> list[CitationRef]:
        """收集引用.

        Args:
            input_data: dict with keys:
                - project: PaperProject
                - kb: KnowledgeBase instance (optional)
        """
        project: PaperProject = input_data["project"]
        kb = input_data.get("kb")

        citations: list[CitationRef] = []
        seen_titles: set[str] = set()

        # 1. 从知识库加载指定文档（含自动调研结果）
        all_doc_ids = list(set(project.reference_doc_ids + project.research_doc_ids))
        if kb and all_doc_ids:
            for doc_id in all_doc_ids:
                try:
                    analysis = kb.get_analysis(doc_id)
                    if analysis and analysis.document_title not in seen_titles:
                        seen_titles.add(analysis.document_title)
                        # 构建深度引用信息
                        key_findings_text = ""
                        methodology_text = ""
                        contributions_text = ""
                        has_full = False

                        if analysis.key_findings:
                            key_findings_text = "; ".join(
                                kf.finding for kf in analysis.key_findings[:5]
                            )
                            has_full = True
                        if analysis.methodology:
                            methodology_text = analysis.methodology.approach
                            has_full = True
                        if analysis.contributions:
                            contributions_text = "; ".join(analysis.contributions[:5])
                            has_full = True

                        citations.append(CitationRef(
                            key=f"kb-{doc_id}",
                            title=analysis.document_title,
                            authors="",
                            year="",
                            abstract=analysis.summary[:300],
                            source="knowledge_base",
                            summary=analysis.summary[:500],
                            key_findings_text=key_findings_text[:500],
                            methodology_text=methodology_text[:300],
                            contributions_text=contributions_text[:500],
                            has_full_analysis=has_full,
                        ))
                except Exception as e:
                    logger.warning(f"Failed to load doc {doc_id}: {e}")

        # 2. 用 LLM 推荐搜索关键词
        keywords = self._get_search_keywords(project)

        # 3. 在知识库中搜索更多相关文献
        if kb and keywords:
            for kw in keywords[:5]:
                try:
                    results = kb.search(kw, limit=3)
                    for r in results:
                        if r["title"] not in seen_titles:
                            seen_titles.add(r["title"])
                            # 尝试加载完整分析
                            ref = CitationRef(
                                key=f"kb-{r['id']}",
                                title=r["title"],
                                abstract=r.get("summary", "")[:300],
                                source="knowledge_base",
                            )
                            try:
                                analysis = kb.get_analysis(r["id"])
                                if analysis:
                                    ref.summary = analysis.summary[:500]
                                    if analysis.key_findings:
                                        ref.key_findings_text = "; ".join(
                                            kf.finding for kf in analysis.key_findings[:5]
                                        )[:500]
                                        ref.has_full_analysis = True
                                    if analysis.methodology:
                                        ref.methodology_text = analysis.methodology.approach[:300]
                                        ref.has_full_analysis = True
                                    if analysis.contributions:
                                        ref.contributions_text = "; ".join(
                                            analysis.contributions[:5]
                                        )[:500]
                                        ref.has_full_analysis = True
                            except Exception:
                                pass
                            citations.append(ref)
                except Exception as e:
                    logger.warning(f"KB search failed for '{kw}': {e}")

        # 4. 外部学术搜索（如果配置了搜索源）
        self._search_external(keywords, citations, seen_titles)

        logger.info(f"Collected {len(citations)} citations for project '{project.name}'")
        return citations

    def _search_external(
        self,
        keywords: list[str],
        citations: list[CitationRef],
        seen_titles: set[str],
    ) -> None:
        """从外部学术搜索 API 补充引用."""
        try:
            from src.core.search_client import SearchManager

            manager = SearchManager()
            if not manager.has_providers:
                logger.debug("No external search providers available, skipping")
                return

            provider_names = [p.name for p in manager.available_providers]
            logger.info(f"Searching external sources: {provider_names}")

            search_keywords = keywords[:3]
            ext_index = 0

            for kw in search_keywords:
                try:
                    results = manager.search(kw, max_results=3)
                    for r in results:
                        title_key = r.title.lower().strip()
                        if title_key and title_key not in seen_titles:
                            seen_titles.add(title_key)
                            ext_index += 1
                            citations.append(CitationRef(
                                key=f"{r.source}-{ext_index}",
                                title=r.title,
                                authors=r.authors,
                                year=r.year,
                                venue=r.venue,
                                doi=r.doi,
                                url=r.url,
                                abstract=r.abstract[:300],
                                source=r.source,
                            ))
                except Exception as e:
                    logger.warning(f"External search failed for '{kw}': {e}")

            manager.close()
            if ext_index > 0:
                logger.info(f"Added {ext_index} citations from external search")

        except Exception as e:
            logger.warning(f"External search initialization failed: {e}")

    def _get_search_keywords(self, project: PaperProject) -> list[str]:
        """用 LLM 推荐搜索关键词."""
        user_content = (
            f"论文主题：{project.topic}\n"
            f"研究问题：{project.research_question}\n"
            f"关键贡献：{', '.join(project.key_contributions)}\n\n"
            f"请推荐搜索关键词，用于在学术数据库中查找相关文献。"
        )

        try:
            result = self._call_llm_json(user_content)
            return result.get("search_keywords", [])
        except Exception as e:
            logger.warning(f"Failed to get search keywords: {e}")
            # Fallback: 用主题和研究问题作为关键词
            fallback = []
            if project.topic:
                fallback.append(project.topic)
            if project.research_question:
                fallback.append(project.research_question)
            return fallback
