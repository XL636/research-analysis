import api from './client'
import type {
  PaperSearchResponse,
  SmartSearchResponse,
  DownloadAnalyzeResponse,
  SummarizeResponse,
} from '../types'

export async function searchPapers(params: {
  q: string
  providers?: string
  max_results?: number
}): Promise<PaperSearchResponse> {
  const { data } = await api.get('/paper-search/search', { params, timeout: 60000 })
  return data
}

export async function smartSearchPapers(params: {
  query: string
  providers?: string
  max_results?: number
  language_hint?: string
}): Promise<SmartSearchResponse> {
  const body = {
    ...params,
    providers: params.providers ? params.providers.split(',') : undefined,
  }
  const { data } = await api.post('/paper-search/smart-search', body, {
    timeout: 300000,
  })
  return data
}

export async function summarizePaper(params: {
  title: string
  abstract: string
}): Promise<SummarizeResponse> {
  const { data } = await api.post('/paper-search/summarize', params, {
    timeout: 30000,
  })
  return data
}

export async function downloadAndAnalyze(paper: {
  title: string
  url: string
  doi?: string
  authors?: string
  year?: string
  venue?: string
  abstract?: string
  source?: string
}): Promise<DownloadAnalyzeResponse> {
  const { data } = await api.post('/paper-search/download-and-analyze', paper, {
    timeout: 120000,
  })
  return data
}
