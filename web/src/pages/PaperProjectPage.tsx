import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  FileText,
  CheckCircle,
  PenLine,
  Sparkles,
  Download,
  RefreshCw,
  Send,
  Loader,
  Search,
  BookOpen,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import {
  usePaperProject,
  useReviseOutline,
  useConfirmOutline,
  useWriteSections,
  useReviseSection,
  usePolishPaper,
  useExportPaper,
  useResearchPapers,
  useReferences,
} from '../hooks/usePaper'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'
import MarkdownRenderer from '../components/ui/MarkdownRenderer'
import type { PaperSectionResponse } from '../types'

type ActiveTab = 'research' | 'outline' | 'draft' | 'export'

const sectionStatusIcon: Record<string, string> = {
  pending: '⏳',
  writing: '✏️',
  draft: '📝',
  revising: '🔄',
  done: '✅',
}

const statusVariant: Record<string, 'default' | 'primary' | 'accent' | 'success' | 'warning'> = {
  created: 'default',
  researched: 'accent',
  outline_draft: 'primary',
  outline_confirmed: 'primary',
  writing: 'warning',
  draft_complete: 'accent',
  polishing: 'warning',
  finished: 'success',
}

const sourceTypeBadgeVariant: Record<string, 'default' | 'primary' | 'accent' | 'success' | 'warning'> = {
  user_upload: 'default',
  auto_research: 'primary',
  manual_reference: 'accent',
}

