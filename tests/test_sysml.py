from dust.models import (
    Constraint,
    Entity,
    EntityKind,
    FormalizationResult,
    Ontology,
    Relation,
    RelationType,
    Requirement,
)
from dust.render.sysml import render_sysml


def _result():
    return FormalizationResult(
        requirements=[
            Requirement(
                id="R001",
                original_text="The fuel system shall maintain fuel pressure at 30 bar.",
                subject="fuel_system",
                action="maintain fuel pressure",
                constraints=[Constraint(parameter="pressure", operator="<=", value="30", unit="bar")],
            )
        ],
        ontology=Ontology(
            entities=[
                Entity(id="aircraft", name="Aircraft", kind=EntityKind.system),
                Entity(id="fuel_system", name="Fuel System", kind=EntityKind.subsystem),
                Entity(id="data_bus", name="Data Bus", kind=EntityKind.interface),
            ],
            relations=[Relation(source="aircraft", type=RelationType.contains, target="fuel_system")],
        ),
    )


def test_package_and_defs():
    out = render_sysml(_result())
    assert out.startswith("package RequirementsModel {")
    assert out.rstrip().endswith("}")
    assert "part def Aircraft" in out
    assert "interface def DataBus" in out


def test_requirement_block_has_subject_and_constraint():
    out = render_sysml(_result())
    assert "requirement def R001_FuelSystem {" in out
    assert "subject fuelSystem : FuelSystem;" in out
    assert "require constraint { pressure <= 30 }" in out


def test_satisfy_relationship_emitted():
    out = render_sysml(_result())
    assert "satisfy r001 by fuelSystem;" in out


def test_unique_type_names():
    result = FormalizationResult(
        ontology=Ontology(
            entities=[Entity(id="a", name="System"), Entity(id="b", name="System")]
        )
    )
    out = render_sysml(result)
    assert "part def System;" in out or "part def System " in out
    assert "System2" in out
