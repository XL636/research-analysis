import { useState, useEffect } from 'react'
import type { StepProgress } from '../types'
import { getProgressUrl } from '../api/pipeline'

const PIPELINE_STEPS = ['parse', 'analyze', 'synthesize', 'generate', 'review']

interface PipelineProgressState {
  steps: { name: string; status: 'pending' | 'running' | 'completed' | 'error' }[]
  isComplete: boolean
  error: string | null
}

export function usePipelineProgress(runId: string | null): PipelineProgressState {
  type StepStatus = 'pending' | 'running' | 'completed' | 'error'
  const [steps, setSteps] = useState<{ name: string; status: StepStatus }[]>(
    PIPELINE_STEPS.map(name => ({ name, status: 'pending' }))
  )
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!runId) return

    // Reset
    setSteps(PIPELINE_STEPS.map(name => ({ name, status: 'pending' as const })))
    setIsComplete(false)
    setError(null)

    const es = new EventSource(getProgressUrl(runId))

    es.onmessage = (event) => {
      try {
        const progress: StepProgress = JSON.parse(event.data)
        if (!progress.step) return // keepalive

        if (progress.step === 'complete') {
          setIsComplete(true)
          es.close()
          return
        }

        if (progress.step === 'error') {
          setError(progress.message || 'Unknown error')
          es.close()
          return
        }

        setSteps(prev =>
          prev.map(s =>
            s.name === progress.step ? { ...s, status: progress.status } : s
          )
        )
      } catch {
        // ignore parse errors
      }
    }

    es.onerror = () => {
      es.close()
    }

    return () => es.close()
  }, [runId])

  return { steps, isComplete, error }
}
