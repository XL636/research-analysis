import { useState, useRef, useEffect } from 'react'
import { Send, Trash2, MessageSquare } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import ChatMessage from './ChatMessage'
import SessionSwitcher from './SessionSwitcher'
import SuggestedQuestions from './SuggestedQuestions'
import type { ReaderChatMessage, ReaderSession } from '../../types'

interface ChatPanelProps {
  messages: ReaderChatMessage[]
  currentPage: number
  isSending: boolean
  onSend: (message: string) => void
  onClear: () => void
  // Session props
  sessions: ReaderSession[]
  activeSessionId: number
  onSessionSelect: (sessionId: number) => void
  onSessionCreate: () => void
  onSessionDelete: (sessionId: number) => void
  // Suggestion props
  suggestions: string[]
  suggestionsLoading: boolean
}

export default function ChatPanel({
  messages,
  currentPage,
  isSending,
  onSend,
  onClear,
  sessions,
  activeSessionId,
  onSessionSelect,
  onSessionCreate,
  onSessionDelete,
  suggestions,
  suggestionsLoading,
}: ChatPanelProps) {
  const { t } = useTranslation()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = (message?: string) => {
    const text = message || input.trim()
    if (!text || isSending) return
    onSend(text)
    if (!message) setInput('')
  }

  const handleClear = () => {
    if (window.confirm(t('reader.chatClearConfirm'))) {
      onClear()
    }
  }

  const handleSuggestionClick = (question: string) => {
    handleSend(question)
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <div className="flex items-center gap-2 min-w-0">
          <MessageSquare className="w-4 h-4 text-primary-600 shrink-0" />
          <h3 className="text-sm font-semibold text-primary-950 shrink-0">{t('reader.chatTitle')}</h3>
          {sessions.length > 0 && (
            <SessionSwitcher
              sessions={sessions}
              activeSessionId={activeSessionId}
              onSelect={onSessionSelect}
              onCreate={onSessionCreate}
              onDelete={onSessionDelete}
            />
          )}
        </div>
        {messages.length > 0 && (
          <button
            onClick={handleClear}
            className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
            title={t('reader.chatClear')}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <SuggestedQuestions
              questions={suggestions}
              isLoading={suggestionsLoading}
              hasMessages={false}
              onSelect={handleSuggestionClick}
            />
            {!suggestionsLoading && suggestions.length === 0 && (
              <>
                <MessageSquare className="w-10 h-10 mb-2 opacity-30" />
                <p className="text-sm">{t('reader.chatEmpty')}</p>
              </>
            )}
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {isSending && (
              <div className="flex justify-start mb-3">
                <div className="bg-gray-100 rounded-xl rounded-bl-sm px-4 py-3">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce [animation-delay:0ms]" />
                    <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce [animation-delay:150ms]" />
                    <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Suggestions (compact mode when messages exist) */}
      {messages.length > 0 && (
        <SuggestedQuestions
          questions={suggestions}
          isLoading={false}
          hasMessages={true}
          onSelect={handleSuggestionClick}
        />
      )}

      {/* Input */}
      <div className="px-4 py-3 border-t border-gray-200">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            placeholder={t('reader.chatPlaceholder')}
            rows={2}
            className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isSending}
            className="p-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <div className="text-[10px] text-gray-400 mt-1">
          {t('reader.chatPageLabel', { num: currentPage })} · Enter {t('reader.chatSend')}
        </div>
      </div>
    </div>
  )
}
