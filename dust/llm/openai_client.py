"""OpenAI adapter."""

from __future__ import annotations

from dust.llm.base import LLMClient, LLMError

_DEFAULT_MODEL = "gpt-4o"


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(**kwargs)
        self.model = self.model or _DEFAULT_MODEL
        if not api_key:
            raise LLMError("OPENAI_API_KEY is not set")
        try:
            from openai import OpenAI  # noqa: PLC0415
        except ImportError as exc:  # pragma: no cover
            raise LLMError("Install the 'openai' extra to use this provider") from exc
        self._client = OpenAI(api_key=api_key)

    def extract_json(self, system: str, user: str) -> dict:
        resp = self._client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return self._parse_json(resp.choices[0].message.content or "")
