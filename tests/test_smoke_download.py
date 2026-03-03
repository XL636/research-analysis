"""真实 HTTP 冒烟测试 — 验证 PaperDownloader 能正确处理真实网络响应.

运行方式: uv run pytest -m smoke
默认跳过: pyproject.toml addopts 已排除 smoke marker
"""

import pytest
from src.utils.paper_downloader import PaperDownloader

pytestmark = pytest.mark.smoke


@pytest.fixture
def downloader(tmp_path):
    """创建以 tmp_path 为下载目录的 PaperDownloader 实例."""
    return PaperDownloader(download_dir=str(tmp_path))


def test_arxiv_download(tmp_path):
    """通过 arxiv_id 下载已知论文 (Attention Is All You Need).

    验证：
    - 返回路径不为 None
    - 文件存在且大于 100KB
    - 文件以 %PDF 魔数开头
    """
    dl = PaperDownloader(download_dir=str(tmp_path))
    result = dl.download(arxiv_id="1706.03762")

    assert result is not None, "arXiv 下载应返回有效路径"
    assert result.exists(), f"下载文件不存在: {result}"
    assert result.stat().st_size > 100 * 1024, (
        f"PDF 文件过小 ({result.stat().st_size} bytes)，可能不完整"
    )
    with open(result, "rb") as f:
        header = f.read(5)
    assert header.startswith(b"%PDF"), f"文件头不是 %PDF，实际: {header!r}"


def test_arxiv_url_extraction(tmp_path):
    """通过 arXiv abs URL 自动提取 ID 并下载.

    验证 PaperDownloader 能从 https://arxiv.org/abs/... 格式的 URL
    中正确提取 arXiv ID，并完成下载。
    """
    dl = PaperDownloader(download_dir=str(tmp_path))
    result = dl.download(url="https://arxiv.org/abs/2301.08745")

    assert result is not None, "从 arXiv URL 提取 ID 并下载应成功"
    assert result.exists(), f"下载文件不存在: {result}"
    assert result.stat().st_size > 0, "下载的 PDF 文件不应为空"


def test_unpaywall_oa_paper(tmp_path):
    """通过 DOI 从 Unpaywall 下载已知 OA 论文 (PeerJ).

    DOI 10.7717/peerj.4375 是一篇 PeerJ 的开放获取论文，
    Unpaywall 应能找到其 OA PDF 链接并完成下载。
    """
    dl = PaperDownloader(download_dir=str(tmp_path))
    result = dl.download(doi="10.7717/peerj.4375")

    assert result is not None, "Unpaywall 应能找到此 OA 论文的 PDF"


def test_pubmed_url_rejected(tmp_path):
    """PubMed 落地页（HTML）应被拒绝而非当作 PDF 保存.

    PubMed 的 URL 返回的是 HTML 页面，PaperDownloader 应检测到
    Content-Type 为 HTML 并拒绝下载，返回 None。
    """
    dl = PaperDownloader(download_dir=str(tmp_path))
    result = dl.download(url="https://pubmed.ncbi.nlm.nih.gov/25681456/")

    assert result is None, "PubMed HTML 落地页应被拒绝，返回 None"


def test_doi_landing_page_rejected(tmp_path):
    """doi.org 重定向到出版商 HTML 页面应被拒绝.

    Nature 付费论文的 doi.org 链接会重定向到 nature.com 的 HTML 页面，
    PaperDownloader 应检测到非 PDF 内容并拒绝下载。
    """
    dl = PaperDownloader(download_dir=str(tmp_path))
    result = dl.download(url="https://doi.org/10.1038/nature12373")

    assert result is None, "doi.org 重定向到 HTML 页面应被拒绝，返回 None"
