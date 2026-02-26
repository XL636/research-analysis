import { useState, useEffect } from 'react'
import {
  FileSearch,
  FileText,
  FileType,
  Presentation,
  Download,
  Plus,
  AlertCircle,
  HelpCircle,
  Loader,
  Zap,
  BookOpen,
  Microscope,
  Users,
  Sliders,
  Info,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import FileDropzone from '../components/ui/FileDropzone'
import ProgressStepper from '../components/ui/ProgressStepper'
import MarkdownRenderer from '../components/ui/MarkdownRenderer'
import EmptyState from '../components/ui/EmptyState'
import { useAnalysis } from '../contexts/AnalysisContext'
import { startPipeline, getDownloadUrl, getAnalysisModes } from '../api/pipeline'
import { checkDuplicate, deleteDocument } from '../api/knowledge'
import { getTemplates } from '../api/templates'
import type { DocumentSummary, AnalysisModeInfo, ReportTemplate } from '../types'

const MODE_ICONS: Record<string, typeof Zap> = {
  quick: Zap,
  standard: BookOpen,
  deep: Microscope,
  meeting: Users,
}

const FORMAT_OPTIONS = [
  { value: 'markdown', label: 'Markdown', icon: FileText },
  { value: 'docx', label: 'DOCX', icon: FileType },
  { value: 'pptx', label: 'PPTX', icon: Presentation },
  { value: 'pdf', label: 'PDF', icon: FileText },
] as const

export default function AnalyzePage() {
  const { t, i18n } = useTranslation()
  const { run: analysisRun, startRun, reset: resetAnalysis } = useAnalysis()

  // Local form state (only for upload phase)
  const [files, setFiles] = useState<File[]>([])
  const [format, setFormat] = useState('markdown')
  const [mode, setMode] = useState('standard')
  const [modes, setModes] = useState<AnalysisModeInfo[]>([])
  const [templates, setTemplates] = useState<ReportTemplate[]>([])
  const [templateId, setTemplateId] = useState<number | undefined>(undefined)
  const [depth, setDepth] = useState('standard')
  const [synthesize, setSynthesize] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Duplicate detection state
  const [showDuplicateDialog, setShowDuplicateDialog] = useState(false)
  const [duplicateDocs, setDuplicateDocs] = useState<DocumentSummary[]>([])

  // Derive phase from global context
  const phase = analysisRun?.phase === 'analyzing' ? 'analyzing'
    : analysisRun?.phase === 'result' ? 'result'
    : 'upload'

  // Load analysis modes and templates
  useEffect(() => {
    getAnalysisModes().then(res => setModes(res.modes)).catch(() => {})
    getTemplates().then(res => setTemplates(res.templates)).catch(() => {})
  }, [])

  const doStartPipeline = async () => {
    setIsSubmitting(true)
    try {
      const fileNames = files.map(f => f.name)
      const response = await startPipeline(files, format, synthesize, mode, templateId, mode === 'custom' ? depth : undefined)
      startRun(response.run_id, fileNames, mode, format)
    } catch {
      // stay on upload phase if start fails
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSubmit = async () => {
    if (files.length === 0 || isSubmitting) return

    // Check for duplicates before starting
    try {
      const result = await checkDuplicate(files[0].name)
      if (result.has_duplicate) {
        setDuplicateDocs(result.existing_documents)
        setShowDuplicateDialog(true)
        return
      }
    } catch {
      // If check fails, proceed normally
    }

    await doStartPipeline()
  }

  const handleDuplicateOverride = async () => {
    setShowDuplicateDialog(false)
    // Start new analysis first, then delete old records
    await doStartPipeline()
    // Delete old duplicates after starting new analysis
    for (const doc of duplicateDocs) {
      try {
        await deleteDocument(doc.id)
      } catch {
        // ignore delete errors
      }
    }
  }

  const handleDuplicateKeepBoth = async () => {
    setShowDuplicateDialog(false)
    await doStartPipeline()
  }

  const handleDuplicateCancel = () => {
    setShowDuplicateDialog(false)
    setDuplicateDocs([])
  }

  const handleReset = () => {
    resetAnalysis()
    setFiles([])
    setFormat('markdown')
    setMode('standard')
    setTemplateId(undefined)
    setDepth('standard')
    setSynthesize(false)
    setIsSubmitting(false)
    setShowDuplicateDialog(false)
    setDuplicateDocs([])
  }

  // ── Phase 1: Upload ──────────────────────────────────────────────────
  if (phase === 'upload') {
    return (
      <div>
        <h1 className="text-2xl font-heading font-bold text-primary-950 mb-6">
          {t('analyze.title')}
        </h1>

        <div className="bg-surface-card rounded-xl shadow-sm p-8">
          <FileDropzone onFilesSelected={setFiles} />

          {/* Analysis mode selector */}
          {modes.length > 0 && (
            <div className="mt-6">
              <label className="block text-sm font-medium text-primary-950 mb-2">
                {t('analyze.analysisMode')}
              </label>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {modes.map(m => {
                  const Icon = MODE_ICONS[m.id] || BookOpen
                  const isSelected = mode === m.id
                  const label = i18n.language.startsWith('zh') ? m.label_zh : m.label_en
                  const desc = i18n.language.startsWith('zh') ? m.description_zh : m.description_en
                  return (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => { setMode(m.id); setTemplateId(undefined) }}
                      className={`flex flex-col items-start gap-1.5 border rounded-lg px-4 py-3 text-left transition-all duration-200 ${
                        isSelected
                          ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-500'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <Icon className={`h-4 w-4 ${isSelected ? 'text-primary-600' : 'text-gray-400'}`} />
                        <span className={`text-sm font-medium ${isSelected ? 'text-primary-700' : 'text-primary-950'}`}>
                          {label}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500 line-clamp-2">{desc}</span>
                    </button>
                  )
                })}
                {/* Custom mode card */}
                <button
                  type="button"
                  onClick={() => setMode('custom')}
                  className={`flex flex-col items-start gap-1.5 border rounded-lg px-4 py-3 text-left transition-all duration-200 ${
                    mode === 'custom'
                      ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-500'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Sliders className={`h-4 w-4 ${mode === 'custom' ? 'text-primary-600' : 'text-gray-400'}`} />
                    <span className={`text-sm font-medium ${mode === 'custom' ? 'text-primary-700' : 'text-primary-950'}`}>
                      {t('analyze.customMode')}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500 line-clamp-2">{t('analyze.customModeDesc')}</span>
                </button>
              </div>

              {/* Mode hint info bar */}
              {(() => {
                const modeInfo = mode === 'custom'
                  ? modes.find(m => m.id === depth)
                  : modes.find(m => m.id === mode)
                if (!modeInfo) return null
                const limit = modeInfo.max_text_length >= 1000
                  ? `${(modeInfo.max_text_length / 1000).toFixed(0)},000`
                  : String(modeInfo.max_text_length)
                const hintKey = mode === 'custom' ? 'custom' : mode
                return (
                  <div className="mt-3 flex items-start gap-2 text-xs text-gray-600 bg-gray-50 rounded-lg px-3 py-2">
                    <Info className="h-3.5 w-3.5 mt-0.5 shrink-0 text-gray-400" />
                    <span>
                      {t('analyze.modeHint.textLimit', { limit })}
                      {' · '}
                      {modeInfo.skip_review ? t('analyze.modeHint.skipReview') : t('analyze.modeHint.hasReview')}
                      {' · '}
                      {t(`analyze.modeHint.${hintKey}`)}
                    </span>
                  </div>
                )
              })()}

              {/* Custom mode sub-panel */}
              {mode === 'custom' && (
                <div className="mt-3 border border-primary-200 bg-primary-50/50 rounded-lg p-4 space-y-4">
                  {/* Template selector (required) */}
                  <div>
                    <label className="block text-sm font-medium text-primary-950 mb-2">
                      {t('template.selectLabel')}
                    </label>
                    {templates.filter(t => !t.is_builtin).length === 0 ? (
                      <div className="flex items-center gap-3 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
                        <AlertCircle className="h-4 w-4 shrink-0" />
                        <div>
                          <p className="font-medium">{t('analyze.customNoTemplate')}</p>
                          <p className="text-xs text-amber-600 mt-0.5">{t('analyze.customNoTemplateDesc')}</p>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {templates.filter(t => !t.is_builtin).map(tpl => (
                          <button
                            key={tpl.id}
                            type="button"
                            onClick={() => setTemplateId(tpl.id)}
                            className={`flex items-center gap-1.5 border rounded-lg px-3 py-1.5 text-sm transition-all duration-200 ${
                              templateId === tpl.id
                                ? 'border-primary-500 bg-primary-50 text-primary-700 ring-1 ring-primary-500'
                                : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                            }`}
                          >
                            <FileText className="h-3.5 w-3.5" />
                            {tpl.display_name}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Depth selector */}
                  <div>
                    <label className="block text-sm font-medium text-primary-950 mb-2">
                      {t('analyze.depthLabel')}
                    </label>
                    <div className="flex gap-2">
                      {(['quick', 'standard', 'deep'] as const).map(d => {
                        const depthIcons = { quick: Zap, standard: BookOpen, deep: Microscope }
                        const DepthIcon = depthIcons[d]
                        const isSelected = depth === d
                        return (
                          <button
                            key={d}
                            type="button"
                            onClick={() => setDepth(d)}
                            className={`flex items-center gap-2 border rounded-lg px-4 py-2 text-sm transition-all duration-200 ${
                              isSelected
                                ? 'border-primary-500 bg-white text-primary-700 ring-1 ring-primary-500'
                                : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                            }`}
                          >
                            <DepthIcon className="h-4 w-4" />
                            {t(`analyze.depth.${d}`)}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Options section */}
          <div className="mt-6 flex flex-wrap gap-6">
            {/* Output format selector */}
            <div>
              <label className="block text-sm font-medium text-primary-950 mb-2">
                {t('analyze.outputFormat')}
              </label>
              <div className="flex gap-2">
                {FORMAT_OPTIONS.map(opt => {
                  const Icon = opt.icon
                  const isSelected = format === opt.value
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setFormat(opt.value)}
                      className={`flex items-center gap-2 border rounded-lg px-4 py-2 text-sm transition-all duration-200 ${
                        isSelected
                          ? 'border-primary-500 bg-primary-50 text-primary-700'
                          : 'border-gray-300 text-gray-600 hover:border-gray-400'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      {opt.label}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Synthesize toggle */}
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <label className="block text-sm font-medium text-primary-950">
                  {t('analyze.crossDocSynthesis')}
                </label>
                <div className="relative group">
                  <HelpCircle className="h-4 w-4 text-gray-400 cursor-help" />
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2
                                  hidden group-hover:block w-56 p-2 text-xs text-white
                                  bg-gray-800 rounded-lg shadow-lg z-10">
                    {t('analyze.crossDocTooltip')}
                    <div className="absolute top-full left-1/2 -translate-x-1/2
                                    border-4 border-transparent border-t-gray-800" />
                  </div>
                </div>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={synthesize}
                onClick={() => setSynthesize(prev => !prev)}
                className="flex items-center gap-3"
              >
                <span
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 ${
                    synthesize ? 'bg-primary-500' : 'bg-gray-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 rounded-full bg-white transition-transform duration-200 ${
                      synthesize ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </span>
                <span className="text-sm text-gray-600">
                  {t('analyze.crossDocDesc')}
                </span>
              </button>
            </div>
          </div>

          {/* Submit button */}
          {mode === 'custom' && templateId === undefined && templates.filter(t => !t.is_builtin).length > 0 && (
            <p className="mt-4 text-xs text-amber-600">{t('analyze.templateRequired')}</p>
          )}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={files.length === 0 || isSubmitting || (mode === 'custom' && templateId === undefined)}
            className={`mt-3 w-full rounded-lg bg-emerald-500 py-3 text-white font-medium transition-all duration-200 ${
              files.length === 0 || isSubmitting || (mode === 'custom' && templateId === undefined)
                ? 'opacity-50 cursor-not-allowed'
                : 'hover:bg-emerald-600'
            }`}
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <Loader className="h-4 w-4 animate-spin" />
                {t('analyze.starting')}
              </span>
            ) : (
              t('analyze.startAnalysis')
            )}
          </button>
        </div>

        {/* Duplicate detection dialog */}
        {showDuplicateDialog && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-white rounded-xl shadow-xl p-6 max-w-md w-full mx-4">
              <div className="flex items-start gap-3 mb-4">
                <AlertCircle className="h-6 w-6 text-amber-500 shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-lg font-heading font-semibold text-primary-950">
                    {t('analyze.duplicateTitle')}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {t('analyze.duplicateDesc')}
                  </p>
                </div>
              </div>

              {/* Existing documents list */}
              <div className="mb-6 bg-gray-50 rounded-lg p-3 space-y-2">
                {duplicateDocs.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between text-sm">
                    <span className="text-primary-950 font-medium truncate">{doc.title}</span>
                    <span className="text-gray-500 shrink-0 ml-2">{doc.date}</span>
                  </div>
                ))}
              </div>

              <div className="flex flex-col gap-2">
                <button
                  type="button"
                  onClick={handleDuplicateOverride}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-amber-500 rounded-lg hover:bg-amber-600 transition-colors duration-200"
                >
                  {t('analyze.duplicateOverride')}
                </button>
                <button
                  type="button"
                  onClick={handleDuplicateKeepBoth}
                  className="w-full px-4 py-2 text-sm font-medium text-primary-700 bg-primary-50 border border-primary-200 rounded-lg hover:bg-primary-100 transition-colors duration-200"
                >
                  {t('analyze.duplicateKeepBoth')}
                </button>
                <button
                  type="button"
                  onClick={handleDuplicateCancel}
                  className="w-full px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200"
                >
                  {t('analyze.duplicateCancel')}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // ── Phase 2: Analyzing ───────────────────────────────────────────────
  if (phase === 'analyzing' && analysisRun) {
    return (
      <div>
        <h1 className="text-2xl font-heading font-bold text-primary-950 mb-6">
          {t('analyze.analyzing')}
        </h1>

        {analysisRun.error && (
          <div className="mb-6 flex items-start gap-3 rounded-lg bg-red-50 p-4">
            <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-500 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-800">{t('analyze.analysisError')}</p>
              <p className="text-sm text-red-600 mt-1">{analysisRun.error}</p>
            </div>
          </div>
        )}

        <div className="bg-surface-card rounded-xl shadow-sm p-8">
          <div className="flex gap-8">
            {/* Left: Progress stepper */}
            <div className="flex-1">
              <ProgressStepper steps={analysisRun.steps} />
            </div>

            {/* Right: Info panel */}
            <div className="flex-1 border-l border-gray-200 pl-8">
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">
                  {t('analyze.filesBeingAnalyzed')}
                </h3>
                <ul className="space-y-2">
                  {analysisRun.fileNames.map((name, index) => (
                    <li
                      key={`${name}-${index}`}
                      className="flex items-center gap-2 text-sm text-primary-950"
                    >
                      <FileText className="h-4 w-4 text-primary-500 flex-shrink-0" />
                      <span className="truncate">{name}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-1">
                  {t('analyze.analysisMode')}
                </h3>
                <p className="text-sm text-primary-950">
                  {(() => {
                    if (analysisRun.mode === 'custom') return t('analyze.customMode')
                    const m = modes.find(m => m.id === analysisRun.mode)
                    return m ? (i18n.language.startsWith('zh') ? m.label_zh : m.label_en) : analysisRun.mode
                  })()}
                </p>
              </div>

              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-1">
                  {t('analyze.outputFormat')}
                </h3>
                <p className="text-sm text-primary-950 capitalize">{analysisRun.format}</p>
              </div>

              <button
                type="button"
                onClick={handleReset}
                className="text-sm text-gray-400 hover:text-gray-600 underline transition-colors duration-200"
              >
                {t('common.cancel')}
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ── Phase 3: Result ──────────────────────────────────────────────────
  const reportContent = analysisRun?.reportContent ?? ''
  const reportTitle = analysisRun?.reportTitle ?? ''
  const runId = analysisRun?.runId ?? null
  const runFormat = analysisRun?.format ?? 'markdown'

  return (
    <div>
      <h1 className="text-2xl font-heading font-bold text-primary-950 mb-6">
        {reportTitle || t('analyze.analysisComplete')}
      </h1>

      {/* Action bar */}
      <div className="flex items-center justify-between mb-6">
        <button
          type="button"
          onClick={handleReset}
          className="flex items-center gap-2 border border-primary-500 text-primary-600 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 hover:bg-primary-50"
        >
          <Plus className="h-4 w-4" />
          {t('analyze.newAnalysis')}
        </button>

        <a
          href={runId ? getDownloadUrl(runId, runFormat) : '#'}
          download
          className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg px-6 py-2 text-sm font-medium transition-all duration-200"
        >
          <Download className="h-4 w-4" />
          {t('analyze.downloadReport')}
        </a>
      </div>

      {/* Report content */}
      <div className="bg-surface-card rounded-xl shadow-sm p-8">
        {reportContent ? (
          <MarkdownRenderer content={reportContent} />
        ) : (
          <EmptyState
            icon={FileSearch}
            title={t('analyze.noReportTitle')}
            description={t('analyze.noReportDesc')}
            action={
              <button
                type="button"
                onClick={handleReset}
                className="text-sm text-primary-600 hover:text-primary-800 underline transition-colors duration-200"
              >
                {t('analyze.tryAgain')}
              </button>
            }
          />
        )}
      </div>
    </div>
  )
}
