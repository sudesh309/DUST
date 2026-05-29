"""Request/response models for the REST API."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from dust.models import FormalizationResult


class Target(str, Enum):
    ir = "ir"
    ears = "ears"
    sysml = "sysml"
    ontology = "ontology"


class FormalizeRequest(BaseModel):
    text: str = Field(..., description="Raw requirements text (one or many statements).")
    targets: list[Target] = Field(
        default_factory=lambda: [Target.ir, Target.ears, Target.sysml, Target.ontology],
        description="Which artifacts to return.",
    )
    provider: str | None = Field(
        default=None,
        description="Override the configured LLM provider (mock|anthropic|openai|huggingface|ollama).",
    )


class OntologyArtifact(BaseModel):
    graph: dict
    mermaid: str
    turtle: str


class FormalizeResponse(BaseModel):
    statements: int
    ir: FormalizationResult | None = None
    ears: list[dict] | None = None
    sysml: str | None = None
    ontology: OntologyArtifact | None = None
