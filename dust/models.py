"""Intermediate representation (IR) for formalized requirements.

The IR is the single source of truth. The LLM extraction step produces it, and
every downstream renderer (EARS, SysML v2, ontology) is a deterministic function
over it.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class DomainLevel(str, Enum):
    aircraft = "aircraft"
    system = "system"
    airframe = "airframe"
    service = "service"
    industrial = "industrial"
    interface = "interface"
    unknown = "unknown"


class ReqType(str, Enum):
    functional = "functional"
    performance = "performance"
    interface = "interface"
    constraint = "constraint"
    safety = "safety"
    operational = "operational"
    unknown = "unknown"


class EarsPattern(str, Enum):
    ubiquitous = "ubiquitous"
    event_driven = "event_driven"
    state_driven = "state_driven"
    optional_feature = "optional_feature"
    unwanted_behavior = "unwanted_behavior"
    complex = "complex"


class EntityKind(str, Enum):
    system = "system"
    subsystem = "subsystem"
    actor = "actor"
    interface = "interface"
    data = "data"
    function = "function"
    environment = "environment"
    unknown = "unknown"


class RelationType(str, Enum):
    contains = "contains"
    connects = "connects"
    interfaces_with = "interfaces_with"
    depends_on = "depends_on"
    satisfies = "satisfies"
    refines = "refines"


class Constraint(BaseModel):
    """A measurable constraint, e.g. pressure <= 30 bar."""

    parameter: str
    operator: str = "="  # one of: <=, >=, =, <, >, range, in
    value: str
    unit: str | None = None


class Entity(BaseModel):
    """An element identified in the requirement set (system, interface, ...)."""

    id: str
    name: str
    kind: EntityKind = EntityKind.unknown
    description: str | None = None


class Relation(BaseModel):
    """A directed relationship between two entities (by id)."""

    source: str
    type: RelationType
    target: str


class Requirement(BaseModel):
    """A single formalized requirement."""

    id: str
    original_text: str
    domain_level: DomainLevel = DomainLevel.unknown
    req_type: ReqType = ReqType.unknown
    subject: str | None = None  # entity id of the responsible system
    trigger: str | None = None  # event clause -> event-driven EARS
    precondition: str | None = None  # state clause -> state-driven EARS
    feature: str | None = None  # feature clause -> optional-feature EARS
    action: str = ""  # the "shall" response
    objects: list[str] = Field(default_factory=list)  # affected entity ids
    constraints: list[Constraint] = Field(default_factory=list)
    ears_pattern: EarsPattern = EarsPattern.ubiquitous
    rationale: str | None = None


class Ontology(BaseModel):
    """Aggregated entities and relations across the whole requirement set."""

    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)


class ExtractedRequirement(BaseModel):
    """One LLM extraction unit: a requirement plus the elements it contributes."""

    requirement: Requirement
    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)


class ExtractionResponse(BaseModel):
    """Top-level shape the LLM is asked to return."""

    requirements: list[ExtractedRequirement] = Field(default_factory=list)


class FormalizationResult(BaseModel):
    """Final assembled result returned to API callers."""

    requirements: list[Requirement] = Field(default_factory=list)
    ontology: Ontology = Field(default_factory=Ontology)
