"""论文 PDF 下载器 — 支持 arXiv、Unpaywall (DOI→OA) 和直接 URL."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import httpx
from loguru import logger

# Unpaywall 要求提供邮箱
_UNPAYWALL_EMAIL = "research-analysis@example.com"
_DOWNLOAD_TIMEOUT = 30  # seconds
_MAX_PDF_SIZE = 50 * 1024 * 1024  # 50 MB


class PaperDownloader:
    """下载论文 PDF 到临时目录."""

    def __init__(self, download_dir: str | None = None):
        if download_dir:
            self._dir = Path(download_dir)
        else:
            self._dir = Path(tempfile.mkdtemp(prefix="research_papers_"))
        self._dir.mkdir(parents=True, exist_ok=True)

    @property
    def download_dir(self) -> Path:
        return self._dir

    def download(
        self,
        url: str = "",
        doi: str = "",
        arxiv_id: str = "",
    ) -> Path | None:
        """尝试下载论文 PDF，返回本地路径或 None.

        优先级: arxiv_id > doi (Unpaywall) > direct url
        """
        # 从 URL 自动提取 arxiv_id
        if not arxiv_id and url:
            arxiv_id = self._extract_arxiv_id(url)

        if arxiv_id:
            result = self._download_arxiv(arxiv_id)
            if result:
                return result

        # Try direct URL download (PDF links from Semantic Scholar / OpenAlex OA)
        if url and url != f"https://doi.org/{doi}" if doi else True:
            result = self._download_direct(url)
            if result:
                return result

        if doi:
            result = self._download_unpaywall(doi)
            if result:
                return result

        logger.warning(f"Failed to download paper: url={url}, doi={doi}, arxiv_id={arxiv_id}")
        return None

    def _download_arxiv(self, arxiv_id: str) -> Path | None:
        """从 arXiv 下载 PDF."""
        # 清理 ID: 去除版本号尾缀如 v1, v2
        clean_id = re.sub(r"v\d+$", "", arxiv_id.strip())
        pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
        filename = f"arxiv_{clean_id.replace('/', '_')}.pdf"
        return self._fetch_pdf(pdf_url, filename, source="arXiv")

    def _download_unpaywall(self, doi: str) -> Path | None:
        """通过 Unpaywall API 查找 OA 版本并下载."""
        api_url = f"https://api.unpaywall.org/v2/{doi}?email={_UNPAYWALL_EMAIL}"
        try:
            with httpx.Client(timeout=_DOWNLOAD_TIMEOUT, follow_redirects=True) as client:
                resp = client.get(api_url)
                if resp.status_code != 200:
                    logger.debug(f"Unpaywall lookup failed for DOI {doi}: HTTP {resp.status_code}")
                    return None
                data = resp.json()
                oa_loc = data.get("best_oa_location") or {}
                pdf_url = oa_loc.get("url_for_pdf") or oa_loc.get("url")
                if not pdf_url:
                    logger.debug(f"No OA PDF found for DOI {doi}")
                    return None
                filename = f"doi_{doi.replace('/', '_')}.pdf"
                return self._fetch_pdf(pdf_url, filename, source="Unpaywall")
        except Exception as e:
            logger.warning(f"Unpaywall error for DOI {doi}: {e}")
            return None

    def _download_direct(self, url: str) -> Path | None:
        """直接下载 PDF URL（支持非 .pdf 结尾的 OA 链接）."""
        filename = Path(url.split("?")[0].split("/")[-1]).name
        if not filename.endswith(".pdf"):
            # Generate a safe filename from URL
            safe_name = url.split("//")[-1].replace("/", "_").replace("?", "_")[:80]
            filename = f"{safe_name}.pdf"
        return self._fetch_pdf(url, filename, source="direct")

    def _fetch_pdf(self, url: str, filename: str, source: str = "") -> Path | None:
        """通用 PDF 下载."""
        target = self._dir / filename
        if target.exists():
            logger.debug(f"Already downloaded: {target}")
            return target

        try:
            with httpx.Client(timeout=_DOWNLOAD_TIMEOUT, follow_redirects=True) as client:
                with client.stream("GET", url) as resp:
                    if resp.status_code != 200:
                        logger.debug(f"[{source}] HTTP {resp.status_code} for {url}")
                        return None

                    content_type = resp.headers.get("content-type", "")
                    if "html" in content_type and "pdf" not in content_type:
                        logger.debug(f"[{source}] Got HTML instead of PDF from {url}")
                        return None

                    size = 0
                    with open(target, "wb") as f:
                        for chunk in resp.iter_bytes(8192):
                            size += len(chunk)
                            if size > _MAX_PDF_SIZE:
                                logger.warning(f"[{source}] PDF too large (>{_MAX_PDF_SIZE} bytes), aborting")
                                f.close()
                                target.unlink(missing_ok=True)
                                return None
                            f.write(chunk)

            # 简单验证：PDF 文件应以 %PDF 开头
            with open(target, "rb") as f:
                header = f.read(5)
            if not header.startswith(b"%PDF"):
                logger.debug(f"[{source}] Downloaded file is not a valid PDF: {target}")
                target.unlink(missing_ok=True)
                return None

            logger.info(f"[{source}] Downloaded PDF: {target.name} ({size / 1024:.0f} KB)")
            return target

        except Exception as e:
            logger.warning(f"[{source}] Download failed for {url}: {e}")
            target.unlink(missing_ok=True)
            return None

    @staticmethod
    def _extract_arxiv_id(url: str) -> str:
        """从 URL 中提取 arXiv ID."""
        # https://arxiv.org/abs/2301.12345v2 → 2301.12345
        # https://arxiv.org/pdf/2301.12345.pdf → 2301.12345
        patterns = [
            r"arxiv\.org/abs/(\d{4}\.\d{4,5}(?:v\d+)?)",
            r"arxiv\.org/pdf/(\d{4}\.\d{4,5}(?:v\d+)?)",
        ]
        for pattern in patterns:
            m = re.search(pattern, url)
            if m:
                return re.sub(r"v\d+$", "", m.group(1))
        return ""
