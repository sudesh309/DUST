"""Hugging Face adapter — uses the hosted Inference API (or a custom endpoint)."""

from __future__ import annotations

import httpx

from dust.llm.base import LLMClient, LLMError

_DEFAULT_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"
_API_ROOT = "https://api-inference.huggingface.co/models"


class HuggingFaceClient(LLMClient):
    def __init__(self, token: str, endpoint: str = "", **kwargs):
        super().__init__(**kwargs)
        self.model = self.model or _DEFAULT_MODEL
        if not token:
            raise LLMError("HF_TOKEN is not set")
        self.token = token
        self.endpoint = endpoint or f"{_API_ROOT}/{self.model}"

    def extract_json(self, system: str, user: str) -> dict:
        prompt = f"{system}\n\n{user}\n\nReturn only the JSON object."
        try:
            resp = httpx.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "temperature": max(self.temperature, 0.01),
                        "max_new_tokens": self.max_tokens,
                        "return_full_text": False,
                    },
                },
                timeout=300,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"Hugging Face request failed: {exc}") from exc
        data = resp.json()
        if isinstance(data, list) and data:
            text = data[0].get("generated_text", "")
        elif isinstance(data, dict):
            text = data.get("generated_text", "")
        else:  # pragma: no cover - unexpected shape
            text = str(data)
        return self._parse_json(text)
