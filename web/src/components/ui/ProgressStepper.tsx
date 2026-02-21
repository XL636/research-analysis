import { Circle, Loader, CheckCircle, XCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'

interface Step {
  name: string
  status: 'pending' | 'running' | 'completed' | 'error'
}

interface ProgressStepperProps {
  steps: Step[]
}

const statusConfig = {
  pending: {
    icon: Circle,
    color: 'text-gray-300',
    lineColor: 'bg-gray-200',
    labelKey: 'status.pending',
  },
  running: {
    icon: Loader,
    color: 'text-primary-500',
    lineColor: 'bg-primary-200',
    labelKey: 'status.running',
  },
  completed: {
    icon: CheckCircle,
    color: 'text-emerald-500',
    lineColor: 'bg-emerald-300',
    labelKey: 'status.completed',
  },
  error: {
    icon: XCircle,
    color: 'text-red-500',
    lineColor: 'bg-red-300',
    labelKey: 'status.error',
  },
}

export default function ProgressStepper({ steps }: ProgressStepperProps) {
  const { t } = useTranslation()

  return (
    <div className="space-y-0">
      {steps.map((step, index) => {
        const config = statusConfig[step.status]
        const Icon = config.icon
        const isLast = index === steps.length - 1

        return (
          <div key={step.name} className="flex items-start gap-3">
            {/* Icon + connecting line */}
            <div className="flex flex-col items-center">
              <Icon
                className={`h-5 w-5 flex-shrink-0 ${config.color} ${
                  step.status === 'running' ? 'animate-spin' : ''
                }`}
              />
              {!isLast && (
                <div
                  className={`w-0.5 h-8 mt-1 ${config.lineColor} transition-colors duration-300`}
                />
              )}
            </div>

            {/* Step label */}
            <div className="pb-8">
              <p
                className={`text-sm font-medium capitalize ${
                  step.status === 'running'
                    ? 'text-primary-700'
                    : step.status === 'completed'
                    ? 'text-emerald-700'
                    : step.status === 'error'
                    ? 'text-red-700'
                    : 'text-gray-400'
                }`}
              >
                {step.name}
              </p>
              <p className="text-xs text-gray-400 mt-0.5">{t(config.labelKey)}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
