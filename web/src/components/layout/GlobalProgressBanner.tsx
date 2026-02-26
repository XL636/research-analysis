import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Loader } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { usePaperOperation } from '../../contexts/PaperOperationContext'
import { useAnalysis } from '../../contexts/AnalysisContext'

export default function GlobalProgressBanner() {
  const { t } = useTranslation()
  const { activeOp } = usePaperOperation()
  const { run: analysisRun } = useAnalysis()
  const [elapsed, setElapsed] = useState(0)

  const startedAt = activeOp?.startedAt ?? (analysisRun?.phase === 'analyzing' ? analysisRun.startedAt : null)

  useEffect(() => {
    if (!startedAt) {
      setElapsed(0)
      return
    }
    setElapsed(Math.floor((Date.now() - startedAt) / 1000))
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startedAt) / 1000))
    }, 1000)
    return () => clearInterval(timer)
  }, [startedAt])

  // Paper operation banner (priority)
  if (activeOp) {
    const minutes = Math.floor(elapsed / 60)
    const seconds = elapsed % 60
    const timeStr = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`
    return (
      <div className="fixed top-0 left-0 right-0 z-50 bg-primary-600 text-white px-4 py-2.5 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-2 text-sm">
          <Loader className="w-4 h-4 animate-spin" />
          <span>
            {t('paper.globalProgress', {
              name: activeOp.projectName,
              operation: t(`paper.op.${activeOp.operation}`),
            })}
          </span>
          <span className="text-primary-200">{timeStr}</span>
        </div>
        <Link
          to={`/paper/${activeOp.projectId}`}
          className="text-sm text-primary-100 hover:text-white underline underline-offset-2"
        >
          {t('paper.goToProject')}
        </Link>
      </div>
    )
  }

  // Analysis running banner
  if (analysisRun?.phase === 'analyzing') {
    const minutes = Math.floor(elapsed / 60)
    const seconds = elapsed % 60
    const timeStr = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`
    const currentStep = analysisRun.steps.find(s => s.status === 'running')
    return (
      <div className="fixed top-0 left-0 right-0 z-50 bg-emerald-600 text-white px-4 py-2.5 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-2 text-sm">
          <Loader className="w-4 h-4 animate-spin" />
          <span>
            {t('analyze.globalProgress', {
              files: analysisRun.fileNames.join(', '),
            })}
          </span>
          {currentStep && (
            <span className="text-emerald-200">
              {t(`status.${currentStep.status}`)} · {currentStep.name}
              {currentStep.message ? ` · ${currentStep.message}` : ''}
            </span>
          )}
          <span className="text-emerald-200">{timeStr}</span>
        </div>
        <Link
          to="/analyze"
          className="text-sm text-emerald-100 hover:text-white underline underline-offset-2"
        >
          {t('analyze.goToAnalysis')}
        </Link>
      </div>
    )
  }

  return null
}
