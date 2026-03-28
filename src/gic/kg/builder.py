from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gic.graph.datasets import GraphSample
from gic.kg.extractors import KGRawSources, load_kg_sources
from gic.kg.features import derive_feature_payload
from gic.kg.relations import make_relation
from gic.kg.rules import evaluate_rule_findings
from gic.kg.schema import KGEntity, KGManifest, KGRelation, KGSchemaDefinition, build_entity_id, build_schema_definition
from gic.kg.validation import ensure_conflict_free, validate_kg_bundle


@dataclass(slots=True)
class KGBuildResult:
    dataset_name: str
    dataset_path: str
    schema: KGSchemaDefinition
    entities: list[KGEntity]
    relations: list[KGRelation]
    manifest: KGManifest
    validation: dict[str, Any]
    feature_payload: dict[str, Any]
    rule_payload: dict[str, Any]
    sample_index: dict[str, dict[str, Any]] = field(default_factory=dict)


def _default_region_name(kg_config: dict[str, Any]) -> str:
    return str(kg_config.get('default_region_name', 'default_region'))


def _default_substation_name(kg_config: dict[str, Any]) -> str:
    return str(kg_config.get('default_substation_name', 'default_substation'))


def _bus_entities(sources: KGRawSources, entity_map: dict[str, KGEntity]) -> None:
    for bus in sources.physics_case.get('buses', []):
        bus_id = str(bus['bus_id'])
        entity = KGEntity(
            entity_id=build_entity_id('Bus', bus_id),
            entity_type='Bus',
            name=bus_id,
            source='physics_ready',
            attributes={
                'base_kv': float(bus.get('base_kv', 0.0) or 0.0),
                'included_in_solver': bool(bus.get('included_in_solver', True)),
                'grounding_assumed': bool(bus.get('grounding', {}).get('assumed', False)),
                'grounding_resistance_ohm': float(bus.get('grounding', {}).get('grounding_resistance_ohm', 0.0) or 0.0),
            },
        )
        ensure_conflict_free(entity_map, entity.entity_id, entity)


def _line_entities(sources: KGRawSources, entity_map: dict[str, KGEntity]) -> None:
    for line in sources.physics_case.get('lines', []):
        line_id = str(line['line_id'])
        entity = KGEntity(
            entity_id=build_entity_id('TransmissionLine', line_id),
            entity_type='TransmissionLine',
            name=line_id,
            source='physics_ready',
            attributes={
                'from_bus': str(line.get('from_bus', '')),
                'to_bus': str(line.get('to_bus', '')),
                'length_km': float(line.get('length_km', 0.0) or 0.0),
                'azimuth_deg': float(line.get('azimuth_deg', 0.0) or 0.0),
                'resistance_ohm': float(line.get('resistance_ohm', 0.0) or 0.0),
            },
        )
        ensure_conflict_free(entity_map, entity.entity_id, entity)


def _transformer_entities(sources: KGRawSources, entity_map: dict[str, KGEntity]) -> None:
    for transformer in sources.physics_case.get('transformers', []):
        transformer_id = str(transformer['transformer_id'])
        entity = KGEntity(
            entity_id=build_entity_id('Transformer', transformer_id),
            entity_type='Transformer',
            name=transformer_id,
            source='physics_ready',
            attributes={
                'from_bus': str(transformer.get('from_bus', '')),
                'to_bus': str(transformer.get('to_bus', '')),
                'associated_line_id': str(transformer.get('associated_line_id', '')),
                'effective_resistance_ohm': float(transformer.get('effective_resistance_ohm', 0.0) or 0.0),
            },
        )
        ensure_conflict_free(entity_map, entity.entity_id, entity)


def _signal_entities(sources: KGRawSources, entity_map: dict[str, KGEntity]) -> dict[str, str]:
    ids: dict[str, str] = {}
    for manifest_path, manifest in sources.signal_manifests.items():
        source_name = str(manifest.get('source_name') or Path(manifest_path).stem)
        sample_name = str(manifest.get('sample_id') or source_name)
        station = KGEntity(
            entity_id=build_entity_id('MagnetometerStation', source_name),
            entity_type='MagnetometerStation',
            name=source_name,
            source='signal_ready',
            attributes={'manifest_path': manifest_path},
        )
        sensor = KGEntity(
            entity_id=build_entity_id('Sensor', sample_name),
            entity_type='Sensor',
            name=sample_name,
            source='signal_ready',
            attributes={'manifest_path': manifest_path, 'source_name': source_name},
        )
        event = KGEntity(
            entity_id=build_entity_id('StormEvent', sample_name),
            entity_type='StormEvent',
            name=sample_name,
            source='signal_ready',
            attributes={'source_name': source_name},
        )
        ensure_conflict_free(entity_map, station.entity_id, station)
        ensure_conflict_free(entity_map, sensor.entity_id, sensor)
        ensure_conflict_free(entity_map, event.entity_id, event)
        ids[manifest_path] = sensor.entity_id
    return ids


