"""Pydantic 数据模型 - Agent 间传递的数据结构."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class FileType(str, Enum):
    PDF = "pdf"
    PPTX = "pptx"
    MARKDOWN = "markdown"
    TXT = "txt"
    DOCX = "docx"
    AUDIO = "audio"


class DocumentSection(BaseModel):
    """文档的一个章节."""

    title: str = ""
    content: str = ""
    level: int = 1  # 标题层级


class ParsedDocument(BaseModel):
    """解析 Agent 输出 - 从原始文件提取的结构化内容."""

    file_path: str
    file_type: FileType
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    abstract: str = ""
    sections: list[DocumentSection] = Field(default_factory=list)
    raw_text: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)
    parsed_at: datetime = Field(default_factory=datetime.now)

    @property
    def full_text(self) -> str:
        """返回完整文本内容."""
        if self.sections:
            parts = []
            if self.title:
                parts.append(f"# {self.title}")
            if self.abstract:
                parts.append(f"\n## Abstract\n{self.abstract}")
            for section in self.sections:
                prefix = "#" * (section.level + 1)
                if section.title:
                    parts.append(f"\n{prefix} {section.title}")
                parts.append(section.content)
            return "\n".join(parts)
        return self.raw_text


class KeyFinding(BaseModel):
    """一个关键发现."""

    finding: str
    evidence: str = ""
    significance: str = ""


class MethodologyAssessment(BaseModel):
    """方法论评估."""

    approach: str = ""
    strengths: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """分析 Agent 输出 - 单篇文档的深度分析."""

    document_title: str
    summary: str = ""
    key_findings: list[KeyFinding] = Field(default_factory=list)
    methodology: MethodologyAssessment = Field(default_factory=MethodologyAssessment)
    contributions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    future_work: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    relevance_score: float = 0.0  # 0-10


class ThemeComparison(BaseModel):
    """主题对比."""

    theme: str
    perspectives: dict[str, str] = Field(default_factory=dict)  # doc_title -> viewpoint


class SynthesisResult(BaseModel):
    """综合 Agent 输出 - 跨文档对比和主题归纳."""

    overall_summary: str = ""
    common_themes: list[str] = Field(default_factory=list)
    key_differences: list[str] = Field(default_factory=list)
    theme_comparisons: list[ThemeComparison] = Field(default_factory=list)
    research_gaps: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    source_analyses: list[AnalysisResult] = Field(default_factory=list)


class Report(BaseModel):
    """生成 Agent 输出 - 最终报告."""

    title: str
    content: str  # Markdown 格式的报告正文
    format: str = "markdown"
    generated_at: datetime = Field(default_factory=datetime.now)
    source_files: list[str] = Field(default_factory=list)


class ReviewFeedback(BaseModel):
    """评审 Agent 输出 - 质量反馈."""

    approved: bool = False
    overall_score: float = 0.0  # 0-10
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    details: str = ""


class PipelineContext(BaseModel):
    """Pipeline 执行上下文 - 贯穿整个工作流."""

    input_files: list[str] = Field(default_factory=list)
    parsed_documents: list[ParsedDocument] = Field(default_factory=list)
    analyses: list[AnalysisResult] = Field(default_factory=list)
    synthesis: SynthesisResult | None = None
    report: Report | None = None
    review: ReviewFeedback | None = None
    output_path: str = ""
    output_format: str = "markdown"
