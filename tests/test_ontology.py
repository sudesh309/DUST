from dust.models import (
    Entity,
    EntityKind,
    FormalizationResult,
    Ontology,
    Relation,
    RelationType,
    Requirement,
)
from dust.ontology.build import to_graph, to_mermaid, to_turtle


def _result():
    return FormalizationResult(
        requirements=[Requirement(id="R001", original_text="x", subject="fuel_system", action="y")],
        ontology=Ontology(
            entities=[
                Entity(id="aircraft", name="Aircraft", kind=EntityKind.system),
                Entity(id="fuel_system", name="Fuel System", kind=EntityKind.subsystem),
            ],
            relations=[Relation(source="aircraft", type=RelationType.contains, target="fuel_system")],
        ),
    )


def test_graph_includes_entities_and_requirements():
    g = to_graph(_result())
    node_ids = {n["id"] for n in g["nodes"]}
    assert {"aircraft", "fuel_system", "R001"} <= node_ids
    edge_types = {e["type"] for e in g["edges"]}
    assert "contains" in edge_types
    assert "satisfied_by" in edge_types


def test_mermaid_is_well_formed():
    m = to_mermaid(_result())
    assert m.startswith("graph LR")
    assert "-->|contains|" in m
    assert "-->|satisfied_by|" in m


def test_turtle_contains_entities():
    t = to_turtle(_result())
    assert "fuel_system" in t
    assert "Aircraft" in t
    assert "contains" in t
