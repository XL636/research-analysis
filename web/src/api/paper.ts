import api from './client'
import type {
  PaperProjectSummary,
  PaperProjectResponse,
  CreatePaperRequest,
  DeleteResponse,
  ResearchResultResponse,
  ReferencesResponse,
} from '../types'

export async function listPaperProjects(limit = 20): Promise<PaperProjectSummary[]> {
  const { data } = await api.get('/paper/projects', { params: { limit } })
  return data
}

export async function getPaperProject(id: string): Promise<PaperProjectResponse> {
  const { data } = await api.get(`/paper/projects/${id}`)
  return data
}

export async function createPaperProject(payload: CreatePaperRequest): Promise<PaperProjectResponse> {
  const { data } = await api.post('/paper/projects', payload, { timeout: 120000 })
  return data
}

export async function deletePaperProject(id: string): Promise<DeleteResponse> {
  const { data } = await api.delete(`/paper/projects/${id}`)
  return data
}

export async function reviseOutline(id: string, feedback: string): Promise<PaperProjectResponse> {
  const { data } = await api.post(`/paper/projects/${id}/outline/revise`, { feedback }, { timeout: 120000 })
  return data
}

export async function confirmOutline(id: string): Promise<PaperProjectResponse> {
  const { data } = await api.post(`/paper/projects/${id}/outline/confirm`)
  return data
}

export async function writeSections(id: string, sectionId?: string): Promise<PaperProjectResponse> {
  const body = sectionId ? { section_id: sectionId } : {}
  const { data } = await api.post(`/paper/projects/${id}/write`, body, { timeout: 300000 })
  return data
}

export async function reviseSection(id: string, sectionId: string, feedback: string): Promise<PaperProjectResponse> {
  const { data } = await api.post(`/paper/projects/${id}/sections/${sectionId}/revise`, { feedback }, { timeout: 120000 })
  return data
}

export async function polishPaper(id: string, instructions?: string): Promise<PaperProjectResponse> {
  const { data } = await api.post(`/paper/projects/${id}/polish`, { instructions: instructions || '' }, { timeout: 300000 })
  return data
}

export async function exportPaper(id: string, format: string): Promise<{ success: boolean; output_path: string }> {
  const { data } = await api.get(`/paper/projects/${id}/export`, { params: { format } })
  return data
}

export async function researchPapers(id: string, maxPapers = 10): Promise<ResearchResultResponse> {
  const { data } = await api.post(`/paper/projects/${id}/research`, { max_papers: maxPapers }, { timeout: 300000 })
  return data
}

export async function getReferences(id: string): Promise<ReferencesResponse> {
  const { data } = await api.get(`/paper/projects/${id}/references`)
  return data
}
