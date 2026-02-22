import api from './client'
import type { DocumentSummary, DocumentDetail, SearchResult, TagCount, DeleteResponse, DuplicateCheckResponse } from '../types'

export async function searchDocuments(q: string, limit = 10): Promise<SearchResult[]> {
  const { data } = await api.get('/knowledge/search', { params: { q, limit } })
  return data
}

export async function listDocuments(tag?: string, limit = 20): Promise<DocumentSummary[]> {
  const { data } = await api.get('/knowledge/documents', { params: { tag, limit } })
  return data
}

export async function getDocument(id: number): Promise<DocumentDetail> {
  const { data } = await api.get(`/knowledge/documents/${id}`)
  return data
}

export async function deleteDocument(id: number): Promise<DeleteResponse> {
  const { data } = await api.delete(`/knowledge/documents/${id}`)
  return data
}

export async function checkDuplicate(filename: string): Promise<DuplicateCheckResponse> {
  const { data } = await api.get('/knowledge/documents/check-duplicate', { params: { filename } })
  return data
}

export function getDocumentReportUrl(docId: number, format: string): string {
  return `/api/knowledge/documents/${docId}/report?format=${format}`
}

export async function getTags(): Promise<TagCount[]> {
  const { data } = await api.get('/knowledge/tags')
  return data
}
