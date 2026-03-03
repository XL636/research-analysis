"""Paper search API 路由集成测试.

被测目标：src/api/routes/paper_search.py 中的 3 个关键路由：
- GET  /api/paper-search/search
- POST /api/paper-search/download-pdf
- POST /api/paper-search/download-and-analyze
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.api.app import create_app
from src.core.search_client import ExternalSearchResult

pytestmark = pytest.mark.anyio


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
async def client(tmp_path):
    """创建异步测试客户端，工作目录切到 tmp_path 避免副作用."""
    original_cwd = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        app = create_app()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c
    finally:
        os.chdir(original_cwd)


def _make_search_results(n: int = 2, source: str = "arxiv") -> list[ExternalSearchResult]:
    """构造 n 条模拟搜索结果."""
    return [
        ExternalSearchResult(
            title=f"Paper Title {i}",
            authors=f"Author {i}",
            year="2024",
            venue="NeurIPS",
            doi=f"10.1234/test.{i}",
            url=f"https://arxiv.org/abs/2401.{i:05d}",
            abstract=f"Abstract for paper {i}.",
            source=source,
        )
        for i in range(1, n + 1)
    ]


def _make_fake_pdf(path: Path) -> Path:
    """在指定路径写入一个最小合法 PDF 文件."""
    # 最小 PDF：header + 空 body + xref + trailer
    pdf_bytes = b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\nxref\n0 3\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \ntrailer<</Size 3/Root 1 0 R>>\nstartxref\n109\n%%EOF"
    path.write_bytes(pdf_bytes)
    return path


# ── TestSearchEndpoint ────────────────────────────────────────────────


class TestSearchEndpoint:
    """GET /api/paper-search/search 搜索路由测试."""

    async def test_search_returns_results(self, client: httpx.AsyncClient):
        """mock SearchManager.search 返回结果列表 → 200 + results 非空."""
        mock_results = _make_search_results(3, source="arxiv")
        mock_sm = MagicMock()
        mock_sm.search.return_value = mock_results
        mock_sm.close.return_value = None

        with patch(
            "src.api.routes.paper_search._get_search_manager", return_value=mock_sm
        ):
            resp = await client.get(
                "/api/paper-search/search", params={"q": "transformer"}
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["results"]) == 3
        assert data["results"][0]["title"] == "Paper Title 1"
        assert data["providers_used"] == ["arxiv"]
        # 验证 SearchManager 被正确调用
        mock_sm.search.assert_called_once_with("transformer", 5, None)
        mock_sm.close.assert_called_once()

    async def test_search_with_provider_filter(self, client: httpx.AsyncClient):
        """传 providers=arxiv → SearchManager 收到 provider_names=["arxiv"]."""
        mock_results = _make_search_results(1, source="arxiv")
        mock_sm = MagicMock()
        mock_sm.search.return_value = mock_results
        mock_sm.close.return_value = None

        with patch(
            "src.api.routes.paper_search._get_search_manager", return_value=mock_sm
        ):
            resp = await client.get(
                "/api/paper-search/search",
                params={"q": "attention", "providers": "arxiv"},
            )

        assert resp.status_code == 200
        # 验证 provider_names 参数被正确传递
        mock_sm.search.assert_called_once_with("attention", 5, ["arxiv"])

    async def test_search_empty_query_rejected(self, client: httpx.AsyncClient):
        """q="" → 422 验证错误（FastAPI Query min_length=1 拦截）."""
        resp = await client.get(
            "/api/paper-search/search", params={"q": ""}
        )
        assert resp.status_code == 422


# ── TestDownloadPdfEndpoint ───────────────────────────────────────────


class TestDownloadPdfEndpoint:
    """POST /api/paper-search/download-pdf 下载 PDF 路由测试."""

    async def test_download_pdf_success(self, client: httpx.AsyncClient, tmp_path):
        """mock _try_download_pdf 返回有效 PDF 路径 → 200 + application/pdf."""
        # 在 tmp_path 中创建真实的小 PDF 文件
        pdf_path = _make_fake_pdf(tmp_path / "test_paper.pdf")

        with patch(
            "src.api.routes.paper_search._try_download_pdf",
            return_value=pdf_path,
        ):
            resp = await client.post(
                "/api/paper-search/download-pdf",
                json={
                    "url": "https://arxiv.org/abs/2401.00001",
                    "title": "Test Paper",
                    "doi": "10.1234/test.1",
                },
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        # 验证响应体包含 PDF 内容
        assert resp.content.startswith(b"%PDF")

    async def test_download_pdf_failure(self, client: httpx.AsyncClient):
        """mock _try_download_pdf 返回 None → 404."""
        with patch(
            "src.api.routes.paper_search._try_download_pdf",
            return_value=None,
        ):
            resp = await client.post(
                "/api/paper-search/download-pdf",
                json={
                    "url": "https://example.com/no-pdf",
                    "title": "Missing Paper",
                },
            )

        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data


# ── TestDownloadAndAnalyzeEndpoint ────────────────────────────────────


class TestDownloadAndAnalyzeEndpoint:
    """POST /api/paper-search/download-and-analyze 下载并分析路由测试."""

    async def test_download_and_analyze_with_pdf(
        self, client: httpx.AsyncClient, tmp_path
    ):
        """mock _try_download_pdf 返回有效路径 + mock _pipeline_analyze 返回 doc_id
        → success=True + has_analysis=True."""
        pdf_path = _make_fake_pdf(tmp_path / "analysis_paper.pdf")

        with patch(
            "src.api.routes.paper_search._try_download_pdf",
            return_value=pdf_path,
        ), patch(
            "src.api.routes.paper_search._pipeline_analyze",
            return_value=42,
        ):
            resp = await client.post(
                "/api/paper-search/download-and-analyze",
                json={
                    "title": "Attention Is All You Need",
                    "url": "https://arxiv.org/abs/1706.03762",
                    "doi": "10.48550/arXiv.1706.03762",
                    "authors": "Vaswani et al.",
                    "year": "2017",
                    "venue": "NeurIPS",
                    "abstract": "The dominant sequence transduction models...",
                    "source": "arxiv",
                    "mode": "quick",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["has_analysis"] is True
        assert data["doc_id"] == 42

    async def test_download_and_analyze_fallback_to_metadata(
        self, client: httpx.AsyncClient
    ):
        """mock _try_download_pdf 返回 None + mock _metadata_analyze_and_store
        → success=True + message 包含 'LLM' 或 '摘要'."""
        from src.api.routes.paper_search import _AnalyzeAndStoreResult

        mock_result = _AnalyzeAndStoreResult(
            doc_id=99,
            message="已保存到知识库",
            has_analysis=True,
        )

        with patch(
            "src.api.routes.paper_search._try_download_pdf",
            return_value=None,
        ), patch(
            "src.api.routes.paper_search._metadata_analyze_and_store",
            return_value=mock_result,
        ):
            resp = await client.post(
                "/api/paper-search/download-and-analyze",
                json={
                    "title": "Some Paper Without PDF",
                    "url": "https://example.com/paper",
                    "abstract": "This paper proposes a novel approach...",
                    "source": "openalex",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["doc_id"] == 99
        assert data["has_analysis"] is True
        # fallback 路径的 message 应包含 "LLM" 或 "摘要"
        assert "LLM" in data["message"] or "摘要" in data["message"]
