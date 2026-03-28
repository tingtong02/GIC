from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


KG_SCHEMA_VERSION = '1.0'
KG_ENTITY_TYPES = [
    'Grid',
    'Region',
    'Substation',
    'Bus',
    'Transformer',
    'TransmissionLine',
    'Sensor',
    'MagnetometerStation',
    'StormEvent',
    'Scenario',
    'Observation',
    'AssumptionRecord',
]
KG_RELATION_TYPES = [
    'connected_to',
    'located_in',
    'belongs_to',
    'contains',
    'observes',
    'influenced_by',
    'has_sensor',
    'has_voltage_level',
    'mapped_to',
    'generated_from',
    'associated_with_event',
    'derived_under_scenario',
    'constrained_by',
    'has_quality_flag',
]
ENTITY_FIELDS = ['entity_id', 'entity_type', 'name', 'source', 'attributes', 'version', 'status']
RELATION_FIELDS = ['relation_id', 'head_entity_id', 'relation_type', 'tail_entity_id', 'source', 'confidence', 'attributes', 'version']


@dataclass(slots=True)
class KGEntity:
    entity_id: str
    entity_type: str
    name: str
    source: str
    attributes: dict[str, Any] = field(default_factory=dict)
    version: str = KG_SCHEMA_VERSION
    status: str = 'active'


@dataclass(slots=True)
class KGRelation:
    relation_id: str
    head_entity_id: str
    relation_type: str
    tail_entity_id: str
    source: str
    confidence: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    version: str = KG_SCHEMA_VERSION


@dataclass(slots=True)
class KGSchemaDefinition:
    schema_version: str
    entity_types: list[str]
    relation_types: list[str]
    entity_fields: list[str]
    relation_fields: list[str]
    notes: str = ''


@dataclass(slots=True)
class KGManifest:
    dataset_name: str
    dataset_path: str
    schema_version: str
    generated_at_utc: str
    entity_count: int
    relation_count: int
    entity_types: list[str]
    relation_types: list[str]
    source_provenance: dict[str, Any] = field(default_factory=dict)
    paths: dict[str, str] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    notes: str = ''
    version: str = KG_SCHEMA_VERSION


def _normalize_token(value: str) -> str:
    token = re.sub(r'[^a-z0-9]+', '_', value.strip().lower())
    token = re.sub(r'_+', '_', token).strip('_')
    return token or 'unknown'


def build_entity_id(entity_type: str, raw_id: str) -> str:
    return f"{_normalize_token(entity_type)}:{_normalize_token(raw_id)}"


def build_relation_id(relation_type: str, head_entity_id: str, tail_entity_id: str) -> str:
    return f"{_normalize_token(relation_type)}:{head_entity_id}:{tail_entity_id}"


def build_schema_definition() -> KGSchemaDefinition:
    return KGSchemaDefinition(
        schema_version=KG_SCHEMA_VERSION,
        entity_types=list(KG_ENTITY_TYPES),
        relation_types=list(KG_RELATION_TYPES),
        entity_fields=list(ENTITY_FIELDS),
        relation_fields=list(RELATION_FIELDS),
        notes='Phase 6 minimal task-scoped KG schema for GIC graph/physics/signal provenance.',
    )


def kg_to_dict(value: Any) -> Any:
    if hasattr(value, '__dataclass_fields__'):
        return asdict(value)
    if isinstance(value, list):
        return [kg_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: kg_to_dict(item) for key, item in value.items()}
    return value
