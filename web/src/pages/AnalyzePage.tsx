import { useState, useEffect } from 'react'
import {
  FileSearch,
  FileText,
  FileType,
  Presentation,
  Download,
  Plus,
  AlertCircle,
  Loader,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import FileDropzone from '../components/ui/FileDropzone'
import ProgressStepper from '../components/ui/ProgressStepper'
import MarkdownRenderer from '../components/ui/MarkdownRenderer'
import EmptyState from '../components/ui/EmptyState'
import { usePipelineProgress } from '../hooks/usePipelineProgress'
import { startPipeline, getPipelineResult, getDownloadUrl } from '../api/pipeline'

type Phase = 'upload' | 'analyzing' | 'result'

const FORMAT_OPTIONS = [
  { value: 'markdown', label: 'Markdown', icon: FileText },
  { value: 'docx', label: 'DOCX', icon: FileType },
  { value: 'pptx', label: 'PPTX', icon: Presentation },
] as const

export default function AnalyzePage() {
  const { t } = useTranslation()
  const [phase, setPhase] = useState<Phase>('upload')
  const [files, setFiles] = useState<File[]>([])
  const [format, setFormat] = useState('markdown')
  const [synthesize, setSynthesize] = useState(false)
  const [runId, setRunId] = useState<string | null>(null)
  const [reportContent, setReportContent] = useState('')
  const [reportTitle, setReportTitle] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { steps, isComplete, error } = usePipelineProgress(runId)

  // Watch for pipeline completion or error
  useEffect(() => {
    if (!runId) return

    if (isComplete) {
      getPipelineResult(runId).then(result => {
        setReportContent(result.report_content)
        setReportTitle(result.report_title)
        setPhase('result')
      }).catch(() => {
        setReportContent('')
        setReportTitle('')
        setPhase('result')
      })
    }
  }, [isComplete, runId])

  const handleSubmit = async () => {
    if (files.length === 0 || isSubmitting) return

    setIsSubmitting(true)
    try {
      const response = await startPipeline(files, format, synthesize)
      setRunId(response.run_id)
      setPhase('analyzing')
    } catch {
      // stay on upload phase if start fails
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleReset = () => {
    setPhase('upload')
    setFiles([])
    setFormat('markdown')
    setSynthesize(false)
    setRunId(null)
    setReportContent('')
    setReportTitle('')
    setIsSubmitting(false)
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
              <label className="block text-sm font-medium text-primary-950 mb-2">
                {t('analyze.crossDocSynthesis')}
              </label>
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
          <button
            type="button"
            onClick={handleSubmit}
            disabled={files.length === 0 || isSubmitting}
            className={`mt-6 w-full rounded-lg bg-emerald-500 py-3 text-white font-medium transition-all duration-200 ${
              files.length === 0 || isSubmitting
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
      </div>
    )
  }

  // ── Phase 2: Analyzing ───────────────────────────────────────────────
  if (phase === 'analyzing') {
    return (
      <div>
        <h1 className="text-2xl font-heading font-bold text-primary-950 mb-6">
          {t('analyze.analyzing')}
        </h1>

        {error && (
          <div className="mb-6 flex items-start gap-3 rounded-lg bg-red-50 p-4">
            <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-500 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-800">{t('analyze.analysisError')}</p>
              <p className="text-sm text-red-600 mt-1">{error}</p>
            </div>
          </div>
        )}

        <div className="bg-surface-card rounded-xl shadow-sm p-8">
          <div className="flex gap-8">
            {/* Left: Progress stepper */}
            <div className="flex-1">
              <ProgressStepper steps={steps} />
            </div>

            {/* Right: Info panel */}
            <div className="flex-1 border-l border-gray-200 pl-8">
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">
                  {t('analyze.filesBeingAnalyzed')}
                </h3>
                <ul className="space-y-2">
                  {files.map((file, index) => (
                    <li
                      key={`${file.name}-${index}`}
                      className="flex items-center gap-2 text-sm text-primary-950"
                    >
                      <FileText className="h-4 w-4 text-primary-500 flex-shrink-0" />
                      <span className="truncate">{file.name}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-1">
                  {t('analyze.outputFormat')}
                </h3>
                <p className="text-sm text-primary-950 capitalize">{format}</p>
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
          href={runId ? getDownloadUrl(runId, format) : '#'}
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
