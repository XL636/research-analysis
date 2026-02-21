"""Dashboard API routes."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends

from src.api.dependencies import get_knowledge_base
from src.api.schemas import DashboardStats, DocumentSummary, TagCount
from src.store.knowledge_base import KnowledgeBase

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """获取仪表盘 KPI 统计."""
    with kb._connect() as conn:
        # Total documents
        total = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()["cnt"]

        # Recent analyses (last 7 days)
        recent_count = conn.execute(
            """SELECT COUNT(*) as cnt FROM documents
               WHERE created_at >= datetime('now', '-7 days')"""
        ).fetchone()["cnt"]

        # Average relevance score
        avg_score = 0.0
        rows = conn.execute(
            "SELECT analysis_json FROM documents WHERE analysis_json IS NOT NULL"
        ).fetchall()
        scores = []
        for row in rows:
            try:
                data = json.loads(row["analysis_json"])
                score = data.get("relevance_score", 0)
                if score > 0:
                    scores.append(score)
            except (json.JSONDecodeError, TypeError):
                pass
        if scores:
            avg_score = round(sum(scores) / len(scores), 1)

        # Top tags
        tag_rows = conn.execute(
            """SELECT t.name, COUNT(dt.document_id) as count
               FROM tags t
               JOIN document_tags dt ON dt.tag_id = t.id
               GROUP BY t.id
               ORDER BY count DESC
               LIMIT 10"""
        ).fetchall()
        top_tags = [TagCount(name=r["name"], count=r["count"]) for r in tag_rows]

        # Recent documents
        doc_rows = conn.execute(
            """SELECT d.id, d.title, d.file_type, d.created_at,
                      GROUP_CONCAT(t.name, ', ') as tags
               FROM documents d
               LEFT JOIN document_tags dt ON dt.document_id = d.id
               LEFT JOIN tags t ON t.id = dt.tag_id
               GROUP BY d.id
               ORDER BY d.created_at DESC
               LIMIT 10"""
        ).fetchall()
        recent_docs = [
            DocumentSummary(
                id=r["id"],
                title=r["title"],
                file_type=r["file_type"] or "",
                tags=r["tags"] or "",
                date=r["created_at"] or "",
            )
            for r in doc_rows
        ]

    return DashboardStats(
        total_documents=total,
        recent_analyses=recent_count,
        avg_score=avg_score,
        top_tags=top_tags,
        recent_documents=recent_docs,
    )
