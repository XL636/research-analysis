import api from './client'
import type {
  PaperSearchResponse,
  SmartSearchResponse,
  SaveToKBResponse,
  DownloadAnalyzeResponse,
  PaperAnalysisMode,
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
  const { data } = await api.post('/paper-search/smart-search', params, {
    timeout: 180000,
  })
  return data
}

export async function saveToKB(paper: {
  title: string
  authors?: string
  year?: string
  venue?: string
  doi?: string
  url?: string
  abstract?: string
  source?: string
  mode?: PaperAnalysisMode
}): Promise<SaveToKBResponse> {
  const { data } = await api.post('/paper-search/save-to-kb', paper)
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
  mode?: PaperAnalysisMode
}): Promise<DownloadAnalyzeResponse> {
  const { data } = await api.post('/paper-search/download-and-analyze', paper, {
    timeout: 120000,
  })
  return data
}

export async function downloadPdf(url: string, title: string): Promise<void> {
  const { data } = await api.post('/paper-search/download-pdf', { url, title }, {
    responseType: 'blob',
    timeout: 60000,
  })
  const blobUrl = URL.createObjectURL(data as Blob)
  const a = document.createElement('a')
  a.href = blobUrl
  a.download = title.slice(0, 60) + '.pdf'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(blobUrl), 100)
}

// --- Paper Chat SSE ---

export interface PaperChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export async function streamPaperChat(
  params: {
    title: string
    abstract: string
    authors: string
    year: string
    venue: string
    message: string
    history: PaperChatMessage[]
  },
  onDelta: (content: string) => void,
  onDone: () => void,
  onError: (error: string) => void,
): Promise<void> {
  const resp = await fetch('/api/paper-search/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
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
        else if (data.type === 'done') onDone()
        else if (data.type === 'error') onError(data.message)
      } catch {
        // 忽略格式不正确的 SSE 行
      }
    }
  }
}
