import { useState } from 'react'
import { Eye, EyeOff, Save, CheckCircle, Globe } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import Badge from '../ui/Badge'
import type { SearchProviderStatus } from '../../types'

interface SearchProviderCardProps {
  provider: SearchProviderStatus
  onToggle: (name: string, enabled: boolean) => void
  onSaveKey: (envVar: string, key: string) => Promise<void>
  isSaving?: boolean
}

export default function SearchProviderCard({
  provider,
  onToggle,
  onSaveKey,
  isSaving,
}: SearchProviderCardProps) {
  const { t } = useTranslation()
  const [keyInput, setKeyInput] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [keySaved, setKeySaved] = useState(false)

  const needsKey = provider.api_key_env && !provider.api_key_configured
  const hasOptionalKey = provider.api_key_env && !provider.api_key_configured

  const handleSaveKey = async () => {
    if (!keyInput.trim() || !provider.api_key_env) return
    await onSaveKey(provider.api_key_env, keyInput.trim())
    setKeyInput('')
    setKeySaved(true)
    setTimeout(() => setKeySaved(false), 3000)
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Globe className="h-5 w-5 text-blue-500" />
          <div>
            <h3 className="font-semibold text-gray-900">
              {t(`settings.searchProvider.${provider.name}`)}
            </h3>
            <p className="text-sm text-gray-500 mt-0.5">
              {t(`settings.searchProviderDesc.${provider.name}`)}
            </p>
          </div>
        </div>
        {provider.api_key_configured ? (
          <Badge variant="success">{t('settings.ready')}</Badge>
        ) : provider.api_key_env ? (
          <Badge variant="primary">{t('settings.optional')}</Badge>
        ) : (
          <Badge variant="success">{t('settings.ready')}</Badge>
        )}
      </div>

      {/* Enable toggle */}
      <label className="flex items-center gap-3 cursor-pointer">
        <input
          type="checkbox"
          checked={provider.enabled}
          onChange={(e) => onToggle(provider.name, e.target.checked)}
          className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
        />
        <span className="text-sm text-gray-700">
          {t('settings.searchProviderEnabled')}
        </span>
      </label>

      {/* API key input (only for providers that accept a key and don't have one yet) */}
      {hasOptionalKey && provider.enabled && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 space-y-2">
          <p className="text-sm text-blue-800">
            {t(`settings.searchProviderKeyHint.${provider.name}`)}
          </p>
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <input
                type={showKey ? 'text' : 'password'}
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                placeholder={provider.api_key_env}
                className="w-full px-3 py-2 pr-10 text-sm border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none font-mono bg-white"
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
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
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
          {provider.api_key_configured && provider.masked_key && (
            <p className="text-xs text-gray-400 font-mono">{provider.masked_key}</p>
          )}
        </div>
      )}
    </div>
  )
}
