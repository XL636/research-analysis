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
} from '../api/reader'

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
