import { useState } from 'react'
import { Plus, Trash2, FileText, BookmarkCheck } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import MarkdownRenderer from '../ui/MarkdownRenderer'
import type { ReaderNote } from '../../types'

interface NotesPanelProps {
  notes: ReaderNote[]
  isLoading: boolean
  onAdd: (content: string, pageNum?: number) => void
  onDelete: (noteId: number) => void
  onPageJump?: (page: number) => void
}

function NoteCard({
  note,
  onDelete,
  onPageJump,
}: {
  note: ReaderNote
  onDelete: (id: number) => void
  onPageJump?: (page: number) => void
}) {
  const { t } = useTranslation()

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3 group hover:border-gray-300 transition-colors">
      <div className="text-sm text-gray-700 mb-2 line-clamp-4">
        <MarkdownRenderer content={note.content} />
      </div>
      <div className="flex items-center justify-between text-[10px] text-gray-400">
        <div className="flex items-center gap-2">
          {note.page_num && (
            <button
              onClick={() => onPageJump?.(note.page_num!)}
              className="flex items-center gap-0.5 px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded hover:bg-blue-100 transition-colors"
            >
              p.{note.page_num}
            </button>
          )}
          {note.source === 'chat' && (
            <span className="flex items-center gap-0.5 text-gray-400">
              <BookmarkCheck className="w-3 h-3" />
              {t('reader.noteFromChat')}
            </span>
          )}
        </div>
        <button
          onClick={() => {
            if (window.confirm(t('reader.noteDeleteConfirm'))) {
              onDelete(note.id)
            }
          }}
          className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all"
        >
          <Trash2 className="w-3 h-3" />
        </button>
      </div>
    </div>
  )
}

export default function NotesPanel({ notes, isLoading, onAdd, onDelete, onPageJump }: NotesPanelProps) {
  const { t } = useTranslation()
  const [showForm, setShowForm] = useState(false)
  const [content, setContent] = useState('')
  const [pageNum, setPageNum] = useState('')

  const handleSubmit = () => {
    if (!content.trim()) return
    onAdd(content.trim(), pageNum ? parseInt(pageNum) : undefined)
    setContent('')
    setPageNum('')
    setShowForm(false)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400">
        <div className="w-5 h-5 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Add note button */}
      <div className="px-4 py-3 border-b border-gray-100">
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-700 font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          {t('reader.addNote')}
        </button>
      </div>

      {/* Add note form */}
      {showForm && (
        <div className="px-4 py-3 border-b border-gray-100 bg-gray-50 space-y-2">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder={t('reader.notePlaceholder')}
            rows={3}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <div className="flex items-center gap-2">
            <input
              type="number"
              value={pageNum}
              onChange={(e) => setPageNum(e.target.value)}
              placeholder={t('reader.notePageLabel')}
              min={1}
              className="w-32 px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
            <button
              onClick={handleSubmit}
              disabled={!content.trim()}
              className="px-3 py-1 bg-primary-600 text-white text-xs font-medium rounded hover:bg-primary-700 disabled:opacity-40 transition-colors"
            >
              {t('reader.addNote')}
            </button>
          </div>
        </div>
      )}

      {/* Notes list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {notes.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <FileText className="w-10 h-10 text-gray-300 mb-3" />
            <p className="text-sm font-medium text-gray-500 mb-1">{t('reader.notesEmpty')}</p>
            <p className="text-xs text-gray-400">{t('reader.notesEmptyDesc')}</p>
          </div>
        ) : (
          notes.map((note) => (
            <NoteCard key={note.id} note={note} onDelete={onDelete} onPageJump={onPageJump} />
          ))
        )}
      </div>
    </div>
  )
}
