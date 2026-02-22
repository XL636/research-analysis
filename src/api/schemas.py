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


class DeleteResponse(BaseModel):
    success: bool
    message: str = ""


class DuplicateCheckResponse(BaseModel):
    has_duplicate: bool
    existing_documents: list[DocumentSummary] = Field(default_factory=list)


# --- Dashboard ---

class DashboardStats(BaseModel):
    total_documents: int = 0
    recent_analyses: int = 0
    avg_score: float = 0.0
    top_tags: list[TagCount] = Field(default_factory=list)
    recent_documents: list[DocumentSummary] = Field(default_factory=list)


# --- Settings ---

class ProviderStatus(BaseModel):
    env_var: str
    provider: str
    configured: bool = False
    masked_key: str = ""
    models: list[str] = Field(default_factory=list)


class ApiKeyStatusResponse(BaseModel):
    providers: list[ProviderStatus]


class ApiKeySaveRequest(BaseModel):
    keys: dict[str, str]  # { "DEEPSEEK_API_KEY": "sk-xxx", ... }


class ApiKeySaveResponse(BaseModel):
    success: bool
    providers: list[ProviderStatus]


# --- Agent Model Assignment ---

class ModelInfo(BaseModel):
    name: str
    provider: str
    api_key_env: str
    api_key_configured: bool


class AgentModelAssignment(BaseModel):
    agent: str
    model: str
    provider: str
    api_key_env: str
    api_key_configured: bool


class AgentModelsResponse(BaseModel):
    agent_models: list[AgentModelAssignment]
    available_models: list[ModelInfo]


class AgentModelsSaveRequest(BaseModel):
    agent_models: dict[str, str]  # {"parser": "qwen-turbo", ...}


class AgentModelsSaveResponse(BaseModel):
    success: bool
    agent_models: list[AgentModelAssignment]
    available_models: list[ModelInfo]
