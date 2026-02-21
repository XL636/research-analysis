import { useQuery } from '@tanstack/react-query'
import { listDocuments, getDocument, getTags } from '../api/knowledge'

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
