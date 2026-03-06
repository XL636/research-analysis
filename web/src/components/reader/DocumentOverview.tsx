import { RefreshCw, BookOpen, Tag, List, Sparkles } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { DocumentOverview as OverviewType } from '../../types'

interface DocumentOverviewProps {
  overview: OverviewType | undefined
  isLoading: boolean
  isGenerating: boolean
  hasError: boolean
  onGenerate: () => void
  onPageJump?: (page: number) => void
}

export default function DocumentOverview({
  overview,
  isLoading,
  isGenerating,
  hasError,
  onGenerate,
  onPageJump,
}: DocumentOverviewProps) {
  const { t } = useTranslation()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400">
        <div className="w-5 h-5 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin" />
      </div>
    )
  }

  if (!overview && !isGenerating) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
        <BookOpen className="w-10 h-10 text-gray-300 mb-3" />
        <p className="text-sm font-medium text-gray-500 mb-1">{t('reader.overviewEmpty')}</p>
        <p className="text-xs text-gray-400 mb-4">{t('reader.overviewEmptyDesc')}</p>
        <button
          onClick={onGenerate}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Sparkles className="w-4 h-4" />
          {t('reader.overviewGenerate')}
        </button>
      </div>
    )
  }

  if (isGenerating) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-400">
        <div className="w-6 h-6 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin mb-3" />
        <p className="text-sm">{t('reader.overviewGenerating')}</p>
      </div>
    )
  }

  if (!overview) return null

  return (
    <div className="p-4 space-y-5 overflow-y-auto">
      {/* Regenerate button */}
      <div className="flex justify-end">
        <button
          onClick={onGenerate}
          disabled={isGenerating}
          className="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-primary-600 transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
          {t('reader.overviewRegenerate')}
        </button>
      </div>

      {/* Summary */}
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <BookOpen className="w-4 h-4 text-primary-600" />
          <h4 className="text-sm font-semibold text-gray-800">{t('reader.overviewSummary')}</h4>
        </div>
        <p className="text-sm text-gray-600 leading-relaxed">{overview.summary}</p>
      </div>

      {/* Key Topics */}
      {overview.key_topics.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <Tag className="w-4 h-4 text-amber-500" />
            <h4 className="text-sm font-semibold text-gray-800">{t('reader.overviewTopics')}</h4>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {overview.key_topics.map((topic, i) => (
              <span
                key={i}
                className="px-2.5 py-1 bg-amber-50 text-amber-700 text-xs rounded-full border border-amber-200"
              >
                {topic}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Outline */}
      {overview.outline.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <List className="w-4 h-4 text-blue-500" />
            <h4 className="text-sm font-semibold text-gray-800">{t('reader.overviewOutline')}</h4>
          </div>
          <div className="space-y-1">
            {overview.outline.map((item, i) => (
              <button
                key={i}
                onClick={() => item.page_num > 0 && onPageJump?.(item.page_num)}
                className="w-full text-left flex items-start gap-2 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors group"
              >
                <span className="text-xs text-gray-400 font-mono mt-0.5 shrink-0">
                  {item.page_num > 0 ? `p.${item.page_num}` : ''}
                </span>
                <div className="min-w-0">
                  <div className="text-sm text-gray-800 font-medium group-hover:text-primary-600 transition-colors">
                    {item.title}
                  </div>
                  {item.description && (
                    <div className="text-xs text-gray-400 mt-0.5 truncate">{item.description}</div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
