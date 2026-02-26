import { Routes, Route } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import DashboardPage from './pages/DashboardPage'
import AnalyzePage from './pages/AnalyzePage'
import KnowledgeBasePage from './pages/KnowledgeBasePage'
import DocumentDetailPage from './pages/DocumentDetailPage'
import PaperListPage from './pages/PaperListPage'
import PaperProjectPage from './pages/PaperProjectPage'
import SettingsPage from './pages/SettingsPage'
import TemplatesPage from './pages/TemplatesPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="analyze" element={<AnalyzePage />} />
        <Route path="knowledge" element={<KnowledgeBasePage />} />
        <Route path="knowledge/:id" element={<DocumentDetailPage />} />
        <Route path="templates" element={<TemplatesPage />} />
        <Route path="paper" element={<PaperListPage />} />
        <Route path="paper/:id" element={<PaperProjectPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}
