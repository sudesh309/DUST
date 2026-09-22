"""Build an :class:`LLMClient` from configuration."""

from __future__ import annotations

from dust.config import Settings, get_settings
from dust.llm.base import LLMClient, LLMError


def build_client(settings: Settings | None = None, provider: str | None = None) -> LLMClient:
    """Instantiate the configured LLM adapter.

    ``provider`` (e.g. supplied per-request) overrides ``settings.llm_provider``.
    """
    settings = settings or get_settings()
    name = (provider or settings.llm_provider).lower().strip()
    common = {
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
    }

    if name == "mock":
        from dust.llm.mock_client import MockClient

        return MockClient(**common)
    if name == "anthropic":
        from dust.llm.anthropic_client import AnthropicClient

        return AnthropicClient(api_key=settings.anthropic_api_key, **common)
    if name == "openai":
        from dust.llm.openai_client import OpenAIClient

        return OpenAIClient(api_key=settings.openai_api_key, **common)
    if name == "huggingface":
        from dust.llm.huggingface_client import HuggingFaceClient

        return HuggingFaceClient(
            token=settings.hf_token, endpoint=settings.hf_model_endpoint, **common
        )
    if name == "ollama":
        from dust.llm.ollama_client import OllamaClient

        return OllamaClient(base_url=settings.ollama_base_url, **common)

    raise LLMError(
        f"Unknown LLM provider '{name}'. "
        "Use one of: mock, anthropic, openai, huggingface, ollama."
    )
