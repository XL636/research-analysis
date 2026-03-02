"""Paper search API routes."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

if TYPE_CHECKING:
    from src.core.models import AnalysisResult

from src.api.schemas import (
    DownloadAnalyzeRequest,
    DownloadAnalyzeResponse,
    DownloadPdfRequest,
    PaperChatRequest,
    PaperSearchResponse,
    PaperSearchResult,
    SaveToKBRequest,
    SaveToKBResponse,
    SmartSearchRequest,
    SmartSearchResponse,
    SmartSearchResultItem,
)

router = APIRouter()

# --- Shared types and constants ---

AnalysisMode = Literal["quick", "standard", "deep"]

_JSON_SCHEMA_TEMPLATE = (
    '{{\n'
    '  "document_title": "论文标题",\n'
    '  "paper_type": "empirical/theoretical/survey/opinion/technical 之一",\n'
    '  "summary": "{summary_hint}",\n'
    '  "key_findings": [{{"finding": "发现", "evidence": "证据", "significance": "意义"}}],\n'
    '  "methodology": {{"approach": "方法", "strengths": ["优势"], "limitations": ["局限"]}},\n'
    '  "contributions": [{contributions}],\n'
    '  "limitations": [{limitations}],\n'
    '  "future_work": [{future_work}],\n'
    '  "tags": [{tags}],\n'
    '  "relevance_score": 7.0\n'
    '}}'
)

_SCHEMA_PARAMS = {
    "quick": {
        "summary_hint": "200字左右的中文摘要总结",
        "contributions": '"贡献1", "贡献2"',
        "limitations": '"局限1"',
        "future_work": '"方向1"',
        "tags": '"标签1", "标签2"',
    },
    "detailed": {
        "summary_hint": "详细中文摘要总结",
        "contributions": '"贡献1", "贡献2", "贡献3"',
        "limitations": '"局限1", "局限2"',
        "future_work": '"方向1", "方向2"',
        "tags": '"标签1", "标签2", "标签3", "标签4"',
    },
}


def _build_json_schema(mode: str) -> str:
    params = _SCHEMA_PARAMS["detailed" if mode in ("standard", "deep") else "quick"]
    return _JSON_SCHEMA_TEMPLATE.format(**params)


# --- Shared helper: metadata → AnalysisResult + store ---

@dataclass
class _AnalyzeAndStoreResult:
    doc_id: int
    message: str
    has_analysis: bool


def _analyze_from_metadata(
    title: str,
    abstract: str,
    authors: str = "",
    year: str = "",
    venue: str = "",
    doi: str = "",
    url: str = "",
    source: str = "",
    mode: str = "quick",
) -> "AnalysisResult":
    """用 LLM 从标题+摘要生成结构化 AnalysisResult."""
    from src.core.llm_client import LLMClient
    from src.core.models import AnalysisResult

    try:
        llm = LLMClient()

        meta_block = (
            f"标题：{title}\n"
            f"作者：{authors}\n"
            f"年份：{year}\n"
            f"期刊/会议：{venue}\n"
            f"摘要：{abstract}\n"
        )

        json_schema = _build_json_schema(mode)

        if mode in ("standard", "deep"):
            depth_hint = "深入" if mode == "deep" else "较详细"
            prompt = (
                f"请基于以下论文信息进行{depth_hint}的结构化分析（JSON 格式）。\n\n"
                f"{meta_block}\n"
                "要求：\n"
                "1. summary 至少 400 字，涵盖背景、方法、结果和意义\n"
                "2. key_findings 至少列出 3 项，每项含 finding/evidence/significance\n"
                "3. methodology 需详细描述 approach，并给出具体的 strengths 和 limitations\n"
                "4. contributions 至少 3 项\n"
                "5. limitations 和 future_work 各至少 2 项\n"
                "6. tags 至少 4 个关键词\n\n"
                f"返回 JSON，字段如下：\n{json_schema}"
            )
        else:
            prompt = (
                "请基于以下论文信息生成结构化分析（JSON 格式）。\n\n"
                f"{meta_block}\n"
                f"返回 JSON，字段如下：\n{json_schema}"
            )

        result_dict = llm.chat_json("glm-4-flash", [{"role": "user", "content": prompt}])
        # 确保 document_title 存在
        result_dict.setdefault("document_title", title)
        return AnalysisResult.model_validate(result_dict)
    except Exception as e:
        logger.warning(f"LLM analysis from metadata failed: {e}")
        # 兜底：返回仅含 summary 的 AnalysisResult
        return AnalysisResult(
            document_title=title,
            summary=abstract or f"论文：{title}",
            tags=["paper_search"],
            relevance_score=5.0,
        )


def _metadata_analyze_and_store(
    *,
    title: str,
    abstract: str,
    authors: str,
    year: str,
    venue: str,
    doi: str,
    url: str,
    source: str,
    mode: str,
) -> _AnalyzeAndStoreResult:
    """LLM 从元数据生成分析 + 存入知识库（共享逻辑）."""
    from src.store.knowledge_base import KnowledgeBase

    kb = KnowledgeBase()
    analysis = _analyze_from_metadata(
        title=title, abstract=abstract, authors=authors, year=year,
        venue=venue, doi=doi, url=url, source=source, mode=mode,
    )
    doc_id = kb.store_analysis(
        analysis=analysis,
        file_path=url or "",
        file_type="paper_search",
        source_type="paper_search",
        parsed_text=abstract or "",
    )
    return _AnalyzeAndStoreResult(doc_id=doc_id, message="已保存到知识库", has_analysis=True)


def _pipeline_analyze(pdf_path: Path, title: str, mode: str) -> int:
    """运行 Pipeline 分析 PDF 并返回 doc_id."""
    from src.core.engine import Pipeline

    pipeline = Pipeline(mode=mode)
    ctx = pipeline.run(
        input_files=[str(pdf_path)],
        output_format="markdown",
        synthesize=False,
    )
    return ctx.doc_ids[0] if ctx.doc_ids else 0


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
            iterations_used=output.iterations_used,
            search_log=output.search_log,
            domain_detected=output.domain_detected,
            quality_score=output.quality_score,
            chinese_db_links=output.chinese_db_links,
        )
    except Exception as e:
        logger.error(f"Smart search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-to-kb", response_model=SaveToKBResponse)
async def save_to_kb(req: SaveToKBRequest):
    """保存论文元数据到知识库."""
    try:
        # 非 quick 模式：先尝试下载 PDF + Pipeline 完整分析
        if req.mode in ("standard", "deep") and req.url:
            try:
                pdf_path = await asyncio.to_thread(_try_download_pdf, req.url, req.title)
                if pdf_path and pdf_path.exists():
                    doc_id = await asyncio.to_thread(
                        _pipeline_analyze, pdf_path, req.title, req.mode,
                    )
                    return SaveToKBResponse(
                        success=True, doc_id=doc_id,
                        message=f"已下载 PDF 并以{req.mode}模式分析入库",
                    )
            except Exception as e:
                logger.warning(f"Pipeline analysis in save_to_kb failed: {e}, falling back to metadata analysis")

        # quick 模式 或 Pipeline 失败 fallback
        result = await asyncio.to_thread(
            _metadata_analyze_and_store,
            title=req.title, abstract=req.abstract, authors=req.authors,
            year=req.year, venue=req.venue, doi=req.doi,
            url=req.url, source=req.source, mode=req.mode,
        )
        return SaveToKBResponse(success=True, doc_id=result.doc_id, message=result.message)
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

    meta_kwargs = dict(
        title=req.title, abstract=req.abstract, authors=req.authors,
        year=req.year, venue=req.venue, doi=req.doi,
        url=req.url, source=req.source, mode=req.mode,
    )

    # Try to download PDF
    pdf_path = _try_download_pdf(req.url, req.title)

    if pdf_path and pdf_path.exists():
        # Parse + Analyze via pipeline
        try:
            doc_id = _pipeline_analyze(pdf_path, req.title, req.mode)
            return DownloadAnalyzeResponse(
                success=True, doc_id=doc_id,
                message="下载并分析完成", has_analysis=True,
            )
        except Exception as e:
            logger.warning(f"Analysis failed after download: {e}")
            # Fallback: 用 LLM 从元数据生成分析
            try:
                result = _metadata_analyze_and_store(**meta_kwargs)
                return DownloadAnalyzeResponse(
                    success=True, doc_id=result.doc_id,
                    message=f"PDF 分析失败，已用 LLM 从摘要生成分析: {e}",
                    has_analysis=True,
                )
            except Exception as e2:
                logger.error(f"LLM fallback also failed: {e2}")
                kb = KnowledgeBase()
                doc_id = kb.store_metadata_only(
                    title=req.title, summary=req.abstract, doi=req.doi,
                    url=req.url, authors=req.authors, year=req.year,
                    source_type="paper_search",
                )
                return DownloadAnalyzeResponse(
                    success=True, doc_id=doc_id,
                    message=f"分析失败，已保存元数据: {e}",
                    has_analysis=False,
                )
    else:
        # PDF 下载失败，用 LLM 从元数据生成分析
        try:
            result = _metadata_analyze_and_store(**meta_kwargs)
            return DownloadAnalyzeResponse(
                success=True, doc_id=result.doc_id,
                message="PDF 下载失败，已用 LLM 从摘要生成分析",
                has_analysis=True,
            )
        except Exception as e:
            logger.error(f"LLM fallback failed: {e}")
            kb = KnowledgeBase()
            doc_id = kb.store_metadata_only(
                title=req.title, summary=req.abstract, doi=req.doi,
                url=req.url, authors=req.authors, year=req.year,
                source_type="paper_search",
            )
            return DownloadAnalyzeResponse(
                success=True, doc_id=doc_id,
                message="PDF 下载失败，已保存元数据",
                has_analysis=False,
            )


@router.post("/chat")
async def paper_chat(req: PaperChatRequest):
    """论文 AI 对话 — SSE 流式响应."""
    import json
    import queue
    import threading

    from fastapi.responses import StreamingResponse

    from src.core.llm_client import LLMClient

    system_prompt = f"""你是一个学术论文助手，正在帮助用户了解以下论文：

