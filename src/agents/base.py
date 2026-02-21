"""Agent 基类 - 提供 LLM 调用、消息构建、Prompt 加载能力."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

from src.core.llm_client import LLMClient


class BaseAgent(ABC):
    """所有 Agent 的基类."""

    agent_type: str = "base"  # 子类覆盖，用于从配置获取模型名

    def __init__(self, llm_client: LLMClient, config_path: str = "config/settings.yaml"):
        self.llm = llm_client
        self._config_path = config_path
        self._model_name: str | None = None
        self._system_prompt: str | None = None

    @property
    def model_name(self) -> str:
        """从配置获取当前 Agent 应使用的模型名."""
        if self._model_name is None:
            with open(self._config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            agent_models = config.get("agent_models", {})
            self._model_name = agent_models.get(self.agent_type, "deepseek-chat")
        return self._model_name

    @property
    def system_prompt(self) -> str:
        """加载 System Prompt 模板."""
        if self._system_prompt is None:
            prompt_path = Path(f"config/prompts/{self.agent_type}_system.txt")
            if prompt_path.exists():
                self._system_prompt = prompt_path.read_text(encoding="utf-8")
            else:
                self._system_prompt = self._default_system_prompt()
        return self._system_prompt

    def _default_system_prompt(self) -> str:
        """默认的 System Prompt，子类可覆盖."""
        return f"You are a helpful {self.agent_type} agent."

    def _build_messages(
        self,
        user_content: str,
        system_override: str | None = None,
    ) -> list[dict[str, str]]:
        """构建消息列表."""
        system = system_override or self.system_prompt
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]

    def _call_llm(self, user_content: str, **kwargs: Any) -> str:
        """调用 LLM 返回文本."""
        messages = self._build_messages(user_content)
        logger.info(f"[{self.agent_type}] Calling LLM ({self.model_name})")
        return self.llm.chat(self.model_name, messages, **kwargs)

    def _call_llm_json(self, user_content: str, **kwargs: Any) -> dict:
        """调用 LLM 返回 JSON."""
        messages = self._build_messages(user_content)
        logger.info(f"[{self.agent_type}] Calling LLM JSON ({self.model_name})")
        return self.llm.chat_json(self.model_name, messages, **kwargs)

    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """处理输入数据，返回输出。子类必须实现."""
        ...
