"""Build ontology exports from the IR.

Three views of the same ontology:
- ``to_graph``   : a JSON node/edge graph (always available).
- ``to_mermaid`` : a Mermaid graph diagram string for quick visualization.
- ``to_turtle``  : RDF Turtle via rdflib if installed, else a JSON-LD-like fallback.
"""

from __future__ import annotations

import re

from dust.models import FormalizationResult, Ontology

_NS = "https://dust.local/ontology#"


def to_graph(result: FormalizationResult) -> dict:
    """Return the ontology as ``{"nodes": [...], "edges": [...]}``."""
    onto = result.ontology
    nodes = [
        {"id": e.id, "label": e.name, "kind": e.kind.value, "description": e.description}
        for e in onto.entities
    ]
    edges = [
        {"source": r.source, "target": r.target, "type": r.type.value}
        for r in onto.relations
    ]
    # Requirements are first-class nodes too, linked to their subject via "satisfied_by".
    for req in result.requirements:
        nodes.append(
            {
                "id": req.id,
                "label": req.id,
                "kind": "requirement",
                "description": req.original_text,
            }
        )
        if req.subject:
            edges.append({"source": req.id, "target": req.subject, "type": "satisfied_by"})
    return {"nodes": nodes, "edges": edges}


def _safe(node_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", node_id) or "n"


def to_mermaid(result: FormalizationResult) -> str:
    """Return a Mermaid ``graph LR`` diagram of the ontology."""
    graph = to_graph(result)
    lines = ["graph LR"]
    for node in graph["nodes"]:
        nid = _safe(node["id"])
        label = node["label"].replace('"', "'")
        if node["kind"] == "requirement":
            lines.append(f'{nid}["{label}"]:::req')
        else:
            lines.append(f'{nid}("{label}"):::{node["kind"]}')
    for edge in graph["edges"]:
        lines.append(f'{_safe(edge["source"])} -->|{edge["type"]}| {_safe(edge["target"])}')
    lines.append("classDef req fill:#fde,stroke:#b06;")
    return "\n".join(lines)


def to_turtle(result: FormalizationResult) -> str:
    """Return the ontology as RDF Turtle (rdflib) or a readable fallback."""
    onto = result.ontology
    try:
        from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef  # noqa: PLC0415
    except ImportError:
        return _turtle_fallback(onto)

    g = Graph()
    ns = Namespace(_NS)
    g.bind("dust", ns)
    for e in onto.entities:
        subj = URIRef(_NS + _safe(e.id))
        g.add((subj, RDF.type, ns[e.kind.value.capitalize()]))
        g.add((subj, RDFS.label, Literal(e.name)))
        if e.description:
            g.add((subj, RDFS.comment, Literal(e.description)))
    for r in onto.relations:
        g.add((URIRef(_NS + _safe(r.source)), ns[r.type.value], URIRef(_NS + _safe(r.target))))
    return g.serialize(format="turtle")


def _turtle_fallback(onto: Ontology) -> str:
    lines = [f"@prefix dust: <{_NS}> .", ""]
    for e in onto.entities:
        sid = _safe(e.id)
        lines.append(f"dust:{sid} a dust:{e.kind.value.capitalize()} ;")
        label = e.name.replace('"', "'")
        if e.description:
            comment = e.description.replace('"', "'")
            lines.append(f'    rdfs:label "{label}" ;')
            lines.append(f'    rdfs:comment "{comment}" .')
        else:
            lines.append(f'    rdfs:label "{label}" .')
    for r in onto.relations:
        lines.append(f"dust:{_safe(r.source)} dust:{r.type.value} dust:{_safe(r.target)} .")
    return "\n".join(lines)
