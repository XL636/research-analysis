"""Pipeline API routes - file upload, SSE progress, results."""

from __future__ import annotations

import asyncio

import yaml
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from src.api.schemas import (
    AnalysisModeInfo,
    AnalysisModesResponse,
    PipelineResultResponse,
    PipelineRunResponse,
)
from src.api.services.file_manager import save_upload
from src.api.services.pipeline_runner import create_run, get_run, run_pipeline

router = APIRouter()


@router.get("/modes", response_model=AnalysisModesResponse)
async def get_analysis_modes(request: Request):
    """Get available analysis modes."""
    with open("config/settings.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    modes_conf = config.get("analysis_modes", {})
    modes = []
    for mode_id, mode_data in modes_conf.items():
        modes.append(AnalysisModeInfo(
            id=mode_id,
            label_zh=mode_data.get("label_zh", mode_id),
            label_en=mode_data.get("label_en", mode_id),
            description_zh=mode_data.get("description_zh", ""),
            description_en=mode_data.get("description_en", ""),
            skip_review=mode_data.get("skip_review", False),
            max_text_length=mode_data.get("max_text_length", 8000),
        ))

    return AnalysisModesResponse(modes=modes)


@router.post("/run", response_model=PipelineRunResponse)
async def start_pipeline(
    files: list[UploadFile] = File(..., description="上传文件（PDF/PPTX/MD/TXT/DOCX）"),
    format: str = Form("markdown", description="输出格式: markdown/docx/pptx/pdf"),
    synthesize: bool = Form(False, description="启用跨文档综合分析"),
    mode: str = Form("standard", description="分析模式: quick/standard/deep/meeting/custom"),
    template_id: int | None = Form(None, description="报告模板 ID（可选）"),
    depth: str = Form("standard", description="分析深度（仅 custom 模式）: quick/standard/deep"),
):
    """Upload files and start analysis pipeline."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    # Load template content if template_id provided
    template_content = None
    if template_id is not None:
        from src.store.template_store import TemplateStore
        store = TemplateStore()
        template = store.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template id={template_id} not found")
        template_content = template.prompt_content

    # Custom mode: use depth as actual mode for analyzer/review config
    actual_mode = mode
    if mode == "custom":
        if depth not in ("quick", "standard", "deep"):
            raise HTTPException(status_code=400, detail=f"Invalid depth: {depth}")
        if template_id is None:
            raise HTTPException(status_code=400, detail="Custom mode requires a template_id")
        actual_mode = depth

    run_id = create_run()

    # Save uploaded files
    file_paths = []
    for f in files:
        try:
            path = await save_upload(f, run_id)
            file_paths.append(path)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Start pipeline in background
    asyncio.create_task(run_pipeline(run_id, file_paths, format, synthesize, actual_mode, template_content=template_content))

    return PipelineRunResponse(run_id=run_id, status="started")


@router.get("/{run_id}/progress")
async def pipeline_progress(run_id: str):
    """SSE endpoint for pipeline progress updates."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    async def event_stream():
        queue: asyncio.Queue = run["queue"]
        while True:
            try:
                progress = await asyncio.wait_for(queue.get(), timeout=60.0)
                yield f"data: {progress.model_dump_json()}\n\n"
                if progress.step in ("complete", "error"):
                    break
            except asyncio.TimeoutError:
                yield f"data: {{}}\n\n"  # keepalive

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{run_id}/result", response_model=PipelineResultResponse)
async def pipeline_result(run_id: str):
    """Get the final pipeline result."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run["status"] == "running":
        return PipelineResultResponse(run_id=run_id, status="running")
    elif run["status"] == "error":
        return PipelineResultResponse(run_id=run_id, status="error", error=run.get("error", "Unknown error"))
    elif run["status"] == "completed" and run.get("result"):
        r = run["result"]
        return PipelineResultResponse(
            run_id=run_id,
            status="completed",
            report_content=r.get("report_content", ""),
            report_title=r.get("report_title", ""),
            output_format=r.get("output_format", "markdown"),
        )

    return PipelineResultResponse(run_id=run_id, status=run["status"])
