"""Settings API routes — API key management."""

from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path

import yaml
from fastapi import APIRouter

from src.api.schemas import (
    AgentModelAssignment,
    AgentModelsSaveRequest,
    AgentModelsSaveResponse,
    AgentModelsResponse,
    ApiKeySaveRequest,
    ApiKeySaveResponse,
    ApiKeyStatusResponse,
    ModelInfo,
    ProviderStatus,
    SearchProviderSaveRequest,
    SearchProviderSaveResponse,
    SearchProviderStatus,
    SearchProvidersResponse,
)

router = APIRouter()

_ENV_FILE = Path("config/.env")


_CONFIG_PATH = Path("config/settings.yaml")


def _load_full_config() -> dict:
    """Load entire settings.yaml."""
    if not _CONFIG_PATH.exists():
        return {}
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save_config(config: dict) -> None:
    """Write config back to settings.yaml."""
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _load_models_config() -> dict:
    """Load models section from settings.yaml."""
    return _load_full_config().get("models", {})


def _build_provider_list() -> list[ProviderStatus]:
    """Build provider status list from settings.yaml + current env."""
    models_config = _load_models_config()

    # Group models by env_var
    env_var_info: dict[str, dict] = {}
    env_var_models: dict[str, list[str]] = defaultdict(list)

    for model_name, conf in models_config.items():
        env_var = conf.get("api_key_env", "")
        provider = conf.get("provider", "")
        if env_var:
            env_var_info[env_var] = {"provider": provider}
            env_var_models[env_var].append(model_name)

    providers = []
    for env_var, info in env_var_info.items():
        current_key = os.environ.get(env_var, "")
        configured = bool(current_key)
        masked = f"****{current_key[-4:]}" if len(current_key) >= 4 else ""
        providers.append(
            ProviderStatus(
                env_var=env_var,
                provider=info["provider"],
                configured=configured,
                masked_key=masked,
                models=env_var_models[env_var],
            )
        )

    return providers


def _read_env_file() -> dict[str, str]:
    """Read existing key=value pairs from config/.env."""
    result: dict[str, str] = {}
    if not _ENV_FILE.exists():
        return result
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


def _write_env_file(data: dict[str, str]) -> None:
    """Write key=value pairs to config/.env."""
    _ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{k}={v}" for k, v in sorted(data.items()) if v]
    _ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


@router.get("/api-keys", response_model=ApiKeyStatusResponse)
async def get_api_key_status():
    """Get current API key configuration status for all providers."""
    return ApiKeyStatusResponse(providers=_build_provider_list())


@router.put("/api-keys", response_model=ApiKeySaveResponse)
async def save_api_keys(req: ApiKeySaveRequest):
    """Save API keys to config/.env and sync to os.environ."""
    # Read existing .env
    env_data = _read_env_file()

    # Merge new keys (only non-empty values)
    valid_env_vars = {
        conf.get("api_key_env")
        for conf in _load_models_config().values()
        if conf.get("api_key_env")
    }
    for key, value in req.keys.items():
        if key in valid_env_vars and value:
            env_data[key] = value
            os.environ[key] = value

    # Write back
    _write_env_file(env_data)

    # Clear LLM client cache so new keys take effect
    try:
        from src.core.llm_client import LLMClient

        client = LLMClient()
        client.clear_clients()
    except Exception:
        pass  # Non-critical — clients will rebuild on next call

    return ApiKeySaveResponse(success=True, providers=_build_provider_list())


# --- Agent Model Assignment ---


