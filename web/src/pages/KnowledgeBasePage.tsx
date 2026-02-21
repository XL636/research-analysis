import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useDocuments, useTags } from '../hooks/useDocuments'
import { useSearch } from '../hooks/useSearch'
import SearchInput from '../components/ui/SearchInput'
import Badge from '../components/ui/Badge'
import DataTable from '../components/ui/DataTable'
import type { Column } from '../components/ui/DataTable'
import EmptyState from '../components/ui/EmptyState'
import type { DocumentSummary, SearchResult } from '../types'

type TableRow = DocumentSummary | SearchResult

export default function KnowledgeBasePage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [selectedTag, setSelectedTag] = useState<string | undefined>(undefined)

  const { query, setQuery, results: searchResults } = useSearch()
  const { data: documents, isLoading: docsLoading } = useDocuments(selectedTag)
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
      key: 'date',
      header: t('table.date'),
    },
  ]

  const handleTagClick = (tagName: string) => {
    setSelectedTag((prev) => (prev === tagName ? undefined : tagName))
  }

  return (
    <div>
      <h1 className="text-2xl font-heading font-bold text-primary-950 mb-6">
        {t('knowledge.title')}
      </h1>

      <div className="space-y-6">
        {/* Search bar */}
        <SearchInput
          value={query}
          onChange={setQuery}
          placeholder={t('knowledge.searchPlaceholder')}
        />

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
          />
        )}
      </div>
    </div>
  )
}
