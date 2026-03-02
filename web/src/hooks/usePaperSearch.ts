import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { searchPapers, smartSearchPapers, downloadAndAnalyze } from '../api/paperSearch'

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

export function useDownloadAndAnalyze() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: downloadAndAnalyze,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}
