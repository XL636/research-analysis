import { useState } from 'react'
import { GraduationCap, HelpCircle, Bookmark, Lightbulb, Wrench, ClipboardCheck } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import MarkdownRenderer from '../ui/MarkdownRenderer'
import type { StudyGuideSection, FaqItem } from '../../types'

type FocusMode = 'conceptual' | 'practical' | 'review'

interface StudyToolsProps {
  onGenerateStudyGuide: (saveAsNote: boolean, focus: FocusMode) => void
  onGenerateFaq: (saveAsNote: boolean) => void
  studyGuide: StudyGuideSection[] | null
  faq: FaqItem[] | null
  isGeneratingGuide: boolean
  isGeneratingFaq: boolean
}

const FOCUS_MODES: { key: FocusMode; icon: typeof Lightbulb }[] = [
  { key: 'conceptual', icon: Lightbulb },
  { key: 'practical', icon: Wrench },
  { key: 'review', icon: ClipboardCheck },
]

export default function StudyTools({
  onGenerateStudyGuide,
  onGenerateFaq,
  studyGuide,
  faq,
  isGeneratingGuide,
  isGeneratingFaq,
}: StudyToolsProps) {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<'guide' | 'faq'>('guide')
  const [focusMode, setFocusMode] = useState<FocusMode>('conceptual')

  return (
    <div className="space-y-4">
      {/* Buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => { setActiveTab('guide'); if (!studyGuide) onGenerateStudyGuide(false, focusMode) }}
          disabled={isGeneratingGuide}
          className={`flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg border transition-colors ${
            activeTab === 'guide'
              ? 'bg-primary-50 border-primary-200 text-primary-700'
              : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
          }`}
        >
          <GraduationCap className="w-3.5 h-3.5" />
          {isGeneratingGuide ? t('reader.studyGuideGenerating') : t('reader.generateStudyGuide')}
        </button>
        <button
          onClick={() => { setActiveTab('faq'); if (!faq) onGenerateFaq(false) }}
          disabled={isGeneratingFaq}
          className={`flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg border transition-colors ${
            activeTab === 'faq'
              ? 'bg-primary-50 border-primary-200 text-primary-700'
              : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
          }`}
        >
          <HelpCircle className="w-3.5 h-3.5" />
          {isGeneratingFaq ? t('reader.faqGenerating') : t('reader.generateFaq')}
        </button>
      </div>

      {/* Focus mode selector (shown when guide tab is active) */}
      {activeTab === 'guide' && (
        <div className="flex gap-1.5">
          {FOCUS_MODES.map(({ key, icon: Icon }) => (
            <button
              key={key}
              onClick={() => {
                setFocusMode(key)
                // If guide already generated with different mode, regenerate
                if (studyGuide) onGenerateStudyGuide(false, key)
              }}
              disabled={isGeneratingGuide}
              className={`flex-1 inline-flex items-center justify-center gap-1 px-2 py-1.5 text-[11px] font-medium rounded-md border transition-colors ${
                focusMode === key
                  ? 'bg-primary-50 border-primary-300 text-primary-700'
                  : 'bg-gray-50 border-gray-200 text-gray-500 hover:bg-gray-100'
              }`}
            >
              <Icon className="w-3 h-3" />
              {t(`reader.focus_${key}`)}
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      {activeTab === 'guide' && studyGuide && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-gray-800">{t('reader.studyGuide')}</h4>
            <button
              onClick={() => onGenerateStudyGuide(true, focusMode)}
              className="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-primary-600"
            >
              <Bookmark className="w-3 h-3" />
              {t('reader.saveToNotes')}
            </button>
          </div>
          {studyGuide.map((section, i) => (
            <div key={i} className="bg-white border border-gray-200 rounded-lg p-3">
              <h5 className="text-sm font-medium text-gray-800 mb-1">{section.title}</h5>
              <div className="text-xs text-gray-600">
                <MarkdownRenderer content={section.content} />
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'faq' && faq && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-gray-800">{t('reader.faq')}</h4>
            <button
              onClick={() => onGenerateFaq(true)}
              className="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-primary-600"
            >
              <Bookmark className="w-3 h-3" />
              {t('reader.saveToNotes')}
            </button>
          </div>
          {faq.map((item, i) => (
            <div key={i} className="bg-white border border-gray-200 rounded-lg p-3">
              <h5 className="text-sm font-medium text-gray-800 mb-1">Q: {item.question}</h5>
              <div className="text-xs text-gray-600">
                <MarkdownRenderer content={item.answer} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Loading states */}
      {activeTab === 'guide' && isGeneratingGuide && (
        <div className="flex items-center justify-center py-8 text-gray-400">
          <div className="w-5 h-5 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin mr-2" />
          <span className="text-sm">{t('reader.studyGuideGenerating')}</span>
        </div>
      )}
      {activeTab === 'faq' && isGeneratingFaq && (
        <div className="flex items-center justify-center py-8 text-gray-400">
          <div className="w-5 h-5 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin mr-2" />
          <span className="text-sm">{t('reader.faqGenerating')}</span>
        </div>
      )}
    </div>
  )
}
