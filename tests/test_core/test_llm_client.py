"""Tests for src/core/llm_client.py — LLMClient with mocked OpenAI."""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from src.core.llm_client import LLMClient, ModelConfig


# ---------------------------------------------------------------------------
# ModelConfig
# ---------------------------------------------------------------------------

class TestModelConfig:
    def test_instantiation(self) -> None:
        mc = ModelConfig(
            provider="openai",
            base_url="https://api.openai.com/v1",
            model="gpt-4",
            api_key_env="OPENAI_API_KEY",
        )
        assert mc.provider == "openai"
        assert mc.base_url == "https://api.openai.com/v1"
        assert mc.model == "gpt-4"
        assert mc.api_key_env == "OPENAI_API_KEY"

    def test_all_fields_required(self) -> None:
        with pytest.raises(Exception):
            ModelConfig(provider="x", base_url="http://x", model="m")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# LLMClient._load_config / available_models
# ---------------------------------------------------------------------------

class TestLLMClientConfig:
    def test_load_config_populates_models(self, tmp_config: str) -> None:
        client = LLMClient(tmp_config)
        assert "test-model" in client._models
        mc = client._models["test-model"]
        assert isinstance(mc, ModelConfig)
        assert mc.provider == "test"
        assert mc.model == "test-v1"
        assert mc.api_key_env == "TEST_API_KEY"

    def test_available_models(self, tmp_config: str) -> None:
        client = LLMClient(tmp_config)
        models = client.available_models
        assert isinstance(models, list)
        assert "test-model" in models

    def test_available_models_reflects_yaml(self, tmp_path) -> None:
        """Config with multiple models returns all of them."""
        import yaml
        config = {
            "models": {
                "model-a": {
                    "provider": "pa",
                    "base_url": "http://a",
                    "model": "a-v1",
                    "api_key_env": "KEY_A",
                },
                "model-b": {
                    "provider": "pb",
                    "base_url": "http://b",
                    "model": "b-v1",
                    "api_key_env": "KEY_B",
                },
            },
            "agent_models": {},
            "pipeline": {},
        }
        path = tmp_path / "multi.yaml"
        path.write_text(yaml.dump(config), encoding="utf-8")
        client = LLMClient(str(path))
        assert set(client.available_models) == {"model-a", "model-b"}

    def test_empty_models_section(self, tmp_path) -> None:
        import yaml
        config: dict = {"models": {}}
        path = tmp_path / "empty.yaml"
        path.write_text(yaml.dump(config), encoding="utf-8")
        client = LLMClient(str(path))
        assert client.available_models == []


# ---------------------------------------------------------------------------
# LLMClient._get_client — error cases
# ---------------------------------------------------------------------------

