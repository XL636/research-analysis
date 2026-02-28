"""Paper search API routes."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from src.api.schemas import (
    DownloadAnalyzeRequest,
    DownloadAnalyzeResponse,
    PaperSearchResponse,
    PaperSearchResult,
    SaveToKBRequest,
    SaveToKBResponse,
    SmartSearchRequest,
    SmartSearchResponse,
    SmartSearchResultItem,
)

router = APIRouter()


def _get_search_manager():
    from src.core.search_client import SearchManager
    return SearchManager()


@router.get("/search", response_model=PaperSearchResponse)
async def search_papers(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    providers: str | None = Query(None, description="搜索源，逗号分隔，如 arxiv,pubmed"),
    max_results: int = Query(5, ge=1, le=50, description="每个搜索源的最大结果数"),
):
    """搜索外部学术论文."""
    sm = _get_search_manager()
    try:
        provider_names = None
        if providers:
            provider_names = [p.strip() for p in providers.split(",") if p.strip()]

        results = await asyncio.to_thread(
            sm.search, q, max_results, provider_names
        )

        providers_used = list({r.source for r in results})

        return PaperSearchResponse(
            results=[
                PaperSearchResult(
                    title=r.title,
                    authors=r.authors,
                    year=r.year,
                    venue=r.venue,
                    doi=r.doi,
                    url=r.url,
                    abstract=r.abstract,
                    source=r.source,
                )
                for r in results
            ],
            total=len(results),
            providers_used=providers_used,
        )
    finally:
        sm.close()


@router.post("/smart-search", response_model=SmartSearchResponse)
async def smart_search(req: SmartSearchRequest):
    """智能论文搜索：LLM 理解意图 + 生成关键词 + 多源搜索 + 筛选排序."""
    from src.agents.paper_search import PaperSearchAgent, SmartSearchInput
    from src.core.llm_client import LLMClient
    from src.core.search_client import SearchManager

    try:
        llm = LLMClient()
        sm = SearchManager()
        agent = PaperSearchAgent(llm_client=llm, search_manager=sm)

        search_input = SmartSearchInput(
            query=req.query,
            providers=req.providers,
            max_results=req.max_results,
            language_hint=req.language_hint,
        )

        output = await asyncio.to_thread(agent.process, search_input)
        sm.close()

        return SmartSearchResponse(
            query=output.query,
            interpreted_intent=output.interpreted_intent,
            generated_keywords=output.generated_keywords,
            results=[
                SmartSearchResultItem(**r.model_dump())
                for r in output.results
            ],
            total_candidates=output.total_candidates,
            providers_used=output.providers_used,
        )
    except Exception as e:
        logger.error(f"Smart search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-to-kb", response_model=SaveToKBResponse)
async def save_to_kb(req: SaveToKBRequest):
    """保存论文元数据到知识库."""
    from src.store.knowledge_base import KnowledgeBase

    try:
        kb = KnowledgeBase()
        doc_id = kb.store_metadata_only(
            title=req.title,
            summary=req.abstract,
            doi=req.doi,
            url=req.url,
            authors=req.authors,
            year=req.year,
            source_type="paper_search",
        )
        return SaveToKBResponse(success=True, doc_id=doc_id, message="已保存到知识库")
    except Exception as e:
        logger.error(f"Save to KB failed: {e}")
        return SaveToKBResponse(success=False, message=str(e))


@router.post("/download-and-analyze", response_model=DownloadAnalyzeResponse)
async def download_and_analyze(req: DownloadAnalyzeRequest):
    """下载论文 PDF 并分析入库."""
    if not req.url:
        raise HTTPException(status_code=400, detail="URL 不能为空")

    try:
        result = await asyncio.to_thread(_do_download_and_analyze, req)
        return result
    except Exception as e:
        logger.error(f"Download and analyze failed: {e}")
        return DownloadAnalyzeResponse(success=False, message=str(e))


def _do_download_and_analyze(req: DownloadAnalyzeRequest) -> DownloadAnalyzeResponse:
    """同步执行下载 + 分析流程."""
    from src.store.knowledge_base import KnowledgeBase

    # Try to download PDF
    pdf_path = _try_download_pdf(req.url, req.title)

    if pdf_path and pdf_path.exists():
        # Parse + Analyze via pipeline
        try:
            from src.core.engine import Pipeline

            pipeline = Pipeline(mode="quick")
            ctx = pipeline.run(
                input_files=[str(pdf_path)],
                output_format="markdown",
                synthesize=False,
            )

            # The pipeline stores to KB automatically; find the doc
            kb = KnowledgeBase()
            results = kb.search(req.title, limit=1)
            doc_id = results[0]["id"] if results else 0

            return DownloadAnalyzeResponse(
                success=True,
                doc_id=doc_id,
                message="下载并分析完成",
                has_analysis=True,
            )
        except Exception as e:
            logger.warning(f"Analysis failed after download: {e}")
            # Fallback: save metadata only
            kb = KnowledgeBase()
            doc_id = kb.store_metadata_only(
                title=req.title,
                summary=req.abstract,
                doi=req.doi,
                url=req.url,
                authors=req.authors,
                year=req.year,
                source_type="paper_search",
            )
            return DownloadAnalyzeResponse(
                success=True,
                doc_id=doc_id,
                message=f"分析失败，已保存元数据: {e}",
                has_analysis=False,
            )
    else:
        # Download failed, save metadata only
        kb = KnowledgeBase()
        doc_id = kb.store_metadata_only(
            title=req.title,
            summary=req.abstract,
            doi=req.doi,
            url=req.url,
            authors=req.authors,
            year=req.year,
            source_type="paper_search",
        )
        return DownloadAnalyzeResponse(
            success=True,
            doc_id=doc_id,
            message="PDF 下载失败，已保存元数据",
            has_analysis=False,
        )


def _try_download_pdf(url: str, title: str) -> Path | None:
    """Attempt to download a PDF from URL."""
    import httpx

    download_dir = Path("downloads/papers")
    download_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in title[:60])
    pdf_path = download_dir / f"{safe_name}.pdf"

    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            # If arXiv abs URL, convert to PDF
            if "arxiv.org/abs/" in url:
                url = url.replace("/abs/", "/pdf/") + ".pdf"

            resp = client.get(url)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if "pdf" not in content_type and not resp.content[:5] == b"%PDF-":
                logger.warning(f"URL did not return PDF: {content_type}")
                return None

            pdf_path.write_bytes(resp.content)
            return pdf_path
    except Exception as e:
        logger.warning(f"PDF download failed from {url}: {e}")
        return None
