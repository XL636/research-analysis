import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, FolderOpen, Plus, Pencil, Trash2, Check, X, Loader } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import {
  useDocuments,
  useTags,
  useCollections,
  useCreateCollection,
  useRenameCollection,
  useDeleteCollection,
  useBatchDeleteDocuments,
} from '../hooks/useDocuments'
import { useSearch } from '../hooks/useSearch'
import SearchInput from '../components/ui/SearchInput'
import Badge from '../components/ui/Badge'
import DataTable from '../components/ui/DataTable'
import type { Column } from '../components/ui/DataTable'
import EmptyState from '../components/ui/EmptyState'
import type { DocumentSummary, SearchResult, CollectionSummary } from '../types'

type TableRow = DocumentSummary | SearchResult

type SelectedCollection = 'all' | 'uncategorized' | number

function CollectionsPanel({
  selectedCollectionId,
  onSelect,
}: {
  selectedCollectionId: SelectedCollection
  onSelect: (id: SelectedCollection) => void
}) {
  const { t } = useTranslation()
  const { data: collections } = useCollections()
  const createCollection = useCreateCollection()
  const renameCollection = useRenameCollection()
  const deleteCollection = useDeleteCollection()

  const [isCreating, setIsCreating] = useState(false)
  const [newName, setNewName] = useState('')
  const [renamingId, setRenamingId] = useState<number | null>(null)
  const [renameValue, setRenameValue] = useState('')

  const createInputRef = useRef<HTMLInputElement>(null)
  const renameInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isCreating && createInputRef.current) {
      createInputRef.current.focus()
    }
  }, [isCreating])

  useEffect(() => {
    if (renamingId !== null && renameInputRef.current) {
      renameInputRef.current.focus()
    }
  }, [renamingId])

  const handleCreate = () => {
    const trimmed = newName.trim()
    if (!trimmed) return
    createCollection.mutate(trimmed, {
      onSuccess: () => {
        setNewName('')
        setIsCreating(false)
      },
    })
  }

  const handleRename = (id: number) => {
    const trimmed = renameValue.trim()
    if (!trimmed) return
    renameCollection.mutate(
      { id, name: trimmed },
      {
        onSuccess: () => {
          setRenamingId(null)
          setRenameValue('')
        },
      },
    )
  }

  const handleDelete = (id: number) => {
    deleteCollection.mutate(id, {
      onSuccess: () => {
        if (selectedCollectionId === id) {
          onSelect('all')
        }
      },
    })
  }

  const itemBase =
    'flex items-center gap-2 px-3 py-2 rounded-lg text-sm cursor-pointer transition-colors duration-150'
  const itemActive = 'bg-primary-50 text-primary-700 font-medium'
  const itemInactive = 'text-gray-600 hover:bg-gray-50'

  return (
    <nav className="space-y-1">
      {/* All documents */}
      <button
        className={`w-full ${itemBase} ${selectedCollectionId === 'all' ? itemActive : itemInactive}`}
        onClick={() => onSelect('all')}
      >
        <FolderOpen className="w-4 h-4 shrink-0" />
        <span className="truncate">{t('knowledge.collectionAll')}</span>
      </button>

      {/* Uncategorized */}
      <button
        className={`w-full ${itemBase} ${selectedCollectionId === 'uncategorized' ? itemActive : itemInactive}`}
        onClick={() => onSelect('uncategorized')}
      >
        <FolderOpen className="w-4 h-4 shrink-0" />
        <span className="truncate">{t('knowledge.collectionUncategorized')}</span>
      </button>

      {/* Separator */}
      <div className="border-t border-gray-200 my-2" />

      {/* Collection list */}
      {collections?.map((col: CollectionSummary) => (
        <div key={col.id} className="group relative">
          {renamingId === col.id ? (
            <div className="flex items-center gap-1 px-2 py-1">
              <input
                ref={renameInputRef}
                type="text"
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleRename(col.id)
                  if (e.key === 'Escape') {
                    setRenamingId(null)
                    setRenameValue('')
                  }
                }}
                className="flex-1 min-w-0 px-2 py-1 text-sm border border-primary-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
              <button
                onClick={() => handleRename(col.id)}
                className="p-1 text-green-600 hover:text-green-700"
              >
                <Check className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => {
                  setRenamingId(null)
                  setRenameValue('')
                }}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              className={`w-full ${itemBase} ${selectedCollectionId === col.id ? itemActive : itemInactive}`}
              onClick={() => onSelect(col.id)}
            >
              <FolderOpen className="w-4 h-4 shrink-0" />
              <span className="flex-1 min-w-0 truncate text-left">{col.name}</span>
              <span className="text-xs text-gray-400 shrink-0 group-hover:hidden">
                {col.document_count}
              </span>
              <span className="hidden group-hover:flex items-center gap-0.5 shrink-0">
                <span
                  role="button"
                  className="p-0.5 text-gray-400 hover:text-primary-600"
                  onClick={(e) => {
                    e.stopPropagation()
                    setRenamingId(col.id)
                    setRenameValue(col.name)
                  }}
                >
                  <Pencil className="w-3.5 h-3.5" />
                </span>
                <span
                  role="button"
                  className="p-0.5 text-gray-400 hover:text-red-600"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(col.id)
                  }}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </span>
              </span>
            </button>
          )}
        </div>
      ))}

      {/* Create new collection */}
      {isCreating ? (
        <div className="flex items-center gap-1 px-2 py-1">
          <input
            ref={createInputRef}
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleCreate()
              if (e.key === 'Escape') {
                setIsCreating(false)
                setNewName('')
              }
            }}
            placeholder={t('knowledge.collectionNewPlaceholder')}
            className="flex-1 min-w-0 px-2 py-1 text-sm border border-primary-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
          <button
            onClick={handleCreate}
            className="p-1 text-green-600 hover:text-green-700"
          >
            <Check className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => {
              setIsCreating(false)
              setNewName('')
            }}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ) : (
        <button
          className={`w-full ${itemBase} ${itemInactive}`}
          onClick={() => setIsCreating(true)}
        >
          <Plus className="w-4 h-4 shrink-0" />
          <span className="truncate">{t('knowledge.collectionNew')}</span>
        </button>
      )}
    </nav>
  )
}

