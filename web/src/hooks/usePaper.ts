import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listPaperProjects,
  getPaperProject,
  createPaperProject,
  deletePaperProject,
  regenerateOutline,
  reviseOutline,
  confirmOutline,
  writeSections,
  reviseSection,
  polishPaper,
  exportPaper,
  researchPapers,
  getReferences,
} from '../api/paper'
import type { CreatePaperRequest } from '../types'

export function usePaperProjects(limit = 20) {
  return useQuery({
    queryKey: ['paperProjects', limit],
    queryFn: () => listPaperProjects(limit),
  })
}

export function usePaperProject(id: string) {
  return useQuery({
    queryKey: ['paperProject', id],
    queryFn: () => getPaperProject(id),
    enabled: !!id,
  })
}

export function useCreatePaper() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreatePaperRequest) => createPaperProject(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['paperProjects'] })
    },
  })
}

export function useDeletePaper() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deletePaperProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['paperProjects'] })
    },
  })
}

export function useRegenerateOutline() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => regenerateOutline(id),
    onSuccess: (data) => {
      queryClient.setQueryData(['paperProject', data.id], data)
    },
  })
}

export function useReviseOutline() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, feedback }: { id: string; feedback: string }) =>
      reviseOutline(id, feedback),
    onSuccess: (data) => {
      queryClient.setQueryData(['paperProject', data.id], data)
    },
  })
}

export function useConfirmOutline() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => confirmOutline(id),
    onSuccess: (data) => {
      queryClient.setQueryData(['paperProject', data.id], data)
    },
  })
}

export function useWriteSections() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, sectionId }: { id: string; sectionId?: string }) =>
      writeSections(id, sectionId),
    onSuccess: (data) => {
      queryClient.setQueryData(['paperProject', data.id], data)
    },
  })
}

export function useReviseSection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, sectionId, feedback }: { id: string; sectionId: string; feedback: string }) =>
      reviseSection(id, sectionId, feedback),
    onSuccess: (data) => {
      queryClient.setQueryData(['paperProject', data.id], data)
    },
  })
}

export function usePolishPaper() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, instructions }: { id: string; instructions?: string }) =>
      polishPaper(id, instructions),
    onSuccess: (data) => {
      queryClient.setQueryData(['paperProject', data.id], data)
    },
  })
}

export function useExportPaper() {
  return useMutation({
    mutationFn: ({ id, format }: { id: string; format: string }) =>
      exportPaper(id, format),
  })
}

export function useResearchPapers() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, maxPapers }: { id: string; maxPapers?: number }) =>
      researchPapers(id, maxPapers),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['paperProject', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['paperReferences', variables.id] })
    },
  })
}

export function useReferences(id: string) {
  return useQuery({
    queryKey: ['paperReferences', id],
    queryFn: () => getReferences(id),
    enabled: !!id,
  })
}
