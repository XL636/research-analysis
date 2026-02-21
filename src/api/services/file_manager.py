"""Upload file management."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from fastapi import UploadFile


def _get_upload_dir() -> Path:
    config_path = Path("config/settings.yaml")
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        upload_dir = config.get("api", {}).get("upload_dir", "./uploads")
    else:
        upload_dir = "./uploads"
    return Path(upload_dir)


ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".md", ".txt", ".docx"}


async def save_upload(file: UploadFile, run_id: str) -> str:
    """Save an uploaded file to disk, return the file path."""
    upload_dir = _get_upload_dir() / run_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = file.filename or "upload"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}")

    dest = upload_dir / filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return str(dest)


def cleanup_uploads(run_id: str) -> None:
    """Remove uploaded files for a run."""
    upload_dir = _get_upload_dir() / run_id
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
