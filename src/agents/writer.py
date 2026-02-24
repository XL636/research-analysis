"""WriterAgent - 论文逐章节写作与修改."""

from __future__ import annotations

from typing import Any

from loguru import logger

from src.agents.base import BaseAgent
from src.core.paper_models import PaperSection, SectionStatus


class WriterAgent(BaseAgent):
    """章节写作 Agent."""

    agent_type = "writer"

    def _default_system_prompt(self) -> str:
        return "You are a professional academic paper writing assistant. Output JSON only."

    def process(self, input_data: Any) -> PaperSection:
        """写作单个章节.

        Args:
            input_data: dict with keys:
                - section: PaperSection (大纲)
                - project_context: str (前文摘要)
                - citations: list[CitationRef]
                - language: str
                - venue: str
        """
        section = input_data["section"]
        project_context = input_data.get("project_context", "")
        citations = input_data.get("citations", [])
        language = input_data.get("language", "zh")
        venue = input_data.get("venue", "generic")

        lang_label = "中文" if language == "zh" else "English"

        parts = [
            f"请撰写论文的以下章节：",
            f"\n## 章节信息",
            f"- 标题：{section.title}",
            f"- 层级：{section.level}",
            f"- 目标字数：{section.word_count}",
            f"- 语言：{lang_label}",
            f"- 会议风格：{venue}",
            f"\n## 大纲要点",
        ]
        for point in section.outline_points:
            parts.append(f"- {point}")

        if project_context:
            parts.append(f"\n## 前文摘要（保持连贯）\n{project_context}")

        if citations:
            parts.append("\n## 可用引用")
            for ref in citations[:20]:
                parts.append(f"\n### [{ref.key}] {ref.title} ({ref.year})")
                if ref.has_full_analysis:
                    if ref.summary:
                        parts.append(f"摘要：{ref.summary[:200]}")
                    if ref.key_findings_text:
                        parts.append(f"关键发现：{ref.key_findings_text[:300]}")
                    if ref.methodology_text:
                        parts.append(f"方法：{ref.methodology_text[:200]}")
                elif ref.abstract:
                    parts.append(f"摘要：{ref.abstract[:200]}")

        user_content = "\n".join(parts)
        result = self._call_llm_json(user_content, max_tokens=16384)
        return self._parse_section(result, section)

    def revise(self, section: PaperSection, feedback: str, project_context: str = "") -> PaperSection:
        """根据反馈修改章节."""
        parts = [
            f"请根据反馈修改以下论文章节：",
            f"\n## 当前内容\n标题：{section.title}\n\n{section.content}",
            f"\n## 修改要求\n{feedback}",
        ]
        if project_context:
            parts.append(f"\n## 前文摘要\n{project_context}")

        parts.append("\n请返回完整的修改后章节（JSON 格式），包含所有字段。")

        user_content = "\n".join(parts)
        result = self._call_llm_json(user_content, max_tokens=16384)
        revised = self._parse_section(result, section)
        revised.revision_history = section.revision_history + [f"Revised: {feedback[:100]}"]
        revised.status = SectionStatus.DRAFT
        return revised

    @staticmethod
    def _parse_section(data: dict, original: PaperSection) -> PaperSection:
        """解析 LLM 返回的章节 JSON."""
        content = data.get("content", "")
        # 计算字数（中文按字符，英文按空格分词）
        word_count = len(content) if any("\u4e00" <= c <= "\u9fff" for c in content) else len(content.split())

        return PaperSection(
            id=original.id,
            title=data.get("title", original.title),
            level=original.level,
            outline_points=original.outline_points,
            content=content,
            word_count=word_count,
            status=SectionStatus.DRAFT,
            citations=data.get("citations", original.citations),
            revision_history=original.revision_history,
        )
