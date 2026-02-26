import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar, { STORAGE_KEY } from './Sidebar'
import { PaperOperationProvider } from '../../contexts/PaperOperationContext'
import { AnalysisProvider } from '../../contexts/AnalysisContext'
import GlobalProgressBanner from './GlobalProgressBanner'
import { usePaperOperation } from '../../contexts/PaperOperationContext'
import { useAnalysis } from '../../contexts/AnalysisContext'

function AppLayoutInner() {
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem(STORAGE_KEY) === 'true'
  })
  const { activeOp } = usePaperOperation()
  const { run: analysisRun } = useAnalysis()
  const hasGlobalBanner = !!activeOp || (analysisRun?.phase === 'analyzing')

  const handleToggle = () => {
    setCollapsed((prev) => {
      const next = !prev
      localStorage.setItem(STORAGE_KEY, String(next))
      return next
    })
  }

  return (
    <div className="flex min-h-screen">
      <GlobalProgressBanner />
      <Sidebar collapsed={collapsed} onToggle={handleToggle} />
      <main
        className={`flex-1 overflow-y-auto bg-surface p-8 min-h-screen transition-all duration-300 ${
          collapsed ? 'ml-16' : 'ml-64'
        } ${hasGlobalBanner ? 'pt-18' : ''}`}
      >
        <Outlet />
      </main>
    </div>
  )
}

export default function AppLayout() {
  return (
    <PaperOperationProvider>
      <AnalysisProvider>
        <AppLayoutInner />
      </AnalysisProvider>
    </PaperOperationProvider>
  )
}
