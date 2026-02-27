import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, MessageSquare, PanelRightClose } from 'lucide-react'
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
} from '../hooks/useReader'
import { getReaderFileUrl } from '../api/reader'
import PdfPageViewer from '../components/reader/PdfPageViewer'
import TextPageViewer from '../components/reader/TextPageViewer'
import PageNavigation from '../components/reader/PageNavigation'
import ChatPanel from '../components/reader/ChatPanel'
import EmptyState from '../components/ui/EmptyState'

export default function ReaderViewPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const docId = Number(id) || 0

  const { data: doc, isLoading: docLoading } = useReaderDocument(docId)
  const [currentPage, setCurrentPage] = useState(1)
  const [chatOpen, setChatOpen] = useState(true)
  const [activeSessionId, setActiveSessionId] = useState(0)

  // Initialize current page from document's saved progress
  useEffect(() => {
    if (doc && doc.current_page) {
      setCurrentPage(doc.current_page)
    }
  }, [doc?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  const isPdf = doc?.file_type === 'pdf'

  // Fetch page content for non-PDF files
  const { data: pageData, isLoading: pageLoading } = useReaderPage(
    docId,
    currentPage,
  )

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
    // If active session was deleted, switch to first available
    if (sessions.length > 0 && !sessions.find((s) => s.id === activeSessionId)) {
      setActiveSessionId(sessions[0].id)
    }
  }, [sessions, activeSessionId])

  // Session chat
  const { data: chatHistoryData } = useSessionChatHistory(docId, activeSessionId)
  const streamChat = useStreamChat()
  const clearChat = useClearSessionChat()

  const chatMessages = chatHistoryData?.messages || []

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
      // Don't capture when typing in input/textarea
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
      streamChat.send({ docId, sessionId: activeSessionId, message, pageNum: currentPage })
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
      {
        onSuccess: (newSession) => {
          setActiveSessionId(newSession.id)
        },
      }
    )
  }

  const handleSessionDelete = (sessionId: number) => {
    deleteSession.mutate({ docId, sessionId })
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

        {/* Right: Chat panel */}
        {chatOpen && (
          <div className="w-[38%] border-l border-gray-200">
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
            />
          </div>
        )}
      </div>
    </div>
  )
}
