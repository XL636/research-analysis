"""PolishAgent - 论文全文润色."""

from __future__ import annotations

from typing import Any

from loguru import logger

from src.agents.base import BaseAgent
from src.core.paper_models import PaperDraft, PaperSection, SectionStatus


class PolishAgent(BaseAgent):
    """全文润色 Agent."""

    agent_type = "polish"

    def _default_system_prompt(self) -> str:
        return "You are a senior academic paper polishing expert. Output JSON only."

    def process(self, input_data: Any) -> PaperDraft:
        """润色完整论文.

        Args:
            input_data: dict with keys:
                - draft: PaperDraft
                - language: str
                - venue: str
                - polish_instructions: str (optional)
        """
        draft: PaperDraft = input_data["draft"]
        language = input_data.get("language", "zh")
        venue = input_data.get("venue", "generic")
        instructions = input_data.get("polish_instructions", "")

        lang_label = "中文" if language == "zh" else "English"

        parts = [
            f"请润色以下论文：",
            f"\n## 论文信息",
            f"- 语言：{lang_label}",
            f"- 会议风格：{venue}",
            f"\n## 论文内容\n\n{draft.full_content}",
        ]

        if instructions:
            parts.append(f"\n## 特别要求\n{instructions}")

        parts.append("\n请返回润色后的完整论文（JSON 格式），包含 title, abstract, sections, acknowledgments。")

        user_content = "\n".join(parts)
        result = self._call_llm_json(user_content)
        return self._parse_draft(result, draft)

    @staticmethod
    def _parse_draft(data: dict, original: PaperDraft) -> PaperDraft:
        """解析 LLM 返回的润色结果."""
        sections = []
        for s_data in data.get("sections", []):
            content = s_data.get("content", "")
            word_count = len(content) if any("\u4e00" <= c <= "\u9fff" for c in content) else len(content.split())

            # 尝试匹配原始章节
            section_id = s_data.get("id", "")
            original_section = None
            for os in original.sections:
                if os.id == section_id:
                    original_section = os
                    break

            sections.append(PaperSection(
                id=section_id or (original_section.id if original_section else ""),
                title=s_data.get("title", ""),
                level=s_data.get("level", original_section.level if original_section else 1),
                outline_points=original_section.outline_points if original_section else [],
                content=content,
                word_count=word_count,
                status=SectionStatus.DONE,
                citations=s_data.get("citations", original_section.citations if original_section else []),
                revision_history=(original_section.revision_history if original_section else []) + ["polished"],
            ))

        return PaperDraft(
            title=data.get("title", original.title),
            abstract=data.get("abstract", original.abstract),
            sections=sections,
            citations=original.citations,
            acknowledgments=data.get("acknowledgments", original.acknowledgments),
        )
