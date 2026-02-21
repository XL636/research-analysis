"""Knowledge Base API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_knowledge_base
from src.api.schemas import DocumentDetail, DocumentSummary, SearchResult, TagCount
from src.store.knowledge_base import KnowledgeBase

router = APIRouter()


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
                      d.analysis_json, d.created_at,
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
        import json
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
