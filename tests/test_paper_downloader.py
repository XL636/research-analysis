"""PaperDownloader 契约测试 — 使用 respx 拦截 httpx 请求."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from src.utils import paper_downloader
from src.utils.paper_downloader import PaperDownloader

# ---------------------------------------------------------------------------
# Fixture 文件路径
# ---------------------------------------------------------------------------
FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_PDF = FIXTURES_DIR / "sample.pdf"
HTML_LANDING = FIXTURES_DIR / "html_landing.html"


@pytest.fixture()
def downloader(tmp_path: Path) -> PaperDownloader:
    """每个测试拿到一个干净的 PaperDownloader，下载目录指向 tmp_path."""
    return PaperDownloader(download_dir=str(tmp_path))


@pytest.fixture()
def pdf_bytes() -> bytes:
    """读取 fixture 中的最小合法 PDF."""
    return SAMPLE_PDF.read_bytes()


@pytest.fixture()
def html_bytes() -> bytes:
    """读取 fixture 中的 HTML 落地页."""
    return HTML_LANDING.read_bytes()


# ===========================================================================
# TestFetchPdfValidation — 验证核心下载逻辑
# ===========================================================================


class TestFetchPdfValidation:
    """验证 _fetch_pdf / _download_direct 对各种响应的处理."""

    def test_rejects_html_content_type(self, downloader: PaperDownloader) -> None:
        """URL 返回 text/html content-type -> _download_direct 返回 None.

        这直接抓住原 bug：PubMed URL 返回 HTML 被当 PDF 保存。
        """
        url = "https://pubmed.example.com/article/12345"
        with respx.mock:
            respx.get(url).mock(
                return_value=httpx.Response(
                    200,
                    content=b"<html><body>Landing page</body></html>",
                    headers={"content-type": "text/html; charset=utf-8"},
                )
            )
            result = downloader._download_direct(url)

        assert result is None

    def test_rejects_non_pdf_magic(self, downloader: PaperDownloader) -> None:
        """content-type 为 application/octet-stream 但内容不以 %PDF 开头 -> 返回 None."""
        url = "https://example.com/maybe-pdf"
        fake_content = b"NOT-A-PDF-FILE-CONTENT-HERE"
        with respx.mock:
            respx.get(url).mock(
                return_value=httpx.Response(
                    200,
                    content=fake_content,
                    headers={"content-type": "application/octet-stream"},
                )
            )
            result = downloader._download_direct(url)

        assert result is None
        # 验证无残留文件
        downloaded_files = list(downloader.download_dir.glob("*.pdf"))
        assert len(downloaded_files) == 0

    def test_accepts_valid_pdf(self, downloader: PaperDownloader, pdf_bytes: bytes) -> None:
        """返回合法 PDF (以 %PDF 开头) -> 返回有效路径."""
        url = "https://example.com/paper.pdf"
        with respx.mock:
            respx.get(url).mock(
                return_value=httpx.Response(
                    200,
                    content=pdf_bytes,
                    headers={"content-type": "application/pdf"},
                )
            )
            result = downloader._download_direct(url)

        assert result is not None
        assert result.exists()
        assert result.suffix == ".pdf"
        # 验证下载内容与 fixture 一致
        assert result.read_bytes() == pdf_bytes

    def test_aborts_oversized_download(
        self, downloader: PaperDownloader, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """模拟超过大小限制的响应 -> 返回 None，文件被清理."""
        # 将 _MAX_PDF_SIZE 设为 1024 字节
        monkeypatch.setattr(paper_downloader, "_MAX_PDF_SIZE", 1024)

        url = "https://example.com/huge-paper.pdf"
        # 生成一个超过 1024 字节的"PDF"内容
        oversized_content = b"%PDF-1.4 " + b"x" * 2048
        with respx.mock:
            respx.get(url).mock(
                return_value=httpx.Response(
                    200,
                    content=oversized_content,
                    headers={"content-type": "application/pdf"},
                )
            )
            result = downloader._download_direct(url)

        assert result is None
        # 验证文件已被清理
        downloaded_files = list(downloader.download_dir.glob("*.pdf"))
        assert len(downloaded_files) == 0

    @pytest.mark.parametrize("status_code", [404, 500])
    def test_http_error_returns_none(
        self, downloader: PaperDownloader, status_code: int
    ) -> None:
        """HTTP 404/500 -> 返回 None."""
        url = "https://example.com/missing.pdf"
        with respx.mock:
            respx.get(url).mock(
                return_value=httpx.Response(status_code, content=b"")
            )
            result = downloader._download_direct(url)

        assert result is None

    def test_skips_if_already_downloaded(
        self, downloader: PaperDownloader, pdf_bytes: bytes
    ) -> None:
        """目标路径已存在 -> 直接返回已有路径，不发网络请求."""
        # 预先创建目标文件
        target = downloader.download_dir / "paper.pdf"
        target.write_bytes(pdf_bytes)

        url = "https://example.com/paper.pdf"
        with respx.mock:
            # 不注册任何 route — 如果发请求会报错
            result = downloader._download_direct(url)

        assert result is not None
        assert result == target
        assert result.read_bytes() == pdf_bytes


# ===========================================================================
# TestDownloadArxiv — arXiv 下载逻辑
# ===========================================================================


class TestDownloadArxiv:
    """验证 arXiv 下载的 URL 构造和版本号处理."""

    def test_arxiv_url_construction(
        self, downloader: PaperDownloader, pdf_bytes: bytes
    ) -> None:
        """arxiv_id='2301.12345' -> 请求 https://arxiv.org/pdf/2301.12345.pdf."""
        expected_url = "https://arxiv.org/pdf/2301.12345.pdf"
        with respx.mock:
            route = respx.get(expected_url).mock(
                return_value=httpx.Response(
                    200,
                    content=pdf_bytes,
                    headers={"content-type": "application/pdf"},
                )
            )
            result = downloader._download_arxiv("2301.12345")

        assert result is not None
        assert result.exists()
        assert route.called

    def test_arxiv_strips_version(
        self, downloader: PaperDownloader, pdf_bytes: bytes
    ) -> None:
        """arxiv_id='2301.12345v2' -> 请求 URL 中无 v2."""
        expected_url = "https://arxiv.org/pdf/2301.12345.pdf"
        with respx.mock:
            route = respx.get(expected_url).mock(
                return_value=httpx.Response(
                    200,
                    content=pdf_bytes,
                    headers={"content-type": "application/pdf"},
                )
            )
            result = downloader._download_arxiv("2301.12345v2")

        assert result is not None
        assert route.called


