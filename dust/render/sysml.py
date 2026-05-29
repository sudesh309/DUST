"""Render the IR as SysML v2 textual notation.

Produces a single ``package`` containing structural elements (``part def`` /
``interface def``) derived from the ontology and one ``requirement def`` +
``requirement`` usage per requirement, with ``subject``, constrained
``attribute``s, and ``satisfy`` relationships.
"""

from __future__ import annotations

import re

from dust.models import Entity, EntityKind, FormalizationResult, Relation, Requirement

_INDENT = "    "


def _pascal(name: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", name)
    return "".join(p[:1].upper() + p[1:] for p in parts) or "Element"


def _camel(name: str) -> str:
    p = _pascal(name)
    return p[:1].lower() + p[1:] if p else "element"


def _doc(text: str, indent: str) -> str:
    safe = text.replace("*/", "* /").strip()
    return f"{indent}doc /* {safe} */"


def _def_keyword(kind: EntityKind) -> str:
    return "interface def" if kind == EntityKind.interface else "part def"


def _structural_defs(entities: list[Entity], type_names: dict[str, str]) -> list[str]:
    lines: list[str] = [f"{_INDENT}// ---- Structure ----"]
    for ent in entities:
        tname = type_names[ent.id]
        kw = _def_keyword(ent.kind)
        if ent.description:
            lines.append(f"{_INDENT}{kw} {tname} {{")
            lines.append(_doc(ent.description, _INDENT * 2))
            lines.append(f"{_INDENT}}}")
        else:
            lines.append(f"{_INDENT}{kw} {tname}; // kind: {ent.kind.value}")
    return lines


def _attr_name(parameter: str) -> str:
    return _camel(parameter)


def _requirement_block(
    req: Requirement, type_names: dict[str, str], usage_names: dict[str, str]
) -> list[str]:
    def_name = f"{req.id}_{_pascal(usage_names.get(req.subject, '') or 'Requirement')}"
    lines = [f"{_INDENT}requirement def {def_name} {{"]
    lines.append(_doc(req.original_text, _INDENT * 2))
    lines.append(f"{_INDENT * 2}// domain: {req.domain_level.value}, type: {req.req_type.value}")

    if req.subject and req.subject in type_names:
        subj_usage = usage_names[req.subject]
        lines.append(f"{_INDENT * 2}subject {subj_usage} : {type_names[req.subject]};")

    for c in req.constraints:
        attr = _attr_name(c.parameter)
        unit = f" [{c.unit}]" if c.unit else ""
        lines.append(f"{_INDENT * 2}attribute {attr};{unit and ' // unit:' + unit}")
        lines.append(f"{_INDENT * 2}require constraint {{ {attr} {c.operator} {c.value} }}")

    lines.append(f"{_INDENT}}}")
    return lines, def_name


def _relation_lines(relations: list[Relation], usage_names: dict[str, str]) -> list[str]:
    if not relations:
        return []
    lines = [f"{_INDENT}// ---- Relationships ----"]
    for rel in relations:
        src = usage_names.get(rel.source, _camel(rel.source))
        tgt = usage_names.get(rel.target, _camel(rel.target))
        if rel.type.value in ("connects", "interfaces_with"):
            lines.append(f"{_INDENT}connection connect {src} to {tgt};")
        elif rel.type.value == "contains":
            lines.append(f"{_INDENT}// {src} contains {tgt} (composition)")
        else:
            lines.append(f"{_INDENT}// {src} {rel.type.value} {tgt}")
    return lines


def render_sysml(result: FormalizationResult, package: str = "RequirementsModel") -> str:
    """Render ``result`` as SysML v2 textual notation."""
    entities = result.ontology.entities
    type_names: dict[str, str] = {}
    usage_names: dict[str, str] = {}
    used_types: set[str] = set()
    for ent in entities:
        tname = _pascal(ent.name)
        base = tname
        i = 2
        while tname in used_types:
            tname = f"{base}{i}"
            i += 1
        used_types.add(tname)
        type_names[ent.id] = tname
        usage_names[ent.id] = _camel(ent.name)

    lines = [f"package {package} {{", ""]
    if entities:
        lines += _structural_defs(entities, type_names)
        lines.append("")

    lines.append(f"{_INDENT}// ---- Requirements ----")
    satisfies: list[tuple[str, str]] = []
    for req in result.requirements:
        block, def_name = _requirement_block(req, type_names, usage_names)
        lines += block
        usage = _camel(req.id)
        lines.append(f"{_INDENT}requirement {usage} : {def_name};")
        if req.subject and req.subject in usage_names:
            satisfies.append((usage, usage_names[req.subject]))
        lines.append("")

    rel_lines = _relation_lines(result.ontology.relations, usage_names)
    if rel_lines:
        lines += rel_lines
        lines.append("")

    if satisfies:
        lines.append(f"{_INDENT}// ---- Satisfaction ----")
        for usage, subj in satisfies:
            lines.append(f"{_INDENT}satisfy {usage} by {subj};")
        lines.append("")

    lines.append("}")
    return "\n".join(lines)
