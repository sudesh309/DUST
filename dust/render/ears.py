"""Render requirements as EARS (Easy Approach to Requirements Syntax) sentences."""

from __future__ import annotations

from dust.models import EarsPattern, Entity, FormalizationResult, Requirement


def _subject_name(req: Requirement, entities: dict[str, Entity]) -> str:
    if req.subject and req.subject in entities:
        return entities[req.subject].name
    return req.subject or "system"


def to_ears(req: Requirement, entities: dict[str, Entity]) -> str:
    """Build a single normalized EARS sentence for ``req``."""
    subject = f"The {_subject_name(req, entities)}"
    response = f"{subject} shall {req.action.rstrip('.')}"

    pattern = req.ears_pattern
    if pattern == EarsPattern.event_driven and req.trigger:
        sentence = f"When {req.trigger.rstrip('.,')}, {response[0].lower()}{response[1:]}"
    elif pattern == EarsPattern.state_driven and req.precondition:
        sentence = f"While {req.precondition.rstrip('.,')}, {response[0].lower()}{response[1:]}"
    elif pattern == EarsPattern.optional_feature and req.feature:
        sentence = f"Where {req.feature.rstrip('.,')}, {response[0].lower()}{response[1:]}"
    elif pattern == EarsPattern.unwanted_behavior and req.trigger:
        sentence = f"If {req.trigger.rstrip('.,')}, then {response[0].lower()}{response[1:]}"
    elif pattern == EarsPattern.complex:
        prefix = []
        if req.precondition:
            prefix.append(f"While {req.precondition.rstrip('.,')}")
        if req.trigger:
            prefix.append(f"when {req.trigger.rstrip('.,')}")
        head = ", ".join(prefix)
        sentence = f"{head}, {response[0].lower()}{response[1:]}" if head else response
    else:
        sentence = response

    if req.constraints:
        clauses = []
        for c in req.constraints:
            unit = f" {c.unit}" if c.unit else ""
            clauses.append(f"{c.parameter} {c.operator} {c.value}{unit}")
        sentence += " (" + "; ".join(clauses) + ")"

    return sentence.rstrip(".") + "."


def render_ears(result: FormalizationResult) -> list[dict]:
    """Return EARS sentences for every requirement in ``result``."""
    entities = {e.id: e for e in result.ontology.entities}
    return [
        {
            "id": req.id,
            "pattern": req.ears_pattern.value,
            "text": to_ears(req, entities),
        }
        for req in result.requirements
    ]
