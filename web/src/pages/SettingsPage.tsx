import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings, Save, Eye, EyeOff, CheckCircle, ChevronDown, ChevronRight, Cpu } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { getApiKeyStatus, saveApiKeys, getAgentModels, saveAgentModels } from '../api/settings'
import Badge from '../components/ui/Badge'
import AgentModelCard from '../components/settings/AgentModelCard'
import type { ProviderStatus } from '../types'

export default function SettingsPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  // Agent models query
  const { data: agentData, isLoading: agentLoading } = useQuery({
    queryKey: ['agent-models'],
    queryFn: getAgentModels,
  })

  // API keys query
  const { data: apiKeyData, isLoading: apiKeyLoading } = useQuery({
    queryKey: ['api-key-status'],
    queryFn: getApiKeyStatus,
  })

  const [keyInputs, setKeyInputs] = useState<Record<string, string>>({})
  const [showKey, setShowKey] = useState<Record<string, boolean>>({})
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [apiKeysExpanded, setApiKeysExpanded] = useState(false)

  // Save API keys mutation
  const apiKeyMutation = useMutation({
    mutationFn: saveApiKeys,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-key-status'] })
      queryClient.invalidateQueries({ queryKey: ['agent-models'] })
      setKeyInputs({})
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    },
  })

  // Save agent models mutation
  const agentModelMutation = useMutation({
    mutationFn: saveAgentModels,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-models'] })
      queryClient.invalidateQueries({ queryKey: ['api-key-status'] })
    },
  })

  const handleModelChange = (agent: string, model: string) => {
    agentModelMutation.mutate({ agent_models: { [agent]: model } })
  }

  const handleInlineKeySave = async (envVar: string, key: string) => {
    await apiKeyMutation.mutateAsync({ keys: { [envVar]: key } })
  }

  const handleBulkSave = () => {
    const nonEmpty = Object.fromEntries(
      Object.entries(keyInputs).filter(([, v]) => v.trim())
    )
    if (Object.keys(nonEmpty).length === 0) return
    apiKeyMutation.mutate({ keys: nonEmpty })
  }

  const hasChanges = Object.values(keyInputs).some((v) => v.trim())

  if (agentLoading || apiKeyLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">{t('common.loading')}</p>
      </div>
    )
  }

  const agentModels = agentData?.agent_models ?? []
  const availableModels = agentData?.available_models ?? []
  const providers = apiKeyData?.providers ?? []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-heading font-bold text-gray-900">
          {t('settings.title')}
        </h1>
      </div>

      {/* Primary: Agent Model Configuration */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="h-5 w-5 text-gray-600" />
          <h2 className="text-lg font-semibold text-gray-900">
            {t('settings.agentModels')}
          </h2>
        </div>
        <p className="text-sm text-gray-500 mb-4">
          {t('settings.agentModelsDesc')}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {agentModels.map((a) => (
            <AgentModelCard
              key={a.agent}
              assignment={a}
              availableModels={availableModels}
              onModelChange={handleModelChange}
              onSaveKey={handleInlineKeySave}
              isSaving={apiKeyMutation.isPending}
            />
          ))}
        </div>
      </div>

      {/* Secondary: Collapsible API Keys Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <button
          type="button"
          onClick={() => setApiKeysExpanded(!apiKeysExpanded)}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Settings className="h-5 w-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">
              {t('settings.advancedApiKeys')}
            </h2>
          </div>
          {apiKeysExpanded ? (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronRight className="h-5 w-5 text-gray-400" />
          )}
        </button>

        {apiKeysExpanded && (
          <>
            <div className="px-6 pb-2 border-t border-gray-100 pt-2">
              <p className="text-sm text-gray-500">
                {t('settings.apiKeysDesc')}
              </p>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <th className="px-6 py-3">{t('settings.provider')}</th>
                    <th className="px-6 py-3">{t('settings.envVar')}</th>
                    <th className="px-6 py-3">{t('settings.models')}</th>
                    <th className="px-6 py-3">{t('settings.status')}</th>
                    <th className="px-6 py-3 min-w-[280px]">API Key</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {providers.map((p: ProviderStatus) => (
                    <tr key={p.env_var} className="hover:bg-gray-50/50">
                      <td className="px-6 py-4">
                        <span className="font-medium text-gray-900 capitalize">
                          {p.provider}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">
                          {p.env_var}
                        </code>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1">
                          {p.models.map((m) => (
                            <Badge key={m} variant="primary">
                              {m}
                            </Badge>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {p.configured ? (
                          <div>
                            <Badge variant="success">{t('settings.configured')}</Badge>
                            <div className="mt-1 text-xs text-gray-400 font-mono">
                              {p.masked_key}
                            </div>
                          </div>
                        ) : (
                          <Badge variant="warning">{t('settings.notConfigured')}</Badge>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className="relative flex-1">
                            <input
                              type={showKey[p.env_var] ? 'text' : 'password'}
                              value={keyInputs[p.env_var] ?? ''}
                              onChange={(e) =>
                                setKeyInputs((prev) => ({
                                  ...prev,
                                  [p.env_var]: e.target.value,
                                }))
                              }
                              placeholder={t('settings.apiKeyPlaceholder')}
                              className="w-full px-3 py-2 pr-10 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none font-mono"
                            />
                            <button
                              type="button"
                              onClick={() =>
                                setShowKey((prev) => ({
                                  ...prev,
                                  [p.env_var]: !prev[p.env_var],
                                }))
                              }
                              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                            >
                              {showKey[p.env_var] ? (
                                <EyeOff className="h-4 w-4" />
                              ) : (
                                <Eye className="h-4 w-4" />
                              )}
                            </button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
              <div>
                {saveSuccess && (
                  <span className="inline-flex items-center gap-1.5 text-sm text-emerald-600">
                    <CheckCircle className="h-4 w-4" />
                    {t('settings.saveSuccess')}
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={handleBulkSave}
                disabled={!hasChanges || apiKeyMutation.isPending}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Save className="h-4 w-4" />
                {apiKeyMutation.isPending ? t('settings.saving') : t('settings.save')}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
