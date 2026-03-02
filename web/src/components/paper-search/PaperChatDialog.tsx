import { useState, useRef, useEffect } from 'react'
import { X, Send, Loader2, MessageSquare } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { streamPaperChat, type PaperChatMessage } from '../../api/paperSearch'
import MarkdownRenderer from '../ui/MarkdownRenderer'
import type { PaperSearchResultItem } from '../../types'

interface PaperChatDialogProps {
  paper: PaperSearchResultItem
  onClose: () => void
}

export default function PaperChatDialog({ paper, onClose }: PaperChatDialogProps) {
  const { t } = useTranslation()
  const [messages, setMessages] = useState<PaperChatMessage[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || streaming) return

    const userMsg: PaperChatMessage = { role: 'user', content: trimmed }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setStreaming(true)
    setStreamingContent('')

    let accumulated = ''

    await streamPaperChat(
      {
        title: paper.title,
        abstract: paper.abstract || '',
        authors: paper.authors || '',
        year: paper.year || '',
        venue: paper.venue || '',
        message: trimmed,
        history: messages,
      },
      (delta) => {
        accumulated += delta
        setStreamingContent(accumulated)
      },
      () => {
        setMessages(prev => [...prev, { role: 'assistant', content: accumulated }])
        setStreamingContent('')
        setStreaming(false)
      },
      (error) => {
        setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${error}` }])
        setStreamingContent('')
        setStreaming(false)
      },
    )
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4 flex flex-col" style={{ maxHeight: '80vh' }}>
        {/* 头部 */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <div className="flex items-center gap-2 min-w-0">
            <MessageSquare className="h-5 w-5 text-primary-600 shrink-0" />
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {t('paperSearch.chatWith', { title: paper.title.slice(0, 50) })}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* 消息列表 */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {messages.length === 0 && !streaming && (
            <div className="text-center py-8 text-gray-400">
              <MessageSquare className="h-10 w-10 mx-auto mb-2 opacity-50" />
              <p className="text-sm">{t('paperSearch.chatEmpty')}</p>
              <p className="text-xs mt-1 text-gray-300">{t('paperSearch.chatHint')}</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-xl px-4 py-2.5 text-sm ${
                msg.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}>
                {msg.role === 'assistant' ? (
                  <MarkdownRenderer content={msg.content} />
                ) : (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                )}
              </div>
            </div>
          ))}

          {streaming && streamingContent && (
            <div className="flex justify-start">
              <div className="max-w-[85%] rounded-xl px-4 py-2.5 text-sm bg-gray-100 text-gray-900">
                <MarkdownRenderer content={streamingContent} />
              </div>
            </div>
          )}

          {streaming && !streamingContent && (
            <div className="flex justify-start">
              <div className="rounded-xl px-4 py-2.5 text-sm bg-gray-100 text-gray-400 flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                {t('reader.chatSending')}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 输入框 */}
        <div className="px-5 py-3 border-t border-gray-200">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t('paperSearch.chatPlaceholder')}
              disabled={streaming}
              className="flex-1 px-4 py-2.5 rounded-lg border border-gray-300 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none disabled:opacity-50 text-sm"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || streaming}
              className="px-4 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {streaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
