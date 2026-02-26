import { useTranslation } from 'react-i18next'

interface SuggestedQuestionsProps {
  questions: string[]
  isLoading: boolean
  hasMessages: boolean
  onSelect: (question: string) => void
}

export default function SuggestedQuestions({
  questions,
  isLoading,
  hasMessages,
  onSelect,
}: SuggestedQuestionsProps) {
  const { t } = useTranslation()

  // Loading skeleton
  if (isLoading) {
    return (
      <div className={`flex flex-wrap gap-2 ${hasMessages ? 'px-4 pb-2' : 'justify-center items-center p-6'}`}>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className={`rounded-full bg-gray-100 animate-pulse ${
              hasMessages ? 'h-7 w-32' : 'h-9 w-40'
            }`}
          />
        ))}
      </div>
    )
  }

  if (questions.length === 0) return null

  // No messages: centered large display
  if (!hasMessages) {
    return (
      <div className="flex flex-col items-center gap-3 p-6">
        <p className="text-xs text-gray-400 mb-1">{t('reader.suggestions')}</p>
        <div className="flex flex-wrap justify-center gap-2 max-w-sm">
          {questions.map((q, i) => (
            <button
              key={i}
              onClick={() => onSelect(q)}
              className="px-4 py-2 text-sm bg-primary-50 text-primary-700 rounded-full hover:bg-primary-100 transition-colors border border-primary-200"
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    )
  }

  // Has messages: compact chip row above input
  return (
    <div className="flex flex-wrap gap-1.5 px-4 pb-2">
      {questions.map((q, i) => (
        <button
          key={i}
          onClick={() => onSelect(q)}
          className="px-2.5 py-1 text-xs bg-gray-50 text-gray-600 rounded-full hover:bg-primary-50 hover:text-primary-700 transition-colors border border-gray-200 hover:border-primary-200 truncate max-w-[200px]"
          title={q}
        >
          {q}
        </button>
      ))}
    </div>
  )
}
