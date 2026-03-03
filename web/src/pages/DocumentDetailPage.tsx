import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  FileText,
  FileType,
  Presentation,
  Lightbulb,
  FlaskConical,
  Award,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  HelpCircle,
  Trash2,
  Download,
  Pencil,
  Check,
  X,
  FolderOpen,
  Info,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import {
  useDocument,
  useDeleteDocument,
  useUpdateDocumentTitle,
  useCollections,
  useMoveDocumentToCollection,
} from '../hooks/useDocuments'
import { getDocumentReportUrl } from '../api/knowledge'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'
import MarkdownRenderer from '../components/ui/MarkdownRenderer'
import type { AnalysisResult } from '../types'

function ScoreIndicator({ score }: { score: number }) {
  const { t } = useTranslation()
  const percentage = (score / 10) * 100
  const circumference = 2 * Math.PI * 54
  const strokeDashoffset = circumference - (percentage / 100) * circumference

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative h-36 w-36">
        <svg className="h-36 w-36 -rotate-90" viewBox="0 0 120 120">
          <circle
            cx="60"
            cy="60"
            r="54"
            fill="none"
            stroke="#E5E7EB"
            strokeWidth="8"
          />
          <circle
            cx="60"
            cy="60"
            r="54"
            fill="none"
            stroke="url(#scoreGradient)"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-500"
          />
          <defs>
            <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#6366F1" />
              <stop offset="100%" stopColor="#10B981" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-3xl font-heading font-bold text-primary-950">
            {score.toFixed(1)}
          </span>
        </div>
      </div>
      <p className="mt-2 text-sm text-gray-500">{t('detail.outOf10')}</p>
    </div>
  )
}

function PaperTypeBadge({ paperType }: { paperType?: string }) {
  const { t } = useTranslation()
  if (!paperType) return null

  const colorMap: Record<string, string> = {
    empirical: 'bg-blue-100 text-blue-800',
    theoretical: 'bg-purple-100 text-purple-800',
    survey: 'bg-teal-100 text-teal-800',
    opinion: 'bg-amber-100 text-amber-800',
    technical: 'bg-slate-100 text-slate-800',
  }

  const colorClass = colorMap[paperType] || 'bg-gray-100 text-gray-800'
  const label = t(`detail.paperType.${paperType}`, paperType)

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
      {label}
    </span>
  )
}

const PAPER_TYPE_METHODOLOGY_KEYS: Record<string, string> = {
  empirical: 'detail.methodology.empirical',
  theoretical: 'detail.methodology.theoretical',
  survey: 'detail.methodology.survey',
  opinion: 'detail.methodology.opinion',
  technical: 'detail.methodology.technical',
}