def _build_agent_model_data() -> tuple[list[AgentModelAssignment], list[ModelInfo]]:
    """Build agent-model assignments and available models from config + env."""
    config = _load_full_config()
    models_config = config.get("models", {})
    agent_models_config = config.get("agent_models", {})

    # Available models
    available_models = []
    for model_name, conf in models_config.items():
        env_var = conf.get("api_key_env", "")
        available_models.append(
            ModelInfo(
                name=model_name,
                provider=conf.get("provider", ""),
                api_key_env=env_var,
                api_key_configured=bool(os.environ.get(env_var, "")),
            )
        )

    # Agent assignments
    agent_assignments = []
    for agent_name, model_name in agent_models_config.items():
        model_conf = models_config.get(model_name, {})
        env_var = model_conf.get("api_key_env", "")
        agent_assignments.append(
            AgentModelAssignment(
                agent=agent_name,
                model=model_name,
                provider=model_conf.get("provider", ""),
                api_key_env=env_var,
                api_key_configured=bool(os.environ.get(env_var, "")),
            )
        )

    return agent_assignments, available_models


@router.get("/agent-models", response_model=AgentModelsResponse)
async def get_agent_models():
    """Get current agent-model assignments and available models."""
    assignments, models = _build_agent_model_data()
    return AgentModelsResponse(agent_models=assignments, available_models=models)


@router.put("/agent-models", response_model=AgentModelsSaveResponse)
async def save_agent_models(req: AgentModelsSaveRequest):
    """Update agent-model assignments in settings.yaml."""
    config = _load_full_config()
    models_config = config.get("models", {})
    valid_agents = set(config.get("agent_models", {}).keys())
    valid_models = set(models_config.keys())

    # Validate
    for agent, model in req.agent_models.items():
        if agent not in valid_agents:
            from fastapi import HTTPException

            raise HTTPException(400, f"Unknown agent: {agent}")
        if model not in valid_models:
            from fastapi import HTTPException

            raise HTTPException(400, f"Unknown model: {model}")

    # Update config
    config["agent_models"].update(req.agent_models)
    _save_config(config)

    # Clear LLM client cache so new assignments take effect
    try:
        from src.core.llm_client import LLMClient

        client = LLMClient()
        client.clear_clients()
    except Exception:
        pass

    assignments, models = _build_agent_model_data()
    return AgentModelsSaveResponse(
        success=True, agent_models=assignments, available_models=models
    )


# --- Search Providers ---


def _build_search_provider_list() -> list[SearchProviderStatus]:
    """Build search provider status list from settings.yaml + env."""
    config = _load_full_config()
    providers_conf = config.get("search_providers", {})
    statuses = []
    for name, conf in providers_conf.items():
        api_key_env = conf.get("api_key_env", "")
        current_key = os.environ.get(api_key_env, "") if api_key_env else ""
        configured = bool(current_key)
        masked = f"****{current_key[-4:]}" if len(current_key) >= 4 else ""
        statuses.append(
            SearchProviderStatus(
                name=name,
                enabled=conf.get("enabled", True),
                api_key_env=api_key_env,
                api_key_configured=configured,
                masked_key=masked,
            )
        )
    return statuses


@router.get("/search-providers", response_model=SearchProvidersResponse)
async def get_search_providers():
    """Get current search provider configuration status."""
    return SearchProvidersResponse(providers=_build_search_provider_list())


@router.put("/search-providers", response_model=SearchProviderSaveResponse)
async def save_search_providers(req: SearchProviderSaveRequest):
    """Update search provider settings and save API keys."""
    config = _load_full_config()
    providers_conf = config.setdefault("search_providers", {})

    # Update enabled/disabled status
    for name, updates in req.providers.items():
        if name in providers_conf:
            for key, value in updates.items():
                if key in ("enabled",):
                    providers_conf[name][key] = value

    _save_config(config)

    # Save API keys to .env and os.environ
    if req.keys:
        valid_env_vars = {
            conf.get("api_key_env")
            for conf in providers_conf.values()
            if conf.get("api_key_env")
        }
        env_data = _read_env_file()
        for key, value in req.keys.items():
            if key in valid_env_vars and value:
                env_data[key] = value
                os.environ[key] = value
        _write_env_file(env_data)

    return SearchProviderSaveResponse(
        success=True, providers=_build_search_provider_list()
    )
