import { useNavigate } from 'react-router-dom'
import Badge from '../ui/Badge'
import DataTable from '../ui/DataTable'
import type { Column } from '../ui/DataTable'
import type { DocumentSummary } from '../../types'

interface RecentActivityProps {
  documents: DocumentSummary[]
}

const columns: Column<DocumentSummary>[] = [
  {
    key: 'title',
    header: 'Title',
  },
  {
    key: 'file_type',
    header: 'Type',
    render: (row) => <Badge variant="primary">{row.file_type}</Badge>,
  },
  {
    key: 'tags',
    header: 'Tags',
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
    header: 'Date',
  },
]

export default function RecentActivity({ documents }: RecentActivityProps) {
  const navigate = useNavigate()

  return (
    <div>
      <h2 className="font-heading text-lg font-semibold text-primary-950 mb-4">
        Recent Activity
      </h2>
      <DataTable<DocumentSummary>
        columns={columns}
        data={documents}
        onRowClick={(row) => navigate(`/knowledge/${row.id}`)}
      />
    </div>
  )
}