# ===========================================================================
# TestDownloadUnpaywall — Unpaywall API 逻辑
# ===========================================================================


class TestDownloadUnpaywall:
    """验证 Unpaywall API 查询和后续 PDF 下载."""

    def test_unpaywall_api_to_pdf(
        self, downloader: PaperDownloader, pdf_bytes: bytes
    ) -> None:
        """Unpaywall API 返回 best_oa_location.url_for_pdf -> 下载该 URL."""
        doi = "10.1038/s41586-024-00001"
        api_url = f"https://api.unpaywall.org/v2/{doi}?email=research-analysis@example.com"
        pdf_url = "https://europepmc.org/articles/PMC1234567/pdf"

        unpaywall_response = {
            "best_oa_location": {
                "url_for_pdf": pdf_url,
                "url": "https://europepmc.org/articles/PMC1234567",
            }
        }

        with respx.mock:
            # Unpaywall API 请求
            respx.get(api_url).mock(
                return_value=httpx.Response(
                    200,
                    content=json.dumps(unpaywall_response).encode(),
                    headers={"content-type": "application/json"},
                )
            )
            # 实际 PDF 下载
            respx.get(pdf_url).mock(
                return_value=httpx.Response(
                    200,
                    content=pdf_bytes,
                    headers={"content-type": "application/pdf"},
                )
            )
            result = downloader._download_unpaywall(doi)

        assert result is not None
        assert result.exists()
        assert result.read_bytes() == pdf_bytes

    def test_unpaywall_no_oa(self, downloader: PaperDownloader) -> None:
        """Unpaywall 返回空 best_oa_location -> 返回 None."""
        doi = "10.1038/s41586-024-99999"
        api_url = f"https://api.unpaywall.org/v2/{doi}?email=research-analysis@example.com"

        unpaywall_response = {
            "best_oa_location": None,
        }

        with respx.mock:
            respx.get(api_url).mock(
                return_value=httpx.Response(
                    200,
                    content=json.dumps(unpaywall_response).encode(),
                    headers={"content-type": "application/json"},
                )
            )
            result = downloader._download_unpaywall(doi)

        assert result is None


# ===========================================================================
# TestDownloadPriority — download() 方法的优先级逻辑
# ===========================================================================


