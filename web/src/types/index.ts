// Analysis Modes
export interface AnalysisModeInfo {
  id: string
  label_zh: string
  label_en: string
  description_zh: string
  description_en: string
  skip_review: boolean
  max_text_length: number
}

export interface AnalysisModesResponse {
  modes: AnalysisModeInfo[]
}

// Pipeline
export interface StepProgress {
  step: string
  status: 'pending' | 'running' | 'completed' | 'error'
  message: string
}

export interface PipelineRunResponse {
  run_id: string
  status: string
}

export interface PipelineResultResponse {
  run_id: string
  status: 'running' | 'completed' | 'error'
  report_content: string
  report_title: string
  output_format: string
  error: string
}

// Knowledge Base
export interface DocumentSummary {
  id: number
  title: string
  file_type: string
  tags: string
  date: string
  collection_id: number | null
  source_type?: string
}

export interface DocumentDetail {
  id: number
  title: string
  file_type: string
  file_path: string
  summary: string
  tags: string
  date: string
  analysis: AnalysisResult | null
  collection_id: number | null
  report_content: string | null
}

export interface UpdateTitleResponse {
  success: boolean
  title: string
}

export interface CollectionSummary {
  id: number
  name: string
  document_count: number
}

export interface MoveToCollectionRequest {
  collection_id: number | null
}

export interface SearchResult {
  id: number
  title: string
  file_type: string
  summary: string
  tags: string
  date: string
}

export interface TagCount {
  name: string
  count: number
}

export interface DeleteResponse {
  success: boolean
  message: string
}

export interface BatchDeleteResponse {
  success: boolean
  deleted_count: number
}

export interface DuplicateCheckResponse {
  has_duplicate: boolean
  existing_documents: DocumentSummary[]
}

// Analysis types
export interface KeyFinding {
  finding: string
  evidence: string
  significance: string
}

export interface MethodologyAssessment {
  approach: string
  strengths: string[]
  limitations: string[]
}

export interface AnalysisResult {
  document_title: string
  paper_type?: string  // empirical / theoretical / survey / opinion / technical
  summary: string
  key_findings: KeyFinding[]
  methodology: MethodologyAssessment
  contributions: string[]
  limitations: string[]
  future_work: string[]
  tags: string[]
  relevance_score: number
}

// Dashboard
export interface DashboardStats {
  total_documents: number
  recent_analyses: number
  avg_score: number
  top_tags: TagCount[]
  recent_documents: DocumentSummary[]
}

// Settings
export interface ProviderStatus {
  env_var: string
  provider: string
  configured: boolean
  masked_key: string
  models: string[]
}

export interface ApiKeyStatusResponse {
  providers: ProviderStatus[]
}

export interface ApiKeySaveRequest {
  keys: Record<string, string>
}

export interface ApiKeySaveResponse {
  success: boolean
  providers: ProviderStatus[]
}

// Search Providers
export interface SearchProviderStatus {
  name: string  // "semantic_scholar" | "openalex" | "arxiv"
  enabled: boolean
  api_key_env: string
  api_key_configured: boolean
  masked_key: string
}

export interface SearchProvidersResponse {
  providers: SearchProviderStatus[]
}

export interface SearchProviderSaveRequest {
  providers: Record<string, Record<string, unknown>>
  keys: Record<string, string>
}

export interface SearchProviderSaveResponse {
  success: boolean
  providers: SearchProviderStatus[]
}

// Agent Model Assignment
export interface ModelInfo {
  name: string
  provider: string
  api_key_env: string
  api_key_configured: boolean
}

export interface AgentModelAssignment {
  agent: string
  model: string
  provider: string
  api_key_env: string
  api_key_configured: boolean
}

export interface AgentModelsResponse {
  agent_models: AgentModelAssignment[]
  available_models: ModelInfo[]
}

export interface AgentModelsSaveRequest {
  agent_models: Record<string, string>
}

export interface AgentModelsSaveResponse {
  success: boolean
  agent_models: AgentModelAssignment[]
  available_models: ModelInfo[]
}

// Paper Writing
export interface PaperProjectSummary {
  id: string
  name: string
  status: string
  created_at: string
  updated_at: string
}

export interface PaperSectionResponse {
  id: string
  title: string
  level: number
  outline_points: string[]
  content: string
  word_count: number
  status: string
  citations: string[]
}

export interface PaperOutlineResponse {
  abstract_draft: string
  sections: PaperSectionResponse[]
  estimated_word_count: number
}

export interface CitationRefResponse {
  key: string
  title: string
  authors: string
  year: string
  venue: string
  source: string
  has_full_analysis: boolean
}

export interface PaperProjectResponse {
  id: string
  name: string
  status: string
  language: string
  venue: string
  topic: string
  research_question: string
  key_contributions: string[]
  target_word_count: number
  outline: PaperOutlineResponse | null
  draft_title: string
  draft_abstract: string
  draft_sections: PaperSectionResponse[]
  draft_total_word_count: number
  citations: CitationRefResponse[]
  created_at: string
  updated_at: string
}

export interface CreatePaperRequest {
  name: string
  topic?: string
  language?: string
  venue?: string
  research_question?: string
  key_contributions?: string[]
  target_word_count?: number
  reference_doc_ids?: number[]
  additional_context?: string
}

// Research
export interface ResearchResultResponse {
  researched_doc_ids: number[]
  downloaded: number
  analyzed: number
  failed: number
}

export interface ReferenceItem {
  doc_id: number
  title: string
  summary: string
  source_type: string
  has_analysis: boolean
}

export interface ReferencesResponse {
  references: ReferenceItem[]
}