def _scenario_and_observation_entities(sources: KGRawSources, entity_map: dict[str, KGEntity]) -> None:
    for sample in sources.graph_samples:
        scenario = KGEntity(
            entity_id=build_entity_id('Scenario', sample.scenario_id),
            entity_type='Scenario',
            name=sample.scenario_id,
            source='graph_ready',
            attributes={
                'scenario_id': sample.scenario_id,
                'source_case_id': sample.metadata.get('source_case_id'),
            },
        )
        observation = KGEntity(
            entity_id=build_entity_id('Observation', sample.graph_id),
            entity_type='Observation',
            name=sample.graph_id,
            source='graph_ready',
            attributes={
                'graph_id': sample.graph_id,
                'sample_id': sample.sample_id,
                'time_index': sample.time_index[0] if sample.time_index else None,
            },
        )
        ensure_conflict_free(entity_map, scenario.entity_id, scenario)
        ensure_conflict_free(entity_map, observation.entity_id, observation)


def _assumption_entities(sources: KGRawSources, entity_map: dict[str, KGEntity]) -> dict[str, str]:
    records: dict[str, str] = {}
    texts: set[str] = set(str(item) for item in sources.physics_case.get('assumptions', []))
    for line in sources.physics_case.get('lines', []):
        texts.update(str(item) for item in line.get('assumptions', []))
    for transformer in sources.physics_case.get('transformers', []):
        texts.update(str(item) for item in transformer.get('assumptions', []))
    for sample in sources.graph_samples:
        texts.update(str(item) for item in sample.metadata.get('assumptions', []))
        texts.update(f'quality:{item}' for item in sample.metadata.get('quality_flags', []))
    for text in sorted(texts):
        entity = KGEntity(
            entity_id=build_entity_id('AssumptionRecord', text),
            entity_type='AssumptionRecord',
            name=text,
            source='physics_ready' if not text.startswith('quality:') else 'graph_ready',
            attributes={'record_type': 'quality_flag' if text.startswith('quality:') else 'assumption', 'text': text},
        )
        ensure_conflict_free(entity_map, entity.entity_id, entity)
        records[text] = entity.entity_id
    return records


