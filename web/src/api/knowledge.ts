import api from './client'
import type { DocumentSummary, DocumentDetail, SearchResult, TagCount } from '../types'

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

export async function getTags(): Promise<TagCount[]> {
  const { data } = await api.get('/knowledge/tags')
  return data
}
