import { useState, useMemo, useEffect } from 'react'
import { Eye, EyeOff, Save, CheckCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import Badge from '../ui/Badge'
import type { AgentModelAssignment, ModelInfo } from '../../types'

interface AgentModelCardProps {
  assignment: AgentModelAssignment
  availableModels: ModelInfo[]
  onModelChange: (agent: string, model: string) => void
  onSaveKey: (envVar: string, key: string) => Promise<void>
  isSaving?: boolean
}

export default function AgentModelCard({
  assignment,
  availableModels,
  onModelChange,
  onSaveKey,
  isSaving,
}: AgentModelCardProps) {
  const { t } = useTranslation()
  const [keyInput, setKeyInput] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [keySaved, setKeySaved] = useState(false)

  const needsKey = !assignment.api_key_configured

  // Group models by provider
  const modelsByProvider = useMemo(() => {
    const grouped: Record<string, ModelInfo[]> = {}
    for (const m of availableModels) {
      if (!grouped[m.provider]) grouped[m.provider] = []
      grouped[m.provider].push(m)
    }
    return grouped
  }, [availableModels])

  // Derive current provider from the assigned model
  const currentProvider = useMemo(() => {
    const match = availableModels.find((m) => m.name === assignment.model)
    return match?.provider ?? Object.keys(modelsByProvider)[0] ?? ''
  }, [assignment.model, availableModels, modelsByProvider])

  const [selectedProvider, setSelectedProvider] = useState(currentProvider)

  // Sync selectedProvider when external model changes
  useEffect(() => {
    setSelectedProvider(currentProvider)
  }, [currentProvider])

  const providerModels = modelsByProvider[selectedProvider] ?? []

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider)
    // Auto-select first model of the new provider
    const first = modelsByProvider[provider]?.[0]
    if (first) {
      onModelChange(assignment.agent, first.name)
    }
  }

  const handleSaveKey = async () => {
    if (!keyInput.trim()) return
    await onSaveKey(assignment.api_key_env, keyInput.trim())
    setKeyInput('')
    setKeySaved(true)
    setTimeout(() => setKeySaved(false), 3000)
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
      {/* Header: agent name + badge */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-900 capitalize">
            {t(`settings.agent.${assignment.agent}`)}
          </h3>
          <p className="text-sm text-gray-500 mt-0.5">
            {t(`settings.agentDesc.${assignment.agent}`)}
          </p>
        </div>
        {needsKey ? (
          <Badge variant="warning">{t('settings.keyRequired')}</Badge>
        ) : (
          <Badge variant="success">{t('settings.ready')}</Badge>
        )}
      </div>

      {/* Two-level model selection */}
      <div className="space-y-3">
        {/* Provider dropdown */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            {t('settings.providerLabel')}
          </label>
          <select
            value={selectedProvider}
            onChange={(e) => handleProviderChange(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none capitalize"
          >
            {Object.keys(modelsByProvider).map((provider) => (
              <option key={provider} value={provider}>
                {provider}
              </option>
            ))}
          </select>
        </div>

        {/* Model dropdown (filtered by provider) */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            {t('settings.modelLabel')}
          </label>
          <select
            value={assignment.model}
            onChange={(e) => onModelChange(assignment.agent, e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          >
            {providerModels.map((m) => (
              <option key={m.name} value={m.name}>
                {m.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Inline API key prompt (only when key is missing) */}
      {needsKey && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 space-y-2">
          <p className="text-sm text-amber-800">
            {t('settings.apiKeyNeeded', { envVar: assignment.api_key_env })}
          </p>
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <input
                type={showKey ? 'text' : 'password'}
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                placeholder={t('settings.apiKeyPlaceholder')}
                className="w-full px-3 py-2 pr-10 text-sm border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none font-mono bg-white"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSaveKey()
                }}
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <button
              type="button"
              onClick={handleSaveKey}
              disabled={!keyInput.trim() || isSaving}
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-amber-600 text-white text-sm font-medium rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
            >
              <Save className="h-3.5 w-3.5" />
              {t('settings.saveKey')}
            </button>
          </div>
          {keySaved && (
            <span className="inline-flex items-center gap-1 text-xs text-emerald-600">
              <CheckCircle className="h-3.5 w-3.5" />
              {t('settings.saveSuccess')}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
