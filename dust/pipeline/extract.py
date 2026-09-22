"""LLM extraction: requirement statements -> validated IR.

Builds the extraction prompt, calls the provider, validates the JSON against the
pydantic IR, and retries once with the validation error fed back on failure.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources

from pydantic import ValidationError

from dust.llm.base import LLMClient, LLMError
from dust.models import ExtractedRequirement, ExtractionResponse


@lru_cache(maxsize=1)
def _system_prompt() -> str:
    return resources.files("dust.prompts").joinpath("extract.txt").read_text(encoding="utf-8")


def _user_prompt(statements: list[str]) -> str:
    # The system prompt already explains the schema and ends with STATEMENTS_JSON:
    return "STATEMENTS_JSON: " + json.dumps(statements, ensure_ascii=False)


def extract(statements: list[str], client: LLMClient) -> list[ExtractedRequirement]:
    """Extract IR for ``statements`` using ``client``."""
    if not statements:
        return []

    system = _system_prompt()
    user = _user_prompt(statements)

    raw = client.extract_json(system, user)
    try:
        return ExtractionResponse.model_validate(raw).requirements
    except ValidationError as first_error:
        # One corrective retry: show the model exactly what failed.
        retry_user = (
            f"{user}\n\nYour previous response failed validation with:\n"
            f"{first_error}\n\nReturn corrected JSON only."
        )
        raw = client.extract_json(system, retry_user)
        try:
            return ExtractionResponse.model_validate(raw).requirements
        except ValidationError as exc:
            raise LLMError(f"Extraction output failed schema validation: {exc}") from exc
