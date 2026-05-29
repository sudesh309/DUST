"""Offline mock provider.

Produces deterministic, schema-valid IR without any network access. Used by the
test suite and for quick demos. It reads the statements embedded in the user
prompt (after the ``STATEMENTS_JSON:`` marker added by the extraction prompt)
and synthesizes a plausible requirement for each one using simple heuristics.
"""

from __future__ import annotations

import json
import re

from dust.llm.base import LLMClient

_TRIGGER_RE = re.compile(r"^\s*(when|if|while|where)\b(.*?),(.*)$", re.IGNORECASE)
_SHALL_RE = re.compile(r"\bshall\b", re.IGNORECASE)
_CONSTRAINT_RE = re.compile(
    r"(?P<param>[A-Za-z][\w\s]*?)\s*(?P<op><=|>=|<|>|=|of|at least|at most|no more than|within)\s*"
    r"(?P<value>[\d.]+)\s*(?P<unit>[A-Za-z%/]+)?",
)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "entity"


def _guess_kind(name: str) -> str:
    low = name.lower()
    if "interface" in low or "bus" in low or "link" in low:
        return "interface"
    if "system" in low:
        return "system"
    if "crew" in low or "pilot" in low or "operator" in low or "user" in low:
        return "actor"
    return "system"


def _guess_domain(text: str) -> str:
    low = text.lower()
    if "aircraft" in low:
        return "aircraft"
    if "interface" in low or "bus" in low:
        return "interface"
    if "airframe" in low or "fuselage" in low or "wing" in low:
        return "airframe"
    if "service" in low or "maintenance" in low:
        return "service"
    if "manufactur" in low or "production" in low or "assembly" in low:
        return "industrial"
    return "system"


_OP_MAP = {
    "at least": ">=",
    "at most": "<=",
    "no more than": "<=",
    "within": "<=",
    "of": "=",
}


class MockClient(LLMClient):
    """Heuristic, deterministic extractor for offline use."""

    def extract_json(self, system: str, user: str) -> dict:
        statements = self._read_statements(user)
        requirements = [self._formalize(i + 1, s) for i, s in enumerate(statements)]
        return {"requirements": requirements}

    @staticmethod
    def _read_statements(user: str) -> list[str]:
        marker = "STATEMENTS_JSON:"
        if marker in user:
            tail = user.split(marker, 1)[1].strip()
            try:
                data = json.loads(tail)
                if isinstance(data, list):
                    return [str(x) for x in data]
            except json.JSONDecodeError:
                pass
        # Fallback: treat each non-empty line as a statement.
        return [ln.strip() for ln in user.splitlines() if ln.strip()]

    def _formalize(self, idx: int, statement: str) -> dict:
        req_id = f"R{idx:03d}"
        subject_name = self._subject(statement)
        subject_id = _slug(subject_name)
        entities = [
            {
                "id": subject_id,
                "name": subject_name,
                "kind": _guess_kind(subject_name),
                "description": None,
            }
        ]

        trigger = precondition = feature = None
        pattern = "ubiquitous"
        m = _TRIGGER_RE.match(statement)
        if m:
            kw = m.group(1).lower()
            clause = m.group(2).strip()
            if kw == "when":
                trigger, pattern = clause, "event_driven"
            elif kw == "if":
                trigger, pattern = clause, "unwanted_behavior"
            elif kw == "while":
                precondition, pattern = clause, "state_driven"
            elif kw == "where":
                feature, pattern = clause, "optional_feature"

        action = statement
        if _SHALL_RE.search(statement):
            action = _SHALL_RE.split(statement, 1)[1].strip(" .,")

        constraints = self._constraints(statement)
        req_type = "performance" if constraints else "functional"
        if trigger and pattern == "unwanted_behavior":
            req_type = "safety"

        requirement = {
            "id": req_id,
            "original_text": statement,
            "domain_level": _guess_domain(statement),
            "req_type": req_type,
            "subject": subject_id,
            "trigger": trigger,
            "precondition": precondition,
            "feature": feature,
            "action": action,
            "objects": [],
            "constraints": constraints,
            "ears_pattern": pattern,
            "rationale": None,
        }
        return {"requirement": requirement, "entities": entities, "relations": []}

    @staticmethod
    def _subject(statement: str) -> str:
        # Take the noun phrase right before "shall" as the subject, else first words.
        m = re.search(r"\bthe\s+([A-Za-z][\w\s]*?)\s+shall\b", statement, re.IGNORECASE)
        if m:
            return m.group(1).strip().title()
        m = re.search(r"\b([A-Za-z][\w\s]*?)\s+shall\b", statement, re.IGNORECASE)
        if m:
            return m.group(1).strip().split(",")[-1].strip().title()
        return "System"

    @staticmethod
    def _constraints(statement: str) -> list[dict]:
        out: list[dict] = []
        for m in _CONSTRAINT_RE.finditer(statement):
            op = m.group("op").lower()
            out.append(
                {
                    "parameter": m.group("param").strip().split()[-1].title(),
                    "operator": _OP_MAP.get(op, op),
                    "value": m.group("value"),
                    "unit": m.group("unit"),
                }
            )
        return out
