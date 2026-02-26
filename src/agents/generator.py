"""生成 Agent - 按模板生成 Markdown 报告."""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from src.agents.base import BaseAgent
from src.core.models import (
    AnalysisResult,
    Report,
    ReviewFeedback,
    SynthesisResult,
)

# 可用模板：名称 -> prompt 文件路径
TEMPLATES: dict[str, str] = {
    "default": "config/prompts/generator_system.txt",
    "meeting": "config/prompts/meeting_report.txt",
}


class GeneratorAgent(BaseAgent):
    """生成 Agent：根据分析结果生成格式化报告."""

    agent_type = "generator"

    def __init__(self, *args, template: str = "default", template_content: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._template = template
        self._template_content = template_content

    @property
    def system_prompt(self) -> str:
        """根据模板选择加载对应的 Prompt.

        优先级：prompt_override > template_content > TEMPLATES > default.
        """
        if self._system_prompt is None:
            # 1. 优先使用 prompt_override（来自分析模式配置）
            if self._prompt_override:
                override_path = Path(self._prompt_override)
                if override_path.exists():
                    self._system_prompt = override_path.read_text(encoding="utf-8")
            # 2. 其次使用 template_content（来自数据库自定义模板）
            if self._system_prompt is None and self._template_content:
                self._system_prompt = self._template_content
            # 3. 使用 TEMPLATES 字典（来自 --template 参数 / 文件系统内置）
            if self._system_prompt is None:
                template_path = TEMPLATES.get(self._template)
                if template_path and Path(template_path).exists():
                    self._system_prompt = Path(template_path).read_text(encoding="utf-8")
                else:
                    # fallback: 尝试默认路径
                    prompt_path = Path(f"config/prompts/{self.agent_type}_system.txt")
                    if prompt_path.exists():
                        self._system_prompt = prompt_path.read_text(encoding="utf-8")
                    else:
                        self._system_prompt = self._default_system_prompt()
        return self._system_prompt

    def _default_system_prompt(self) -> str:
        return """你是一位专业的学术报告撰写专家。你的任务是根据文档分析结果，生成结构清晰、内容丰富的组会报告。

报告要求：
1. 使用 Markdown 格式
2. 结构清晰，包含标题、摘要、关键发现、方法论评价、讨论等章节
3. 语言专业但易读
4. 每个关键发现都要有简要说明
5. 在末尾提供总结和建议

如果收到评审反馈，请根据反馈意见改进报告。"""

    def _build_analysis_summary(self, analysis: AnalysisResult) -> str:
        """将分析结果格式化为文本摘要."""
        parts = [f"## 文档：{analysis.document_title}\n"]
        parts.append(f"**摘要**：{analysis.summary}\n")

        if analysis.key_findings:
            parts.append("**关键发现**：")
            for i, kf in enumerate(analysis.key_findings, 1):
                parts.append(f"  {i}. {kf.finding}")
                if kf.evidence:
                    parts.append(f"     证据：{kf.evidence}")

        if analysis.methodology.approach:
            parts.append(f"\n**研究方法**：{analysis.methodology.approach}")

        if analysis.contributions:
            parts.append("\n**主要贡献**：")
            for c in analysis.contributions:
                parts.append(f"  - {c}")

        if analysis.limitations:
            parts.append("\n**局限性**：")
            for lim in analysis.limitations:
                parts.append(f"  - {lim}")

        parts.append(f"\n**相关度评分**：{analysis.relevance_score}/10")
        parts.append(f"**标签**：{', '.join(analysis.tags)}")

        return "\n".join(parts)

    def process(
        self,
        input_data: list[AnalysisResult] | SynthesisResult,
        feedback: ReviewFeedback | None = None,
    ) -> Report:
        """生成报告.

        Args:
            input_data: 分析结果列表或综合分析结果
            feedback: 评审反馈（可选，用于改进报告）

        Returns:
            生成的报告
        """
        # 构建输入摘要
        if isinstance(input_data, SynthesisResult):
            user_content = self._build_synthesis_content(input_data)
            source_files = [a.document_title for a in input_data.source_analyses]
            title = "综合分析报告"
        else:
            analyses = input_data
            summaries = [self._build_analysis_summary(a) for a in analyses]
            user_content = "请根据以下分析结果生成组会报告：\n\n" + "\n\n---\n\n".join(summaries)
            source_files = [a.document_title for a in analyses]
            title = analyses[0].document_title if len(analyses) == 1 else "多文档分析报告"

        if feedback and not feedback.approved:
            user_content += "\n\n---\n\n**评审反馈（请根据以下意见改进报告）**：\n"
            if feedback.issues:
                user_content += "问题：\n" + "\n".join(f"- {i}" for i in feedback.issues)
            if feedback.suggestions:
                user_content += "\n建议：\n" + "\n".join(f"- {s}" for s in feedback.suggestions)

        logger.info(f"Generating report: {title}")
        content = self._call_llm(user_content, max_tokens=16384)

        return Report(
            title=title,
            content=content,
            source_files=source_files,
        )

    def _build_synthesis_content(self, synthesis: SynthesisResult) -> str:
        """将综合分析结果格式化为文本."""
        parts = ["请根据以下跨文档综合分析结果生成组会报告：\n"]
        parts.append(f"**总体概述**：{synthesis.overall_summary}\n")

        if synthesis.common_themes:
            parts.append("**共同主题**：")
            for t in synthesis.common_themes:
                parts.append(f"  - {t}")

        if synthesis.key_differences:
            parts.append("\n**主要差异**：")
            for d in synthesis.key_differences:
                parts.append(f"  - {d}")

        if synthesis.research_gaps:
            parts.append("\n**研究空白**：")
            for g in synthesis.research_gaps:
                parts.append(f"  - {g}")

        if synthesis.recommendations:
            parts.append("\n**建议**：")
            for r in synthesis.recommendations:
                parts.append(f"  - {r}")

        # 附加各文档的分析摘要
        for analysis in synthesis.source_analyses:
            parts.append(f"\n---\n{self._build_analysis_summary(analysis)}")

        return "\n".join(parts)
