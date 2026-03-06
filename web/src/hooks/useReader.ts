import { useState, useCallback, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listReaderDocuments,
  getReaderDocument,
  uploadReaderDocument,
  deleteReaderDocument,
  getReaderPage,
  updateReaderProgress,
  sendReaderChat,
  getReaderChatHistory,
  clearReaderChatHistory,
  listSessions,
  createSession,
  deleteSession,
  getSessionChatHistory,
  sendSessionChat,
  clearSessionChatHistory,
  getSuggestedQuestions,
  streamSessionChat,
  getDocumentOverview,
  regenerateOverview,
  listNotes,
  createNote,
  updateNote,
  deleteNote,
  generateStudyGuide,
  generateFaq,
} from '../api/reader'
import type { ReaderChatMessage } from '../types'

export function useReaderDocuments() {
  return useQuery({
    queryKey: ['readerDocuments'],
    queryFn: listReaderDocuments,
  })
}

export function useReaderDocument(id: number) {
  return useQuery({
    queryKey: ['readerDocument', id],
    queryFn: () => getReaderDocument(id),
    enabled: id > 0,
  })
}

export function useUploadReaderDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => uploadReaderDocument(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['readerDocuments'] })
    },
  })
}

export function useDeleteReaderDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteReaderDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['readerDocuments'] })
    },
  })
}

export function useReaderPage(id: number, pageNum: number) {
  return useQuery({
    queryKey: ['readerPage', id, pageNum],
    queryFn: () => getReaderPage(id, pageNum),
    enabled: id > 0 && pageNum > 0,
  })
}

export function useUpdateReaderProgress() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, currentPage }: { id: number; currentPage: number }) =>
      updateReaderProgress(id, currentPage),
    onSuccess: (data) => {
      queryClient.setQueryData(['readerDocument', data.id], data)
    },
  })
}

// Legacy hooks (still functional)
export function useSendReaderChat() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, message, pageNum }: { id: number; message: string; pageNum: number }) =>
      sendReaderChat(id, message, pageNum),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: ['readerChatHistory', vars.id] })
    },
  })
}

export function useReaderChatHistory(id: number) {
  return useQuery({
    queryKey: ['readerChatHistory', id],
    queryFn: () => getReaderChatHistory(id),
    enabled: id > 0,
  })
}

export function useClearReaderChat() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => clearReaderChatHistory(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ['readerChatHistory', id] })
    },
  })
}

// Session hooks
export function useReaderSessions(docId: number) {
  return useQuery({
    queryKey: ['readerSessions', docId],
    queryFn: () => listSessions(docId),
    enabled: docId > 0,
  })
}

export function useCreateReaderSession() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ docId, title }: { docId: number; title?: string }) =>
      createSession(docId, title),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: ['readerSessions', vars.docId] })
    },
  })
}

export function useDeleteReaderSession() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ docId, sessionId }: { docId: number; sessionId: number }) =>
      deleteSession(docId, sessionId),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: ['readerSessions', vars.docId] })
    },
  })
}

export function useSessionChatHistory(docId: number, sessionId: number) {
  return useQuery({
    queryKey: ['sessionChatHistory', docId, sessionId],
    queryFn: () => getSessionChatHistory(docId, sessionId),
    enabled: docId > 0 && sessionId > 0,
  })
}

export function useSendSessionChat() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ docId, sessionId, message, pageNum }: {
      docId: number; sessionId: number; message: string; pageNum: number
    }) => sendSessionChat(docId, sessionId, message, pageNum),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: ['sessionChatHistory', vars.docId, vars.sessionId] })
      queryClient.invalidateQueries({ queryKey: ['readerSessions', vars.docId] })
    },
  })
}

export function useClearSessionChat() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ docId, sessionId }: { docId: number; sessionId: number }) =>
      clearSessionChatHistory(docId, sessionId),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: ['sessionChatHistory', vars.docId, vars.sessionId] })
      queryClient.invalidateQueries({ queryKey: ['readerSessions', vars.docId] })
    },
  })
}

// Suggestions hook
export function useReaderSuggestions(docId: number, pageNum: number) {
  return useQuery({
    queryKey: ['readerSuggestions', docId, pageNum],
    queryFn: () => getSuggestedQuestions(docId, pageNum),
    enabled: docId > 0 && pageNum > 0,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  })
}

