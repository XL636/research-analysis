import api from './client'
import type {
  DocumentSummary,
  DocumentDetail,
  SearchResult,
  TagCount,
  DeleteResponse,
  DuplicateCheckResponse,
  UpdateTitleResponse,
  CollectionSummary,
} from '../types'

export async function searchDocuments(q: string, limit = 10): Promise<SearchResult[]> {
  const { data } = await api.get('/knowledge/search', { params: { q, limit } })
  return data
}

export async function listDocuments(params?: {
  tag?: string
  limit?: number
  collection_id?: number
  uncategorized?: boolean
  source_type?: string
}): Promise<DocumentSummary[]> {
  const { data } = await api.get('/knowledge/documents', { params })
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

export async function updateDocumentTitle(id: number, title: string): Promise<UpdateTitleResponse> {
  const { data } = await api.patch(`/knowledge/documents/${id}/title`, { title })
  return data
}

export async function moveDocumentToCollection(docId: number, collectionId: number | null): Promise<DeleteResponse> {
  const { data } = await api.patch(`/knowledge/documents/${docId}/collection`, { collection_id: collectionId })
  return data
}

export async function listCollections(): Promise<CollectionSummary[]> {
  const { data } = await api.get('/knowledge/collections')
  return data
}

export async function createCollection(name: string): Promise<CollectionSummary> {
  const { data } = await api.post('/knowledge/collections', { name })
  return data
}

export async function renameCollection(id: number, name: string): Promise<DeleteResponse> {
  const { data } = await api.patch(`/knowledge/collections/${id}`, { name })
  return data
}

export async function deleteCollection(id: number): Promise<DeleteResponse> {
  const { data } = await api.delete(`/knowledge/collections/${id}`)
  return data
}
