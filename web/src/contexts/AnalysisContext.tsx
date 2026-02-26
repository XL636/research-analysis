import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import type { StepProgress } from '../types'
import { getProgressUrl, getPipelineResult } from '../api/pipeline'

const PIPELINE_STEPS = ['parse', 'analyze', 'synthesize', 'generate', 'review']

interface StepState {
  name: string
  status: 'pending' | 'running' | 'completed' | 'error'
  message: string
}

type Phase = 'idle' | 'analyzing' | 'result'

interface AnalysisRun {
  runId: string
  phase: Phase
  fileNames: string[]
  mode: string
  format: string
  steps: StepState[]
  isComplete: boolean
  error: string | null
  reportContent: string
  reportTitle: string
  startedAt: number
}

interface AnalysisContextValue {
  run: AnalysisRun | null
  startRun: (runId: string, fileNames: string[], mode: string, format: string) => void
  reset: () => void
}

const AnalysisContext = createContext<AnalysisContextValue>({
  run: null,
  startRun: () => {},
  reset: () => {},
})

function makeInitialSteps(): StepState[] {
  return PIPELINE_STEPS.map(name => ({ name, status: 'pending' as const, message: '' }))
}

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [run, setRun] = useState<AnalysisRun | null>(null)

  const startRun = useCallback((runId: string, fileNames: string[], mode: string, format: string) => {
    setRun({
      runId,
      phase: 'analyzing',
      fileNames,
      mode,
      format,
      steps: makeInitialSteps(),
      isComplete: false,
      error: null,
      reportContent: '',
      reportTitle: '',
      startedAt: Date.now(),
    })
  }, [])

  const reset = useCallback(() => {
    setRun(null)
  }, [])

  // SSE connection — managed at context level, survives page navigation
  useEffect(() => {
    if (!run || run.phase !== 'analyzing') return

    const es = new EventSource(getProgressUrl(run.runId))

    es.onmessage = (event) => {
      try {
        const progress: StepProgress = JSON.parse(event.data)
        if (!progress.step) return

        if (progress.step === 'complete') {
          setRun(prev => prev ? { ...prev, isComplete: true } : prev)
          es.close()
          return
        }

        if (progress.step === 'error') {
          setRun(prev => prev ? { ...prev, error: progress.message || 'Unknown error', phase: 'analyzing' } : prev)
          es.close()
          return
        }

        setRun(prev => {
          if (!prev) return prev
          const steps = prev.steps.map(s =>
            s.name === progress.step
              ? { ...s, status: progress.status, message: progress.message || '' }
              : s
          )
          return { ...prev, steps }
        })
      } catch {
        // ignore parse errors
      }
    }

    es.onerror = () => {
      es.close()
    }

    return () => es.close()
  }, [run?.runId, run?.phase])

  // Fetch result when SSE signals completion
  useEffect(() => {
    if (!run || !run.isComplete || run.phase === 'result') return

    getPipelineResult(run.runId).then(result => {
      setRun(prev => prev ? {
        ...prev,
        phase: 'result',
        reportContent: result.report_content || '',
        reportTitle: result.report_title || '',
      } : prev)
    }).catch(() => {
      setRun(prev => prev ? {
        ...prev,
        phase: 'result',
        reportContent: '',
        reportTitle: '',
      } : prev)
    })
  }, [run?.isComplete])

  return (
    <AnalysisContext.Provider value={{ run, startRun, reset }}>
      {children}
    </AnalysisContext.Provider>
  )
}

export function useAnalysis() {
  return useContext(AnalysisContext)
}
