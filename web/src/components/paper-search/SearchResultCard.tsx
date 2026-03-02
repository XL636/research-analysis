import { useState } from 'react'
import { ExternalLink, BookmarkPlus, Download, FileDown, ChevronDown, ChevronUp, Loader2, Check, MessageSquare } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { PaperSearchResultItem, SmartSearchResultItem } from '../../types'

const SOURCE_COLORS: Record<string, string> = {
  pubmed: 'bg-emerald-100 text-emerald-700',
  arxiv: 'bg-red-100 text-red-700',
  biorxiv: 'bg-blue-100 text-blue-700',
  medrxiv: 'bg-sky-100 text-sky-700',
  semantic_scholar: 'bg-purple-100 text-purple-700',
  openalex: 'bg-orange-100 text-orange-700',
  crossref: 'bg-teal-100 text-teal-700',
}

const SOURCE_LABELS: Record<string, string> = {
  pubmed: 'PubMed',
  arxiv: 'arXiv',
  biorxiv: 'bioRxiv',
  medrxiv: 'medRxiv',
  semantic_scholar: 'Semantic Scholar',
  openalex: 'OpenAlex',
  crossref: 'CrossRef',
}

type AnalysisMode = 'quick' | 'standard' | 'deep'

function isSmartResult(r: PaperSearchResultItem): r is SmartSearchResultItem {
  return 'relevance_score' in r
}

function scoreBadgeColor(score: number): string {
  if (score >= 7) return 'bg-green-100 text-green-700 border-green-200'
  if (score >= 4) return 'bg-yellow-100 text-yellow-700 border-yellow-200'
  return 'bg-gray-100 text-gray-500 border-gray-200'
}

interface SearchResultCardProps {
  result: PaperSearchResultItem
  onSave: (result: PaperSearchResultItem, mode: AnalysisMode) => void
  onDownload: (result: PaperSearchResultItem, mode: AnalysisMode) => void
  onDownloadPdf?: (result: PaperSearchResultItem) => void
  onChat?: (result: PaperSearchResultItem) => void
  isSaving: boolean
  isDownloading: boolean
  isDownloadingPdf?: boolean
  savedDocId: number | null
}

export default function SearchResultCard({
  result,
  onSave,
  onDownload,
  onDownloadPdf,
  onChat,
  isSaving,
  isDownloading,
  isDownloadingPdf,
  savedDocId,
}: SearchResultCardProps) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const [mode, setMode] = useState<AnalysisMode>('quick')

  const badgeColor = SOURCE_COLORS[result.source] || 'bg-gray-100 text-gray-700'
  const sourceLabel = SOURCE_LABELS[result.source] || result.source

  const modeOptions: { value: AnalysisMode; labelKey: string }[] = [
    { value: 'quick', labelKey: 'paperSearch.modeQuick' },
    { value: 'standard', labelKey: 'paperSearch.modeStandard' },
    { value: 'deep', labelKey: 'paperSearch.modeDeep' },
  ]

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
      {/* Header: source badge + score badge + title */}
      <div className="flex items-start gap-3">
        <div className="shrink-0 mt-0.5 flex items-center gap-1.5">
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${badgeColor}`}>
            {sourceLabel}
          </span>
          {isSmartResult(result) && (
            <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${scoreBadgeColor(result.relevance_score)}`}>
              {result.relevance_score.toFixed(1)}
            </span>
          )}
        </div>
        <h3 className="text-base font-semibold text-gray-900 leading-snug flex-1">
          {result.title}
        </h3>
      </div>

      {/* Meta line */}
      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-gray-500">
        {result.authors && <span>{result.authors}</span>}
        {result.year && <span>{result.year}</span>}
        {result.venue && <span className="text-gray-400">| {result.venue}</span>}
      </div>

      {/* Relevance reason */}
      {isSmartResult(result) && result.relevance_reason && (
        <p className="mt-2 text-sm text-primary-600 italic">
          {result.relevance_reason}
        </p>
      )}

      {/* Abstract */}
      {result.abstract && (
        <div className="mt-3">
          <p className={`text-sm text-gray-600 leading-relaxed ${!expanded ? 'line-clamp-3' : ''}`}>
            {result.abstract}
          </p>
          {result.abstract.length > 150 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="mt-1 text-xs text-primary-600 hover:text-primary-800 flex items-center gap-0.5"
            >
              {expanded ? (
                <>
                  {t('paperSearch.collapse')} <ChevronUp className="h-3 w-3" />
                </>
              ) : (
                <>
                  {t('paperSearch.expand')} <ChevronDown className="h-3 w-3" />
                </>
              )}
            </button>
          )}
        </div>
      )}

      {/* Mode selector */}
      <div className="mt-3 flex items-center gap-1.5">
        {modeOptions.map(({ value, labelKey }) => (
          <button
            key={value}
            onClick={() => setMode(value)}
            className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
              mode === value
                ? 'bg-primary-600 text-white border-primary-600'
                : 'bg-white text-gray-500 border-gray-300 hover:border-primary-400'
            }`}
          >
            {t(labelKey)}
          </button>
        ))}
      </div>

      {/* Actions */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          onClick={() => onSave(result, mode)}
          disabled={isSaving || savedDocId !== null}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSaving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : savedDocId !== null ? (
            <Check className="h-4 w-4 text-green-600" />
          ) : (
            <BookmarkPlus className="h-4 w-4" />
          )}
          {savedDocId !== null ? t('paperSearch.saved') : t('paperSearch.saveToKB')}
        </button>

        {onChat && (
          <button
            onClick={() => onChat(result)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-primary-300 text-primary-700 hover:bg-primary-50 transition-colors"
          >
            <MessageSquare className="h-4 w-4" />
            {t('paperSearch.chatAbout')}
          </button>
        )}

        {result.url && (
          <>
            <button
              onClick={() => onDownload(result, mode)}
              disabled={isDownloading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isDownloading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              {t('paperSearch.downloadAnalyze')}
            </button>

            {onDownloadPdf && (
              <button
                onClick={() => onDownloadPdf(result)}
                disabled={isDownloadingPdf}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isDownloadingPdf ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileDown className="h-4 w-4" />
                )}
                {t('paperSearch.downloadPdf')}
              </button>
            )}

            <a
              href={result.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <ExternalLink className="h-4 w-4" />
              {t('paperSearch.viewOriginal')}
            </a>
          </>
        )}
      </div>
    </div>
  )
}
