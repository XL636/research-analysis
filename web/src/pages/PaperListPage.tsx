import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PenLine, Plus, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { usePaperProjects, useCreatePaper, useDeletePaper } from '../hooks/usePaper'
import Badge from '../components/ui/Badge'
import DataTable from '../components/ui/DataTable'
import type { Column } from '../components/ui/DataTable'
import EmptyState from '../components/ui/EmptyState'
import type { PaperProjectSummary } from '../types'

const statusVariant: Record<string, 'default' | 'primary' | 'accent' | 'success' | 'warning'> = {
  created: 'default',
  outline_draft: 'primary',
  outline_confirmed: 'primary',
  writing: 'warning',
  draft_complete: 'accent',
  polishing: 'warning',
  finished: 'success',
}

export default function PaperListPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { data: projects, isLoading } = usePaperProjects()
  const createPaper = useCreatePaper()
  const deletePaper = useDeletePaper()

  const [showCreate, setShowCreate] = useState(false)
  const [formName, setFormName] = useState('')
  const [formTopic, setFormTopic] = useState('')
  const [formLang, setFormLang] = useState('zh')
  const [formVenue, setFormVenue] = useState('generic')
  const [formQuestion, setFormQuestion] = useState('')
  const [formWords, setFormWords] = useState(8000)

  const handleCreate = () => {
    if (!formName.trim()) return
    createPaper.mutate(
      {
        name: formName.trim(),
        topic: formTopic.trim() || undefined,
        language: formLang,
        venue: formVenue,
        research_question: formQuestion.trim() || undefined,
        target_word_count: formWords,
      },
      {
        onSuccess: (data) => {
          setShowCreate(false)
          setFormName('')
          setFormTopic('')
          setFormQuestion('')
          navigate(`/paper/${data.id}`)
        },
      },
    )
  }

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    deletePaper.mutate(id)
  }

  const columns: Column<PaperProjectSummary>[] = [
    { key: 'name', header: t('paper.name') },
    {
      key: 'status',
      header: t('paper.status'),
      render: (row) => (
        <Badge variant={statusVariant[row.status] || 'default'}>
          {t(`paper.statusLabel.${row.status}`)}
        </Badge>
      ),
    },
    { key: 'updated_at', header: t('paper.updatedAt') },
    {
      key: 'id',
      header: '',
      render: (row) => (
        <button
          onClick={(e) => handleDelete(e, row.id)}
          className="p-1.5 text-gray-400 hover:text-red-500 transition-colors duration-200"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      ),
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-heading font-bold text-primary-950">
          {t('paper.title')}
        </h1>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors duration-200"
        >
          <Plus className="w-4 h-4" />
          {t('paper.newProject')}
        </button>
      </div>

      {isLoading ? (
        <p className="text-gray-500">{t('common.loading')}</p>
      ) : !projects || projects.length === 0 ? (
        <EmptyState
          icon={PenLine}
          title={t('paper.emptyTitle')}
          description={t('paper.emptyDesc')}
          action={
            <button
              onClick={() => setShowCreate(true)}
              className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors duration-200"
            >
              {t('paper.newProject')}
            </button>
          }
        />
      ) : (
        <DataTable<PaperProjectSummary>
          columns={columns}
          data={projects}
          onRowClick={(row) => navigate(`/paper/${row.id}`)}
        />
      )}

      {/* Create dialog */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-lg w-full mx-4">
            <h3 className="text-lg font-heading font-semibold text-primary-950 mb-4">
              {t('paper.createTitle')}
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('paper.name')} *</label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder={t('paper.namePlaceholder')}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('paper.topicLabel')}</label>
                <input
                  type="text"
                  value={formTopic}
                  onChange={(e) => setFormTopic(e.target.value)}
                  placeholder={t('paper.topicPlaceholder')}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('paper.questionLabel')}</label>
                <input
                  type="text"
                  value={formQuestion}
                  onChange={(e) => setFormQuestion(e.target.value)}
                  placeholder={t('paper.questionPlaceholder')}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('paper.langLabel')}</label>
                  <select
                    value={formLang}
                    onChange={(e) => setFormLang(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="zh">{t('paper.langZh')}</option>
                    <option value="en">{t('paper.langEn')}</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('paper.venueLabel')}</label>
                  <select
                    value={formVenue}
                    onChange={(e) => setFormVenue(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="generic">{t('paper.venueGeneric')}</option>
                    <option value="neurips">NeurIPS</option>
                    <option value="icml">ICML</option>
                    <option value="iclr">ICLR</option>
                    <option value="acl">ACL</option>
                    <option value="aaai">AAAI</option>
                    <option value="chinese_journal">{t('paper.venueChinese')}</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('paper.wordsLabel')}</label>
                  <input
                    type="number"
                    value={formWords}
                    onChange={(e) => setFormWords(Number(e.target.value))}
                    min={1000}
                    max={50000}
                    step={1000}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleCreate}
                disabled={!formName.trim() || createPaper.isPending}
                className="px-4 py-2 text-sm text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {createPaper.isPending ? t('paper.creating') : t('paper.create')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
