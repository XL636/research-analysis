import { FileText, TrendingUp, Star, Tag } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import KpiCard from '../ui/KpiCard'
import type { DashboardStats } from '../../types'

interface StatsGridProps {
  stats: DashboardStats
}

export default function StatsGrid({ stats }: StatsGridProps) {
  const { t } = useTranslation()
  const topTag = stats.top_tags[0]

  return (
    <div className="grid grid-cols-4 gap-6">
      <KpiCard
        title={t('dashboard.totalDocuments')}
        value={stats.total_documents}
        icon={FileText}
      />
      <KpiCard
        title={t('dashboard.recentAnalyses')}
        value={stats.recent_analyses}
        icon={TrendingUp}
        trend={t('dashboard.last7Days')}
      />
      <KpiCard
        title={t('dashboard.avgScore')}
        value={stats.avg_score.toFixed(1)}
        icon={Star}
      />
      <KpiCard
        title={t('dashboard.topTag')}
        value={topTag?.name || 'N/A'}
        icon={Tag}
        trend={topTag ? t('dashboard.nDocuments', { count: topTag.count }) : undefined}
      />
    </div>
  )
}
