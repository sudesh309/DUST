"""Anthropic (Claude) adapter."""

from __future__ import annotations

from dust.llm.base import LLMClient, LLMError

_DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicClient(LLMClient):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(**kwargs)
        self.model = self.model or _DEFAULT_MODEL
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY is not set")
        try:
            import anthropic  # noqa: PLC0415
        except ImportError as exc:  # pragma: no cover
            raise LLMError("Install the 'anthropic' extra to use this provider") from exc
        self._client = anthropic.Anthropic(api_key=api_key)

    def extract_json(self, system: str, user: str) -> dict:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        return self._parse_json(text)
