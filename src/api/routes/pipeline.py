"""Pipeline API routes - file upload, SSE progress, results."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from src.api.schemas import PipelineResultResponse, PipelineRunResponse
from src.api.services.file_manager import save_upload
from src.api.services.pipeline_runner import create_run, get_run, run_pipeline

router = APIRouter()


@router.post("/run", response_model=PipelineRunResponse)
async def start_pipeline(
    files: list[UploadFile] = File(..., description="上传文件（PDF/PPTX/MD/TXT/DOCX）"),
    format: str = Form("markdown", description="输出格式: markdown/docx/pptx/pdf"),
    synthesize: bool = Form(False, description="启用跨文档综合分析"),
):
    """Upload files and start analysis pipeline."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

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
    asyncio.create_task(run_pipeline(run_id, file_paths, format, synthesize))

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
