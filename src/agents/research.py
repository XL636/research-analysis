"""ResearchAgent - 全自动文献调研：搜索 → 筛选 → 下载 → 解析 → 分析 → 入库."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from src.agents.base import BaseAgent
from src.core.paper_models import PaperProject

console = Console()


@dataclass
class ResearchResult:
    """文献调研结果."""

    researched_doc_ids: list[int] = field(default_factory=list)
    downloaded: int = 0
    analyzed: int = 0
    failed: int = 0


class ResearchAgent(BaseAgent):
    """全自动文献调研 Agent."""

    agent_type = "research"

    def _default_system_prompt(self) -> str:
        return "You are an academic literature research assistant. Output JSON only."

    def process(self, input_data: Any) -> ResearchResult:
        """执行全自动文献调研.

        Args:
            input_data: dict with keys:
                - project: PaperProject
                - kb: KnowledgeBase instance
                - max_papers: int (default 10)
                - download_enabled: bool (default True)
        """
        project: PaperProject = input_data["project"]
        kb = input_data["kb"]
        max_papers: int = input_data.get("max_papers", 10)
        download_enabled: bool = input_data.get("download_enabled", True)

        result = ResearchResult()

        # Phase 1: 生成搜索关键词
        console.print("[bold blue]Phase 1:[/] 生成搜索关键词...")
        keywords = self._generate_keywords(project)
        if not keywords:
            logger.warning("No search keywords generated, returning empty result")
            return result
        console.print(f"  生成了 {len(keywords)} 个关键词")

        # Phase 2: 搜索外部 API
        console.print("[bold blue]Phase 2:[/] 搜索学术数据库...")
        candidates = self._search_candidates(keywords)
        if not candidates:
            logger.warning("No candidate papers found from search")
            return result
        console.print(f"  找到 {len(candidates)} 篇候选论文")

        # Phase 3: LLM 筛选
        console.print("[bold blue]Phase 3:[/] 智能筛选最相关论文...")
        selected = self._filter_papers(project, candidates, max_papers)
        console.print(f"  选出 {len(selected)} 篇论文")

        # Phase 4: 下载 + 解析 + 分析
        console.print(f"[bold blue]Phase 4:[/] 处理 {len(selected)} 篇论文...")
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("处理论文", total=len(selected))

            for paper in selected:
                title = paper.get("title", "Unknown")[:60]
                progress.update(task, description=f"处理: {title}...")

                doc_id = self._process_single_paper(
                    paper, kb, download_enabled=download_enabled, result=result
                )
                if doc_id:
                    result.researched_doc_ids.append(doc_id)

                progress.advance(task)

        console.print(
            f"[bold green]调研完成:[/] "
            f"已分析 {result.analyzed} 篇 | "
            f"跳过 {result.failed} 篇"
        )
        return result

    def _generate_keywords(self, project: PaperProject) -> list[str]:
        """Phase 1: 用 LLM 生成搜索关键词."""
        user_content = (
            f"论文主题：{project.topic}\n"
            f"研究问题：{project.research_question}\n"
            f"关键贡献：{', '.join(project.key_contributions)}\n"
            f"目标会议：{project.venue.value}\n\n"
            f"请生成 10-15 个搜索关键词，用于在学术数据库中全面调研相关文献。"
        )

        try:
            result = self._call_llm_json(user_content)
            keywords = result.get("search_keywords", [])
            if not keywords:
                # fallback
                keywords = [project.topic]
                if project.research_question:
                    keywords.append(project.research_question)
            return keywords
        except Exception as e:
            logger.warning(f"Failed to generate keywords: {e}")
            fallback = []
            if project.topic:
                fallback.append(project.topic)
            if project.research_question:
                fallback.append(project.research_question)
            return fallback

    def _search_candidates(self, keywords: list[str]) -> list[dict]:
        """Phase 2: 搜索外部 API 收集候选论文."""
        try:
            from src.core.search_client import SearchManager

            manager = SearchManager()
            if not manager.has_providers:
                logger.warning("No search providers available")
                return []

            all_results: list[dict] = []
            seen_titles: set[str] = set()

            for kw in keywords[:8]:  # 最多搜 8 个关键词
                try:
                    results = manager.search(kw, max_results=5)
                    for r in results:
                        title_key = r.title.lower().strip()
                        if title_key and title_key not in seen_titles:
                            seen_titles.add(title_key)
                            all_results.append({
                                "title": r.title,
                                "authors": r.authors,
                                "year": r.year,
                                "venue": r.venue,
                                "doi": r.doi,
                                "url": r.url,
                                "abstract": r.abstract,
                                "source": r.source,
                            })
                except Exception as e:
                    logger.warning(f"Search failed for keyword '{kw}': {e}")

            manager.close()
            return all_results

        except Exception as e:
            logger.warning(f"Search initialization failed: {e}")
            return []

    def _filter_papers(
        self, project: PaperProject, candidates: list[dict], max_papers: int
    ) -> list[dict]:
        """Phase 3: LLM 筛选最相关的论文."""
        if len(candidates) <= max_papers:
            return candidates

        # 构造候选列表给 LLM
        paper_list_parts = []
        for i, p in enumerate(candidates):
            abstract_preview = (p.get("abstract") or "")[:200]
            paper_list_parts.append(
                f"[{i}] {p['title']} ({p.get('year', '?')})\n"
                f"    摘要：{abstract_preview}"
            )

        user_content = (
            f"论文主题：{project.topic}\n"
            f"研究问题：{project.research_question}\n"
            f"关键贡献：{', '.join(project.key_contributions)}\n\n"
            f"以下是 {len(candidates)} 篇候选论文，请选出最相关的 {max_papers} 篇：\n\n"
            + "\n\n".join(paper_list_parts)
            + "\n\n请返回 JSON，包含 selected_papers 列表，每项有 index 和 relevance_score。"
        )

        try:
            result = self._call_llm_json(user_content)
            selected_indices = []
            for item in result.get("selected_papers", []):
                idx = item.get("index", -1)
                if 0 <= idx < len(candidates):
                    selected_indices.append(idx)

            if selected_indices:
                return [candidates[i] for i in selected_indices[:max_papers]]
        except Exception as e:
            logger.warning(f"LLM filtering failed: {e}")

        # Fallback: 取前 max_papers 个
        return candidates[:max_papers]

    def _process_single_paper(
        self,
        paper: dict,
        kb,
        download_enabled: bool,
        result: ResearchResult,
    ) -> int | None:
        """Phase 4: 处理单篇论文：下载 → 解析 → 分析 → 入库."""
        title = paper.get("title", "Unknown")

        if download_enabled:
            try:
                pdf_path = self._try_download(paper)
                if pdf_path:
                    # 解析 + 分析
                    doc_id = self._parse_and_analyze(pdf_path, kb)
                    if doc_id:
                        result.downloaded += 1
                        result.analyzed += 1
                        return doc_id
            except Exception as e:
                logger.warning(f"Download/analyze failed for '{title}': {e}")

        # 下载失败：跳过，不存元数据
        logger.info(f"Skipping paper (download failed): {title}")
        result.failed += 1
        return None

    def _try_download(self, paper: dict) -> str | None:
        """尝试下载论文 PDF."""
        from src.utils.paper_downloader import PaperDownloader

        downloader = PaperDownloader()
        path = downloader.download(
            url=paper.get("url", ""),
            doi=paper.get("doi", ""),
        )
        return str(path) if path else None

    def _parse_and_analyze(self, pdf_path: str, kb) -> int | None:
        """解析 PDF + 分析 + 存入 KB."""
        from src.parsers.pdf_parser import parse_pdf
        from src.agents.analyzer import AnalyzerAgent
        from src.core.llm_client import LLMClient

        # 解析 PDF
        parsed = parse_pdf(pdf_path)

        # 分析
        llm = LLMClient(self._config_path)
        analyzer = AnalyzerAgent(llm, self._config_path)
        analysis = analyzer.process(parsed)

        # 存入 KB
        doc_id = kb.store_analysis(
            analysis,
            file_path=pdf_path,
            file_type="pdf",
            source_type="auto_research",
            parsed_text=parsed.full_text,
        )
        return doc_id
