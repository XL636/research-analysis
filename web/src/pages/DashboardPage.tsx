import { useQuery } from '@tanstack/react-query'
import { Inbox } from 'lucide-react'
import { getStats } from '../api/dashboard'
import StatsGrid from '../components/dashboard/StatsGrid'
import RecentActivity from '../components/dashboard/RecentActivity'
import EmptyState from '../components/ui/EmptyState'

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getStats,
  })

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-heading font-bold text-primary-950 mb-6">
          Dashboard
        </h1>
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  if (!stats || stats.total_documents === 0) {
    return (
      <div>
        <h1 className="text-2xl font-heading font-bold text-primary-950 mb-6">
          Dashboard
        </h1>
        <EmptyState
          icon={Inbox}
          title="No data yet"
          description="Upload and analyze your first research document to see dashboard statistics."
        />
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-heading font-bold text-primary-950 mb-6">
        Dashboard
      </h1>
      <div className="space-y-8">
        <StatsGrid stats={stats} />
        <RecentActivity documents={stats.recent_documents} />
      </div>
    </div>
  )
}