标题：{req.title}
作者：{req.authors}
年份：{req.year}
期刊/会议：{req.venue}
摘要：{req.abstract}

请基于论文信息回答用户的问题。回答应准确、简洁，使用中文。如果信息不足以回答某个问题，请如实说明。"""

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for msg in req.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": req.message})

    q: queue.Queue = queue.Queue()

    def _run():
        try:
            llm = LLMClient()
            for chunk in llm.stream_chat(
                "glm-4-flash", messages, temperature=0.7, max_tokens=2048
            ):
                q.put(chunk)
        except Exception as e:
            q.put(("error", str(e)))
        finally:
            q.put(None)

    threading.Thread(target=_run, daemon=True).start()

    async def event_generator():
        while True:
            try:
                item = await asyncio.to_thread(q.get, timeout=60)
            except Exception:
                yield f"data: {json.dumps({'type': 'error', 'message': 'timeout'}, ensure_ascii=False)}\n\n"
                break
            if item is None:
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                break
            if isinstance(item, tuple) and item[0] == "error":
                yield f"data: {json.dumps({'type': 'error', 'message': item[1]}, ensure_ascii=False)}\n\n"
                break
            yield f"data: {json.dumps({'type': 'delta', 'content': item}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/download-pdf")
async def download_pdf(req: DownloadPdfRequest):
    """直接下载论文 PDF 文件."""
    from fastapi import BackgroundTasks
    from fastapi.responses import FileResponse

    pdf_path = await asyncio.to_thread(_try_download_pdf, req.url, req.title or "paper")
    if not pdf_path or not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF 下载失败")

    bg = BackgroundTasks()
    bg.add_task(pdf_path.unlink, missing_ok=True)
    return FileResponse(
        pdf_path, filename=pdf_path.name, media_type="application/pdf",
        background=bg,
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
