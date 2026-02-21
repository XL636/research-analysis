import api from './client'
import type { PipelineRunResponse, PipelineResultResponse } from '../types'

export async function startPipeline(
  files: File[],
  format: string = 'markdown',
  synthesize: boolean = false,
): Promise<PipelineRunResponse> {
  const formData = new FormData()
  files.forEach(f => formData.append('files', f))
  formData.append('format', format)
  formData.append('synthesize', String(synthesize))
  const { data } = await api.post('/pipeline/run', formData)
  return data
}

export async function getPipelineResult(runId: string): Promise<PipelineResultResponse> {
  const { data } = await api.get(`/pipeline/${runId}/result`)
  return data
}

export function getProgressUrl(runId: string): string {
  return `/api/pipeline/${runId}/progress`
}

export function getDownloadUrl(runId: string, format: string = 'markdown'): string {
  return `/api/reports/${runId}/download?format=${format}`
}
