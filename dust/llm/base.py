"""Abstract LLM client interface.

Every provider adapter implements :meth:`LLMClient.extract_json`, which takes a
system + user prompt and returns a parsed JSON object. Keeping the interface this
small lets the extraction pipeline stay provider-agnostic.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod


class LLMError(RuntimeError):
    """Raised when a provider call or its JSON parsing fails."""


class LLMClient(ABC):
    """Common interface for all LLM providers."""

    def __init__(self, model: str = "", temperature: float = 0.0, max_tokens: int = 4096):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def extract_json(self, system: str, user: str) -> dict:
        """Return a JSON object generated from the given prompts."""
        raise NotImplementedError

    @staticmethod
    def _parse_json(text: str) -> dict:
        """Best-effort extraction of a JSON object from a model response."""
        text = text.strip()
        # Strip Markdown code fences if present.
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.lstrip().startswith("json"):
                text = text.lstrip()[4:]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fall back to the outermost {...} span.
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError as exc:  # pragma: no cover - rare
                    raise LLMError(f"Could not parse JSON from response: {exc}") from exc
            raise LLMError("Model response did not contain valid JSON")
