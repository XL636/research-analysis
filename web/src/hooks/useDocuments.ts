import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listDocuments,
  getDocument,
  getTags,
  deleteDocument,
  batchDeleteDocuments,
  updateDocumentTitle,
  moveDocumentToCollection,
  listCollections,
  createCollection,
  renameCollection,
  deleteCollection,
} from '../api/knowledge'

export function useDocuments(params?: {
  tag?: string
  collection_id?: number
  uncategorized?: boolean
  source_type?: string
}) {
  return useQuery({
    queryKey: ['documents', params],
    queryFn: () => listDocuments(params),
  })
}

export function useDocument(id: number) {
  return useQuery({
    queryKey: ['document', id],
    queryFn: () => getDocument(id),
    enabled: id > 0,
  })
}

export function useTags() {
  return useQuery({
    queryKey: ['tags'],
    queryFn: getTags,
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      queryClient.invalidateQueries({ queryKey: ['search'] })
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

export function useBatchDeleteDocuments() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (ids: number[]) => batchDeleteDocuments(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      queryClient.invalidateQueries({ queryKey: ['search'] })
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

export function useUpdateDocumentTitle() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, title }: { id: number; title: string }) =>
      updateDocumentTitle(id, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document'] })
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['search'] })
    },
  })
}

export function useCollections() {
  return useQuery({
    queryKey: ['collections'],
    queryFn: listCollections,
  })
}

export function useCreateCollection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => createCollection(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

export function useRenameCollection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      renameCollection(id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

export function useDeleteCollection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteCollection(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}

export function useMoveDocumentToCollection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ docId, collectionId }: { docId: number; collectionId: number | null }) =>
      moveDocumentToCollection(docId, collectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document'] })
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}
