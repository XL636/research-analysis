import api from './client'
import type { ApiKeyStatusResponse, ApiKeySaveRequest, ApiKeySaveResponse } from '../types'

export async function getApiKeyStatus(): Promise<ApiKeyStatusResponse> {
  const { data } = await api.get<ApiKeyStatusResponse>('/settings/api-keys')
  return data
}

export async function saveApiKeys(req: ApiKeySaveRequest): Promise<ApiKeySaveResponse> {
  const { data } = await api.put<ApiKeySaveResponse>('/settings/api-keys', req)
  return data
}
