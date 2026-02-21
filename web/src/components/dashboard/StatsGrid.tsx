import { FileText, TrendingUp, Star, Tag } from 'lucide-react'
import KpiCard from '../ui/KpiCard'
import type { DashboardStats } from '../../types'

interface StatsGridProps {
  stats: DashboardStats
}

export default function StatsGrid({ stats }: StatsGridProps) {
  const topTag = stats.top_tags[0]

  return (
    <div className="grid grid-cols-4 gap-6">
      <KpiCard
        title="Total Documents"
        value={stats.total_documents}
        icon={FileText}
      />
      <KpiCard
        title="Recent Analyses"
        value={stats.recent_analyses}
        icon={TrendingUp}
        trend="Last 7 days"
      />
      <KpiCard
        title="Avg. Score"
        value={stats.avg_score.toFixed(1)}
        icon={Star}
      />
      <KpiCard
        title="Top Tag"
        value={topTag?.name || 'N/A'}
        icon={Tag}
        trend={topTag ? `${topTag.count} documents` : undefined}
      />
    </div>
  )
}
