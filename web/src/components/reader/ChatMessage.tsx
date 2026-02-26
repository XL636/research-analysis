import { useTranslation } from 'react-i18next'
import MarkdownRenderer from '../ui/MarkdownRenderer'
import type { ReaderChatMessage as ChatMsg } from '../../types'

interface ChatMessageProps {
  message: ChatMsg
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const { t } = useTranslation()
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
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
            <MarkdownRenderer content={message.content} />
          </div>
        )}
        <div className={`text-[10px] mt-1 ${isUser ? 'text-primary-200' : 'text-gray-400'}`}>
          {t('reader.chatPageLabel', { num: message.page_num })}
        </div>
      </div>
    </div>
  )
}
