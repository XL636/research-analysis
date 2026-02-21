import type { LucideIcon } from 'lucide-react'

interface KpiCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  trend?: string
}

export default function KpiCard({ title, value, icon: Icon, trend }: KpiCardProps) {
  return (
    <div className="bg-surface-card rounded-xl shadow-sm p-6 transition-all duration-200 hover:shadow-md">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="mt-1 text-2xl font-heading font-bold text-primary-950">
            {value}
          </p>
          {trend && (
            <p className="mt-1 text-xs text-accent font-medium">{trend}</p>
          )}
        </div>
        <div className="rounded-lg bg-primary-100 p-3">
          <Icon className="h-5 w-5 text-primary-600" />
        </div>
      </div>
    </div>
  )
}