function AnalysisCards({ analysis }: { analysis: AnalysisResult }) {
  const { t } = useTranslation()

  // 防御性处理：metadata-only 或空分析数据
  if (!analysis.key_findings?.length && !analysis.methodology?.approach) {
    return (
      <div className="bg-surface-card rounded-xl shadow-sm p-6">
        <p className="text-gray-500">{analysis.summary || t('detail.noAnalysisDesc')}</p>
      </div>
    )
  }

  const methKey = analysis.paper_type && PAPER_TYPE_METHODOLOGY_KEYS[analysis.paper_type]
  const methodologyTitle = methKey ? t(methKey) : t('detail.methodology')

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="bg-surface-card rounded-xl shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <FileText className="h-5 w-5 text-primary-600" />
          <h2 className="font-heading text-lg font-semibold text-primary-950">
            {t('detail.summary')}
          </h2>
        </div>
        <p className="text-primary-950 leading-relaxed">{analysis.summary}</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Key Findings */}
        <div className="bg-surface-card rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb className="h-5 w-5 text-primary-600" />
            <h2 className="font-heading text-lg font-semibold text-primary-950">
              {t('detail.keyFindings')}
            </h2>
          </div>
          <ol className="space-y-4">
            {analysis.key_findings.map((kf, idx) => (
              <li key={idx} className="space-y-1">
                <p className="font-bold text-primary-950">
                  {idx + 1}. {kf.finding}
                </p>
                <p className="text-sm italic text-gray-600">{kf.evidence}</p>
                <p className="text-sm text-primary-950">{kf.significance}</p>
              </li>
            ))}
          </ol>
        </div>

        {/* Methodology */}
        <div className="bg-surface-card rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <FlaskConical className="h-5 w-5 text-primary-600" />
            <h2 className="font-heading text-lg font-semibold text-primary-950">
              {methodologyTitle}
            </h2>
          </div>
          <p className="text-primary-950 mb-4">{analysis.methodology.approach}</p>
          <div className="space-y-3">
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                {t('detail.strengths')}
              </h3>
              <ul className="space-y-1.5">
                {analysis.methodology.strengths.map((s, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-primary-950">
                    <span className="mt-0.5 text-emerald-500 shrink-0">&#10003;</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                {t('detail.limitations')}
              </h3>
              <ul className="space-y-1.5">
                {analysis.methodology.limitations.map((l, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-primary-950">
                    <span className="mt-0.5 text-red-500 shrink-0">&#10007;</span>
                    {l}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Contributions */}
        <div className="bg-surface-card rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <Award className="h-5 w-5 text-primary-600" />
            <h2 className="font-heading text-lg font-semibold text-primary-950">
              {t('detail.contributions')}
            </h2>
          </div>
          <ul className="space-y-2">
            {analysis.contributions.map((c, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-primary-950">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-primary-500 shrink-0" />
                {c}
              </li>
            ))}
          </ul>
        </div>

        {/* Limitations */}
        <div className="bg-surface-card rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="h-5 w-5 text-primary-600" />
            <h2 className="font-heading text-lg font-semibold text-primary-950">
              {t('detail.limitationsCard')}
            </h2>
          </div>
          <ul className="space-y-2">
            {analysis.limitations.map((l, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-primary-950">
                <AlertTriangle className="mt-0.5 h-4 w-4 text-amber-500 shrink-0" />
                {l}
              </li>
            ))}
          </ul>
        </div>

        {/* Future Work */}
        <div className="bg-surface-card rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <ArrowRight className="h-5 w-5 text-primary-600" />
            <h2 className="font-heading text-lg font-semibold text-primary-950">
              {t('detail.futureWork')}
            </h2>
          </div>
          <ul className="space-y-2">
            {analysis.future_work.map((fw, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-primary-950">
                <ArrowRight className="mt-0.5 h-4 w-4 text-primary-500 shrink-0" />
                {fw}
              </li>
            ))}
          </ul>
        </div>

        {/* Relevance Score */}
        <div className="bg-surface-card rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="h-5 w-5 text-primary-600" />
            <h2 className="font-heading text-lg font-semibold text-primary-950">
              {t('detail.relevanceScore')}
            </h2>
            <div className="relative group">
              <HelpCircle className="h-4 w-4 text-gray-400 cursor-help" />
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2
                              hidden group-hover:block w-56 p-2 text-xs text-white
                              bg-gray-800 rounded-lg shadow-lg z-10">
                {t('detail.relevanceScoreTooltip')}
                <div className="absolute top-full left-1/2 -translate-x-1/2
                                border-4 border-transparent border-t-gray-800" />
              </div>
            </div>
          </div>
          <ScoreIndicator score={analysis.relevance_score} />
        </div>
      </div>
    </div>
  )
}

const DOWNLOAD_FORMATS = [
  { value: 'markdown', label: 'Markdown', icon: FileText },
  { value: 'docx', label: 'DOCX', icon: FileType },
  { value: 'pptx', label: 'PPTX', icon: Presentation },
  { value: 'pdf', label: 'PDF', icon: FileText },
] as const

export default function DocumentDetailPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { id } = useParams()
  const { data: doc, isLoading } = useDocument(Number(id))
  const deleteMutation = useDeleteDocument()
  const titleMutation = useUpdateDocumentTitle()
  const { data: collections } = useCollections()
  const moveMutation = useMoveDocumentToCollection()
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isEditingTitle, setIsEditingTitle] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [activeTab, setActiveTab] = useState<'cards' | 'report' | 'original'>('cards')
  const [originalLoaded, setOriginalLoaded] = useState(false)

  const handleDelete = () => {
    deleteMutation.mutate(Number(id), {
      onSuccess: () => navigate('/knowledge'),
    })
  }

  const handleStartEditTitle = () => {
    if (doc) {
      setEditTitle(doc.title)
      setIsEditingTitle(true)
    }
  }

  const handleSaveTitle = () => {
    const trimmed = editTitle.trim()
    if (trimmed && trimmed !== doc?.title) {
      titleMutation.mutate(
        { id: Number(id), title: trimmed },
        { onSuccess: () => setIsEditingTitle(false) },
      )
    } else {
      setIsEditingTitle(false)
    }
  }

  const handleCancelEditTitle = () => {
    setIsEditingTitle(false)
    setEditTitle('')
  }

  const handleTitleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSaveTitle()
    } else if (e.key === 'Escape') {
      handleCancelEditTitle()
    }
  }

  const handleCollectionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value
    const collectionId = value === '' ? null : Number(value)
    moveMutation.mutate({ docId: Number(id), collectionId })
  }

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-heading font-bold text-primary-950 mb-6">
          {t('detail.title')}
        </h1>
        <p className="text-gray-500">{t('common.loading')}</p>
      </div>
    )
  }

  if (!doc) {
    return (
      <div>
        <Link
          to="/knowledge"
          className="inline-flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-800 transition-colors duration-200 mb-6"
        >
          <ArrowLeft className="h-4 w-4" />
          {t('detail.backToKB')}
        </Link>
        <EmptyState
          icon={FileText}
          title={t('detail.notFoundTitle')}
          description={t('detail.notFoundDesc')}
        />
      </div>
    )
  }

  return (
    <div>
      {/* Back button */}
      <Link
        to="/knowledge"
        className="inline-flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-800 transition-colors duration-200 mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        {t('detail.backToKB')}
      </Link>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-start justify-between mb-3">
          {isEditingTitle ? (
            <div className="flex items-center gap-2 flex-1 mr-4">
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onKeyDown={handleTitleKeyDown}
                autoFocus
                className="text-2xl font-heading font-bold text-primary-950 bg-white border border-primary-300 rounded-lg px-3 py-1 flex-1 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
              <button
                type="button"
                onClick={handleSaveTitle}
                disabled={titleMutation.isPending}
                title={t('detail.titleSave')}
                className="p-1.5 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-md transition-colors duration-200 disabled:opacity-50"
              >
                <Check className="h-5 w-5" />
              </button>
              <button
                type="button"
                onClick={handleCancelEditTitle}
                title={t('detail.titleCancel')}
                className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors duration-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-heading font-bold text-primary-950">
                {doc.title}
              </h1>
              <button
                type="button"
                onClick={handleStartEditTitle}
                title={t('detail.titleEdit')}
                className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-md transition-colors duration-200"
              >
                <Pencil className="h-4 w-4" />
              </button>
            </div>
          )}
          <button
            type="button"
            onClick={() => setShowDeleteConfirm(true)}
            className="flex items-center gap-1.5 text-sm text-red-500 hover:text-red-700 border border-red-300 hover:border-red-400 rounded-lg px-3 py-1.5 transition-all duration-200 shrink-0 ml-4"
          >
            <Trash2 className="h-4 w-4" />
            {t('detail.delete')}
          </button>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="primary">{doc.file_type}</Badge>
          {doc.analysis?.paper_type && (
            <PaperTypeBadge paperType={doc.analysis.paper_type} />
          )}
          {doc.tags
            .split(', ')
            .filter(Boolean)
            .map((tag) => (
              <Badge key={tag} variant="accent">
                {tag}
              </Badge>
            ))}
          <span className="text-sm text-gray-500">{doc.date}</span>
        </div>

        {/* Collection selector */}
        <div className="flex items-center gap-2 mt-3">
          <FolderOpen className="h-4 w-4 text-gray-500" />
          <label className="text-sm text-gray-500" htmlFor="collection-select">
            {t('detail.collection')}
          </label>
          <select
            id="collection-select"
            value={doc.collection_id ?? ''}
            onChange={handleCollectionChange}
            disabled={moveMutation.isPending}
            className="text-sm border border-gray-300 rounded-lg px-2 py-1 bg-white text-primary-950 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50 transition-colors duration-200"
          >
            <option value="">{t('detail.uncategorized')}</option>
            {collections?.map((col) => (
              <option key={col.id} value={col.id}>
                {col.name}
              </option>
            ))}
          </select>
        </div>

        {/* Download buttons */}
        {doc.analysis && (
          <div className="flex items-center gap-2 mt-4">
            <span className="text-sm text-gray-500">{t('detail.downloadAs')}</span>
            {DOWNLOAD_FORMATS.map((fmt) => {
              const Icon = fmt.icon
              return (
                <a
                  key={fmt.value}
                  href={getDocumentReportUrl(doc.id, fmt.value)}
                  download
                  className="inline-flex items-center gap-1.5 text-sm border border-gray-300 hover:border-primary-400 hover:bg-primary-50 text-gray-700 hover:text-primary-700 rounded-lg px-3 py-1.5 transition-all duration-200"
                >
                  <Icon className="h-4 w-4" />
                  {fmt.label}
                </a>
              )
            })}
          </div>
        )}
      </div>

      {/* Tab bar (when report_content or parsed_text exists) */}
      {doc.analysis && (doc.report_content || doc.parsed_text) && (() => {
        const isPaperSearch = doc.source_type === 'paper_search'
        const isAbstractOnly = isPaperSearch && (!doc.parsed_text || doc.parsed_text.length < 1000)
        const originalTabLabel = isAbstractOnly ? t('detail.tabAbstract') : t('detail.tabOriginal')
        return (
          <div className="flex border-b border-gray-200 mb-6">
            <button
              type="button"
              onClick={() => setActiveTab('cards')}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors duration-200 ${
                activeTab === 'cards'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {t('detail.tabCards')}
            </button>
            {doc.report_content && (
              <button
                type="button"
                onClick={() => setActiveTab('report')}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors duration-200 ${
                  activeTab === 'report'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {t('detail.tabReport')}
              </button>
            )}
            {doc.parsed_text && (
              <button
                type="button"
                onClick={() => setActiveTab('original')}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors duration-200 ${
                  activeTab === 'original'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {originalTabLabel}
              </button>
            )}
          </div>
        )
      })()}

      {/* Analysis content or empty state */}
      {doc.analysis && !(doc.analysis as any).metadata_only ? (
        activeTab === 'report' && doc.report_content ? (
          <div className="bg-surface-card rounded-xl shadow-sm p-8">
            <MarkdownRenderer content={doc.report_content} />
          </div>
        ) : activeTab === 'original' && doc.parsed_text ? (() => {
          const isPaperSearch = doc.source_type === 'paper_search'
          const isAbstractOnly = isPaperSearch && doc.parsed_text!.length < 1000

          if (isAbstractOnly) {
            // 场景 A：paper_search 仅有摘要 — 直接显示 + 提示
            return (
              <div className="bg-surface-card rounded-xl shadow-sm p-8">
                <div className="flex items-start gap-3 mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <Info className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                  <p className="text-sm text-amber-800">{t('detail.abstractOnlyNote')}</p>
                </div>
                <MarkdownRenderer content={doc.parsed_text!} />
              </div>
            )
          }

          // 场景 B：完整原文 — 懒加载
          return (
            <div className="bg-surface-card rounded-xl shadow-sm p-8">
              {originalLoaded ? (
                <>
                  <MarkdownRenderer content={doc.parsed_text!} />
                  <div className="mt-6 flex justify-center">
                    <button
                      type="button"
                      onClick={() => setOriginalLoaded(false)}
                      className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 border border-gray-300 hover:border-gray-400 rounded-lg px-4 py-2 transition-all duration-200"
                    >
                      <ChevronUp className="h-4 w-4" />
                      {t('detail.collapseText')}
                    </button>
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <FileText className="h-12 w-12 text-gray-300 mb-4" />
                  <p className="text-gray-500 mb-4">{t('detail.originalNotLoaded')}</p>
                  <button
                    type="button"
                    onClick={() => setOriginalLoaded(true)}
                    className="inline-flex items-center gap-1.5 text-sm font-medium text-primary-600 hover:text-primary-700 border border-primary-300 hover:border-primary-400 rounded-lg px-4 py-2 transition-all duration-200"
                  >
                    <ChevronDown className="h-4 w-4" />
                    {t('detail.loadOriginal')}
                  </button>
                </div>
              )}
            </div>
          )
        })() : (
          <AnalysisCards analysis={doc.analysis} />
        )
      ) : (
        <EmptyState
          icon={FileText}
          title={t('detail.noAnalysisTitle')}
          description={t('detail.noAnalysisDesc')}
        />
      )}

      {/* Delete confirmation dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-heading font-semibold text-primary-950 mb-2">
              {t('detail.deleteConfirmTitle')}
            </h3>
            <p className="text-sm text-gray-600 mb-6">
              {t('detail.deleteConfirmDesc')}
            </p>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200"
              >
                {t('common.cancel')}
              </button>
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 text-sm text-white bg-red-500 rounded-lg hover:bg-red-600 transition-colors duration-200 disabled:opacity-50"
              >
                {deleteMutation.isPending ? t('common.loading') : t('detail.confirmDelete')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
