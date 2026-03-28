from __future__ import annotations

from gic.kg.schema import KGRelation, build_relation_id


def make_relation(
    head_entity_id: str,
    relation_type: str,
    tail_entity_id: str,
    *,
    source: str,
    confidence: float | None = None,
    attributes: dict[str, object] | None = None,
) -> KGRelation:
    return KGRelation(
        relation_id=build_relation_id(relation_type, head_entity_id, tail_entity_id),
        head_entity_id=head_entity_id,
        relation_type=relation_type,
        tail_entity_id=tail_entity_id,
        source=source,
        confidence=confidence,
        attributes=dict(attributes or {}),
    )
