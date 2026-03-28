from __future__ import annotations

from typing import Iterable

from gic.kg.schema import KG_ENTITY_TYPES, KG_RELATION_TYPES, KGEntity, KGManifest, KGRelation, KGSchemaDefinition, kg_to_dict


def validate_schema_definition(schema: KGSchemaDefinition) -> None:
    missing_entities = sorted(set(KG_ENTITY_TYPES) - set(schema.entity_types))
    missing_relations = sorted(set(KG_RELATION_TYPES) - set(schema.relation_types))
    if missing_entities:
        raise ValueError(f'Missing KG entity types: {missing_entities}')
    if missing_relations:
        raise ValueError(f'Missing KG relation types: {missing_relations}')


def validate_entities(entities: Iterable[KGEntity]) -> dict[str, int]:
    seen: set[str] = set()
    counts: dict[str, int] = {}
    for entity in entities:
        if entity.entity_type not in KG_ENTITY_TYPES:
            raise ValueError(f'Unsupported KG entity type: {entity.entity_type}')
        if entity.entity_id in seen:
            raise ValueError(f'Duplicate KG entity id: {entity.entity_id}')
        seen.add(entity.entity_id)
        counts[entity.entity_type] = counts.get(entity.entity_type, 0) + 1
    return counts


def validate_relations(relations: Iterable[KGRelation], entity_ids: set[str]) -> dict[str, int]:
    seen: set[str] = set()
    counts: dict[str, int] = {}
    for relation in relations:
        if relation.relation_type not in KG_RELATION_TYPES:
            raise ValueError(f'Unsupported KG relation type: {relation.relation_type}')
        if relation.relation_id in seen:
            raise ValueError(f'Duplicate KG relation id: {relation.relation_id}')
        if relation.head_entity_id not in entity_ids:
            raise ValueError(f'KG relation head missing: {relation.relation_id}')
        if relation.tail_entity_id not in entity_ids:
            raise ValueError(f'KG relation tail missing: {relation.relation_id}')
        seen.add(relation.relation_id)
        counts[relation.relation_type] = counts.get(relation.relation_type, 0) + 1
    return counts


def validate_manifest(manifest: KGManifest) -> None:
    if manifest.entity_count < 1:
        raise ValueError('KG manifest entity_count must be positive')
    if manifest.relation_count < 1:
        raise ValueError('KG manifest relation_count must be positive')


def validate_kg_bundle(
    schema: KGSchemaDefinition,
    entities: list[KGEntity],
    relations: list[KGRelation],
) -> dict[str, object]:
    validate_schema_definition(schema)
    entity_counts = validate_entities(entities)
    entity_ids = {entity.entity_id for entity in entities}
    relation_counts = validate_relations(relations, entity_ids)
    return {
        'entity_counts': entity_counts,
        'relation_counts': relation_counts,
        'entity_total': len(entities),
        'relation_total': len(relations),
        'schema_version': schema.schema_version,
    }


def ensure_conflict_free(existing: dict[str, object], key: str, payload: object) -> None:
    if key in existing and kg_to_dict(existing[key]) != kg_to_dict(payload):
        raise ValueError(f'Conflicting KG payload for id: {key}')
    existing[key] = payload
