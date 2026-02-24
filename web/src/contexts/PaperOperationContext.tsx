import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

interface ActiveOperation {
  projectId: string
  projectName: string
  operation: string
  startedAt: number
}

interface PaperOperationContextValue {
  activeOp: ActiveOperation | null
  startOperation: (projectId: string, projectName: string, operation: string) => void
  clearOperation: () => void
}

const PaperOperationContext = createContext<PaperOperationContextValue>({
  activeOp: null,
  startOperation: () => {},
  clearOperation: () => {},
})

export function PaperOperationProvider({ children }: { children: ReactNode }) {
  const [activeOp, setActiveOp] = useState<ActiveOperation | null>(null)

  const startOperation = useCallback((projectId: string, projectName: string, operation: string) => {
    setActiveOp({ projectId, projectName, operation, startedAt: Date.now() })
  }, [])

  const clearOperation = useCallback(() => {
    setActiveOp(null)
  }, [])

  return (
    <PaperOperationContext.Provider value={{ activeOp, startOperation, clearOperation }}>
      {children}
    </PaperOperationContext.Provider>
  )
}

export function usePaperOperation() {
  return useContext(PaperOperationContext)
}
