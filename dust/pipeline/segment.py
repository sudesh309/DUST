"""Split a requirements document into individual requirement statements.

Uses spaCy for sentence segmentation when available, otherwise a lightweight
heuristic splitter. Bulleted / numbered list items and blank-line separated
blocks are each treated as one statement.
"""

from __future__ import annotations

import re

_BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)]|R\d+[:.)]?|REQ[-\s]?\d+[:.)]?)\s+", re.IGNORECASE)
_SENTENCE_RE = re.compile(r"(?<=[.;])\s+(?=[A-Z])")


def _strip_bullet(line: str) -> str:
    return _BULLET_RE.sub("", line).strip()


def segment(text: str) -> list[str]:
    """Return a list of requirement statements found in ``text``."""
    text = (text or "").strip()
    if not text:
        return []

    lines = [ln for ln in text.splitlines()]
    bulleted = [_strip_bullet(ln) for ln in lines if _BULLET_RE.match(ln)]
    if len(bulleted) >= 2:
        return [b for b in bulleted if b]

    # Otherwise split on blank lines into blocks, then sentences within blocks.
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    statements: list[str] = []
    for block in blocks:
        block = " ".join(block.split())  # collapse internal newlines/whitespace
        parts = _SENTENCE_RE.split(block) if len(block) > 0 else [block]
        statements.extend(p.strip(" .") + "." for p in parts if p.strip())
    return statements or [text]
