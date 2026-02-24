"""统一 LLM 调用层 - 多模型切换，OpenAI 兼容接口."""

from __future__ import annotations

import json
import os
from typing import Any

import yaml
from loguru import logger
from httpx import Timeout
from openai import OpenAI
from pydantic import BaseModel

from src.core.models import UsageStats


class ModelConfig(BaseModel):
    """单个模型配置."""

    provider: str
    base_url: str
    model: str
    api_key_env: str


class LLMClient:
    """统一 LLM 客户端，按 model_name 懒加载 OpenAI 客户端."""

    def __init__(self, config_path: str = "config/settings.yaml"):
        self._config_path = config_path
        self._models: dict[str, ModelConfig] = {}
        self._clients: dict[str, OpenAI] = {}
        self.usage_stats = UsageStats()
        self._load_config()

    def _load_config(self) -> None:
        with open(self._config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        for name, model_conf in config.get("models", {}).items():
            self._models[name] = ModelConfig(**model_conf)

    def _get_client(self, model_name: str) -> tuple[OpenAI, str]:
        """懒加载并返回 (OpenAI 客户端, 模型 ID)."""
        if model_name not in self._models:
            raise ValueError(f"Unknown model: {model_name}. Available: {list(self._models.keys())}")

        model_config = self._models[model_name]

        if model_name not in self._clients:
            api_key = os.environ.get(model_config.api_key_env, "")
            if not api_key:
                raise ValueError(
                    f"API key not found. Set environment variable: {model_config.api_key_env}"
                )

            self._clients[model_name] = OpenAI(
                api_key=api_key,
                base_url=model_config.base_url,
                timeout=Timeout(300.0, connect=10.0),
            )
            logger.debug(f"Initialized client for {model_name} ({model_config.provider})")

        return self._clients[model_name], model_config.model

    def chat(
        self,
        model_name: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        """发送聊天请求，返回文本响应."""
        client, model_id = self._get_client(model_name)

        logger.info(f"LLM call: model={model_name}, messages={len(messages)}")

        response = client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # 记录 token 用量
        if response.usage:
            self.usage_stats.record(
                model_name=model_name,
                prompt_tokens=response.usage.prompt_tokens or 0,
                completion_tokens=response.usage.completion_tokens or 0,
            )
            logger.debug(
                f"Token usage: prompt={response.usage.prompt_tokens}, "
                f"completion={response.usage.completion_tokens}"
            )

        content = response.choices[0].message.content or ""
        logger.debug(f"LLM response: {len(content)} chars")
        return content

    def chat_json(
        self,
        model_name: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> dict:
        """发送聊天请求，返回 JSON 解析后的字典."""
        content = self.chat(
            model_name=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            **kwargs,
        )

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取 JSON 块
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            if "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            raise

    @property
    def available_models(self) -> list[str]:
        return list(self._models.keys())

    def clear_clients(self) -> None:
        """清除缓存的客户端，下次调用时将用新的 API Key 重建."""
        self._clients.clear()
