"""Settings API routes — API key management."""

from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path

import yaml
from fastapi import APIRouter

from src.api.schemas import (
    ApiKeySaveRequest,
    ApiKeySaveResponse,
    ApiKeyStatusResponse,
    ProviderStatus,
)

router = APIRouter()

_ENV_FILE = Path("config/.env")


def _load_models_config() -> dict:
    """Load models section from settings.yaml."""
    config_path = Path("config/settings.yaml")
    if not config_path.exists():
        return {}
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f).get("models", {})


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
