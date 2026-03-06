import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, MessageSquare, PanelRightClose, BookOpen, FileText } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import {
  useReaderDocument,
  useReaderPage,
  useUpdateReaderProgress,
  useReaderSessions,
  useCreateReaderSession,
  useDeleteReaderSession,
  useSessionChatHistory,
  useClearSessionChat,
  useReaderSuggestions,
  useStreamChat,
  useDocumentOverview,
  useRegenerateOverview,
  useReaderNotes,
  useCreateNote,
  useDeleteNote,
  useGenerateStudyGuide,
  useGenerateFaq,
} from '../hooks/useReader'
import { getReaderFileUrl } from '../api/reader'
import PdfPageViewer from '../components/reader/PdfPageViewer'
import TextPageViewer from '../components/reader/TextPageViewer'
import PageNavigation from '../components/reader/PageNavigation'
import ChatPanel from '../components/reader/ChatPanel'
import DocumentOverview from '../components/reader/DocumentOverview'
import NotesPanel from '../components/reader/NotesPanel'
import StudyTools from '../components/reader/StudyTools'
import EmptyState from '../components/ui/EmptyState'
import type { StudyGuideSection, FaqItem } from '../types'

type RightTab = 'chat' | 'overview' | 'notes'

export default function ReaderViewPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const docId = Number(id) || 0

  const { data: doc, isLoading: docLoading } = useReaderDocument(docId)
  const [currentPage, setCurrentPage] = useState(1)
  const [chatOpen, setChatOpen] = useState(true)
  const [activeSessionId, setActiveSessionId] = useState(0)
  const [agentMode, setAgentMode] = useState(false)
  const [rightTab, setRightTab] = useState<RightTab>('chat')

  // Study tools state
  const [studyGuide, setStudyGuide] = useState<StudyGuideSection[] | null>(null)
  const [faq, setFaq] = useState<FaqItem[] | null>(null)

  // Initialize current page from document's saved progress
  useEffect(() => {
    if (doc && doc.current_page) {
      setCurrentPage(doc.current_page)
    }
  }, [doc?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  const isPdf = doc?.file_type === 'pdf'

  // Fetch page content for non-PDF files
  const { data: pageData, isLoading: pageLoading } = useReaderPage(docId, currentPage)

  // Prefetch adjacent pages
  useReaderPage(docId, currentPage > 1 ? currentPage - 1 : 0)
  useReaderPage(docId, doc ? Math.min(currentPage + 1, doc.total_pages) : 0)

  const updateProgress = useUpdateReaderProgress()

  // Sessions
  const { data: sessions = [] } = useReaderSessions(docId)
  const createSession = useCreateReaderSession()
  const deleteSession = useDeleteReaderSession()

  // Auto-select latest session when sessions load
  useEffect(() => {
    if (sessions.length > 0 && activeSessionId === 0) {
      setActiveSessionId(sessions[0].id)
    }
    if (sessions.length > 0 && !sessions.find((s) => s.id === activeSessionId)) {
      setActiveSessionId(sessions[0].id)
    }
  }, [sessions, activeSessionId])

  // Session chat
  const { data: chatHistoryData } = useSessionChatHistory(docId, activeSessionId)
  const streamChat = useStreamChat()
  const clearChat = useClearSessionChat()
  const chatMessages = chatHistoryData?.messages || []

  // Overview
  const { data: overview, isLoading: overviewLoading, isError: overviewError } = useDocumentOverview(docId)
  const regenerateOverview = useRegenerateOverview()

  // Notes
  const { data: notes = [], isLoading: notesLoading } = useReaderNotes(docId)
  const createNote = useCreateNote()
  const deleteNote = useDeleteNote()

  // Study tools
  const generateStudyGuideMutation = useGenerateStudyGuide()
  const generateFaqMutation = useGenerateFaq()

  // Suggestions with debounced page
  const [debouncedPage, setDebouncedPage] = useState(currentPage)
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedPage(currentPage), 500)
    return () => clearTimeout(timer)
  }, [currentPage])

  const { data: suggestionsData, isLoading: suggestionsLoading } = useReaderSuggestions(docId, debouncedPage)
  const suggestions = suggestionsData?.questions || []

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page)
    if (docId > 0) {
      updateProgress.mutate({ id: docId, currentPage: page })
    }
  }, [docId, updateProgress])

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA') return

      if (e.key === 'ArrowLeft') {
        e.preventDefault()
        if (currentPage > 1) handlePageChange(currentPage - 1)
      } else if (e.key === 'ArrowRight') {
        e.preventDefault()
        if (doc && currentPage < doc.total_pages) handlePageChange(currentPage + 1)
      } else if (e.key === 'Escape') {
        setChatOpen((prev) => !prev)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [currentPage, doc, handlePageChange])

  const handleSendChat = (message: string) => {
    if (activeSessionId > 0) {
      streamChat.send({ docId, sessionId: activeSessionId, message, pageNum: currentPage, agentMode })
    }
  }

  const handleClearChat = () => {
    if (activeSessionId > 0) {
      clearChat.mutate({ docId, sessionId: activeSessionId })
    }
  }

  const handleSessionCreate = () => {
    createSession.mutate(
      { docId },
      { onSuccess: (newSession) => setActiveSessionId(newSession.id) },
    )
  }

  const handleSessionDelete = (sessionId: number) => {
    deleteSession.mutate({ docId, sessionId })
  }

  const handleSaveNote = (content: string, pageNum: number) => {
    createNote.mutate({ docId, content, pageNum, source: 'chat' })
  }

  const handleAddNote = (content: string, pageNum?: number) => {
    createNote.mutate({ docId, content, pageNum, source: 'manual' })
  }

  const handleDeleteNote = (noteId: number) => {
    deleteNote.mutate({ docId, noteId })
  }

  const handleGenerateStudyGuide = (saveAsNote: boolean, focus: string = 'conceptual') => {
    generateStudyGuideMutation.mutate(
      { docId, saveAsNote, focus },
      { onSuccess: (data) => setStudyGuide(data.sections) },
    )
  }

  const handleGenerateFaq = (saveAsNote: boolean) => {
    generateFaqMutation.mutate(
      { docId, saveAsNote },
      { onSuccess: (data) => setFaq(data.questions) },
    )
  }

  if (docLoading) {
    return <div className="text-center py-20 text-gray-500">{t('common.loading')}</div>
  }

  if (!doc) {
    return (
      <EmptyState
        icon={MessageSquare}
        title={t('reader.notFoundTitle')}
        description={t('reader.notFoundDesc')}
        action={
          <button
            onClick={() => navigate('/reader')}
            className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
          >
            {t('reader.backToList')}
          </button>
        }
      />
    )
  }

  const tabs: { key: RightTab; icon: typeof MessageSquare; label: string }[] = [
    { key: 'chat', icon: MessageSquare, label: t('reader.tabChat') },
    { key: 'overview', icon: BookOpen, label: t('reader.tabOverview') },
    { key: 'notes', icon: FileText, label: t('reader.tabNotes') },
  ]

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] -mx-6 -mt-6">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border-b border-gray-200 shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => navigate('/reader')}
            className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <h2 className="text-base font-semibold text-primary-950 truncate">{doc.title}</h2>
          <span className="text-xs text-gray-400 shrink-0">
            {doc.file_type.toUpperCase()} · {doc.total_pages} {t('reader.pages')}
          </span>
        </div>
        <button
          onClick={() => setChatOpen(!chatOpen)}
          className={`p-2 rounded-lg transition-colors ${
            chatOpen ? 'bg-primary-100 text-primary-700' : 'hover:bg-gray-100 text-gray-500'
          }`}
          title={t('reader.toggleChat')}
        >
          {chatOpen ? <PanelRightClose className="w-5 h-5" /> : <MessageSquare className="w-5 h-5" />}
        </button>
      </div>

      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Document content */}
        <div className={`flex flex-col transition-all duration-300 ${chatOpen ? 'w-[62%]' : 'w-full'}`}>
          <div className="flex-1 overflow-y-auto bg-gray-50 p-4">
            {isPdf ? (
              <PdfPageViewer
                fileUrl={getReaderFileUrl(docId)}
                pageNumber={currentPage}
              />
            ) : (
              <div className="max-w-3xl mx-auto bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <TextPageViewer
                  content={pageData?.content || ''}
                  isLoading={pageLoading}
                />
              </div>
            )}
          </div>
          <PageNavigation
            currentPage={currentPage}
            totalPages={doc.total_pages}
            onPageChange={handlePageChange}
          />
        </div>

        {/* Right: Tab panel */}
        {chatOpen && (
          <div className="w-[38%] border-l border-gray-200 flex flex-col">
            {/* Tab bar */}
            <div className="flex border-b border-gray-200 bg-white shrink-0">
              {tabs.map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.key}
                    onClick={() => setRightTab(tab.key)}
                    className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-2.5 text-xs font-medium transition-colors border-b-2 ${
                      rightTab === tab.key
                        ? 'border-primary-600 text-primary-700'
                        : 'border-transparent text-gray-400 hover:text-gray-600'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {tab.label}
                    {tab.key === 'notes' && notes.length > 0 && (
                      <span className="ml-0.5 px-1.5 py-0.5 bg-gray-100 text-gray-500 text-[10px] rounded-full">
                        {notes.length}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-hidden">
              {rightTab === 'chat' && (
                <ChatPanel
                  messages={chatMessages}
                  currentPage={currentPage}
                  isSending={streamChat.isStreaming}
                  sendError={streamChat.error}
                  onSend={handleSendChat}
                  onClear={handleClearChat}
                  sessions={sessions}
                  activeSessionId={activeSessionId}
                  onSessionSelect={setActiveSessionId}
                  onSessionCreate={handleSessionCreate}
                  onSessionDelete={handleSessionDelete}
                  suggestions={suggestions}
                  suggestionsLoading={suggestionsLoading}
                  streamingContent={streamChat.streamingContent}
                  isStreaming={streamChat.isStreaming}
                  agentMode={agentMode}
                  onToggleAgent={() => setAgentMode(prev => !prev)}
                  agentSteps={streamChat.agentSteps}
                  onPageJump={handlePageChange}
                  onSaveNote={handleSaveNote}
                />
              )}
              {rightTab === 'overview' && (
                <div className="h-full overflow-y-auto">
                  <DocumentOverview
                    overview={overview}
                    isLoading={overviewLoading}
                    isGenerating={regenerateOverview.isPending}
                    hasError={overviewError}
                    onGenerate={() => regenerateOverview.mutate(docId)}
                    onPageJump={handlePageChange}
                  />
                  {/* Study tools below overview */}
                  {overview && (
                    <div className="px-4 pb-4 border-t border-gray-100 pt-4">
                      <StudyTools
                        onGenerateStudyGuide={handleGenerateStudyGuide}
                        onGenerateFaq={handleGenerateFaq}
                        studyGuide={studyGuide}
                        faq={faq}
                        isGeneratingGuide={generateStudyGuideMutation.isPending}
                        isGeneratingFaq={generateFaqMutation.isPending}
                      />
                    </div>
                  )}
                </div>
              )}
              {rightTab === 'notes' && (
                <NotesPanel
                  notes={notes}
                  isLoading={notesLoading}
                  onAdd={handleAddNote}
                  onDelete={handleDeleteNote}
                  onPageJump={handlePageChange}
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
