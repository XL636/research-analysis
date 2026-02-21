import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Badge from '../ui/Badge'
import DataTable from '../ui/DataTable'
import type { Column } from '../ui/DataTable'
import type { DocumentSummary } from '../../types'

interface RecentActivityProps {
  documents: DocumentSummary[]
}

export default function RecentActivity({ documents }: RecentActivityProps) {
  const navigate = useNavigate()
  const { t } = useTranslation()

  const columns: Column<DocumentSummary>[] = [
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

  return (
    <div>
      <h2 className="font-heading text-lg font-semibold text-primary-950 mb-4">
        {t('dashboard.recentActivity')}
      </h2>
      <DataTable<DocumentSummary>
        columns={columns}
        data={documents}
        onRowClick={(row) => navigate(`/knowledge/${row.id}`)}
      />
    </div>
  )
}
