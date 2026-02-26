import { useState, useEffect } from 'react'
import type { StepProgress } from '../types'
import { getProgressUrl } from '../api/pipeline'

const PIPELINE_STEPS = ['parse', 'analyze', 'synthesize', 'generate', 'review']

interface StepState {
  name: string
  status: 'pending' | 'running' | 'completed' | 'error'
  message: string
}

interface PipelineProgressState {
  steps: StepState[]
  isComplete: boolean
  error: string | null
}

export function usePipelineProgress(runId: string | null): PipelineProgressState {
  const [steps, setSteps] = useState<StepState[]>(
    PIPELINE_STEPS.map(name => ({ name, status: 'pending' as const, message: '' }))
  )
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!runId) return

    // Reset
    setSteps(PIPELINE_STEPS.map(name => ({ name, status: 'pending' as const, message: '' })))
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
            s.name === progress.step
              ? { ...s, status: progress.status, message: progress.message || '' }
              : s
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
