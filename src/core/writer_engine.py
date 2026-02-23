"""WriterPipeline - 交互式论文写作状态机引擎."""

from __future__ import annotations

from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.core.llm_client import LLMClient
from src.core.paper_models import (
    PaperDraft,
    PaperLanguage,
    PaperOutline,
    PaperProject,
    PaperSection,
    PaperVenue,
    ProjectStatus,
    SectionStatus,
)
from src.store.paper_store import PaperStore

console = Console()


class WriterPipeline:
    """交互式论文写作管线，每步暂停等待用户确认."""

    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = config_path
        self.llm = LLMClient(config_path)
        self.store = PaperStore()

        from src.agents.citation import CitationAgent
        from src.agents.outline import OutlineAgent
        from src.agents.polish import PolishAgent
        from src.agents.writer import WriterAgent

        self.outline_agent = OutlineAgent(self.llm, config_path)
        self.writer_agent = WriterAgent(self.llm, config_path)
        self.citation_agent = CitationAgent(self.llm, config_path)
        self.polish_agent = PolishAgent(self.llm, config_path)

    def create_project(
        self,
        name: str,
        topic: str = "",
        language: PaperLanguage = PaperLanguage.ZH,
        venue: PaperVenue = PaperVenue.GENERIC,
        research_question: str = "",
        key_contributions: list[str] | None = None,
        target_word_count: int = 8000,
        reference_doc_ids: list[int] | None = None,
        additional_context: str = "",
    ) -> PaperProject:
        """Step 1: 创建论文项目."""
        project = PaperProject(
            name=name,
            topic=topic or name,
            language=language,
            venue=venue,
            research_question=research_question,
            key_contributions=key_contributions or [],
            target_word_count=target_word_count,
            reference_doc_ids=reference_doc_ids or [],
            additional_context=additional_context,
            status=ProjectStatus.CREATED,
        )

        self.store.save(project)
        logger.info(f"Created paper project: {name} (id={project.id})")
        return project

    def generate_outline(self, project: PaperProject) -> PaperProject:
        """Step 2: 收集引用 + 生成大纲 → OUTLINE_DRAFT."""
        # 收集引用
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            task = progress.add_task("收集参考文献...", total=None)
            kb = self._get_kb()
            project.citations = self.citation_agent.process({
                "project": project,
                "kb": kb,
            })
            progress.update(task, description=f"已收集 {len(project.citations)} 篇引用")

        # 生成大纲
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            task = progress.add_task("生成论文大纲...", total=None)
            project.outline = self.outline_agent.process(project)
            progress.update(task, description="大纲生成完成")

        project.status = ProjectStatus.OUTLINE_DRAFT
        self.store.save(project)
        return project

    def revise_outline(self, project: PaperProject, feedback: str) -> PaperProject:
        """Step 3a: 修改大纲（可多次调用）."""
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            progress.add_task("修改大纲...", total=None)
            project.outline = self.outline_agent.revise(project, feedback)

        project.status = ProjectStatus.OUTLINE_DRAFT
        self.store.save(project)
        return project

    def confirm_outline(self, project: PaperProject) -> PaperProject:
        """Step 3b: 确认大纲 → OUTLINE_CONFIRMED，初始化 draft."""
        if not project.outline:
            raise ValueError("No outline to confirm")

        project.status = ProjectStatus.OUTLINE_CONFIRMED

        # 初始化 draft
        project.draft = PaperDraft(
            title=project.name,
            abstract=project.outline.abstract_draft,
            sections=[s.model_copy() for s in project.outline.sections],
            citations=project.citations,
        )

        self.store.save(project)
        return project

    def write_section(self, project: PaperProject, section_id: str) -> PaperProject:
        """Step 4: 写单个章节."""
        if not project.draft:
            raise ValueError("No draft initialized. Confirm outline first.")

        section = self._find_section(project.draft, section_id)
        if not section:
            raise ValueError(f"Section not found: {section_id}")

        project.status = ProjectStatus.WRITING
        section.status = SectionStatus.WRITING
        self.store.save(project)

        context = self._build_writing_context(project, section_id)

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            progress.add_task(f"撰写: {section.title}...", total=None)
            written = self.writer_agent.process({
                "section": section,
                "project_context": context,
                "citations": project.citations,
                "language": project.language.value,
                "venue": project.venue.value,
            })

        # 更新 draft 中对应章节
        self._update_section(project.draft, written)

        # 检查是否所有章节都完成
        if all(s.status in (SectionStatus.DRAFT, SectionStatus.DONE) for s in project.draft.sections):
            project.status = ProjectStatus.DRAFT_COMPLETE

        self.store.save(project)
        return project

    def write_all_sections(self, project: PaperProject) -> PaperProject:
        """Step 4 batch: 按顺序写所有待写章节."""
        if not project.draft:
            raise ValueError("No draft initialized. Confirm outline first.")

        project.status = ProjectStatus.WRITING
        self.store.save(project)

        pending = [s for s in project.draft.sections if s.status == SectionStatus.PENDING]

        for section in pending:
            section.status = SectionStatus.WRITING
            context = self._build_writing_context(project, section.id)

            with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
                progress.add_task(f"撰写: {section.title}...", total=None)
                written = self.writer_agent.process({
                    "section": section,
                    "project_context": context,
                    "citations": project.citations,
                    "language": project.language.value,
                    "venue": project.venue.value,
                })

            self._update_section(project.draft, written)
            self.store.save(project)

        project.status = ProjectStatus.DRAFT_COMPLETE
        self.store.save(project)
        return project

    def revise_section(self, project: PaperProject, section_id: str, feedback: str) -> PaperProject:
        """Step 5: 修改单个章节."""
        if not project.draft:
            raise ValueError("No draft initialized.")

        section = self._find_section(project.draft, section_id)
        if not section:
            raise ValueError(f"Section not found: {section_id}")

        section.status = SectionStatus.REVISING
        context = self._build_writing_context(project, section_id)

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            progress.add_task(f"修改: {section.title}...", total=None)
            revised = self.writer_agent.revise(section, feedback, context)

        self._update_section(project.draft, revised)
        self.store.save(project)
        return project

    def polish(self, project: PaperProject, instructions: str = "") -> PaperProject:
        """Step 6: 全文润色 → FINISHED."""
        if not project.draft:
            raise ValueError("No draft to polish.")

        project.status = ProjectStatus.POLISHING
        self.store.save(project)

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            progress.add_task("全文润色中...", total=None)
            project.draft = self.polish_agent.process({
                "draft": project.draft,
                "language": project.language.value,
                "venue": project.venue.value,
                "polish_instructions": instructions,
            })

        project.status = ProjectStatus.FINISHED
        self.store.save(project)
        return project

    def export(self, project: PaperProject, fmt: str = "markdown", output_path: str = "") -> str:
        """Step 7: 导出论文."""
        if not project.draft:
            raise ValueError("No draft to export.")

        import yaml

        if not output_path:
            with open(self.config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            base_dir = config.get("paper", {}).get("output_dir", "./output/papers")
            output_path = str(Path(base_dir) / project.id)

        if fmt == "latex":
            from src.outputs.latex_writer import write_latex

            return write_latex(project.draft, output_path, project.venue, project.language)

        # markdown / docx / pdf — 通过 Report 适配
        from src.outputs.paper_adapters import draft_to_report

        report = draft_to_report(project.draft)

        if fmt == "docx":
            from src.outputs.docx_writer import write_docx

            if not output_path.endswith(".docx"):
                output_path = str(Path(output_path) / f"{project.name}.docx")
            return write_docx(report, output_path)

        if fmt == "pdf":
            from src.outputs.pdf_writer import write_pdf

            if not output_path.endswith(".pdf"):
                output_path = str(Path(output_path) / f"{project.name}.pdf")
            return write_pdf(report, output_path)

        # 默认 markdown
        from src.outputs.markdown_writer import write_markdown

        if not output_path.endswith(".md"):
            output_path = str(Path(output_path) / f"{project.name}.md")
        return write_markdown(report, output_path)

    # ── 辅助方法 ──

    def _get_kb(self):
        """获取知识库实例（可能失败，不阻断）."""
        try:
            from src.store.knowledge_base import KnowledgeBase

            return KnowledgeBase()
        except Exception as e:
            logger.warning(f"Failed to load KnowledgeBase: {e}")
            return None

    @staticmethod
    def _find_section(draft: PaperDraft, section_id: str) -> PaperSection | None:
        """在 draft 中查找章节."""
        for s in draft.sections:
            if s.id == section_id:
                return s
        return None

    @staticmethod
    def _update_section(draft: PaperDraft, updated: PaperSection) -> None:
        """更新 draft 中对应的章节."""
        for i, s in enumerate(draft.sections):
            if s.id == updated.id:
                draft.sections[i] = updated
                return

    @staticmethod
    def _build_writing_context(project: PaperProject, current_section_id: str) -> str:
        """构建写作上下文：前文摘要 + 大纲 + 论文元信息."""
        if not project.draft:
            return ""

        parts = [
            f"论文标题：{project.name}",
            f"主题：{project.topic}",
            f"研究问题：{project.research_question}",
        ]

        # 前文已写内容的摘要（每章限 500 字）
        prev_content = []
        for s in project.draft.sections:
            if s.id == current_section_id:
                break
            if s.content:
                summary = s.content[:500]
                if len(s.content) > 500:
                    summary += "..."
                prev_content.append(f"[{s.title}]: {summary}")

        if prev_content:
            parts.append("\n前文摘要：")
            parts.extend(prev_content)

        return "\n".join(parts)
