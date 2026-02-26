import { useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useTranslation } from 'react-i18next'

interface PageNavigationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export default function PageNavigation({ currentPage, totalPages, onPageChange }: PageNavigationProps) {
  const { t } = useTranslation()
  const [inputValue, setInputValue] = useState('')

  const goPrev = () => {
    if (currentPage > 1) onPageChange(currentPage - 1)
  }

  const goNext = () => {
    if (currentPage < totalPages) onPageChange(currentPage + 1)
  }

  const handleJump = () => {
    const num = parseInt(inputValue, 10)
    if (num >= 1 && num <= totalPages) {
      onPageChange(num)
      setInputValue('')
    }
  }

  return (
    <div className="flex items-center justify-center gap-3 py-3 px-4 bg-white border-t border-gray-200">
      <button
        onClick={goPrev}
        disabled={currentPage <= 1}
        className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        title={t('reader.prevPage')}
      >
        <ChevronLeft className="w-5 h-5" />
      </button>

      <span className="text-sm text-gray-700 font-medium min-w-[100px] text-center">
        {t('reader.pageOf', { current: currentPage, total: totalPages })}
      </span>

      <button
        onClick={goNext}
        disabled={currentPage >= totalPages}
        className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        title={t('reader.nextPage')}
      >
        <ChevronRight className="w-5 h-5" />
      </button>

      <div className="ml-2 flex items-center gap-1">
        <input
          type="number"
          min={1}
          max={totalPages}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleJump()}
          placeholder="#"
          className="w-14 px-2 py-1 text-sm border border-gray-300 rounded-lg text-center focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
        <button
          onClick={handleJump}
          className="px-2 py-1 text-xs text-primary-600 hover:bg-primary-50 rounded transition-colors"
        >
          {t('reader.goToPage')}
        </button>
      </div>
    </div>
  )
}
