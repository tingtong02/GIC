from __future__ import annotations

from gic.kg.schema import build_entity_id, build_relation_id, build_schema_definition


def test_build_entity_id_normalizes_tokens() -> None:
    assert build_entity_id('StormEvent', 'Geomagnetic Storm Day') == 'stormevent:geomagnetic_storm_day'
    assert build_entity_id('Bus', 'Bus 1') == 'bus:bus_1'


def test_build_relation_id_includes_head_and_tail() -> None:
    relation_id = build_relation_id('connected_to', 'bus:bus_1', 'line:line_1')
    assert relation_id == 'connected_to:bus:bus_1:line:line_1'


def test_build_schema_definition_contains_phase6_minimum_sets() -> None:
    schema = build_schema_definition()
    assert 'Grid' in schema.entity_types
    assert 'Observation' in schema.entity_types
    assert 'connected_to' in schema.relation_types
    assert 'has_quality_flag' in schema.relation_types
