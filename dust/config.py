"""Runtime configuration, sourced from environment variables / .env."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    All values can be overridden via environment variables (prefix ``DUST_``)
    or a local ``.env`` file. Provider SDK keys use their conventional names.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Which LLM adapter to use: anthropic | openai | huggingface | ollama | mock
    llm_provider: str = "mock"
    # Model id passed to the provider (provider-specific default applied if empty).
    llm_model: str = ""
    # Sampling temperature for extraction (kept low for deterministic structure).
    llm_temperature: float = 0.0
    # Max tokens for the extraction response.
    llm_max_tokens: int = 4096

    # Provider credentials / endpoints.
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    hf_token: str = ""
    hf_model_endpoint: str = ""  # optional custom HF inference endpoint URL
    ollama_base_url: str = "http://localhost:11434"


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