class TestGetClientErrors:
    def test_unknown_model_raises_value_error(self, tmp_config: str) -> None:
        client = LLMClient(tmp_config)
        with pytest.raises(ValueError, match="Unknown model"):
            client._get_client("nonexistent-model")

    def test_missing_api_key_env_raises_value_error(self, tmp_config: str) -> None:
        """When the env var is absent, _get_client raises ValueError."""
        client = LLMClient(tmp_config)
        # Ensure the env var is NOT set
        env_without_key = {k: v for k, v in os.environ.items() if k != "TEST_API_KEY"}
        with patch.dict(os.environ, env_without_key, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                client._get_client("test-model")


# ---------------------------------------------------------------------------
# LLMClient.chat
# ---------------------------------------------------------------------------

class TestLLMClientChat:
    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    @patch("src.core.llm_client.OpenAI")
    def test_chat_returns_content(self, MockOpenAI, tmp_config: str) -> None:
        mock_openai_instance = MagicMock()
        MockOpenAI.return_value = mock_openai_instance

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello response"
        mock_openai_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(tmp_config)
        messages = [{"role": "user", "content": "test"}]
        result = client.chat("test-model", messages)

        assert result == "Hello response"

    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    @patch("src.core.llm_client.OpenAI")
    def test_chat_passes_correct_model_id(self, MockOpenAI, tmp_config: str) -> None:
        mock_openai_instance = MagicMock()
        MockOpenAI.return_value = mock_openai_instance

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"
        mock_openai_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(tmp_config)
        messages = [{"role": "user", "content": "hi"}]
        client.chat("test-model", messages)

        call_kwargs = mock_openai_instance.chat.completions.create.call_args
        # model in kwargs should be the model ID from config ("test-v1"), not the alias
        assert call_kwargs.kwargs["model"] == "test-v1" or call_kwargs[1]["model"] == "test-v1" or \
               call_kwargs[0][0] == "test-v1"  # positional fallback

    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    @patch("src.core.llm_client.OpenAI")
    def test_chat_passes_temperature_and_max_tokens(self, MockOpenAI, tmp_config: str) -> None:
        mock_openai_instance = MagicMock()
        MockOpenAI.return_value = mock_openai_instance

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"
        mock_openai_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(tmp_config)
        messages = [{"role": "user", "content": "hi"}]
        client.chat("test-model", messages, temperature=0.1, max_tokens=512)

        call_kwargs = mock_openai_instance.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.1
        assert call_kwargs["max_tokens"] == 512

    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    @patch("src.core.llm_client.OpenAI")
    def test_chat_none_content_returns_empty_string(self, MockOpenAI, tmp_config: str) -> None:
        mock_openai_instance = MagicMock()
        MockOpenAI.return_value = mock_openai_instance

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_openai_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(tmp_config)
        result = client.chat("test-model", [{"role": "user", "content": "hi"}])
        assert result == ""

    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    @patch("src.core.llm_client.OpenAI")
    def test_chat_reuses_client_instance(self, MockOpenAI, tmp_config: str) -> None:
        """Second call to same model should not create a new OpenAI client."""
        mock_openai_instance = MagicMock()
        MockOpenAI.return_value = mock_openai_instance

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response"
        mock_openai_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(tmp_config)
        messages = [{"role": "user", "content": "hi"}]
        client.chat("test-model", messages)
        client.chat("test-model", messages)

        # OpenAI constructor should have been called only once
        assert MockOpenAI.call_count == 1


# ---------------------------------------------------------------------------
# LLMClient.chat_json
# ---------------------------------------------------------------------------

class TestLLMClientChatJson:
    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    @patch("src.core.llm_client.OpenAI")
    def test_chat_json_returns_parsed_dict(self, MockOpenAI, tmp_config: str) -> None:
        mock_openai_instance = MagicMock()
        MockOpenAI.return_value = mock_openai_instance

        payload = {"result": "value", "score": 9}
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(payload)
        mock_openai_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(tmp_config)
        result = client.chat_json("test-model", [{"role": "user", "content": "go"}])

        assert isinstance(result, dict)
        assert result["result"] == "value"
        assert result["score"] == 9

    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    @patch("src.core.llm_client.OpenAI")
    def test_chat_json_passes_response_format(self, MockOpenAI, tmp_config: str) -> None:
        """chat_json must forward response_format={"type": "json_object"} to OpenAI."""
        mock_openai_instance = MagicMock()
        MockOpenAI.return_value = mock_openai_instance

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"ok": true}'
        mock_openai_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(tmp_config)
        client.chat_json("test-model", [{"role": "user", "content": "go"}])

        call_kwargs = mock_openai_instance.chat.completions.create.call_args.kwargs
        assert call_kwargs.get("response_format") == {"type": "json_object"}

    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    @patch("src.core.llm_client.OpenAI")
    def test_chat_json_handles_markdown_json_block(self, MockOpenAI, tmp_config: str) -> None:
        """Fallback: response wrapped in ```json ... ``` code fence."""
        mock_openai_instance = MagicMock()
        MockOpenAI.return_value = mock_openai_instance

        wrapped = '```json\n{"key": "value"}\n```'
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = wrapped
        mock_openai_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(tmp_config)
        result = client.chat_json("test-model", [{"role": "user", "content": "go"}])

        assert result["key"] == "value"

    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    @patch("src.core.llm_client.OpenAI")
    def test_chat_json_handles_plain_code_fence(self, MockOpenAI, tmp_config: str) -> None:
        """Fallback: response wrapped in plain ``` ... ``` code fence."""
        mock_openai_instance = MagicMock()
        MockOpenAI.return_value = mock_openai_instance

        wrapped = '```\n{"answer": 42}\n```'
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = wrapped
        mock_openai_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(tmp_config)
        result = client.chat_json("test-model", [{"role": "user", "content": "go"}])

        assert result["answer"] == 42

    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    @patch("src.core.llm_client.OpenAI")
    def test_chat_json_raises_on_invalid_json(self, MockOpenAI, tmp_config: str) -> None:
        """If response is not valid JSON and has no code fence, JSONDecodeError is raised."""
        mock_openai_instance = MagicMock()
        MockOpenAI.return_value = mock_openai_instance

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is not JSON at all."
        mock_openai_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(tmp_config)
        with pytest.raises(json.JSONDecodeError):
            client.chat_json("test-model", [{"role": "user", "content": "go"}])

    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    @patch("src.core.llm_client.OpenAI")
    def test_chat_json_default_temperature(self, MockOpenAI, tmp_config: str) -> None:
        """chat_json uses temperature=0.3 by default."""
        mock_openai_instance = MagicMock()
        MockOpenAI.return_value = mock_openai_instance

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "{}"
        mock_openai_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(tmp_config)
        client.chat_json("test-model", [{"role": "user", "content": "hi"}])

        call_kwargs = mock_openai_instance.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.3


