import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  action?: ReactNode
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <Icon className="h-12 w-12 text-gray-300 mb-4" />
      <h3 className="text-lg font-heading font-semibold text-gray-500 mb-1">
        {title}
      </h3>
      <p className="text-sm text-gray-400 text-center max-w-sm mb-6">
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  )
}
