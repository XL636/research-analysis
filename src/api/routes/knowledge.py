"""Knowledge Base API routes."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from src.api.dependencies import get_knowledge_base
from src.api.schemas import (
    DeleteResponse,
    DocumentDetail,
    DocumentSummary,
    DuplicateCheckResponse,
    SearchResult,
    TagCount,
)
from src.core.models import AnalysisResult, Report
from src.store.knowledge_base import KnowledgeBase

router = APIRouter()


def _analysis_to_report(analysis: AnalysisResult) -> Report:
    """将 AnalysisResult 转换为 Report 对象以复用 writer."""
    sections = []
    sections.append(f"## 摘要\n\n{analysis.summary}")

    if analysis.key_findings:
        items = "\n".join(
            f"- **{kf.finding}**\n  - 证据：{kf.evidence}\n  - 意义：{kf.significance}"
            for kf in analysis.key_findings
        )
        sections.append(f"## 关键发现\n\n{items}")

    if analysis.methodology.approach:
        m = analysis.methodology
        md = f"**方法**：{m.approach}\n\n"
        if m.strengths:
            md += "**优势**：\n" + "\n".join(f"- {s}" for s in m.strengths) + "\n\n"
        if m.limitations:
            md += "**局限**：\n" + "\n".join(f"- {l}" for l in m.limitations)
        sections.append(f"## 研究方法\n\n{md}")

    if analysis.contributions:
        items = "\n".join(f"- {c}" for c in analysis.contributions)
        sections.append(f"## 贡献\n\n{items}")

    if analysis.limitations:
        items = "\n".join(f"- {l}" for l in analysis.limitations)
        sections.append(f"## 局限性\n\n{items}")

    if analysis.future_work:
        items = "\n".join(f"- {fw}" for fw in analysis.future_work)
        sections.append(f"## 未来工作\n\n{items}")

    sections.append(f"## 相关性评分\n\n**{analysis.relevance_score}/10**")

    content = "\n\n".join(sections)

    return Report(
        title=analysis.document_title,
        content=content,
        format="markdown",
    )


@router.get("/search", response_model=list[SearchResult])
async def search_documents(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=100),
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """FTS5 全文搜索知识库."""
    try:
        results = kb.search(q, limit=limit)
    except Exception:
        # FTS5 query syntax error etc.
        return []
    return [SearchResult(**r) for r in results]


@router.get("/documents", response_model=list[DocumentSummary])
async def list_documents(
    tag: str | None = Query(None, description="按标签筛选"),
    limit: int = Query(20, ge=1, le=200),
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """列出知识库文档."""
    docs = kb.list_documents(tag=tag, limit=limit)
    return [DocumentSummary(**d) for d in docs]


# ── check-duplicate 必须在 {doc_id} 之前注册 ──
@router.get("/documents/check-duplicate", response_model=DuplicateCheckResponse)
async def check_duplicate(
    filename: str = Query(..., description="文件名"),
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """检测重复文件名."""
    existing = kb.find_by_filename(filename)
    return DuplicateCheckResponse(
        has_duplicate=len(existing) > 0,
        existing_documents=[DocumentSummary(**d) for d in existing],
    )


@router.get("/documents/{doc_id}", response_model=DocumentDetail)
async def get_document(
    doc_id: int,
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """获取文档详情 + AnalysisResult."""
    # Get basic document info
    with kb._connect() as conn:
        row = conn.execute(
            """SELECT d.id, d.title, d.file_type, d.file_path, d.summary,
                      d.analysis_json,
                      strftime('%Y-%m-%d %H:%M', d.created_at) as created_at,
                      GROUP_CONCAT(t.name, ', ') as tags
               FROM documents d
               LEFT JOIN document_tags dt ON dt.document_id = d.id
               LEFT JOIN tags t ON t.id = dt.tag_id
               WHERE d.id = ?
               GROUP BY d.id""",
            (doc_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    analysis = None
    if row["analysis_json"]:
        analysis = json.loads(row["analysis_json"])

    return DocumentDetail(
        id=row["id"],
        title=row["title"],
        file_type=row["file_type"] or "",
        file_path=row["file_path"] or "",
        summary=row["summary"] or "",
        tags=row["tags"] or "",
        date=row["created_at"] or "",
        analysis=analysis,
    )


@router.delete("/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document(
    doc_id: int,
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """删除文档."""
    success = kb.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return DeleteResponse(success=True, message="Document deleted")


@router.get("/documents/{doc_id}/report")
async def download_document_report(
    doc_id: int,
    background_tasks: BackgroundTasks,
    format: str = Query("markdown", regex="^(markdown|docx|pptx)$"),
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """下载文档分析报告（支持 markdown / docx / pptx）."""
    analysis = kb.get_analysis(doc_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    report = _analysis_to_report(analysis)
    tmp_dir = tempfile.mkdtemp()

    ext_map = {"markdown": ".md", "docx": ".docx", "pptx": ".pptx"}
    ext = ext_map[format]
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in report.title)[:60]
    output_path = str(Path(tmp_dir) / f"{safe_title}{ext}")

    if format == "markdown":
        from src.outputs.markdown_writer import write_markdown
        write_markdown(report, output_path)
        media_type = "text/markdown"
    elif format == "docx":
        from src.outputs.docx_writer import write_docx
        write_docx(report, output_path)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:  # pptx
        from src.outputs.pptx_writer import write_pptx
        write_pptx(report, output_path)
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    background_tasks.add_task(shutil.rmtree, tmp_dir, True)

    return FileResponse(
        path=output_path,
        filename=f"{safe_title}{ext}",
        media_type=media_type,
    )


@router.get("/tags", response_model=list[TagCount])
async def list_tags(
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """获取标签列表 + 计数."""
    with kb._connect() as conn:
        rows = conn.execute(
            """SELECT t.name, COUNT(dt.document_id) as count
               FROM tags t
               JOIN document_tags dt ON dt.tag_id = t.id
               GROUP BY t.id
               ORDER BY count DESC"""
        ).fetchall()

    return [TagCount(name=row["name"], count=row["count"]) for row in rows]