def _sample_index(samples: list[GraphSample]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for sample in samples:
        index[sample.graph_id] = {
            'graph_id': sample.graph_id,
            'sample_id': sample.sample_id,
            'scenario_id': sample.scenario_id,
            'time_index': sample.time_index[0] if sample.time_index else None,
            'source_case_id': sample.metadata.get('source_case_id'),
            'quality_flags': [str(item) for item in sample.metadata.get('quality_flags', [])],
            'assumptions': [str(item) for item in sample.metadata.get('assumptions', [])],
            'signal_manifest_path': sample.metadata.get('signal_manifest_path'),
        }
    return index


def _build_entities(sources: KGRawSources, kg_config: dict[str, Any]) -> tuple[list[KGEntity], dict[str, str], dict[str, str], dict[str, KGEntity]]:
    entity_map: dict[str, KGEntity] = {}
    source_case_id = str(sources.graph_samples[0].metadata.get('source_case_id', 'unknown_case')) if sources.graph_samples else 'unknown_case'
    grid = KGEntity(
        entity_id=build_entity_id('Grid', source_case_id),
        entity_type='Grid',
        name=source_case_id,
        source='graph_ready',
        attributes={'source_case_id': source_case_id},
    )
    region_name = f'{source_case_id}_{_default_region_name(kg_config)}'
    region = KGEntity(
        entity_id=build_entity_id('Region', region_name),
        entity_type='Region',
        name=region_name,
        source='phase6_default',
        attributes={'reason': 'Phase 6 default fallback region mapping'},
    )
    substation_name = f'{source_case_id}_{_default_substation_name(kg_config)}'
    substation = KGEntity(
        entity_id=build_entity_id('Substation', substation_name),
        entity_type='Substation',
        name=substation_name,
        source='phase6_default',
        attributes={'reason': 'Phase 6 default fallback substation mapping'},
    )
    ensure_conflict_free(entity_map, grid.entity_id, grid)
    ensure_conflict_free(entity_map, region.entity_id, region)
    ensure_conflict_free(entity_map, substation.entity_id, substation)
    _bus_entities(sources, entity_map)
    _line_entities(sources, entity_map)
    _transformer_entities(sources, entity_map)
    signal_sensor_ids = _signal_entities(sources, entity_map)
    _scenario_and_observation_entities(sources, entity_map)
    assumption_ids = _assumption_entities(sources, entity_map)
    return list(entity_map.values()), signal_sensor_ids, assumption_ids, entity_map


def _build_relations(
    sources: KGRawSources,
    *,
    entity_map: dict[str, KGEntity],
    signal_sensor_ids: dict[str, str],
    assumption_ids: dict[str, str],
    kg_config: dict[str, Any],
) -> list[KGRelation]:
    relations: dict[str, KGRelation] = {}
    source_case_id = str(sources.graph_samples[0].metadata.get('source_case_id', 'unknown_case')) if sources.graph_samples else 'unknown_case'
    grid_id = build_entity_id('Grid', source_case_id)
    region_id = build_entity_id('Region', f'{source_case_id}_{_default_region_name(kg_config)}')
    substation_id = build_entity_id('Substation', f'{source_case_id}_{_default_substation_name(kg_config)}')

    def add(relation: KGRelation) -> None:
        ensure_conflict_free(relations, relation.relation_id, relation)

    add(make_relation(grid_id, 'contains', region_id, source='phase6_default'))
    add(make_relation(region_id, 'contains', substation_id, source='phase6_default'))
    add(make_relation(substation_id, 'located_in', region_id, source='phase6_default'))
    add(make_relation(substation_id, 'belongs_to', grid_id, source='phase6_default'))

    for entity in entity_map.values():
        if entity.entity_type == 'Bus':
            add(make_relation(grid_id, 'contains', entity.entity_id, source='physics_ready'))
            add(make_relation(entity.entity_id, 'belongs_to', substation_id, source='phase6_default'))
            add(make_relation(entity.entity_id, 'located_in', region_id, source='phase6_default'))
            base_kv = entity.attributes.get('base_kv')
            if base_kv:
                voltage_id = build_entity_id('AssumptionRecord', f'voltage_{base_kv}')
                if voltage_id in entity_map:
                    add(make_relation(entity.entity_id, 'has_voltage_level', voltage_id, source='physics_ready'))
        elif entity.entity_type in {'TransmissionLine', 'Transformer'}:
            add(make_relation(grid_id, 'contains', entity.entity_id, source='physics_ready'))
    for line in sources.physics_case.get('lines', []):
        line_id = build_entity_id('TransmissionLine', str(line['line_id']))
        add(make_relation(line_id, 'connected_to', build_entity_id('Bus', str(line['from_bus'])), source='physics_ready'))
        add(make_relation(line_id, 'connected_to', build_entity_id('Bus', str(line['to_bus'])), source='physics_ready'))
        for assumption in line.get('assumptions', []):
            assumption_id = assumption_ids.get(str(assumption))
            if assumption_id:
                add(make_relation(line_id, 'constrained_by', assumption_id, source='physics_ready'))
    for transformer in sources.physics_case.get('transformers', []):
        transformer_id = build_entity_id('Transformer', str(transformer['transformer_id']))
        add(make_relation(transformer_id, 'connected_to', build_entity_id('Bus', str(transformer['from_bus'])), source='physics_ready'))
        add(make_relation(transformer_id, 'connected_to', build_entity_id('Bus', str(transformer['to_bus'])), source='physics_ready'))
        associated_line_id = str(transformer.get('associated_line_id', '')).strip()
        if associated_line_id:
            add(make_relation(transformer_id, 'generated_from', build_entity_id('TransmissionLine', associated_line_id), source='physics_ready'))
        for assumption in transformer.get('assumptions', []):
            assumption_id = assumption_ids.get(str(assumption))
            if assumption_id:
                add(make_relation(transformer_id, 'constrained_by', assumption_id, source='physics_ready'))
    for manifest_path, sensor_id in signal_sensor_ids.items():
        manifest = sources.signal_manifests[manifest_path]
        station_id = build_entity_id('MagnetometerStation', str(manifest.get('source_name') or Path(manifest_path).stem))
        event_id = build_entity_id('StormEvent', str(manifest.get('sample_id') or manifest.get('source_name') or Path(manifest_path).stem))
        add(make_relation(grid_id, 'has_sensor', sensor_id, source='signal_ready'))
        add(make_relation(sensor_id, 'mapped_to', station_id, source='signal_ready'))
        add(make_relation(sensor_id, 'observes', grid_id, source='signal_ready'))
        add(make_relation(station_id, 'located_in', region_id, source='phase6_default'))
        add(make_relation(event_id, 'influenced_by', station_id, source='signal_ready'))
    for sample in sources.graph_samples:
        observation_id = build_entity_id('Observation', sample.graph_id)
        scenario_id = build_entity_id('Scenario', sample.scenario_id)
        add(make_relation(observation_id, 'derived_under_scenario', scenario_id, source='graph_ready'))
        add(make_relation(observation_id, 'belongs_to', grid_id, source='graph_ready'))
        manifest_path = sample.metadata.get('signal_manifest_path')
        if manifest_path:
            resolved_manifest_path = str(Path(manifest_path)) if Path(str(manifest_path)).is_absolute() else str((sources.dataset_path.parents[2] / str(manifest_path)).resolve())
            if resolved_manifest_path in signal_sensor_ids:
                sensor_id = signal_sensor_ids[resolved_manifest_path]
                manifest = sources.signal_manifests[resolved_manifest_path]
                event_id = build_entity_id('StormEvent', str(manifest.get('sample_id') or manifest.get('source_name') or Path(resolved_manifest_path).stem))
                add(make_relation(observation_id, 'generated_from', sensor_id, source='graph_ready'))
                add(make_relation(scenario_id, 'associated_with_event', event_id, source='graph_ready'))
        for assumption in sample.metadata.get('assumptions', []):
            assumption_id = assumption_ids.get(str(assumption))
            if assumption_id:
                add(make_relation(observation_id, 'constrained_by', assumption_id, source='graph_ready'))
        for quality_flag in sample.metadata.get('quality_flags', []):
            assumption_id = assumption_ids.get(f'quality:{quality_flag}')
            if assumption_id:
                add(make_relation(observation_id, 'has_quality_flag', assumption_id, source='graph_ready'))
    return list(relations.values())


def build_kg_bundle(*, dataset_path: str | Path, project_root: Path, kg_config: dict[str, Any]) -> KGBuildResult:
    sources = load_kg_sources(dataset_path, project_root=project_root)
    schema = build_schema_definition()
    entities, signal_sensor_ids, assumption_ids, entity_map = _build_entities(sources, kg_config)
    relations = _build_relations(
        sources,
        entity_map=entity_map,
        signal_sensor_ids=signal_sensor_ids,
        assumption_ids=assumption_ids,
        kg_config=kg_config,
    )
    validation = validate_kg_bundle(schema, entities, relations)
    manifest = KGManifest(
        dataset_name=sources.dataset.dataset_name,
        dataset_path=str(sources.dataset_path),
        schema_version=schema.schema_version,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        entity_count=len(entities),
        relation_count=len(relations),
        entity_types=sorted({entity.entity_type for entity in entities}),
        relation_types=sorted({relation.relation_type for relation in relations}),
        source_provenance={
            'graph_dataset_path': str(sources.dataset_path),
            'graph_manifest_path': sources.dataset.manifest_path,
            'physics_case_path': str(sources.physics_case_path) if sources.physics_case_path else '',
            'grid_case_path': str(sources.grid_case_path) if sources.grid_case_path else '',
            'signal_manifest_paths': sorted(sources.signal_manifests.keys()),
        },
        validation=validation,
        notes='Phase 6 minimal KG bundle built from graph-ready, physics-ready, signal-ready, and metadata sources.',
    )
    rule_payload = evaluate_rule_findings(sources.graph_samples)
    feature_payload = derive_feature_payload(
        entities=entities,
        relations=relations,
        graph_samples=sources.graph_samples,
        rule_payload=rule_payload,
        include_rule_features=bool(kg_config.get('use_rule_layer', True)),
    )
    return KGBuildResult(
        dataset_name=sources.dataset.dataset_name,
        dataset_path=str(sources.dataset_path),
        schema=schema,
        entities=entities,
        relations=relations,
        manifest=manifest,
        validation=validation,
        feature_payload=feature_payload,
        rule_payload=rule_payload,
        sample_index=_sample_index(sources.graph_samples),
    )
