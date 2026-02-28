import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { searchPapers, smartSearchPapers, saveToKB, downloadAndAnalyze } from '../api/paperSearch'

export function usePaperSearch(params: {
  q: string
  providers?: string
  max_results?: number
}) {
  return useQuery({
    queryKey: ['paper-search', params],
    queryFn: () => searchPapers(params),
    enabled: params.q.length > 0,
    staleTime: 5 * 60 * 1000, // 5 min cache
  })
}

export function useSmartSearch() {
  return useMutation({
    mutationFn: smartSearchPapers,
  })
}

export function useSaveToKB() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: saveToKB,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}

export function useDownloadAndAnalyze() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: downloadAndAnalyze,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}
