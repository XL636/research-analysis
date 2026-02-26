import { useState, useEffect } from 'react'
import { Plus, FileText, Lock, Pencil, Trash2, X, Eye } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import EmptyState from '../components/ui/EmptyState'
import { getTemplates, createTemplate, updateTemplate, deleteTemplate } from '../api/templates'
import type { ReportTemplate } from '../types'

type DialogMode = 'create' | 'edit' | 'preview' | null

export default function TemplatesPage() {
  const { t } = useTranslation()
  const [templates, setTemplates] = useState<ReportTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogMode, setDialogMode] = useState<DialogMode>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null)

  // Form state
  const [formName, setFormName] = useState('')
  const [formDisplayName, setFormDisplayName] = useState('')
  const [formDescription, setFormDescription] = useState('')
  const [formPrompt, setFormPrompt] = useState('')
  const [saving, setSaving] = useState(false)

  const loadTemplates = async () => {
    try {
      const res = await getTemplates()
      setTemplates(res.templates)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadTemplates() }, [])

  const openCreate = () => {
    setFormName('')
    setFormDisplayName('')
    setFormDescription('')
    setFormPrompt('')
    setSelectedTemplate(null)
    setDialogMode('create')
  }

  const openEdit = (tpl: ReportTemplate) => {
    setFormName(tpl.name)
    setFormDisplayName(tpl.display_name)
    setFormDescription(tpl.description)
    setFormPrompt(tpl.prompt_content)
    setSelectedTemplate(tpl)
    setDialogMode('edit')
  }

  const openPreview = (tpl: ReportTemplate) => {
    setSelectedTemplate(tpl)
    setDialogMode('preview')
  }

  const closeDialog = () => {
    setDialogMode(null)
    setSelectedTemplate(null)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      if (dialogMode === 'create') {
        await createTemplate({
          name: formName,
          display_name: formDisplayName,
          description: formDescription,
          prompt_content: formPrompt,
        })
      } else if (dialogMode === 'edit' && selectedTemplate) {
        await updateTemplate(selectedTemplate.id, {
          display_name: formDisplayName,
          description: formDescription,
          prompt_content: formPrompt,
        })
      }
      closeDialog()
      await loadTemplates()
    } catch {
      // ignore
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (tpl: ReportTemplate) => {
    if (!confirm(t('template.deleteConfirm'))) return
    try {
      await deleteTemplate(tpl.id)
      await loadTemplates()
    } catch {
      // ignore
    }
  }

  if (loading) {
    return <div className="text-center py-12 text-gray-500">{t('common.loading')}</div>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-heading font-bold text-primary-950">
          {t('template.title')}
        </h1>
        <button
          type="button"
          onClick={openCreate}
          className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200"
        >
          <Plus className="h-4 w-4" />
          {t('template.create')}
        </button>
      </div>

      {templates.length === 0 ? (
        <EmptyState
          icon={FileText}
          title={t('template.emptyTitle')}
          description={t('template.emptyDesc')}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map(tpl => (
            <div
              key={tpl.id}
              className="bg-surface-card rounded-xl shadow-sm p-5 border border-gray-100 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary-500" />
                  <h3 className="font-medium text-primary-950">{tpl.display_name}</h3>
                </div>
                {tpl.is_builtin ? (
                  <span className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
                    <Lock className="h-3 w-3" />
                    {t('template.builtin')}
                  </span>
                ) : (
                  <span className="text-xs text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                    {t('template.custom')}
                  </span>
                )}
              </div>

              <p className="text-sm text-gray-500 mb-3 line-clamp-2">
                {tpl.description || t('template.noDescription')}
              </p>

              <div className="text-xs text-gray-400 mb-4">
                {tpl.name} · {tpl.prompt_content.length} {t('template.chars')}
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => openPreview(tpl)}
                  className="flex items-center gap-1 text-xs text-gray-500 hover:text-primary-600 transition-colors"
                >
                  <Eye className="h-3.5 w-3.5" />
                  {t('template.preview')}
                </button>
                {!tpl.is_builtin && (
                  <>
                    <button
                      type="button"
                      onClick={() => openEdit(tpl)}
                      className="flex items-center gap-1 text-xs text-gray-500 hover:text-primary-600 transition-colors"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      {t('template.edit')}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(tpl)}
                      className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-500 transition-colors"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      {t('template.delete')}
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Dialog: Create / Edit */}
      {(dialogMode === 'create' || dialogMode === 'edit') && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-heading font-semibold text-primary-950">
                {dialogMode === 'create' ? t('template.createTitle') : t('template.editTitle')}
              </h3>
              <button type="button" onClick={closeDialog} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              {dialogMode === 'create' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('template.nameLabel')}</label>
                  <input
                    type="text"
                    value={formName}
                    onChange={e => setFormName(e.target.value)}
                    placeholder="my-template"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('template.displayNameLabel')}</label>
                <input
                  type="text"
                  value={formDisplayName}
                  onChange={e => setFormDisplayName(e.target.value)}
                  placeholder={t('template.displayNamePlaceholder')}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('template.descLabel')}</label>
                <input
                  type="text"
                  value={formDescription}
                  onChange={e => setFormDescription(e.target.value)}
                  placeholder={t('template.descPlaceholder')}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('template.promptLabel')}</label>
                <textarea
                  value={formPrompt}
                  onChange={e => setFormPrompt(e.target.value)}
                  rows={12}
                  placeholder={t('template.promptPlaceholder')}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                type="button"
                onClick={closeDialog}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                {t('common.cancel')}
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={saving || (dialogMode === 'create' && (!formName || !formDisplayName))}
                className="px-4 py-2 text-sm font-medium text-white bg-emerald-500 rounded-lg hover:bg-emerald-600 disabled:opacity-50"
              >
                {saving ? t('settings.saving') : t('settings.save')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dialog: Preview */}
      {dialogMode === 'preview' && selectedTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-heading font-semibold text-primary-950">
                {selectedTemplate.display_name}
              </h3>
              <button type="button" onClick={closeDialog} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="text-sm text-gray-500 mb-4">{selectedTemplate.description}</div>
            <div className="bg-gray-50 rounded-lg p-4">
              <pre className="text-xs font-mono text-gray-700 whitespace-pre-wrap">
                {selectedTemplate.prompt_content}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