export default function PaperProjectPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { data: project, isLoading } = usePaperProject(id || '')

  const reviseOutline = useReviseOutline()
  const confirmOutlineMut = useConfirmOutline()
  const writeSections = useWriteSections()
  const reviseSectionMut = useReviseSection()
  const polishPaper = usePolishPaper()
  const exportPaper = useExportPaper()
  const researchPapersMut = useResearchPapers()
  const { data: referencesData } = useReferences(id || '')

  const [activeTab, setActiveTab] = useState<ActiveTab>('research')
  const [feedback, setFeedback] = useState('')
  const [selectedSection, setSelectedSection] = useState<string | null>(null)
  const [sectionFeedback, setSectionFeedback] = useState('')
  const [polishInstructions, setPolishInstructions] = useState('')
  const [exportFormat, setExportFormat] = useState('markdown')

  const isAnyMutating =
    reviseOutline.isPending ||
    confirmOutlineMut.isPending ||
    writeSections.isPending ||
    reviseSectionMut.isPending ||
    polishPaper.isPending ||
    exportPaper.isPending ||
    researchPapersMut.isPending

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-heading font-bold text-primary-950 mb-6">
          {t('paper.projectTitle')}
        </h1>
        <p className="text-gray-500">{t('common.loading')}</p>
      </div>
    )
  }

  if (!project) {
    return (
      <div>
        <h1 className="text-2xl font-heading font-bold text-primary-950 mb-6">
          {t('paper.projectTitle')}
        </h1>
        <EmptyState
          icon={FileText}
          title={t('paper.notFoundTitle')}
          description={t('paper.notFoundDesc')}
        />
      </div>
    )
  }

  const hasDraft = project.draft_sections.length > 0
  const hasOutline = project.outline !== null

  // Determine default tab based on project status
  const effectiveTab =
    activeTab === 'draft' && !hasDraft
      ? 'outline'
      : activeTab === 'outline' && !hasOutline
        ? 'outline'
        : activeTab

  const handleReviseOutline = () => {
    if (!feedback.trim()) return
    reviseOutline.mutate({ id: project.id, feedback: feedback.trim() })
    setFeedback('')
  }

  const handleConfirmOutline = () => {
    confirmOutlineMut.mutate(project.id)
  }

  const handleWriteAll = () => {
    writeSections.mutate({ id: project.id })
  }

  const handleWriteSection = (sectionId: string) => {
    writeSections.mutate({ id: project.id, sectionId })
  }

  const handleReviseSection = () => {
    if (!selectedSection || !sectionFeedback.trim()) return
    reviseSectionMut.mutate({
      id: project.id,
      sectionId: selectedSection,
      feedback: sectionFeedback.trim(),
    })
    setSectionFeedback('')
    setSelectedSection(null)
  }

  const handlePolish = () => {
    polishPaper.mutate({ id: project.id, instructions: polishInstructions.trim() || undefined })
    setPolishInstructions('')
  }

  const handleExport = () => {
    exportPaper.mutate(
      { id: project.id, format: exportFormat },
      {
        onSuccess: (data) => {
          alert(`${t('paper.exportSuccess')}: ${data.output_path}`)
        },
      },
    )
  }

  const handleStartResearch = () => {
    researchPapersMut.mutate({ id: project.id })
  }

  const tabs: { key: ActiveTab; labelKey: string }[] = [
    { key: 'research', labelKey: 'paper.tabResearch' },
    { key: 'outline', labelKey: 'paper.tabOutline' },
    { key: 'draft', labelKey: 'paper.tabDraft' },
    { key: 'export', labelKey: 'paper.tabExport' },
  ]

  return (
    <div>
      {/* Header */}
      <button
        onClick={() => navigate('/paper')}
        className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-800 mb-4 transition-colors duration-200"
      >
        <ArrowLeft className="w-4 h-4" />
        {t('paper.backToList')}
      </button>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-heading font-bold text-primary-950">
            {project.name}
          </h1>
          <div className="flex items-center gap-3 mt-2">
            <Badge variant={statusVariant[project.status] || 'default'}>
              {t(`paper.statusLabel.${project.status}`)}
            </Badge>
            <span className="text-sm text-gray-500">
              {project.language === 'zh' ? t('paper.langZh') : t('paper.langEn')}
            </span>
            {project.venue !== 'generic' && (
              <span className="text-sm text-gray-500">{project.venue.toUpperCase()}</span>
            )}
            <span className="text-sm text-gray-500">
              {t('paper.wordTarget')}: {project.target_word_count.toLocaleString()}
            </span>
            {hasDraft && (
              <span className="text-sm text-gray-500">
                {t('paper.currentWords')}: {project.draft_total_word_count.toLocaleString()}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors duration-200 ${
              effectiveTab === tab.key
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {t(tab.labelKey)}
          </button>
        ))}
      </div>

      {/* Loading overlay for mutations */}
      {isAnyMutating && (
        <div className="flex items-center gap-2 mb-4 px-4 py-3 bg-primary-50 rounded-lg text-sm text-primary-700">
          <Loader className="w-4 h-4 animate-spin" />
          {t('paper.processing')}
        </div>
      )}

      {/* Tab: Research */}
      {effectiveTab === 'research' && (
        <div className="space-y-6">
          {/* Research action */}
          <div className="bg-surface-card rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-heading text-lg font-semibold text-primary-950 flex items-center gap-2">
                <Search className="w-5 h-5" />
                {t('paper.researchTitle')}
              </h3>
              <button
                onClick={handleStartResearch}
                disabled={researchPapersMut.isPending}
                className="flex items-center gap-1.5 px-4 py-2 text-sm text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors duration-200 disabled:opacity-50"
              >
                {researchPapersMut.isPending ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    {t('paper.researching')}
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    {t('paper.startResearch')}
                  </>
                )}
              </button>
            </div>

            {researchPapersMut.isSuccess && (
              <div className="px-4 py-3 bg-emerald-50 rounded-lg text-sm text-emerald-700">
                {t('paper.researchComplete')} —{' '}
                {t('paper.researchStats', {
                  analyzed: researchPapersMut.data?.analyzed || 0,
                  metadataOnly: researchPapersMut.data?.metadata_only || 0,
                  failed: researchPapersMut.data?.failed || 0,
                })}
              </div>
            )}
          </div>

          {/* References list */}
          {referencesData && referencesData.references.length > 0 ? (
            <div className="bg-surface-card rounded-xl shadow-sm p-6">
              <h3 className="font-heading text-lg font-semibold text-primary-950 mb-4 flex items-center gap-2">
                <BookOpen className="w-5 h-5" />
                {t('paper.referencesList')} ({referencesData.references.length})
              </h3>
              <div className="space-y-3">
                {referencesData.references.map((ref) => (
                  <div
                    key={ref.doc_id}
                    className="border border-gray-200 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-primary-950 text-sm">
                        {ref.title}
                      </span>
                      <div className="flex items-center gap-2">
                        {ref.has_analysis ? (
                          <Badge variant="success">{t('paper.refAnalyzed')}</Badge>
                        ) : (
                          <Badge variant="warning">{t('paper.refMetadataOnly')}</Badge>
                        )}
                        <Badge
                          variant={sourceTypeBadgeVariant[ref.source_type] || 'default'}
                        >
                          {ref.source_type === 'auto_research'
                            ? t('paper.refSourceAuto')
                            : ref.source_type === 'manual_reference'
                              ? t('paper.refSourceManual')
                              : t('paper.refSourceUser')}
                        </Badge>
                      </div>
                    </div>
                    {ref.summary && (
                      <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                        {ref.summary}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <EmptyState
              icon={Search}
              title={t('paper.researchEmpty')}
              description={t('paper.researchEmptyDesc')}
            />
          )}
        </div>
      )}

      {/* Tab: Outline */}
      {effectiveTab === 'outline' && (
        <div className="space-y-6">
          {!hasOutline ? (
            <EmptyState
              icon={FileText}
              title={t('paper.noOutlineTitle')}
              description={t('paper.noOutlineDesc')}
            />
          ) : (
            <>
              {/* Abstract draft */}
              {project.outline!.abstract_draft && (
                <div className="bg-surface-card rounded-xl shadow-sm p-6">
                  <h3 className="font-heading text-lg font-semibold text-primary-950 mb-3">
                    {t('paper.abstractDraft')}
                  </h3>
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {project.outline!.abstract_draft}
                  </p>
                </div>
              )}

              {/* Sections */}
              <div className="bg-surface-card rounded-xl shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-heading text-lg font-semibold text-primary-950">
                    {t('paper.outlineSections')}
                  </h3>
                  <span className="text-sm text-gray-500">
                    {t('paper.estimatedWords')}: {project.outline!.estimated_word_count.toLocaleString()}
                  </span>
                </div>

                <div className="space-y-3">
                  {project.outline!.sections.map((section) => (
                    <div
                      key={section.id}
                      className="border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400 font-mono">{section.id}</span>
                          <span
                            className="font-medium text-primary-950"
                            style={{ paddingLeft: `${(section.level - 1) * 16}px` }}
                          >
                            {section.title}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500">{section.word_count} {t('paper.words')}</span>
                      </div>
                      {section.outline_points.length > 0 && (
                        <ul className="list-disc list-inside text-sm text-gray-600 space-y-1 ml-2">
                          {section.outline_points.map((point, i) => (
                            <li key={i}>{point}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Outline actions */}
              {(project.status === 'outline_draft' || project.status === 'created') && (
                <div className="bg-surface-card rounded-xl shadow-sm p-6 space-y-4">
                  <h3 className="font-heading text-lg font-semibold text-primary-950">
                    {t('paper.outlineActions')}
                  </h3>

                  {/* Revise */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={feedback}
                      onChange={(e) => setFeedback(e.target.value)}
                      placeholder={t('paper.revisePlaceholder')}
                      className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      onKeyDown={(e) => e.key === 'Enter' && handleReviseOutline()}
                    />
                    <button
                      onClick={handleReviseOutline}
                      disabled={!feedback.trim() || reviseOutline.isPending}
                      className="flex items-center gap-1.5 px-4 py-2 text-sm text-white bg-amber-500 rounded-lg hover:bg-amber-600 transition-colors duration-200 disabled:opacity-50"
                    >
                      <RefreshCw className="w-4 h-4" />
                      {t('paper.revise')}
                    </button>
                  </div>

                  {/* Confirm */}
                  <button
                    onClick={handleConfirmOutline}
                    disabled={confirmOutlineMut.isPending}
                    className="flex items-center gap-1.5 px-4 py-2 text-sm text-white bg-emerald-500 rounded-lg hover:bg-emerald-600 transition-colors duration-200 disabled:opacity-50"
                  >
                    <CheckCircle className="w-4 h-4" />
                    {t('paper.confirmOutline')}
                  </button>
                </div>
              )}

              {/* Citations */}
              {project.citations.length > 0 && (
                <div className="bg-surface-card rounded-xl shadow-sm p-6">
                  <h3 className="font-heading text-lg font-semibold text-primary-950 mb-3">
                    {t('paper.citations')} ({project.citations.length})
                  </h3>
                  <div className="space-y-2">
                    {project.citations.map((ref, i) => (
                      <div key={i} className="text-sm text-gray-700">
                        <span className="font-mono text-xs text-gray-400 mr-2">[{ref.key}]</span>
                        {ref.authors && <span>{ref.authors}. </span>}
                        <span className="font-medium">{ref.title}</span>
                        {ref.venue && <span className="text-gray-500">. {ref.venue}</span>}
                        {ref.year && <span className="text-gray-500">, {ref.year}</span>}
                        {' '}
                        <Badge variant={ref.source === 'knowledge_base' ? 'accent' : 'default'}>
                          {ref.source}
                        </Badge>
                        {ref.has_full_analysis && (
                          <Badge variant="success">{t('paper.hasDeepAnalysis')}</Badge>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Tab: Draft */}
      {effectiveTab === 'draft' && (
        <div className="space-y-6">
          {!hasDraft ? (
            <EmptyState
              icon={PenLine}
              title={t('paper.noDraftTitle')}
              description={t('paper.noDraftDesc')}
            />
          ) : (
            <>
              {/* Action bar */}
              <div className="flex items-center gap-3">
                {project.draft_sections.some((s) => s.status === 'pending') && (
                  <button
                    onClick={handleWriteAll}
                    disabled={writeSections.isPending}
                    className="flex items-center gap-1.5 px-4 py-2 text-sm text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors duration-200 disabled:opacity-50"
                  >
                    <PenLine className="w-4 h-4" />
                    {t('paper.writeAll')}
                  </button>
                )}
                {project.draft_sections.every((s) => s.status === 'draft' || s.status === 'done') && (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={polishInstructions}
                      onChange={(e) => setPolishInstructions(e.target.value)}
                      placeholder={t('paper.polishPlaceholder')}
                      className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                    <button
                      onClick={handlePolish}
                      disabled={polishPaper.isPending}
                      className="flex items-center gap-1.5 px-4 py-2 text-sm text-white bg-amber-500 rounded-lg hover:bg-amber-600 transition-colors duration-200 disabled:opacity-50"
                    >
                      <Sparkles className="w-4 h-4" />
                      {t('paper.polish')}
                    </button>
                  </div>
                )}
              </div>

              {/* Abstract */}
              {project.draft_abstract && (
                <div className="bg-surface-card rounded-xl shadow-sm p-6">
                  <h3 className="font-heading text-lg font-semibold text-primary-950 mb-3">
                    {t('paper.abstract')}
                  </h3>
                  <p className="text-sm text-gray-700 leading-relaxed">{project.draft_abstract}</p>
                </div>
              )}

              {/* Sections */}
              {project.draft_sections.map((section: PaperSectionResponse) => (
                <div
                  key={section.id}
                  className="bg-surface-card rounded-xl shadow-sm p-6"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <span>{sectionStatusIcon[section.status] || '❓'}</span>
                      <h3 className="font-heading text-lg font-semibold text-primary-950">
                        {section.title}
                      </h3>
                      <Badge variant={section.status === 'done' ? 'success' : section.status === 'draft' ? 'accent' : 'default'}>
                        {t(`paper.sectionStatus.${section.status}`)}
                      </Badge>
                      <span className="text-xs text-gray-500">{section.word_count} {t('paper.words')}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {section.status === 'pending' && (
                        <button
                          onClick={() => handleWriteSection(section.id)}
                          disabled={writeSections.isPending}
                          className="flex items-center gap-1 px-3 py-1.5 text-xs text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors duration-200 disabled:opacity-50"
                        >
                          <PenLine className="w-3 h-3" />
                          {t('paper.write')}
                        </button>
                      )}
                      {(section.status === 'draft' || section.status === 'done') && (
                        <button
                          onClick={() => setSelectedSection(selectedSection === section.id ? null : section.id)}
                          className="flex items-center gap-1 px-3 py-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg hover:bg-amber-100 transition-colors duration-200"
                        >
                          <RefreshCw className="w-3 h-3" />
                          {t('paper.revise')}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Revise input for this section */}
                  {selectedSection === section.id && (
                    <div className="flex gap-2 mb-4">
                      <input
                        type="text"
                        value={sectionFeedback}
                        onChange={(e) => setSectionFeedback(e.target.value)}
                        placeholder={t('paper.sectionRevisePlaceholder')}
                        className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        onKeyDown={(e) => e.key === 'Enter' && handleReviseSection()}
                      />
                      <button
                        onClick={handleReviseSection}
                        disabled={!sectionFeedback.trim() || reviseSectionMut.isPending}
                        className="flex items-center gap-1 px-3 py-2 text-sm text-white bg-amber-500 rounded-lg hover:bg-amber-600 transition-colors duration-200 disabled:opacity-50"
                      >
                        <Send className="w-4 h-4" />
                      </button>
                    </div>
                  )}

                  {/* Content */}
                  {section.content ? (
                    <div className="prose-sm">
                      <MarkdownRenderer content={section.content} />
                    </div>
                  ) : (
                    <p className="text-sm text-gray-400 italic">{t('paper.sectionEmpty')}</p>
                  )}
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {/* Tab: Export */}
      {effectiveTab === 'export' && (
        <div className="bg-surface-card rounded-xl shadow-sm p-6 space-y-6">
          <h3 className="font-heading text-lg font-semibold text-primary-950">
            {t('paper.exportTitle')}
          </h3>

          {!hasDraft ? (
            <p className="text-sm text-gray-500">{t('paper.exportNoDraft')}</p>
          ) : (
            <>
              {/* Full content preview */}
              <div className="border border-gray-200 rounded-lg p-6 max-h-96 overflow-y-auto">
                <MarkdownRenderer
                  content={
                    `# ${project.draft_title}\n\n## Abstract\n\n${project.draft_abstract}\n\n` +
                    project.draft_sections
                      .map((s) => `${'#'.repeat(s.level + 1)} ${s.title}\n\n${s.content || ''}`)
                      .join('\n\n')
                  }
                />
              </div>

              {/* Export controls */}
              <div className="flex items-center gap-3">
                <select
                  value={exportFormat}
                  onChange={(e) => setExportFormat(e.target.value)}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="markdown">Markdown</option>
                  <option value="docx">DOCX</option>
                  <option value="pdf">PDF</option>
                  <option value="latex">LaTeX</option>
                </select>
                <button
                  onClick={handleExport}
                  disabled={exportPaper.isPending}
                  className="flex items-center gap-1.5 px-4 py-2 text-sm text-white bg-emerald-500 rounded-lg hover:bg-emerald-600 transition-colors duration-200 disabled:opacity-50"
                >
                  <Download className="w-4 h-4" />
                  {t('paper.export')}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
