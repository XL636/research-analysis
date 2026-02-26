import api from './client'
import type {
  ReaderDocument,
  ReaderDocumentListResponse,
  ReaderPage,
  ReaderChatResponse,
  ReaderChatHistoryResponse,
  DeleteResponse,
} from '../types'

export async function uploadReaderDocument(file: File): Promise<ReaderDocument> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/reader/upload', formData, {
    timeout: 120000,
  })
  return data
}

export async function listReaderDocuments(): Promise<ReaderDocument[]> {
  const { data } = await api.get<ReaderDocumentListResponse>('/reader/documents')
  return data.documents
}

export async function getReaderDocument(id: number): Promise<ReaderDocument> {
  const { data } = await api.get(`/reader/${id}`)
  return data
}

export async function deleteReaderDocument(id: number): Promise<DeleteResponse> {
  const { data } = await api.delete(`/reader/${id}`)
  return data
}

export async function getReaderPage(id: number, pageNum: number): Promise<ReaderPage> {
  const { data } = await api.get(`/reader/${id}/page/${pageNum}`)
  return data
}

export function getReaderFileUrl(id: number): string {
  return `/api/reader/${id}/file`
}

export async function updateReaderProgress(id: number, currentPage: number): Promise<ReaderDocument> {
  const { data } = await api.patch(`/reader/${id}/progress`, { current_page: currentPage })
  return data
}

export async function sendReaderChat(
  id: number,
  message: string,
  pageNum: number,
): Promise<ReaderChatResponse> {
  const { data } = await api.post(`/reader/${id}/chat`, {
    message,
    page_num: pageNum,
  }, {
    timeout: 120000,
  })
  return data
}

export async function getReaderChatHistory(id: number): Promise<ReaderChatHistoryResponse> {
  const { data } = await api.get(`/reader/${id}/chat/history`)
  return data
}

export async function clearReaderChatHistory(id: number): Promise<DeleteResponse> {
  const { data } = await api.delete(`/reader/${id}/chat/history`)
  return data
}
