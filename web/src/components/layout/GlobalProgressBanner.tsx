import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Loader } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { usePaperOperation } from '../../contexts/PaperOperationContext'

export default function GlobalProgressBanner() {
  const { t } = useTranslation()
  const { activeOp } = usePaperOperation()
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (!activeOp) {
      setElapsed(0)
      return
    }
    setElapsed(Math.floor((Date.now() - activeOp.startedAt) / 1000))
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - activeOp.startedAt) / 1000))
    }, 1000)
    return () => clearInterval(timer)
  }, [activeOp])

  if (!activeOp) return null

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
