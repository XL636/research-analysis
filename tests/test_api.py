"""Tests for FastAPI API routes."""

from __future__ import annotations

import os

import pytest
import httpx

from src.api.app import create_app
from src.api.dependencies import get_knowledge_base
from src.core.models import AnalysisResult, KeyFinding
from src.store.knowledge_base import KnowledgeBase

pytestmark = pytest.mark.anyio


@pytest.fixture
def temp_kb(tmp_path):
    """Create a temporary KnowledgeBase backed by a temp SQLite DB."""
    db_path = str(tmp_path / "test.db")
    return KnowledgeBase(db_path=db_path)


@pytest.fixture
async def client(temp_kb, tmp_path):
    """Create an httpx async test client with the temp KnowledgeBase injected.

    We change the working directory to a temp dir so that ``create_app()``
    does not detect ``web/dist`` and register the SPA catch-all route that
    would shadow ``/api/health``.
    """
    original_cwd = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        app = create_app()
        app.dependency_overrides[get_knowledge_base] = lambda: temp_kb
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c
    finally:
        os.chdir(original_cwd)


def _make_analysis(
    title: str = "Test Paper",
    summary: str = "A test summary",
    tags: list[str] | None = None,
    relevance_score: float = 7.5,
) -> AnalysisResult:
    """Helper to build an AnalysisResult for testing."""
    return AnalysisResult(
        document_title=title,
        summary=summary,
        key_findings=[
            KeyFinding(
                finding="Key finding one",
                evidence="Some evidence",
                significance="High",
            )
        ],
        contributions=["Contribution A"],
        tags=tags or ["deep-learning", "nlp"],
        relevance_score=relevance_score,
    )


# ── 1. Health endpoint ──────────────────────────────────────────────


async def test_health(client: httpx.AsyncClient):
    """GET /api/health returns {"status": "ok"}."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ── 2. Dashboard stats ──────────────────────────────────────────────


async def test_dashboard_stats_empty(client: httpx.AsyncClient):
    """Empty DB yields total_documents=0."""
    resp = await client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_documents"] == 0
    assert data["recent_analyses"] == 0
    assert data["avg_score"] == 0.0
    assert data["top_tags"] == []
    assert data["recent_documents"] == []


async def test_dashboard_stats_with_data(
    client: httpx.AsyncClient, temp_kb: KnowledgeBase
):
    """After inserting data the dashboard reflects it."""
    analysis = _make_analysis()
    temp_kb.store_analysis(analysis, file_path="test.pdf", file_type="pdf")

    resp = await client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_documents"] == 1
    assert data["recent_analyses"] == 1
    assert data["avg_score"] == 7.5
    assert len(data["top_tags"]) == 2
    assert len(data["recent_documents"]) == 1
    assert data["recent_documents"][0]["title"] == "Test Paper"


# ── 3. Knowledge Base endpoints ─────────────────────────────────────


async def test_knowledge_documents_empty(client: httpx.AsyncClient):
    """Empty KB returns an empty document list."""
    resp = await client.get("/api/knowledge/documents")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_knowledge_documents_list(
    client: httpx.AsyncClient, temp_kb: KnowledgeBase
):
    """After storing an analysis, the document list contains it."""
    analysis = _make_analysis(title="Stored Paper")
    temp_kb.store_analysis(analysis, file_path="paper.pdf", file_type="pdf")

    resp = await client.get("/api/knowledge/documents")
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 1
    assert docs[0]["title"] == "Stored Paper"


async def test_knowledge_document_detail(
    client: httpx.AsyncClient, temp_kb: KnowledgeBase
):
    """GET /api/knowledge/documents/{id} returns detail with analysis."""
    analysis = _make_analysis(title="Detail Paper", summary="Detailed summary")
    doc_id = temp_kb.store_analysis(
        analysis, file_path="detail.pdf", file_type="pdf"
    )

    resp = await client.get(f"/api/knowledge/documents/{doc_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == doc_id
    assert data["title"] == "Detail Paper"
    assert data["summary"] == "Detailed summary"
    assert data["analysis"] is not None
    assert data["analysis"]["document_title"] == "Detail Paper"


async def test_knowledge_document_not_found(client: httpx.AsyncClient):
    """GET /api/knowledge/documents/999 returns 404."""
    resp = await client.get("/api/knowledge/documents/999")
    assert resp.status_code == 404


async def test_knowledge_search(
    client: httpx.AsyncClient, temp_kb: KnowledgeBase
):
    """Searching for a known keyword returns matching results."""
    analysis = _make_analysis(
        title="Neural Network Study",
        summary="This paper explores neural network architectures",
    )
    temp_kb.store_analysis(analysis)

    resp = await client.get("/api/knowledge/search", params={"q": "neural"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert any("Neural" in r["title"] for r in results)


async def test_knowledge_search_empty(client: httpx.AsyncClient):
    """Searching for a nonexistent keyword returns an empty list."""
    resp = await client.get(
        "/api/knowledge/search", params={"q": "nonexistentxyz123"}
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_knowledge_tags(
    client: httpx.AsyncClient, temp_kb: KnowledgeBase
):
    """After storing analysis with tags, the tags endpoint returns them."""
    analysis = _make_analysis(tags=["reinforcement-learning", "robotics"])
    temp_kb.store_analysis(analysis)

    resp = await client.get("/api/knowledge/tags")
    assert resp.status_code == 200
    tags = resp.json()
    names = [t["name"] for t in tags]
    assert "reinforcement-learning" in names
    assert "robotics" in names
    # Each tag should have count >= 1
    for t in tags:
        assert t["count"] >= 1


# ── 4. Pipeline endpoints ───────────────────────────────────────────


async def test_pipeline_run_no_files(client: httpx.AsyncClient):
    """POST /api/pipeline/run with no files returns 422."""
    resp = await client.post("/api/pipeline/run")
    assert resp.status_code == 422


async def test_pipeline_result_not_found(client: httpx.AsyncClient):
    """GET /api/pipeline/{run_id}/result for unknown run_id returns 404."""
    resp = await client.get("/api/pipeline/xyz/result")
    assert resp.status_code == 404


async def test_pipeline_progress_not_found(client: httpx.AsyncClient):
    """GET /api/pipeline/{run_id}/progress for unknown run_id returns 404."""
    resp = await client.get("/api/pipeline/xyz/progress")
    assert resp.status_code == 404


# ── 5. Reports endpoint ─────────────────────────────────────────────


async def test_reports_not_found(client: httpx.AsyncClient):
    """GET /api/reports/{run_id}/download for unknown run_id returns 404."""
    resp = await client.get("/api/reports/xyz/download")
    assert resp.status_code == 404
