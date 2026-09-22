"""End-to-end pipeline: text -> FormalizationResult.

Segments the document, runs LLM extraction, then aggregates the per-requirement
entities and relations into a single deduplicated ontology with consistent ids.
"""

from __future__ import annotations

import re

from dust.llm.base import LLMClient
from dust.models import (
    Entity,
    ExtractedRequirement,
    FormalizationResult,
    Ontology,
    Relation,
    Requirement,
)
from dust.pipeline.extract import extract
from dust.pipeline.segment import segment


def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", name.lower()).strip()


def _aggregate(extracted: list[ExtractedRequirement]) -> tuple[list[Requirement], Ontology]:
    canonical: dict[str, Entity] = {}  # normalized name -> canonical entity
    alias: dict[str, str] = {}  # any original id -> canonical id

    for er in extracted:
        for ent in er.entities:
            key = _norm(ent.name)
            if key not in canonical:
                canonical[key] = ent.model_copy()
            else:
                # Enrich the canonical entity with any extra detail.
                existing = canonical[key]
                if existing.description is None and ent.description:
                    existing.description = ent.description
                if existing.kind.value == "unknown" and ent.kind.value != "unknown":
                    existing.kind = ent.kind
            alias[ent.id] = canonical[key].id

    def resolve(eid: str | None) -> str | None:
        if eid is None:
            return None
        return alias.get(eid, eid)

    relations: list[Relation] = []
    seen: set[tuple[str, str, str]] = set()
    for er in extracted:
        for rel in er.relations:
            src, tgt = resolve(rel.source), resolve(rel.target)
            sig = (src, rel.type.value, tgt)
            if src and tgt and sig not in seen:
                seen.add(sig)
                relations.append(Relation(source=src, type=rel.type, target=tgt))

    requirements: list[Requirement] = []
    for er in extracted:
        req = er.requirement.model_copy()
        req.subject = resolve(req.subject)
        req.objects = [resolve(o) for o in req.objects if resolve(o)]
        requirements.append(req)

    ontology = Ontology(entities=list(canonical.values()), relations=relations)
    return requirements, ontology


def formalize(text: str, client: LLMClient) -> FormalizationResult:
    """Run the full formalization pipeline over ``text``."""
    statements = segment(text)
    extracted = extract(statements, client)
    requirements, ontology = _aggregate(extracted)
    return FormalizationResult(requirements=requirements, ontology=ontology)
