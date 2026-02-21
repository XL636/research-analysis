"""Reports download API routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from src.api.services.pipeline_runner import get_run

router = APIRouter()


@router.get("/{run_id}/download")
async def download_report(
    run_id: str,
    format: str = Query("markdown", description="Report format: markdown/docx/pptx"),
):
    """Download the generated report file."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run["status"] != "completed" or not run.get("result"):
        raise HTTPException(status_code=400, detail="Report not ready")

    output_path = run["result"].get("output_path", "")
    if not output_path or not Path(output_path).exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    media_types = {
        "markdown": "text/markdown",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }

    return FileResponse(
        path=output_path,
        media_type=media_types.get(format, "application/octet-stream"),
        filename=Path(output_path).name,
    )
