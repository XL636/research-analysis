import { useTranslation } from 'react-i18next'
import { Bookmark } from 'lucide-react'
import MarkdownRenderer from '../ui/MarkdownRenderer'
import type { ReaderChatMessage as ChatMsg } from '../../types'

interface ChatMessageProps {
  message: ChatMsg
  onPageJump?: (page: number) => void
  onSaveNote?: (content: string, pageNum: number) => void
}

function PageRefContent({ content, onPageJump }: { content: string; onPageJump?: (page: number) => void }) {
  // Replace [p.X] patterns with clickable badges
  const parts = content.split(/(\[p\.\d+\])/g)
  if (parts.length <= 1) return <MarkdownRenderer content={content} />

  // Process content: replace [p.X] in the markdown content before rendering
  const processed = content.replace(
    /\[p\.(\d+)\]/g,
    '<button class="page-ref-badge" data-page="$1">[p.$1]</button>'
  )

  return (
    <div
      className="markdown-content"
      onClick={(e) => {
        const target = e.target as HTMLElement
        if (target.classList.contains('page-ref-badge')) {
          const page = parseInt(target.dataset.page || '0')
          if (page > 0) onPageJump?.(page)
        }
      }}
    >
      <MarkdownRenderer content={processed} />
      <style>{`
        .page-ref-badge {
          display: inline;
          padding: 0 4px;
          margin: 0 1px;
          font-size: 0.75rem;
          font-weight: 600;
          color: #2563eb;
          background: #dbeafe;
          border-radius: 4px;
          cursor: pointer;
          border: none;
          font-family: inherit;
          transition: background 0.15s;
        }
        .page-ref-badge:hover {
          background: #bfdbfe;
        }
      `}</style>
    </div>
  )
}

export default function ChatMessage({ message, onPageJump, onSaveNote }: ChatMessageProps) {
  const { t } = useTranslation()
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3 group`}>
      <div
        className={`max-w-[85%] rounded-xl px-4 py-2.5 ${
          isUser
            ? 'bg-primary-600 text-white rounded-br-sm'
            : 'bg-gray-100 text-primary-950 rounded-bl-sm'
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="text-sm [&_.markdown-content_p]:mb-2 [&_.markdown-content_p:last-child]:mb-0">
            <PageRefContent content={message.content} onPageJump={onPageJump} />
          </div>
        )}
        <div className={`flex items-center justify-between mt-1 ${isUser ? 'text-primary-200' : 'text-gray-400'}`}>
          <span className="text-[10px]">
            {t('reader.chatPageLabel', { num: message.page_num })}
          </span>
          {!isUser && onSaveNote && (
            <button
              onClick={() => onSaveNote(message.content, message.page_num)}
              className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 hover:text-primary-600"
              title={t('reader.saveAsNote')}
            >
              <Bookmark className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
