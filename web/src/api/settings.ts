import api from './client'
import type {
  AgentModelsResponse,
  AgentModelsSaveRequest,
  AgentModelsSaveResponse,
  ApiKeyStatusResponse,
  ApiKeySaveRequest,
  ApiKeySaveResponse,
  SearchProvidersResponse,
  SearchProviderSaveRequest,
  SearchProviderSaveResponse,
} from '../types'

export async function getApiKeyStatus(): Promise<ApiKeyStatusResponse> {
  const { data } = await api.get<ApiKeyStatusResponse>('/settings/api-keys')
  return data
}

export async function saveApiKeys(req: ApiKeySaveRequest): Promise<ApiKeySaveResponse> {
  const { data } = await api.put<ApiKeySaveResponse>('/settings/api-keys', req)
  return data
}

export async function getAgentModels(): Promise<AgentModelsResponse> {
  const { data } = await api.get<AgentModelsResponse>('/settings/agent-models')
  return data
}

export async function saveAgentModels(req: AgentModelsSaveRequest): Promise<AgentModelsSaveResponse> {
  const { data } = await api.put<AgentModelsSaveResponse>('/settings/agent-models', req)
  return data
}

export async function getSearchProviders(): Promise<SearchProvidersResponse> {
  const { data } = await api.get<SearchProvidersResponse>('/settings/search-providers')
  return data
}

export async function saveSearchProviders(req: SearchProviderSaveRequest): Promise<SearchProviderSaveResponse> {
  const { data } = await api.put<SearchProviderSaveResponse>('/settings/search-providers', req)
  return data
}
