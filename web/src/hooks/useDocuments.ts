import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listDocuments, getDocument, getTags, deleteDocument } from '../api/knowledge'

export function useDocuments(tag?: string) {
  return useQuery({
    queryKey: ['documents', tag],
    queryFn: () => listDocuments(tag),
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
    },
  })
}