// Overview hooks
export function useDocumentOverview(docId: number) {
  return useQuery({
    queryKey: ['documentOverview', docId],
    queryFn: () => getDocumentOverview(docId),
    enabled: docId > 0,
    retry: false, // Don't retry 404 (overview not generated yet)
  })
}

export function useRegenerateOverview() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (docId: number) => regenerateOverview(docId),
    onSuccess: (data) => {
      queryClient.setQueryData(['documentOverview', data.document_id], data)
    },
  })
}

// Notes hooks
export function useReaderNotes(docId: number) {
  return useQuery({
    queryKey: ['readerNotes', docId],
    queryFn: () => listNotes(docId),
    enabled: docId > 0,
  })
}

export function useCreateNote() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ docId, content, pageNum, source, sourceMessageId }: {
      docId: number; content: string; pageNum?: number; source?: string; sourceMessageId?: number
    }) => createNote(docId, content, pageNum, source, sourceMessageId),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: ['readerNotes', vars.docId] })
    },
  })
}

export function useUpdateNote() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ docId, noteId, content, pageNum }: {
      docId: number; noteId: number; content: string; pageNum?: number
    }) => updateNote(docId, noteId, content, pageNum),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: ['readerNotes', vars.docId] })
    },
  })
}

export function useDeleteNote() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ docId, noteId }: { docId: number; noteId: number }) =>
      deleteNote(docId, noteId),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: ['readerNotes', vars.docId] })
    },
  })
}

// Study tools hooks
export function useGenerateStudyGuide() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ docId, saveAsNote, focus }: { docId: number; saveAsNote?: boolean; focus?: string }) =>
      generateStudyGuide(docId, saveAsNote, focus),
    onSuccess: (_data, vars) => {
      if (vars.saveAsNote) {
        queryClient.invalidateQueries({ queryKey: ['readerNotes', vars.docId] })
      }
    },
  })
}

export function useGenerateFaq() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ docId, saveAsNote }: { docId: number; saveAsNote?: boolean }) =>
      generateFaq(docId, saveAsNote),
    onSuccess: (_data, vars) => {
      if (vars.saveAsNote) {
        queryClient.invalidateQueries({ queryKey: ['readerNotes', vars.docId] })
      }
    },
  })
}

// Agent step type for tool use tracking
export interface AgentStep {
  type: 'tool_use' | 'tool_result'
  tool: string
  detail: string
}

// Stream chat hook
export function useStreamChat() {
  const queryClient = useQueryClient()
  const [streamingContent, setStreamingContent] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([])
  const abortRef = useRef(false)

  const send = useCallback(async (params: {
    docId: number
    sessionId: number
    message: string
    pageNum: number
    agentMode?: boolean
  }) => {
    const { docId, sessionId, message, pageNum, agentMode } = params
    setStreamingContent('')
    setIsStreaming(true)
    setError(null)
    setAgentSteps([])
    abortRef.current = false

    try {
      await streamSessionChat(
        docId,
        sessionId,
        message,
        pageNum,
        // onDelta
        (content: string) => {
          if (!abortRef.current) {
            setStreamingContent(prev => prev + content)
          }
        },
        // onDone
        (_msg: ReaderChatMessage) => {
          setStreamingContent('')
          setIsStreaming(false)
          setAgentSteps([])
          queryClient.invalidateQueries({ queryKey: ['sessionChatHistory', docId, sessionId] })
          queryClient.invalidateQueries({ queryKey: ['readerSessions', docId] })
        },
        // onError
        (errMsg: string) => {
          setError(errMsg)
          setIsStreaming(false)
          setStreamingContent('')
          setAgentSteps([])
        },
        // options
        {
          agentMode,
          onToolUse: (tool: string, args: Record<string, unknown>) => {
            setAgentSteps(prev => [...prev, {
              type: 'tool_use',
              tool,
              detail: JSON.stringify(args),
            }])
          },
          onToolResult: (tool: string, summary: string) => {
            setAgentSteps(prev => [...prev, {
              type: 'tool_result',
              tool,
              detail: summary,
            }])
          },
        },
      )
    } catch (e) {
      setError(String(e))
      setIsStreaming(false)
      setStreamingContent('')
      setAgentSteps([])
    }
  }, [queryClient])

  return { send, streamingContent, isStreaming, error, agentSteps }
}
