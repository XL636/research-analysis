"""OutlineAgent - 论文大纲生成与修改."""

from __future__ import annotations

from typing import Any

from loguru import logger

from src.agents.base import BaseAgent
from src.core.paper_models import CitationRef, PaperOutline, PaperProject, PaperSection, SectionStatus


class OutlineAgent(BaseAgent):
    """大纲生成 Agent."""

    agent_type = "outline"

    def _default_system_prompt(self) -> str:
        return "You are an academic paper outline design expert. Output JSON only."

    def process(self, input_data: Any) -> PaperOutline:
        """根据项目信息生成大纲.

        Args:
            input_data: PaperProject 实例
        """
        project: PaperProject = input_data
        return self._generate_outline(project)

    def _generate_outline(self, project: PaperProject) -> PaperOutline:
        """生成大纲."""
        lang_label = "中文" if project.language.value == "zh" else "English"
        venue_label = project.venue.value.upper() if project.venue.value != "generic" else "通用"

        parts = [
            f"请为以下论文生成详细大纲：",
            f"\n## 论文信息",
            f"- 标题/名称：{project.name}",
            f"- 主题：{project.topic}",
            f"- 语言：{lang_label}",
            f"- 目标会议/期刊：{venue_label}",
            f"- 目标字数：{project.target_word_count}",
        ]

        if project.research_question:
            parts.append(f"- 研究问题：{project.research_question}")

        if project.key_contributions:
            parts.append("\n## 关键贡献")
            for i, c in enumerate(project.key_contributions, 1):
                parts.append(f"{i}. {c}")

        if project.citations:
            parts.append("\n## 可用参考文献摘要")
            for ref in project.citations[:20]:  # 限制数量避免过长
                parts.append(f"- [{ref.key}] {ref.title} ({ref.year}): {ref.abstract[:200]}")

        if project.additional_context:
            parts.append(f"\n## 补充说明\n{project.additional_context}")

        user_content = "\n".join(parts)
        result = self._call_llm_json(user_content)
        return self._parse_outline(result, project.target_word_count)

    def revise(self, project: PaperProject, feedback: str) -> PaperOutline:
        """根据用户反馈修改大纲."""
        if not project.outline:
            return self._generate_outline(project)

        current = project.outline.model_dump_json(indent=2)

        user_content = (
            f"请根据以下反馈修改论文大纲：\n\n"
            f"## 当前大纲\n```json\n{current}\n```\n\n"
            f"## 用户反馈\n{feedback}\n\n"
            f"请返回完整的修改后大纲（JSON 格式），保持未修改部分不变。"
        )

        result = self._call_llm_json(user_content)
        outline = self._parse_outline(result, project.target_word_count)
        outline.revision_notes.append(f"Revised: {feedback[:100]}")
        return outline

    @staticmethod
    def _parse_outline(data: dict, target_words: int) -> PaperOutline:
        """解析 LLM 返回的大纲 JSON."""
        sections = []
        for s in data.get("sections", []):
            sections.append(PaperSection(
                id=s.get("id", ""),
                title=s.get("title", ""),
                level=s.get("level", 1),
                outline_points=s.get("outline_points", []),
                word_count=s.get("word_count", 0),
                status=SectionStatus.PENDING,
                citations=s.get("citations", []),
            ))

        return PaperOutline(
            abstract_draft=data.get("abstract_draft", ""),
            sections=sections,
            estimated_word_count=data.get("estimated_word_count", target_words),
            revision_notes=data.get("revision_notes", []),
        )
