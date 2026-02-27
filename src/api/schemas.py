"""API request/response Pydantic models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# --- Pipeline ---

class AnalysisModeInfo(BaseModel):
    id: str
    label_zh: str = ""
    label_en: str = ""
    description_zh: str = ""
    description_en: str = ""
    skip_review: bool = False
    max_text_length: int = 8000


class AnalysisModesResponse(BaseModel):
    modes: list[AnalysisModeInfo] = Field(default_factory=list)


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
    collection_id: int | None = None


class DocumentDetail(BaseModel):
    id: int
    title: str
    file_type: str = ""
    file_path: str = ""
    summary: str = ""
    tags: str = ""
    date: str = ""
    analysis: dict | None = None
    collection_id: int | None = None
    report_content: str | None = None


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


class BatchDeleteRequest(BaseModel):
    ids: list[int]


class BatchDeleteResponse(BaseModel):
    success: bool
    deleted_count: int = 0


class DuplicateCheckResponse(BaseModel):
    has_duplicate: bool
    existing_documents: list[DocumentSummary] = Field(default_factory=list)


# --- Title Update ---

class UpdateTitleRequest(BaseModel):
    title: str


class UpdateTitleResponse(BaseModel):
    success: bool
    title: str


# --- Collections ---

class CollectionSummary(BaseModel):
    id: int
    name: str
    document_count: int = 0


class CreateCollectionRequest(BaseModel):
    name: str


class RenameCollectionRequest(BaseModel):
    name: str


class MoveToCollectionRequest(BaseModel):
    collection_id: int | None = None


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


# --- Search Providers ---

class SearchProviderStatus(BaseModel):
    name: str  # "semantic_scholar" | "openalex" | "arxiv"
    enabled: bool = True
    api_key_env: str = ""
    api_key_configured: bool = False
    masked_key: str = ""


class SearchProvidersResponse(BaseModel):
    providers: list[SearchProviderStatus]


class SearchProviderSaveRequest(BaseModel):
    providers: dict[str, dict] = Field(default_factory=dict)  # {"semantic_scholar": {"enabled": true}}
    keys: dict[str, str] = Field(default_factory=dict)  # {"SEMANTIC_SCHOLAR_API_KEY": "xxx"}


class SearchProviderSaveResponse(BaseModel):
    success: bool
    providers: list[SearchProviderStatus]


# --- Agent Model Assignment ---

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


# --- Paper Writing ---

class CreatePaperRequest(BaseModel):
    name: str
    topic: str = ""
    language: str = "zh"
    venue: str = "generic"
    research_question: str = ""
    key_contributions: list[str] = Field(default_factory=list)
    target_word_count: int = 8000
    reference_doc_ids: list[int] = Field(default_factory=list)
    additional_context: str = ""


class PaperProjectSummary(BaseModel):
    id: str
    name: str
    status: str = ""
    created_at: str = ""
    updated_at: str = ""


class PaperSectionResponse(BaseModel):
    id: str = ""
    title: str = ""
    level: int = 1
    outline_points: list[str] = Field(default_factory=list)
    content: str = ""
    word_count: int = 0
    status: str = "pending"
    citations: list[str] = Field(default_factory=list)


class PaperOutlineResponse(BaseModel):
    abstract_draft: str = ""
    sections: list[PaperSectionResponse] = Field(default_factory=list)
    estimated_word_count: int = 0


class CitationRefResponse(BaseModel):
    key: str = ""
    title: str = ""
    authors: str = ""
    year: str = ""
    venue: str = ""
    source: str = ""
    has_full_analysis: bool = False


class PaperProjectResponse(BaseModel):
    id: str
    name: str
    status: str = ""
    language: str = "zh"
    venue: str = "generic"
    topic: str = ""
    research_question: str = ""
    key_contributions: list[str] = Field(default_factory=list)
    target_word_count: int = 8000
    outline: PaperOutlineResponse | None = None
    draft_title: str = ""
    draft_abstract: str = ""
    draft_sections: list[PaperSectionResponse] = Field(default_factory=list)
    draft_total_word_count: int = 0
    citations: list[CitationRefResponse] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class OutlineReviseRequest(BaseModel):
    feedback: str


class SectionWriteRequest(BaseModel):
    section_id: str = ""  # 空则写全部


class SectionReviseRequest(BaseModel):
    feedback: str


class PolishRequest(BaseModel):
    instructions: str = ""


class PaperExportRequest(BaseModel):
    format: str = "markdown"  # markdown/docx/pdf/latex


# --- Research ---

class ResearchRequest(BaseModel):
    max_papers: int = 10
    download_enabled: bool = True


class ResearchResultResponse(BaseModel):
    researched_doc_ids: list[int] = Field(default_factory=list)
    downloaded: int = 0
    analyzed: int = 0
    failed: int = 0


class ReferenceItem(BaseModel):
    doc_id: int
    title: str = ""
    summary: str = ""
    source_type: str = ""
    has_analysis: bool = False


class ReferencesResponse(BaseModel):
    references: list[ReferenceItem] = Field(default_factory=list)


# --- Templates ---

class TemplateSectionSchema(BaseModel):
    title: str
    description: str = ""
    required: bool = True


class TemplateResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: str = ""
    prompt_content: str = ""
    sections: list[TemplateSectionSchema] = Field(default_factory=list)
    is_builtin: bool = False
    created_at: str = ""
    updated_at: str = ""


class TemplateListResponse(BaseModel):
    templates: list[TemplateResponse] = Field(default_factory=list)


class CreateTemplateRequest(BaseModel):
    name: str
    display_name: str
    description: str = ""
    prompt_content: str = ""
    sections: list[TemplateSectionSchema] = Field(default_factory=list)


class UpdateTemplateRequest(BaseModel):
    display_name: str | None = None
    description: str | None = None
    prompt_content: str | None = None
    sections: list[TemplateSectionSchema] | None = None


# --- Reader ---

class ReaderDocumentResponse(BaseModel):
    id: int
    title: str
    file_name: str
    file_type: str
    file_path: str = ""
    total_pages: int = 0
    current_page: int = 1
    created_at: str = ""
    updated_at: str = ""


class ReaderDocumentListResponse(BaseModel):
    documents: list[ReaderDocumentResponse] = Field(default_factory=list)


class ReaderPageResponse(BaseModel):
    page_num: int
    content: str = ""


class ReaderProgressRequest(BaseModel):
    current_page: int


class ReaderChatRequest(BaseModel):
    message: str
    page_num: int = 1
    agent_mode: bool = False


class ReaderChatMessage(BaseModel):
    id: int
    role: str
    content: str
    page_num: int = 1
    created_at: str = ""


class ReaderChatResponse(BaseModel):
    reply: str
    message: ReaderChatMessage


class ReaderChatHistoryResponse(BaseModel):
    messages: list[ReaderChatMessage] = Field(default_factory=list)


# --- Reader Sessions ---

class CreateSessionRequest(BaseModel):
    title: str = "新对话"


class ReaderSessionResponse(BaseModel):
    id: int
    document_id: int
    title: str
    message_count: int = 0
    created_at: str = ""
    updated_at: str = ""


class ReaderSessionListResponse(BaseModel):
    sessions: list[ReaderSessionResponse] = Field(default_factory=list)


class SuggestedQuestionsResponse(BaseModel):
    questions: list[str] = Field(default_factory=list)
    page_num: int = 0
    cached: bool = False
