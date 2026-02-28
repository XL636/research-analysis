import { useState, useCallback } from 'react'
import { Search, Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { usePaperSearch, useSaveToKB, useDownloadAndAnalyze } from '../hooks/usePaperSearch'
import SearchResultCard from '../components/paper-search/SearchResultCard'
import type { PaperSearchResultItem } from '../types'

const PROVIDER_OPTIONS = [
  { key: 'all', labelKey: 'paperSearch.providerAll' },
  { key: 'pubmed', labelKey: 'paperSearch.providerPubMed' },
  { key: 'biorxiv', labelKey: 'paperSearch.providerBiorxiv' },
  { key: 'arxiv', labelKey: 'paperSearch.providerArxiv' },
  { key: 'semantic_scholar', labelKey: 'paperSearch.providerS2' },
  { key: 'openalex', labelKey: 'paperSearch.providerOpenAlex' },
]

export default function PaperSearchPage() {
  const { t } = useTranslation()
  const [inputValue, setInputValue] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedProviders, setSelectedProviders] = useState<string[]>([])
  const [maxResults, setMaxResults] = useState(5)

  // Track per-result save/download state
  const [savedMap, setSavedMap] = useState<Record<string, number>>({})
  const [savingKey, setSavingKey] = useState<string | null>(null)
  const [downloadingKey, setDownloadingKey] = useState<string | null>(null)

  const providersParam = selectedProviders.length > 0 ? selectedProviders.join(',') : undefined

  const { data, isLoading, isFetching } = usePaperSearch({
    q: searchQuery,
    providers: providersParam,
    max_results: maxResults,
  })

  const saveMutation = useSaveToKB()
  const downloadMutation = useDownloadAndAnalyze()

  const handleSearch = useCallback(() => {
    if (inputValue.trim()) {
      setSearchQuery(inputValue.trim())
      setSavedMap({})
    }
  }, [inputValue])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch()
  }

  const toggleProvider = (key: string) => {
    if (key === 'all') {
      setSelectedProviders([])
    } else {
      setSelectedProviders(prev => {
        if (prev.includes(key)) {
          return prev.filter(p => p !== key)
        }
        return [...prev, key]
      })
    }
  }

  const resultKey = (r: PaperSearchResultItem) => `${r.source}:${r.title}`

  const handleSave = async (result: PaperSearchResultItem) => {
    const key = resultKey(result)
    setSavingKey(key)
    try {
      const resp = await saveMutation.mutateAsync({
        title: result.title,
        authors: result.authors,
        year: result.year,
        venue: result.venue,
        doi: result.doi,
        url: result.url,
        abstract: result.abstract,
        source: result.source,
      })
      if (resp.success) {
        setSavedMap(prev => ({ ...prev, [key]: resp.doc_id }))
      }
    } finally {
      setSavingKey(null)
    }
  }

  const handleDownload = async (result: PaperSearchResultItem) => {
    const key = resultKey(result)
    setDownloadingKey(key)
    try {
      const resp = await downloadMutation.mutateAsync({
        title: result.title,
        url: result.url,
        doi: result.doi,
        authors: result.authors,
        year: result.year,
        venue: result.venue,
        abstract: result.abstract,
        source: result.source,
      })
      if (resp.success && resp.doc_id) {
        setSavedMap(prev => ({ ...prev, [key]: resp.doc_id }))
      }
    } finally {
      setDownloadingKey(null)
    }
  }

  const results = data?.results || []
  const showLoading = isLoading || isFetching

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-heading font-bold text-gray-900 mb-6">
        {t('paperSearch.title')}
      </h1>

      {/* Search bar */}
      <div className="flex gap-2 mb-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('paperSearch.placeholder')}
            className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-300 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={!inputValue.trim() || showLoading}
          className="px-5 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {showLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          {t('paperSearch.search')}
        </button>
      </div>

      {/* Provider filters */}
      <div className="flex flex-wrap gap-2 mb-6">
        {PROVIDER_OPTIONS.map(({ key, labelKey }) => {
          const isActive = key === 'all' ? selectedProviders.length === 0 : selectedProviders.includes(key)
          return (
            <button
              key={key}
              onClick={() => toggleProvider(key)}
              className={`px-3 py-1.5 text-sm rounded-full border transition-colors ${
                isActive
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-primary-400'
              }`}
            >
              {t(labelKey)}
            </button>
          )
        })}

        {/* Max results selector */}
        <select
          value={maxResults}
          onChange={e => setMaxResults(Number(e.target.value))}
          className="px-3 py-1.5 text-sm rounded-full border border-gray-300 bg-white text-gray-600 outline-none"
        >
          <option value={3}>3 {t('paperSearch.perProvider')}</option>
          <option value={5}>5 {t('paperSearch.perProvider')}</option>
          <option value={10}>10 {t('paperSearch.perProvider')}</option>
          <option value={20}>20 {t('paperSearch.perProvider')}</option>
        </select>
      </div>

      {/* Results */}
      {showLoading && (
        <div className="flex flex-col items-center justify-center py-16 text-gray-400">
          <Loader2 className="h-8 w-8 animate-spin mb-3" />
          <p>{t('paperSearch.searching')}</p>
        </div>
      )}

      {!showLoading && searchQuery && results.length > 0 && (
        <>
          <p className="text-sm text-gray-500 mb-4">
            {t('paperSearch.resultCount', {
              count: data?.total || 0,
              providers: data?.providers_used.length || 0,
            })}
          </p>
          <div className="space-y-4">
            {results.map((result, idx) => (
              <SearchResultCard
                key={`${result.source}-${result.title}-${idx}`}
                result={result}
                onSave={handleSave}
                onDownload={handleDownload}
                isSaving={savingKey === resultKey(result)}
                isDownloading={downloadingKey === resultKey(result)}
                savedDocId={savedMap[resultKey(result)] ?? null}
              />
            ))}
          </div>
        </>
      )}

      {!showLoading && searchQuery && results.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <Search className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="text-lg font-medium">{t('paperSearch.noResults')}</p>
          <p className="text-sm mt-1">{t('paperSearch.noResultsDesc')}</p>
        </div>
      )}

      {!searchQuery && (
        <div className="text-center py-16 text-gray-400">
          <Search className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="text-lg font-medium">{t('paperSearch.emptyTitle')}</p>
          <p className="text-sm mt-1">{t('paperSearch.emptyDesc')}</p>
        </div>
      )}
    </div>
  )
}
