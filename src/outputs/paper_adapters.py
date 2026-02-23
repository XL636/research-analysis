"""论文输出适配器 - PaperDraft 转换为 Report，复用已有输出模块."""

from __future__ import annotations

from src.core.models import Report
from src.core.paper_models import PaperDraft


def draft_to_report(draft: PaperDraft) -> Report:
    """将 PaperDraft 转为 Report，以复用 write_markdown/write_docx/write_pdf.

    Args:
        draft: 论文草稿

    Returns:
        Report 对象
    """
    return Report(
        title=draft.title,
        content=draft.full_content,
        source_files=[],
    )
