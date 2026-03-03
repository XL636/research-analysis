"""Knowledge Base API routes."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from loguru import logger

from src.api.dependencies import get_knowledge_base
from src.api.schemas import (
    BatchDeleteRequest,
    BatchDeleteResponse,
    CollectionSummary,
    CreateCollectionRequest,
    DeleteResponse,
    DocumentDetail,
    DocumentSummary,
    DuplicateCheckResponse,
    MoveToCollectionRequest,
    RenameCollectionRequest,
    SearchResult,
    TagCount,
    UpdateTitleRequest,
    UpdateTitleResponse,
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
        logger.warning("FTS5 search failed", exc_info=True)
        return []
    return [SearchResult(**r) for r in results]


@router.get("/documents", response_model=list[DocumentSummary])
async def list_documents(
    tag: str | None = Query(None, description="按标签筛选"),
    limit: int = Query(20, ge=1, le=200),
    collection_id: int | None = Query(None, description="按分组筛选"),
    uncategorized: bool = Query(False, description="只显示未分类文档"),
    source_type: str | None = Query(None, description="按来源类型筛选"),
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """列出知识库文档."""
    docs = kb.list_documents(
        tag=tag, limit=limit, collection_id=collection_id,
        uncategorized=uncategorized, source_type=source_type,
    )
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
                      d.analysis_json, d.report_content, d.parsed_text, d.collection_id,
                      d.source_type,
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

    report_content = row["report_content"] or None

    # 存量数据懒生成 report_content
    if not report_content and analysis and not analysis.get("metadata_only"):
        try:
            ar = AnalysisResult.model_validate(analysis)
            report = _analysis_to_report(ar)
            if report.content:
                kb.update_report_content(doc_id, report.content)
                report_content = report.content
        except Exception:
            pass

    return DocumentDetail(
        id=row["id"],
        title=row["title"],
        file_type=row["file_type"] or "",
        file_path=row["file_path"] or "",
        summary=row["summary"] or "",
        tags=row["tags"] or "",
        date=row["created_at"] or "",
        analysis=analysis,
        collection_id=row["collection_id"],
        report_content=report_content,
        parsed_text=row["parsed_text"] or None,
        source_type=row["source_type"] or "user_upload",
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


@router.post("/documents/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_documents(
    body: BatchDeleteRequest,
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """批量删除文档."""
    deleted = kb.delete_documents(body.ids)
    return BatchDeleteResponse(success=True, deleted_count=deleted)


@router.patch("/documents/{doc_id}/title", response_model=UpdateTitleResponse)
async def update_document_title(
    doc_id: int,
    body: UpdateTitleRequest,
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """更新文档标题."""
    success = kb.update_title(doc_id, body.title)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return UpdateTitleResponse(success=True, title=body.title)


@router.patch("/documents/{doc_id}/collection", response_model=DeleteResponse)
async def move_document_to_collection(
    doc_id: int,
    body: MoveToCollectionRequest,
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """移动文档到分组."""
    success = kb.move_document_to_collection(doc_id, body.collection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document or collection not found")
    return DeleteResponse(success=True, message="Document moved")


@router.get("/collections", response_model=list[CollectionSummary])
async def list_collections(
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """列出分组."""
    return [CollectionSummary(**c) for c in kb.list_collections()]


@router.post("/collections", response_model=CollectionSummary)
async def create_collection(
    body: CreateCollectionRequest,
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """新建分组."""
    coll_id = kb.create_collection(body.name)
    return CollectionSummary(id=coll_id, name=body.name, document_count=0)


@router.patch("/collections/{collection_id}", response_model=DeleteResponse)
async def rename_collection(
    collection_id: int,
    body: RenameCollectionRequest,
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """重命名分组."""
    success = kb.rename_collection(collection_id, body.name)
    if not success:
        raise HTTPException(status_code=404, detail="Collection not found")
    return DeleteResponse(success=True, message="Collection renamed")


@router.delete("/collections/{collection_id}", response_model=DeleteResponse)
async def delete_collection(
    collection_id: int,
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """删除分组."""
    success = kb.delete_collection(collection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Collection not found")
    return DeleteResponse(success=True, message="Collection deleted")


@router.get("/documents/{doc_id}/report")
async def download_document_report(
    doc_id: int,
    background_tasks: BackgroundTasks,
    format: str = Query("markdown", pattern="^(markdown|docx|pptx|pdf)$"),
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """下载文档分析报告（支持 markdown / docx / pptx）."""
    # 优先使用存储的完整报告
    stored_content = kb.get_report_content(doc_id)
    analysis = kb.get_analysis(doc_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if stored_content:
        report = Report(
            title=analysis.document_title,
            content=stored_content,
            format="markdown",
        )
    else:
        report = _analysis_to_report(analysis)
    tmp_dir = tempfile.mkdtemp()

    ext_map = {"markdown": ".md", "docx": ".docx", "pptx": ".pptx", "pdf": ".pdf"}
    ext = ext_map[format]
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in report.title)[:60]
    output_path = str(Path(tmp_dir) / f"{safe_title}{ext}")

    try:
        if format == "markdown":
            from src.outputs.markdown_writer import write_markdown
            write_markdown(report, output_path)
            media_type = "text/markdown"
        elif format == "docx":
            from src.outputs.docx_writer import write_docx
            write_docx(report, output_path)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif format == "pptx":
            from src.outputs.pptx_writer import write_pptx
            write_pptx(report, output_path)
            media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        else:  # pdf
            from src.outputs.pdf_writer import write_pdf
            write_pdf(report, output_path)
            media_type = "application/pdf"
    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise

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
