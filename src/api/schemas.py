"""API request/response Pydantic models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# --- Pipeline ---

class PipelineRunResponse(BaseModel):
    run_id: str
    status: str = "started"


class StepProgress(BaseModel):
    step: str  # parse, analyze, synthesize, generate, review
    status: str  # pending, running, completed, error
    message: str = ""


class PipelineResultResponse(BaseModel):
    run_id: str
    status: str  # running, completed, error
    report_content: str = ""
    report_title: str = ""
    output_format: str = "markdown"
    error: str = ""


# --- Knowledge Base ---

class DocumentSummary(BaseModel):
    id: int
    title: str
    file_type: str = ""
    tags: str = ""
    date: str = ""


class DocumentDetail(BaseModel):
    id: int
    title: str
    file_type: str = ""
    file_path: str = ""
    summary: str = ""
    tags: str = ""
    date: str = ""
    analysis: dict | None = None


class SearchResult(BaseModel):
    id: int
    title: str
    file_type: str = ""
    summary: str = ""
    tags: str = ""
    date: str = ""


class TagCount(BaseModel):
    name: str
    count: int


# --- Dashboard ---

class DashboardStats(BaseModel):
    total_documents: int = 0
    recent_analyses: int = 0
    avg_score: float = 0.0
    top_tags: list[TagCount] = Field(default_factory=list)
    recent_documents: list[DocumentSummary] = Field(default_factory=list)