# ---------------------------------------------------------------------------
# LLMClient.usage_stats — token tracking
# ---------------------------------------------------------------------------

class TestLLMClientUsageTracking:
    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    @patch("src.core.llm_client.OpenAI")
    def test_chat_tracks_token_usage(self, MockOpenAI, tmp_config: str) -> None:
        mock_openai_instance = MagicMock()
        MockOpenAI.return_value = mock_openai_instance

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_openai_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(tmp_config)
        client.chat("test-model", [{"role": "user", "content": "hi"}])

        assert client.usage_stats.total_calls == 1
        assert client.usage_stats.total_prompt_tokens == 100
        assert client.usage_stats.total_completion_tokens == 50

    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    @patch("src.core.llm_client.OpenAI")
    def test_chat_accumulates_usage_across_calls(self, MockOpenAI, tmp_config: str) -> None:
        mock_openai_instance = MagicMock()
        MockOpenAI.return_value = mock_openai_instance

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"
        mock_response.usage.prompt_tokens = 80
        mock_response.usage.completion_tokens = 40
        mock_openai_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(tmp_config)
        client.chat("test-model", [{"role": "user", "content": "a"}])
        client.chat("test-model", [{"role": "user", "content": "b"}])

        assert client.usage_stats.total_calls == 2
        assert client.usage_stats.total_prompt_tokens == 160
        assert client.usage_stats.total_completion_tokens == 80

    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    @patch("src.core.llm_client.OpenAI")
    def test_chat_handles_no_usage(self, MockOpenAI, tmp_config: str) -> None:
        """When response.usage is None, no error is raised."""
        mock_openai_instance = MagicMock()
        MockOpenAI.return_value = mock_openai_instance

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"
        mock_response.usage = None
        mock_openai_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(tmp_config)
        result = client.chat("test-model", [{"role": "user", "content": "hi"}])
        assert result == "ok"
        assert client.usage_stats.total_calls == 0

    def test_initial_usage_stats_empty(self, tmp_config: str) -> None:
        client = LLMClient(tmp_config)
        assert client.usage_stats.total_calls == 0
        assert client.usage_stats.total_tokens == 0
