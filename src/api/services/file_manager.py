"""Upload file management."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from fastapi import UploadFile


def _get_upload_config() -> tuple[Path, int]:
    """Return (upload_dir, max_upload_size_bytes)."""
    config_path = Path("config/settings.yaml")
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        api_conf = config.get("api", {})
        upload_dir = api_conf.get("upload_dir", "./uploads")
        max_size = api_conf.get("max_upload_size", 52428800)
    else:
        upload_dir = "./uploads"
        max_size = 52428800  # 50 MB
    return Path(upload_dir), int(max_size)


def _get_upload_dir() -> Path:
    upload_dir, _ = _get_upload_config()
    return upload_dir


ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".md", ".txt", ".docx"}


async def save_upload(file: UploadFile, run_id: str) -> str:
    """Save an uploaded file to disk, return the file path."""
    upload_dir, max_size = _get_upload_config()
    run_dir = upload_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename: strip directory components to prevent path traversal
    raw_name = file.filename or "upload"
    filename = Path(raw_name).name
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}")

    # Enforce upload size limit
    contents = await file.read()
    if len(contents) > max_size:
        raise ValueError(
            f"File too large: {len(contents)} bytes (max {max_size} bytes)"
        )

    dest = run_dir / filename
    with open(dest, "wb") as f:
        f.write(contents)

    return str(dest)


def cleanup_uploads(run_id: str) -> None:
    """Remove uploaded files for a run."""
    upload_dir = _get_upload_dir() / run_id
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
