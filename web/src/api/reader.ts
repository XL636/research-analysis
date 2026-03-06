import api from './client'
import type {
  ReaderDocument,
  ReaderDocumentListResponse,
  ReaderPage,
  ReaderChatMessage,
  ReaderChatResponse,
  ReaderChatHistoryResponse,
  ReaderSession,
  ReaderSessionListResponse,
  SuggestedQuestionsResponse,
  DeleteResponse,
  DocumentOverview,
  ReaderNote,
  NoteListResponse,
  StudyGuideResponse,
  FaqResponse,
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

// Legacy chat endpoints (still work, use latest session internally)
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

// Session endpoints
export async function listSessions(docId: number): Promise<ReaderSession[]> {
  const { data } = await api.get<ReaderSessionListResponse>(`/reader/${docId}/sessions`)
  return data.sessions
}

export async function createSession(docId: number, title?: string): Promise<ReaderSession> {
  const { data } = await api.post(`/reader/${docId}/sessions`, title ? { title } : {})
  return data
}

export async function deleteSession(docId: number, sessionId: number): Promise<DeleteResponse> {
  const { data } = await api.delete(`/reader/${docId}/sessions/${sessionId}`)
  return data
}

export async function getSessionChatHistory(docId: number, sessionId: number): Promise<ReaderChatHistoryResponse> {
  const { data } = await api.get(`/reader/${docId}/sessions/${sessionId}/history`)
  return data
}

export async function sendSessionChat(
  docId: number,
  sessionId: number,
  message: string,
  pageNum: number,
): Promise<ReaderChatResponse> {
  const { data } = await api.post(`/reader/${docId}/sessions/${sessionId}/chat`, {
    message,
    page_num: pageNum,
  }, {
    timeout: 120000,
  })
  return data
}

export async function clearSessionChatHistory(docId: number, sessionId: number): Promise<DeleteResponse> {
  const { data } = await api.delete(`/reader/${docId}/sessions/${sessionId}/history`)
  return data
}

// Stream chat (SSE via POST)
export async function streamSessionChat(
  docId: number,
  sessionId: number,
  message: string,
  pageNum: number,
  onDelta: (content: string) => void,
  onDone: (message: ReaderChatMessage) => void,
  onError: (error: string) => void,
  options?: {
    agentMode?: boolean
    onToolUse?: (tool: string, args: Record<string, unknown>) => void
    onToolResult?: (tool: string, summary: string) => void
  },
): Promise<void> {
  const resp = await fetch(`/api/reader/${docId}/sessions/${sessionId}/stream-chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      page_num: pageNum,
      agent_mode: options?.agentMode ?? false,
    }),
  })

  if (!resp.ok) {
    onError(`HTTP ${resp.status}: ${resp.statusText}`)
    return
  }

  const reader = resp.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6))
        if (data.type === 'delta') onDelta(data.content)
        else if (data.type === 'done') onDone(data.message)
        else if (data.type === 'error') onError(data.message)
        else if (data.type === 'tool_use') options?.onToolUse?.(data.tool, data.args)
        else if (data.type === 'tool_result') options?.onToolResult?.(data.tool, data.summary)
      } catch {
        // ignore malformed SSE lines
      }
    }
  }
}

// Document Overview
export async function getDocumentOverview(docId: number): Promise<DocumentOverview> {
  const { data } = await api.get(`/reader/${docId}/overview`)
  return data
}

export async function regenerateOverview(docId: number): Promise<DocumentOverview> {
  const { data } = await api.post(`/reader/${docId}/overview/regenerate`, {}, { timeout: 120000 })
  return data
}

// Notes
export async function listNotes(docId: number, pageNum?: number): Promise<ReaderNote[]> {
  const params = pageNum !== undefined ? { page_num: pageNum } : {}
  const { data } = await api.get<NoteListResponse>(`/reader/${docId}/notes`, { params })
  return data.notes
}

export async function createNote(
  docId: number,
  content: string,
  pageNum?: number,
  source: string = 'manual',
  sourceMessageId?: number,
): Promise<ReaderNote> {
  const { data } = await api.post(`/reader/${docId}/notes`, {
    content, page_num: pageNum ?? null, source, source_message_id: sourceMessageId ?? null,
  })
  return data
}

export async function updateNote(docId: number, noteId: number, content: string, pageNum?: number): Promise<ReaderNote> {
  const { data } = await api.put(`/reader/${docId}/notes/${noteId}`, {
    content, page_num: pageNum ?? null,
  })
  return data
}

export async function deleteNote(docId: number, noteId: number): Promise<DeleteResponse> {
  const { data } = await api.delete(`/reader/${docId}/notes/${noteId}`)
  return data
}

// Study Tools
export async function generateStudyGuide(docId: number, focus: string = 'conceptual'): Promise<StudyGuideResponse> {
  const { data } = await api.post(`/reader/${docId}/generate/study-guide`, null, {
    params: { focus },
    timeout: 120000,
  })
  return data
}

export async function generateFaq(docId: number): Promise<FaqResponse> {
  const { data } = await api.post(`/reader/${docId}/generate/faq`, null, {
    timeout: 120000,
  })
  return data
}

// Suggested questions
export async function getSuggestedQuestions(docId: number, pageNum: number): Promise<SuggestedQuestionsResponse> {
  const { data } = await api.get(`/reader/${docId}/suggestions`, { params: { page_num: pageNum } })
  return data
}
