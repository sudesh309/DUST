"""Ollama (local) adapter — talks to a running Ollama server over HTTP."""

from __future__ import annotations

import httpx

from dust.llm.base import LLMClient, LLMError

_DEFAULT_MODEL = "llama3.1"


class OllamaClient(LLMClient):
    def __init__(self, base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(**kwargs)
        self.model = self.model or _DEFAULT_MODEL
        self.base_url = base_url.rstrip("/")

    def extract_json(self, system: str, user: str) -> dict:
        try:
            resp = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": self.temperature},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=300,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"Ollama request failed: {exc}") from exc
        content = resp.json().get("message", {}).get("content", "")
        return self._parse_json(content)
