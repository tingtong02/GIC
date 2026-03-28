# KG Schema

## Entity Types

- Grid
- Region
- Substation
- Bus
- Transformer
- TransmissionLine
- Sensor
- MagnetometerStation
- StormEvent
- Scenario
- Observation
- AssumptionRecord

## Relation Types

- connected_to
- located_in
- belongs_to
- contains
- observes
- influenced_by
- has_sensor
- has_voltage_level
- mapped_to
- generated_from
- associated_with_event
- derived_under_scenario
- constrained_by
- has_quality_flag

## Entity Fields

- entity_id
- entity_type
- name
- source
- attributes
- version
- status

## Relation Fields

- relation_id
- head_entity_id
- relation_type
- tail_entity_id
- source
- confidence
- attributes
- version

## ID Rules

- entity ids use `entity_type:normalized_raw_id`
- relation ids use `relation_type:head_entity_id:tail_entity_id`
- normalization lowercases text, replaces non alphanumeric characters with `_`, and trims redundant separators

## Export Layout

Phase 6 exports live under `data/processed/kg/` and include:
- `schema/`
- `entities/`
- `relations/`
- `manifests/`
- `exports/`