class TestDownloadPriority:
    """验证 download() 方法中 arxiv_id > url > doi 的优先级."""

    def test_arxiv_id_takes_priority(
        self, downloader: PaperDownloader, pdf_bytes: bytes
    ) -> None:
        """同时提供 arxiv_id + url + doi -> 只用 arxiv_id 下载."""
        arxiv_url = "https://arxiv.org/pdf/2301.12345.pdf"
        direct_url = "https://example.com/paper.pdf"
        doi = "10.1038/s41586-024-00001"
        unpaywall_api = f"https://api.unpaywall.org/v2/{doi}?email=research-analysis@example.com"

        with respx.mock:
            # arXiv route — 应该被命中
            arxiv_route = respx.get(arxiv_url).mock(
                return_value=httpx.Response(
                    200,
                    content=pdf_bytes,
                    headers={"content-type": "application/pdf"},
                )
            )
            # direct URL — 不应被命中
            direct_route = respx.get(direct_url).mock(
                return_value=httpx.Response(
                    200,
                    content=pdf_bytes,
                    headers={"content-type": "application/pdf"},
                )
            )
            # Unpaywall — 不应被命中
            unpaywall_route = respx.get(unpaywall_api).mock(
                return_value=httpx.Response(200, content=b"{}")
            )

            result = downloader.download(
                url=direct_url, doi=doi, arxiv_id="2301.12345"
            )

        assert result is not None
        assert arxiv_route.called
        assert not direct_route.called
        assert not unpaywall_route.called

    def test_url_before_doi(
        self, downloader: PaperDownloader, pdf_bytes: bytes
    ) -> None:
        """提供 url + doi（url 不是 doi.org URL）-> 先尝试 url."""
        direct_url = "https://europepmc.org/articles/PMC1234567/pdf"
        doi = "10.1038/s41586-024-00001"
        unpaywall_api = f"https://api.unpaywall.org/v2/{doi}?email=research-analysis@example.com"

        with respx.mock:
            # direct URL — 应该被命中
            direct_route = respx.get(direct_url).mock(
                return_value=httpx.Response(
                    200,
                    content=pdf_bytes,
                    headers={"content-type": "application/pdf"},
                )
            )
            # Unpaywall — 不应被命中
            unpaywall_route = respx.get(unpaywall_api).mock(
                return_value=httpx.Response(200, content=b"{}")
            )

            result = downloader.download(url=direct_url, doi=doi)

        assert result is not None
        assert direct_route.called
        assert not unpaywall_route.called

    def test_doi_url_skipped_for_direct(
        self, downloader: PaperDownloader, pdf_bytes: bytes
    ) -> None:
        """url == f'https://doi.org/{doi}' -> 跳过 direct，走 Unpaywall."""
        doi = "10.1038/s41586-024-00001"
        doi_url = f"https://doi.org/{doi}"
        unpaywall_api = f"https://api.unpaywall.org/v2/{doi}?email=research-analysis@example.com"
        pdf_url = "https://europepmc.org/articles/PMC9999/pdf"

        unpaywall_response = {
            "best_oa_location": {
                "url_for_pdf": pdf_url,
            }
        }

        with respx.mock:
            # doi.org URL — 不应被命中（跳过 direct）
            doi_route = respx.get(doi_url).mock(
                return_value=httpx.Response(
                    200,
                    content=b"<html>redirect</html>",
                    headers={"content-type": "text/html"},
                )
            )
            # Unpaywall API
            respx.get(unpaywall_api).mock(
                return_value=httpx.Response(
                    200,
                    content=json.dumps(unpaywall_response).encode(),
                    headers={"content-type": "application/json"},
                )
            )
            # 最终 PDF 下载
            pdf_route = respx.get(pdf_url).mock(
                return_value=httpx.Response(
                    200,
                    content=pdf_bytes,
                    headers={"content-type": "application/pdf"},
                )
            )

            result = downloader.download(url=doi_url, doi=doi)

        assert result is not None
        assert not doi_route.called
        assert pdf_route.called


# ===========================================================================
# TestExtractArxivId — 从 URL 中提取 arXiv ID
# ===========================================================================


class TestExtractArxivId:
    """验证 _extract_arxiv_id 的正则提取逻辑."""

    def test_extract_from_abs_url(self) -> None:
        """'https://arxiv.org/abs/2301.12345v2' -> '2301.12345'."""
        result = PaperDownloader._extract_arxiv_id("https://arxiv.org/abs/2301.12345v2")
        assert result == "2301.12345"

    def test_extract_from_pdf_url(self) -> None:
        """'https://arxiv.org/pdf/2301.12345.pdf' -> '2301.12345'."""
        result = PaperDownloader._extract_arxiv_id("https://arxiv.org/pdf/2301.12345.pdf")
        assert result == "2301.12345"

    def test_no_arxiv_id_in_random_url(self) -> None:
        """'https://example.com/paper.pdf' -> ''."""
        result = PaperDownloader._extract_arxiv_id("https://example.com/paper.pdf")
        assert result == ""
