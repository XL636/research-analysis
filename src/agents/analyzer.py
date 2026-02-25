"""分析 Agent - 对单篇文档进行深度分析."""

from __future__ import annotations


from loguru import logger

from src.agents.base import BaseAgent
from src.core.models import (
    AnalysisResult,
    KeyFinding,
    MethodologyAssessment,
    ParsedDocument,
)


class AnalyzerAgent(BaseAgent):
    """分析 Agent：深度分析单篇文档，输出 AnalysisResult."""

    agent_type = "analyzer"

    def __init__(self, *args, max_text_length: int = 8000, **kwargs):
        super().__init__(*args, **kwargs)
        self._max_text_length = max_text_length

    def _default_system_prompt(self) -> str:
        return """你是一位资深的学术论文分析专家。你的任务是对学术论文或研究材料进行深度分析。

请从以下维度进行分析：
1. **摘要总结**：用 2-3 段话概括论文的核心内容
2. **关键发现**：列出 3-5 个最重要的发现，每个发现包含证据和重要性说明
3. **方法论评估**：描述研究方法，指出优势和局限
4. **主要贡献**：列出论文对领域的贡献
5. **局限性**：指出研究的不足
6. **未来方向**：可能的后续研究方向
7. **标签**：3-5 个关键词标签
8. **相关度评分**：1-10 分，评估研究的创新性和重要性

请以 JSON 格式回答，结构如下：
{
  "summary": "...",
  "key_findings": [{"finding": "...", "evidence": "...", "significance": "..."}],
  "methodology": {"approach": "...", "strengths": ["..."], "limitations": ["..."]},
  "contributions": ["..."],
  "limitations": ["..."],
  "future_work": ["..."],
  "tags": ["..."],
  "relevance_score": 8.0
}"""

    def process(self, input_data: ParsedDocument) -> AnalysisResult:
        """分析单篇文档.

        Args:
            input_data: 解析后的文档

        Returns:
            深度分析结果
        """
        logger.info(f"Analyzing: {input_data.title or input_data.file_path}")

        # 构建用户消息
        user_content = f"""请分析以下研究材料：

标题：{input_data.title}
作者：{', '.join(input_data.authors) if input_data.authors else '未知'}

摘要：
{input_data.abstract or '无'}

正文：
{input_data.full_text[:self._max_text_length]}"""  # 限制长度避免超出上下文

        result = self._call_llm_json(user_content)

        return AnalysisResult(
            document_title=input_data.title or input_data.file_path,
            summary=result.get("summary", ""),
            key_findings=[
                KeyFinding(**kf) for kf in result.get("key_findings", [])
            ],
            methodology=MethodologyAssessment(**result.get("methodology", {})),
            contributions=result.get("contributions", []),
            limitations=result.get("limitations", []),
            future_work=result.get("future_work", []),
            tags=result.get("tags", []),
            relevance_score=float(result.get("relevance_score", 0)),
        )
