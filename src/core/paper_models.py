"""论文写作数据模型 - 交互式论文写作的 Pydantic 结构."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, computed_field


class PaperLanguage(str, Enum):
    """论文语言."""

    ZH = "zh"
    EN = "en"


class PaperVenue(str, Enum):
    """目标会议/期刊."""

    GENERIC = "generic"
    NEURIPS = "neurips"
    ICML = "icml"
    ICLR = "iclr"
    ACL = "acl"
    AAAI = "aaai"
    COLM = "colm"
    CHINESE_JOURNAL = "chinese_journal"


class ProjectStatus(str, Enum):
    """论文项目状态."""

    CREATED = "created"
    OUTLINE_DRAFT = "outline_draft"
    OUTLINE_CONFIRMED = "outline_confirmed"
    WRITING = "writing"
    DRAFT_COMPLETE = "draft_complete"
    POLISHING = "polishing"
    FINISHED = "finished"


class SectionStatus(str, Enum):
    """章节写作状态."""

    PENDING = "pending"
    WRITING = "writing"
    DRAFT = "draft"
    REVISING = "revising"
    DONE = "done"


class CitationRef(BaseModel):
    """引用文献."""

    key: str = ""
    title: str = ""
    authors: str = ""
    year: str = ""
    venue: str = ""
    doi: str = ""
    url: str = ""
    abstract: str = ""
    source: str = "manual"  # "knowledge_base" | "semantic_scholar" | "manual"


class PaperSection(BaseModel):
    """论文章节."""

    id: str = ""
    title: str = ""
    level: int = 1
    outline_points: list[str] = Field(default_factory=list)
    content: str = ""
    word_count: int = 0
    status: SectionStatus = SectionStatus.PENDING
    citations: list[str] = Field(default_factory=list)
    revision_history: list[str] = Field(default_factory=list)


class PaperOutline(BaseModel):
    """论文大纲."""

    abstract_draft: str = ""
    sections: list[PaperSection] = Field(default_factory=list)
    estimated_word_count: int = 0
    revision_notes: list[str] = Field(default_factory=list)


class PaperDraft(BaseModel):
    """论文草稿."""

    title: str = ""
    abstract: str = ""
    sections: list[PaperSection] = Field(default_factory=list)
    citations: list[CitationRef] = Field(default_factory=list)
    acknowledgments: str = ""

    @computed_field
    @property
    def full_content(self) -> str:
        """拼接完整 Markdown 内容."""
        parts = []
        if self.title:
            parts.append(f"# {self.title}")
        if self.abstract:
            parts.append(f"\n## Abstract\n\n{self.abstract}")
        for section in self.sections:
            prefix = "#" * (section.level + 1)
            parts.append(f"\n{prefix} {section.title}")
            if section.content:
                parts.append(f"\n{section.content}")
        if self.acknowledgments:
            parts.append(f"\n## Acknowledgments\n\n{self.acknowledgments}")
        if self.citations:
            parts.append("\n## References\n")
            for i, ref in enumerate(self.citations, 1):
                entry = f"[{i}] {ref.authors}. {ref.title}."
                if ref.venue:
                    entry += f" {ref.venue},"
                if ref.year:
                    entry += f" {ref.year}."
                parts.append(entry)
        return "\n".join(parts)

    @computed_field
    @property
    def total_word_count(self) -> int:
        """统计总字数."""
        return sum(s.word_count for s in self.sections)


def _gen_id() -> str:
    return uuid.uuid4().hex[:12]


class PaperProject(BaseModel):
    """论文项目 - 顶层状态容器."""

    id: str = Field(default_factory=_gen_id)
    name: str = ""
    language: PaperLanguage = PaperLanguage.ZH
    venue: PaperVenue = PaperVenue.GENERIC
    status: ProjectStatus = ProjectStatus.CREATED

    # 用户输入
    topic: str = ""
    research_question: str = ""
    key_contributions: list[str] = Field(default_factory=list)
    target_word_count: int = 8000
    reference_doc_ids: list[int] = Field(default_factory=list)
    additional_context: str = ""

    # 生成物
    outline: PaperOutline | None = None
    draft: PaperDraft | None = None
    citations: list[CitationRef] = Field(default_factory=list)

    created_at: str = ""
    updated_at: str = ""
