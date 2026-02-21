"""综合 Agent - 跨文档对比和主题归纳."""

from __future__ import annotations


from loguru import logger

from src.agents.base import BaseAgent
from src.core.models import AnalysisResult, SynthesisResult, ThemeComparison


class SynthesizerAgent(BaseAgent):
    """综合 Agent：对多篇文档进行跨文档对比和主题归纳."""

    agent_type = "synthesizer"

    def _default_system_prompt(self) -> str:
        return """你是一位跨学科研究综合分析专家。你的任务是对多篇研究材料进行跨文档对比和主题归纳。

请从以下维度进行综合分析：
1. **总体概述**：概括所有文档的研究主题和方向
2. **共同主题**：找出各文档共同关注的研究主题
3. **主要差异**：分析各文档在方法、观点、结论上的差异
4. **主题对比**：对每个重要主题，对比各文档的不同观点
5. **研究空白**：识别现有研究未覆盖的领域
6. **建议**：对后续研究方向的建议

请以 JSON 格式回答，结构如下：
{
  "overall_summary": "...",
  "common_themes": ["..."],
  "key_differences": ["..."],
  "theme_comparisons": [{"theme": "...", "perspectives": {"文档A": "...", "文档B": "..."}}],
  "research_gaps": ["..."],
  "recommendations": ["..."]
}"""

    def _format_analysis(self, analysis: AnalysisResult) -> str:
        """将单篇分析格式化为输入文本."""
        parts = [f"### {analysis.document_title}"]
        parts.append(f"摘要：{analysis.summary}")
        if analysis.key_findings:
            parts.append("关键发现：")
            for kf in analysis.key_findings:
                parts.append(f"  - {kf.finding}")
        if analysis.methodology.approach:
            parts.append(f"研究方法：{analysis.methodology.approach}")
        if analysis.contributions:
            parts.append("贡献：" + "；".join(analysis.contributions))
        if analysis.tags:
            parts.append(f"标签：{', '.join(analysis.tags)}")
        return "\n".join(parts)

    def process(self, input_data: list[AnalysisResult]) -> SynthesisResult:
        """跨文档综合分析.

        Args:
            input_data: 多篇文档的分析结果

        Returns:
            综合分析结果
        """
        if len(input_data) < 2:
            raise ValueError("综合分析至少需要 2 篇文档的分析结果")

        logger.info(f"Synthesizing {len(input_data)} documents")

        # 构建用户消息
        doc_summaries = [self._format_analysis(a) for a in input_data]
        user_content = f"""请对以下 {len(input_data)} 篇研究材料进行跨文档综合分析：

{chr(10).join(doc_summaries)}"""

        result = self._call_llm_json(user_content)

        # 解析主题对比
        theme_comparisons = []
        for tc in result.get("theme_comparisons", []):
            theme_comparisons.append(ThemeComparison(
                theme=tc.get("theme", ""),
                perspectives=tc.get("perspectives", {}),
            ))

        return SynthesisResult(
            overall_summary=result.get("overall_summary", ""),
            common_themes=result.get("common_themes", []),
            key_differences=result.get("key_differences", []),
            theme_comparisons=theme_comparisons,
            research_gaps=result.get("research_gaps", []),
            recommendations=result.get("recommendations", []),
            source_analyses=input_data,
        )
