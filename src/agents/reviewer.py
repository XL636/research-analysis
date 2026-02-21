"""评审 Agent - 对生成报告做质量检查."""

from __future__ import annotations


from loguru import logger

from src.agents.base import BaseAgent
from src.core.models import Report, ReviewFeedback


class ReviewerAgent(BaseAgent):
    """评审 Agent：检查报告质量，不合格则打回重做."""

    agent_type = "reviewer"

    def _default_system_prompt(self) -> str:
        return """你是一位严格的学术报告评审专家。你的任务是评估组会报告的质量，确保其准确性、完整性和可读性。

请从以下维度评审：
1. **内容完整性**：是否涵盖了所有重要的分析要点
2. **准确性**：分析是否准确，有无事实错误
3. **结构合理性**：报告结构是否清晰，逻辑是否通顺
4. **语言质量**：表达是否专业、简洁、易懂
5. **实用价值**：报告对于组会讨论是否有帮助

评分标准：
- 8-10 分：质量优秀，可以直接使用
- 6-7 分：基本合格，有小问题但不影响使用
- 4-5 分：需要修改，存在明显问题
- 1-3 分：质量不合格，需要重写

请以 JSON 格式回答：
{
  "approved": true/false,
  "overall_score": 8.0,
  "issues": ["问题1", "问题2"],
  "suggestions": ["建议1", "建议2"],
  "details": "详细评审意见..."
}

评分 >= 7 时 approved 为 true，否则为 false。"""

    def process(self, input_data: Report) -> ReviewFeedback:
        """评审报告.

        Args:
            input_data: 待评审的报告

        Returns:
            评审反馈
        """
        logger.info(f"Reviewing report: {input_data.title}")

        user_content = f"""请评审以下组会报告：

标题：{input_data.title}
来源文件：{', '.join(input_data.source_files)}

报告内容：
{input_data.content[:6000]}"""

        result = self._call_llm_json(user_content)

        feedback = ReviewFeedback(
            approved=result.get("approved", False),
            overall_score=float(result.get("overall_score", 0)),
            issues=result.get("issues", []),
            suggestions=result.get("suggestions", []),
            details=result.get("details", ""),
        )

        logger.info(
            f"Review result: {'APPROVED' if feedback.approved else 'REJECTED'} "
            f"(score: {feedback.overall_score})"
        )
        return feedback
