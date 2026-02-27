import { useState, useRef, useEffect } from 'react'
import { Send, Trash2, MessageSquare } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import ChatMessage from './ChatMessage'
import SessionSwitcher from './SessionSwitcher'
import SuggestedQuestions from './SuggestedQuestions'
import MarkdownRenderer from '../ui/MarkdownRenderer'
import type { AgentStep } from '../../hooks/useReader'
import type { ReaderChatMessage, ReaderSession } from '../../types'

const TOOL_NAME_MAP: Record<string, string> = {
  search_pages: 'reader.agentSearchPages',
  get_page: 'reader.agentGetPage',
  search_knowledge_base: 'reader.agentSearchKB',
  get_document_info: 'reader.agentGetInfo',
}

interface ChatPanelProps {
  messages: ReaderChatMessage[]
  currentPage: number
  isSending: boolean
  sendError?: string | null
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
  // Streaming props
  streamingContent?: string
  isStreaming?: boolean
  // Agent mode props
  agentMode?: boolean
  onToggleAgent?: () => void
  agentSteps?: AgentStep[]
}

export default function ChatPanel({
  messages,
  currentPage,
  isSending,
  sendError,
  onSend,
  onClear,
  sessions,
  activeSessionId,
  onSessionSelect,
  onSessionCreate,
  onSessionDelete,
  suggestions,
  suggestionsLoading,
  streamingContent = '',
  isStreaming = false,
  agentMode = false,
  onToggleAgent,
  agentSteps = [],
}: ChatPanelProps) {
  const { t } = useTranslation()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const handleSend = (message?: string) => {
    const text = message || input.trim()
    if (!text || isSending || isStreaming) return
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
              disabled={isSending}
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
            {(isSending || isStreaming) && (
              <div className="flex justify-start mb-3">
                <div className="max-w-[85%] bg-gray-100 text-primary-950 rounded-xl rounded-bl-sm px-4 py-2.5">
                  {/* Agent thinking steps */}
                  {isStreaming && agentSteps.length > 0 && (
                    <div className="text-xs text-gray-500 mb-2 space-y-1">
                      {agentSteps.map((step, i) => (
                        <div key={i} className="flex items-center gap-1.5">
                          {step.type === 'tool_use' ? (
                            <>
                              <span className="inline-block w-3 h-3 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                              <span>{t(TOOL_NAME_MAP[step.tool] || step.tool)}...</span>
                            </>
                          ) : (
                            <>
                              <span className="text-green-500 text-xs">&#10003;</span>
                              <span className="text-gray-400 truncate max-w-[200px]">{step.detail}</span>
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  {isStreaming && streamingContent ? (
                    <div className="text-sm [&_.markdown-content_p]:mb-2 [&_.markdown-content_p:last-child]:mb-0">
                      <MarkdownRenderer content={streamingContent} />
                      <span className="inline-block w-0.5 h-4 bg-primary-500 animate-pulse ml-0.5 align-text-bottom" />
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 py-0.5">
                      <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce [animation-delay:0ms]" />
                      <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce [animation-delay:150ms]" />
                      <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce [animation-delay:300ms]" />
                    </div>
                  )}
                </div>
              </div>
            )}
            {sendError && !isSending && (
              <div className="flex justify-start mb-3">
                <div className="bg-red-50 text-red-600 text-xs rounded-xl rounded-bl-sm px-4 py-2 border border-red-200">
                  {t('reader.chatError')}
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
          disabled={isSending}
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
            disabled={!input.trim() || isSending || isStreaming}
            className="p-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <div className="flex items-center justify-between mt-1">
          <div className="text-[10px] text-gray-400">
            {t('reader.chatPageLabel', { num: currentPage })} · Enter {t('reader.chatSend')}
          </div>
          {onToggleAgent && (
            <button
              onClick={onToggleAgent}
              className={`text-[10px] px-2 py-0.5 rounded-full border transition-colors ${
                agentMode
                  ? 'bg-amber-50 border-amber-300 text-amber-700'
                  : 'bg-gray-50 border-gray-200 text-gray-400 hover:border-gray-300'
              }`}
              title={t('reader.agentTooltip')}
            >
              Agent
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
