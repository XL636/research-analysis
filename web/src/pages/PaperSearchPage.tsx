import { useState, useCallback } from 'react'
import { Search, Loader2, Sparkles, Zap, ChevronDown, ChevronUp } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { usePaperSearch, useSmartSearch, useSaveToKB, useDownloadAndAnalyze } from '../hooks/usePaperSearch'
import SearchResultCard from '../components/paper-search/SearchResultCard'
import type { PaperSearchResultItem, SmartSearchResponse } from '../types'

type SearchMode = 'keyword' | 'smart'

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
  const [searchMode, setSearchMode] = useState<SearchMode>('keyword')

  // Track per-result save/download state
  const [savedMap, setSavedMap] = useState<Record<string, number>>({})
  const [savingKey, setSavingKey] = useState<string | null>(null)
  const [downloadingKey, setDownloadingKey] = useState<string | null>(null)
  const [showSearchLog, setShowSearchLog] = useState(false)

  const providersParam = selectedProviders.length > 0 ? selectedProviders.join(',') : undefined

  // Keyword search (useQuery)
  const { data: keywordData, isLoading: keywordLoading, isFetching: keywordFetching } = usePaperSearch({
    q: searchMode === 'keyword' ? searchQuery : '',
    providers: providersParam,
    max_results: maxResults,
  })

  // Smart search (useMutation)
  const smartSearch = useSmartSearch()
  const smartData = smartSearch.data as SmartSearchResponse | undefined

  const saveMutation = useSaveToKB()
  const downloadMutation = useDownloadAndAnalyze()

  const handleSearch = useCallback(() => {
    if (!inputValue.trim()) return
    setSavedMap({})
    if (searchMode === 'smart') {
      smartSearch.mutate({
        query: inputValue.trim(),
        providers: providersParam,
        max_results: maxResults,
      })
    }
    setSearchQuery(inputValue.trim())
  }, [inputValue, searchMode, providersParam, maxResults, smartSearch])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch()
  }

  const toggleProvider = (key: string) => {
    if (key === 'all') {
      setSelectedProviders([])
    } else {
      setSelectedProviders(prev =>
        prev.includes(key) ? prev.filter(p => p !== key) : [...prev, key]
      )
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

  // Determine results and loading state based on mode
  const isSmartMode = searchMode === 'smart'
  const showLoading = isSmartMode
    ? smartSearch.isPending
    : (keywordLoading || keywordFetching)
  const results: PaperSearchResultItem[] = isSmartMode
    ? (smartData?.results || [])
    : (keywordData?.results || [])
  const hasSearched = isSmartMode
    ? (smartSearch.isSuccess || smartSearch.isError)
    : !!searchQuery

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-heading font-bold text-gray-900 mb-6">
        {t('paperSearch.title')}
      </h1>

      {/* Mode toggle */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-lg w-fit mb-4">
        <button
          onClick={() => { setSearchMode('keyword'); setSearchQuery(''); smartSearch.reset() }}
          className={`inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            searchMode === 'keyword'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <Zap className="h-4 w-4" />
          {t('paperSearch.modeKeyword')}
        </button>
        <button
          onClick={() => { setSearchMode('smart'); setSearchQuery(''); smartSearch.reset() }}
          className={`inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            searchMode === 'smart'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <Sparkles className="h-4 w-4" />
          {t('paperSearch.modeSmart')}
        </button>
      </div>

      {/* Search bar */}
      <div className="flex gap-2 mb-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isSmartMode ? t('paperSearch.smartPlaceholder') : t('paperSearch.placeholder')}
            className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-300 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={!inputValue.trim() || showLoading}
          className={`px-5 py-2.5 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 ${
            isSmartMode
              ? 'bg-violet-600 hover:bg-violet-700'
              : 'bg-primary-600 hover:bg-primary-700'
          }`}
        >
          {showLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : isSmartMode ? (
            <Sparkles className="h-4 w-4" />
          ) : (
            <Search className="h-4 w-4" />
          )}
          {isSmartMode ? t('paperSearch.smartSearch') : t('paperSearch.search')}
        </button>
      </div>

      {/* Provider filters + result count selector */}
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

        <select
          value={maxResults}
          onChange={e => setMaxResults(Number(e.target.value))}
          className="px-3 py-1.5 text-sm rounded-full border border-gray-300 bg-white text-gray-600 outline-none"
        >
          {isSmartMode ? (
            <>
              <option value={10}>10 {t('paperSearch.results')}</option>
              <option value={20}>20 {t('paperSearch.results')}</option>
              <option value={30}>30 {t('paperSearch.results')}</option>
            </>
          ) : (
            <>
              <option value={3}>3 {t('paperSearch.perProvider')}</option>
              <option value={5}>5 {t('paperSearch.perProvider')}</option>
              <option value={10}>10 {t('paperSearch.perProvider')}</option>
              <option value={20}>20 {t('paperSearch.perProvider')}</option>
            </>
          )}
        </select>
      </div>

      {/* Loading */}
      {showLoading && (
        <div className="flex flex-col items-center justify-center py-16 text-gray-400">
          <Loader2 className="h-8 w-8 animate-spin mb-3" />
          <p>{isSmartMode ? t('paperSearch.smartSearching') : t('paperSearch.searching')}</p>
        </div>
      )}

      {/* Smart search intent card */}
      {!showLoading && isSmartMode && smartData && (
        <div className="mb-4 p-4 bg-violet-50 border border-violet-200 rounded-xl">
          <p className="text-sm font-medium text-violet-900 mb-2">
            {smartData.interpreted_intent}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {smartData.generated_keywords.map((kw, i) => (
              <span key={i} className="px-2 py-0.5 text-xs bg-violet-100 text-violet-700 rounded-full">
                {kw}
              </span>
            ))}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-violet-500">
            <span>
              {t('paperSearch.smartStats', {
                total: smartData.total_candidates,
                filtered: smartData.results.length,
                providers: smartData.providers_used.length,
              })}
            </span>
            {(smartData.iterations_used ?? 1) > 1 && (
              <span className="px-1.5 py-0.5 bg-violet-100 text-violet-700 rounded">
                {t('paperSearch.iterationsUsed')}: {t('paperSearch.iterationRounds', { count: smartData.iterations_used })}
              </span>
            )}
            {smartData.domain_detected && (
              <span className="px-1.5 py-0.5 bg-violet-100 text-violet-700 rounded">
                {t('paperSearch.domainDetected')}: {smartData.domain_detected}
              </span>
            )}
            {(smartData.quality_score ?? 0) > 0 && (
              <span className="px-1.5 py-0.5 bg-violet-100 text-violet-700 rounded">
                {t('paperSearch.qualityScore')}: {((smartData.quality_score ?? 0) * 100).toFixed(0)}%
              </span>
            )}
          </div>
          {/* 搜索日志折叠面板（仅多轮时显示） */}
          {smartData.search_log && smartData.search_log.length > 0 && (smartData.iterations_used ?? 1) > 1 && (
            <div className="mt-3 border-t border-violet-200 pt-2">
              <button
                onClick={() => setShowSearchLog(!showSearchLog)}
                className="flex items-center gap-1 text-xs text-violet-600 hover:text-violet-800 transition-colors"
              >
                {showSearchLog ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                {showSearchLog ? t('paperSearch.hideSearchLog') : t('paperSearch.showSearchLog')}
              </button>
              {showSearchLog && (
                <div className="mt-2 p-2 bg-violet-100/50 rounded-lg text-xs text-violet-700 font-mono space-y-0.5 max-h-48 overflow-y-auto">
                  {smartData.search_log.map((log, i) => (
                    <div key={i}>{log}</div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Results */}
      {!showLoading && hasSearched && results.length > 0 && (
        <>
          {!isSmartMode && (
            <p className="text-sm text-gray-500 mb-4">
              {t('paperSearch.resultCount', {
                count: keywordData?.total || 0,
                providers: keywordData?.providers_used.length || 0,
              })}
            </p>
          )}
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

      {/* No results */}
      {!showLoading && hasSearched && results.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <Search className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="text-lg font-medium">{t('paperSearch.noResults')}</p>
          <p className="text-sm mt-1">{t('paperSearch.noResultsDesc')}</p>
        </div>
      )}

      {/* Empty state */}
      {!hasSearched && !showLoading && (
        <div className="text-center py-16 text-gray-400">
          {isSmartMode ? (
            <Sparkles className="h-12 w-12 mx-auto mb-3 opacity-50" />
          ) : (
            <Search className="h-12 w-12 mx-auto mb-3 opacity-50" />
          )}
          <p className="text-lg font-medium">
            {isSmartMode ? t('paperSearch.smartEmptyTitle') : t('paperSearch.emptyTitle')}
          </p>
          <p className="text-sm mt-1">
            {isSmartMode ? t('paperSearch.smartEmptyDesc') : t('paperSearch.emptyDesc')}
          </p>
        </div>
      )}
    </div>
  )
}
