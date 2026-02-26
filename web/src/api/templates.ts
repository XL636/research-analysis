import api from './client'
import type { TemplateListResponse, ReportTemplate, CreateTemplateRequest, UpdateTemplateRequest } from '../types'

export async function getTemplates(): Promise<TemplateListResponse> {
  const { data } = await api.get('/templates/')
  return data
}

export async function getTemplate(id: number): Promise<ReportTemplate> {
  const { data } = await api.get(`/templates/${id}`)
  return data
}

export async function createTemplate(req: CreateTemplateRequest): Promise<ReportTemplate> {
  const { data } = await api.post('/templates/', req)
  return data
}

export async function updateTemplate(id: number, req: UpdateTemplateRequest): Promise<ReportTemplate> {
  const { data } = await api.put(`/templates/${id}`, req)
  return data
}

export async function deleteTemplate(id: number): Promise<void> {
  await api.delete(`/templates/${id}`)
}