const sourceTypeOptions = [
  { value: '', labelKey: 'knowledge.sourceAll' },
  { value: 'user_upload', labelKey: 'knowledge.sourceUserUpload' },
  { value: 'auto_research', labelKey: 'knowledge.sourceAutoResearch' },
  { value: 'manual_reference', labelKey: 'knowledge.sourceManualRef' },
]

export default function KnowledgeBasePage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [selectedTag, setSelectedTag] = useState<string | undefined>(undefined)
  const [selectedCollectionId, setSelectedCollectionId] =
    useState<SelectedCollection>('all')
  const [selectedSourceType, setSelectedSourceType] = useState<string>('')
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [showBatchDeleteConfirm, setShowBatchDeleteConfirm] = useState(false)
  const batchDeleteMut = useBatchDeleteDocuments()

  const { query, setQuery, results: searchResults } = useSearch()

  const baseParams = selectedTag
    ? { tag: selectedTag }
    : selectedCollectionId === 'all'
      ? undefined
      : selectedCollectionId === 'uncategorized'
        ? { uncategorized: true }
        : { collection_id: selectedCollectionId as number }

  const docParams = selectedSourceType
    ? { ...baseParams, source_type: selectedSourceType }
    : baseParams

  const { data: documents, isLoading: docsLoading } = useDocuments(docParams)
  const { data: tags } = useTags()

  const isSearching = query.length > 0
  const displayData: TableRow[] = isSearching
    ? searchResults.data ?? []
    : documents ?? []
  const isLoading = isSearching ? searchResults.isLoading : docsLoading

  const columns: Column<TableRow>[] = [
    {
      key: 'title',
      header: t('table.title'),
    },
    {
      key: 'file_type',
      header: t('table.type'),
      render: (row) => <Badge variant="primary">{row.file_type}</Badge>,
    },
    {
      key: 'tags',
      header: t('table.tags'),
      render: (row) => (
        <div className="flex flex-wrap gap-1">
          {row.tags
            .split(', ')
            .filter(Boolean)
            .map((tag) => (
              <Badge key={tag} variant="accent">
                {tag}
              </Badge>
            ))}
        </div>
      ),
    },
    {
      key: 'source_type',
      header: t('table.type'),
      render: (row) => {
        const st = ('source_type' in row ? (row as DocumentSummary).source_type : undefined) || 'user_upload'
        const label = st === 'auto_research'
          ? t('knowledge.sourceAutoResearch')
          : st === 'manual_reference'
            ? t('knowledge.sourceManualRef')
            : t('knowledge.sourceUserUpload')
        const variant = st === 'auto_research' ? 'primary' : st === 'manual_reference' ? 'accent' : 'default'
        return <Badge variant={variant as 'default' | 'primary' | 'accent'}>{label}</Badge>
      },
    },
    {
      key: 'date',
      header: t('table.date'),
    },
  ]

  const handleTagClick = (tagName: string) => {
    setSelectedTag((prev) => (prev === tagName ? undefined : tagName))
  }

  const handleBatchDelete = () => {
    if (selectedIds.size === 0) return
    setShowBatchDeleteConfirm(true)
  }

  const confirmBatchDelete = () => {
    batchDeleteMut.mutate([...selectedIds], {
      onSuccess: () => {
        setSelectedIds(new Set())
        setShowBatchDeleteConfirm(false)
      },
    })
  }

  return (
    <div>
      <h1 className="text-2xl font-heading font-bold text-primary-950 mb-6">
        {t('knowledge.title')}
      </h1>

      <div className="flex gap-6">
        {/* Left sidebar */}
        <div className="w-48 shrink-0">
          <CollectionsPanel
            selectedCollectionId={selectedCollectionId}
            onSelect={setSelectedCollectionId}
          />
        </div>

        {/* Right content */}
        <div className="flex-1 min-w-0">
          <div className="space-y-6">
            {/* Search bar */}
            <SearchInput
              value={query}
              onChange={setQuery}
              placeholder={t('knowledge.searchPlaceholder')}
            />

            {/* Source type filter */}
            <div className="flex flex-wrap gap-2">
              {sourceTypeOptions.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setSelectedSourceType(opt.value)}
                  className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
                    selectedSourceType === opt.value
                      ? 'bg-primary-500 text-white'
                      : 'bg-white border border-gray-300 text-gray-700 hover:border-primary-300'
                  }`}
                >
                  {t(opt.labelKey)}
                </button>
              ))}
            </div>

            {/* Tag filter */}
            {tags && tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {tags.map((tag) => (
                  <button
                    key={tag.name}
                    onClick={() => handleTagClick(tag.name)}
                    className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 ${
                      selectedTag === tag.name
                        ? 'bg-primary-500 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:border-primary-300'
                    }`}
                  >
                    {tag.name}
                    <span
                      className={`ml-1.5 text-xs ${
                        selectedTag === tag.name
                          ? 'text-primary-200'
                          : 'text-gray-400'
                      }`}
                    >
                      {tag.count}
                    </span>
                  </button>
                ))}
              </div>
            )}

            {/* Batch action bar */}
            {selectedIds.size > 0 && (
              <div className="flex items-center gap-3 px-4 py-3 bg-primary-50 rounded-lg">
                <span className="text-sm text-primary-700">
                  {t('knowledge.batchSelected', { count: selectedIds.size })}
                </span>
                <button
                  onClick={handleBatchDelete}
                  disabled={batchDeleteMut.isPending}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-white bg-red-500 rounded-lg hover:bg-red-600 transition-colors duration-200 disabled:opacity-50"
                >
                  {batchDeleteMut.isPending ? (
                    <Loader className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Trash2 className="w-3.5 h-3.5" />
                  )}
                  {t('knowledge.batchDelete')}
                </button>
                <button
                  onClick={() => setSelectedIds(new Set())}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  {t('knowledge.batchClearSelection')}
                </button>
              </div>
            )}

            {/* Batch delete confirm dialog */}
            {showBatchDeleteConfirm && (
              <div className="px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800 space-y-3">
                <p>
                  {t('knowledge.batchDeleteConfirm', { count: selectedIds.size })}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={confirmBatchDelete}
                    disabled={batchDeleteMut.isPending}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors duration-200 disabled:opacity-50"
                  >
                    {batchDeleteMut.isPending && <Loader className="w-3.5 h-3.5 animate-spin" />}
                    {t('detail.confirmDelete')}
                  </button>
                  <button
                    onClick={() => setShowBatchDeleteConfirm(false)}
                    className="px-3 py-1.5 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200"
                  >
                    {t('common.cancel')}
                  </button>
                </div>
              </div>
            )}

            {/* Document list */}
            {isLoading ? (
              <p className="text-gray-500">{t('common.loading')}</p>
            ) : displayData.length === 0 ? (
              <EmptyState
                icon={Search}
                title={t('knowledge.noDocsTitle')}
                description={
                  isSearching
                    ? t('knowledge.noDocsSearch')
                    : t('knowledge.noDocsDefault')
                }
              />
            ) : (
              <DataTable<TableRow>
                columns={columns}
                data={displayData}
                onRowClick={(row) => navigate(`/knowledge/${row.id}`)}
                selectable
                selectedIds={selectedIds}
                onSelectionChange={setSelectedIds}
                getRowId={(row) => row.id}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
