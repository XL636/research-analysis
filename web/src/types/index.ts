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
