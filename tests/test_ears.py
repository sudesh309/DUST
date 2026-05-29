from dust.models import (
    Constraint,
    EarsPattern,
    Entity,
    EntityKind,
    FormalizationResult,
    Ontology,
    Requirement,
)
from dust.render.ears import render_ears, to_ears


def _entities(*ents):
    return {e.id: e for e in ents}


def test_ubiquitous():
    req = Requirement(id="R1", original_text="x", subject="ac", action="maintain level flight")
    ents = _entities(Entity(id="ac", name="Aircraft", kind=EntityKind.system))
    assert to_ears(req, ents) == "The Aircraft shall maintain level flight."


def test_event_driven_lowercases_subject():
    req = Requirement(
        id="R2",
        original_text="x",
        subject="gear",
        action="extend",
        trigger="the landing gear is commanded down",
        ears_pattern=EarsPattern.event_driven,
    )
    ents = _entities(Entity(id="gear", name="Landing Gear System"))
    out = to_ears(req, ents)
    assert out.startswith("When the landing gear is commanded down, the Landing Gear System shall extend")


def test_unwanted_behavior_uses_if_then():
    req = Requirement(
        id="R3",
        original_text="x",
        subject="fp",
        action="discharge the extinguisher",
        trigger="engine fire is detected",
        ears_pattern=EarsPattern.unwanted_behavior,
    )
    ents = _entities(Entity(id="fp", name="Fire Protection System"))
    out = to_ears(req, ents)
    assert out.startswith("If engine fire is detected, then the Fire Protection System shall")


def test_constraints_are_appended():
    req = Requirement(
        id="R4",
        original_text="x",
        subject="fs",
        action="maintain fuel pressure",
        constraints=[Constraint(parameter="pressure", operator="=", value="30", unit="bar")],
    )
    ents = _entities(Entity(id="fs", name="Fuel System"))
    out = to_ears(req, ents)
    assert "(pressure = 30 bar)" in out


def test_render_ears_over_result():
    result = FormalizationResult(
        requirements=[Requirement(id="R1", original_text="x", subject="ac", action="fly")],
        ontology=Ontology(entities=[Entity(id="ac", name="Aircraft")]),
    )
    rows = render_ears(result)
    assert rows == [{"id": "R1", "pattern": "ubiquitous", "text": "The Aircraft shall fly."}]
