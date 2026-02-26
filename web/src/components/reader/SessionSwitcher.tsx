import { useState, useRef, useEffect } from 'react'
import { ChevronDown, Plus, Trash2, MessageSquare } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { ReaderSession } from '../../types'

interface SessionSwitcherProps {
  sessions: ReaderSession[]
  activeSessionId: number
  onSelect: (sessionId: number) => void
  onCreate: () => void
  onDelete: (sessionId: number) => void
}

export default function SessionSwitcher({
  sessions,
  activeSessionId,
  onSelect,
  onCreate,
  onDelete,
}: SessionSwitcherProps) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const activeSession = sessions.find((s) => s.id === activeSessionId)
  const displayTitle = activeSession
    ? activeSession.title.length > 15
      ? activeSession.title.slice(0, 15) + '...'
      : activeSession.title
    : t('reader.defaultSessionTitle')

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleDelete = (e: React.MouseEvent, sessionId: number) => {
    e.stopPropagation()
    if (sessions.length <= 1) return
    if (window.confirm(t('reader.deleteSessionConfirm'))) {
      onDelete(sessionId)
    }
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md transition-colors max-w-[180px]"
      >
        <span className="truncate">{displayTitle}</span>
        <ChevronDown className={`w-3 h-3 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-50 py-1">
          <div className="max-h-60 overflow-y-auto">
            {sessions.map((s) => (
              <div
                key={s.id}
                onClick={() => { onSelect(s.id); setOpen(false) }}
                className={`flex items-center justify-between px-3 py-2 cursor-pointer group transition-colors ${
                  s.id === activeSessionId ? 'bg-primary-50 text-primary-700' : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <MessageSquare className="w-3.5 h-3.5 shrink-0 text-gray-400" />
                  <div className="min-w-0">
                    <div className="text-xs font-medium truncate">
                      {s.title.length > 15 ? s.title.slice(0, 15) + '...' : s.title}
                    </div>
                    <div className="text-[10px] text-gray-400">
                      {t('reader.sessionMessages', { count: s.message_count })}
                    </div>
                  </div>
                </div>
                {sessions.length > 1 && (
                  <button
                    onClick={(e) => handleDelete(e, s.id)}
                    className="p-1 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                )}
              </div>
            ))}
          </div>
          <div className="border-t border-gray-100 mt-1 pt-1">
            <button
              onClick={() => { onCreate(); setOpen(false) }}
              className="flex items-center gap-2 w-full px-3 py-2 text-xs text-primary-600 hover:bg-primary-50 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              {t('reader.newSession')}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
