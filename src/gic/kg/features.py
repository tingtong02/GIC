from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from gic.graph.datasets import GraphSample
from gic.kg.schema import KGEntity, KGRelation, build_entity_id


BASE_GLOBAL_FEATURE_NAMES = [
    'kg.global.assumption_count',
    'kg.global.quality_flag_count',
    'kg.global.signal_manifest_available',
    'kg.global.scenario_is_timeseries',
    'kg.global.scenario_is_sweep',
    'kg.global.scenario_sample_count',
    'kg.global.scenario_position',
    'kg.global.scenario_progress',
    'kg.global.time_minutes_from_start',
    'kg.global.bus_count',
    'kg.global.line_count',
    'kg.global.transformer_count',
]
RULE_GLOBAL_FEATURE_NAMES = [
    'kg.rule.hit_count',
    'kg.rule.warning_count',
    'kg.rule.info_count',
    'kg.rule.assumption_present',
    'kg.rule.quality_flags_present',
    'kg.rule.signal_context_available',
    'kg.rule.missing_physics_case',
]
NODE_FEATURE_NAMES = [
    'kg.node.is_bus',
    'kg.node.connected_line_count',
    'kg.node.connected_transformer_count',
    'kg.node.grounding_assumed',
    'kg.node.in_solver',
    'kg.node.sample_assumption_count',
    'kg.node.sample_quality_flag_count',
    'kg.node.incident_line_length_km_sum',
    'kg.node.incident_line_resistance_ohm_sum',
    'kg.node.incident_line_azimuth_abs_mean',
    'kg.node.transformer_resistance_sum',
    'kg.node.neighbor_bus_count',
]


def _parse_time_index(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None



def _scenario_temporal_context(graph_samples: list[GraphSample]) -> dict[str, dict[str, float]]:
    by_scenario: dict[str, list[GraphSample]] = defaultdict(list)
    for sample in graph_samples:
        by_scenario[str(sample.scenario_id)].append(sample)
    context: dict[str, dict[str, float]] = {}
    for scenario_samples in by_scenario.values():
        ordered = sorted(
            scenario_samples,
            key=lambda sample: (sample.time_index[0] if sample.time_index else sample.graph_id),
        )
        parsed_times = [_parse_time_index(sample.time_index[0] if sample.time_index else None) for sample in ordered]
        anchor = next((item for item in parsed_times if item is not None), None)
        scenario_count = max(1, len(ordered))
        for index, sample in enumerate(ordered):
            current_time = parsed_times[index]
            minutes_from_start = 0.0
            if anchor is not None and current_time is not None:
                minutes_from_start = float((current_time - anchor).total_seconds() / 60.0)
            progress = float(index) / float(max(1, scenario_count - 1)) if scenario_count > 1 else 0.0
            context[sample.graph_id] = {
                'scenario_sample_count': float(scenario_count),
                'scenario_position': float(index),
                'scenario_progress': progress,
                'time_minutes_from_start': minutes_from_start,
            }
    return context



def _rule_feature_values(graph_id: str, rule_payload: dict[str, Any]) -> list[float]:
    findings = [dict(item) for item in rule_payload.get('graph_rules', {}).get(graph_id, [])]
    warning_count = sum(1 for item in findings if str(item.get('severity', '')) == 'warning')
    info_count = sum(1 for item in findings if str(item.get('severity', '')) == 'info')
    rule_names = {str(item.get('rule_name', '')) for item in findings}
    return [
        float(len(findings)),
        float(warning_count),
        float(info_count),
        float('assumption_present' in rule_names),
        float('quality_flags_present' in rule_names),
        float('signal_context_available' in rule_names),
        float('missing_physics_case' in rule_names),
    ]



def derive_feature_payload(
    *,
    entities: list[KGEntity],
    relations: list[KGRelation],
    graph_samples: list[GraphSample],
    rule_payload: dict[str, Any],
    include_rule_features: bool = True,
) -> dict[str, Any]:
    entity_map = {entity.entity_id: entity for entity in entities}
    connected_line_counts: defaultdict[str, int] = defaultdict(int)
    connected_transformer_counts: defaultdict[str, int] = defaultdict(int)
    incident_line_length_sums: defaultdict[str, float] = defaultdict(float)
    incident_line_resistance_sums: defaultdict[str, float] = defaultdict(float)
    incident_line_azimuth_sums: defaultdict[str, float] = defaultdict(float)
    incident_line_azimuth_counts: defaultdict[str, int] = defaultdict(int)
    transformer_resistance_sums: defaultdict[str, float] = defaultdict(float)
    neighbor_bus_sets: defaultdict[str, set[str]] = defaultdict(set)
    for relation in relations:
        if relation.relation_type != 'connected_to':
            continue
        head_entity = entity_map.get(relation.head_entity_id)
        if head_entity is None:
            continue
        if head_entity.entity_type == 'TransmissionLine':
            connected_line_counts[relation.tail_entity_id] += 1
            incident_line_length_sums[relation.tail_entity_id] += float(head_entity.attributes.get('length_km', 0.0) or 0.0)
            incident_line_resistance_sums[relation.tail_entity_id] += float(head_entity.attributes.get('resistance_ohm', 0.0) or 0.0)
            incident_line_azimuth_sums[relation.tail_entity_id] += abs(float(head_entity.attributes.get('azimuth_deg', 0.0) or 0.0))
            incident_line_azimuth_counts[relation.tail_entity_id] += 1
            from_bus = str(head_entity.attributes.get('from_bus', ''))
            to_bus = str(head_entity.attributes.get('to_bus', ''))
            source_bus_entity_id = build_entity_id('Bus', from_bus) if from_bus else ''
            target_bus_entity_id = build_entity_id('Bus', to_bus) if to_bus else ''
            if relation.tail_entity_id == source_bus_entity_id and target_bus_entity_id:
                neighbor_bus_sets[relation.tail_entity_id].add(target_bus_entity_id)
            if relation.tail_entity_id == target_bus_entity_id and source_bus_entity_id:
                neighbor_bus_sets[relation.tail_entity_id].add(source_bus_entity_id)
        if head_entity.entity_type == 'Transformer':
            connected_transformer_counts[relation.tail_entity_id] += 1
            transformer_resistance_sums[relation.tail_entity_id] += float(head_entity.attributes.get('effective_resistance_ohm', 0.0) or 0.0)
    bus_entities = [entity for entity in entities if entity.entity_type == 'Bus']
    line_entities = [entity for entity in entities if entity.entity_type == 'TransmissionLine']
    transformer_entities = [entity for entity in entities if entity.entity_type == 'Transformer']
    scenario_context = _scenario_temporal_context(graph_samples)
    global_feature_names = list(BASE_GLOBAL_FEATURE_NAMES)
    if include_rule_features:
        global_feature_names.extend(RULE_GLOBAL_FEATURE_NAMES)
    graph_features: dict[str, Any] = {}
    for sample in graph_samples:
        assumptions = [str(item) for item in sample.metadata.get('assumptions', [])]
        quality_flags = [str(item) for item in sample.metadata.get('quality_flags', [])]
        temporal_context = scenario_context.get(sample.graph_id, {})
        global_values = [
            float(len(assumptions)),
            float(len(quality_flags)),
            float(bool(sample.metadata.get('signal_manifest_path'))),
            float(str(sample.scenario_id).startswith('timeseries')),
            float(str(sample.scenario_id).startswith('sweep')),
            float(temporal_context.get('scenario_sample_count', 1.0)),
            float(temporal_context.get('scenario_position', 0.0)),
            float(temporal_context.get('scenario_progress', 0.0)),
            float(temporal_context.get('time_minutes_from_start', 0.0)),
            float(len(bus_entities)),
            float(len(line_entities)),
            float(len(transformer_entities)),
        ]
        if include_rule_features:
            global_values.extend(_rule_feature_values(sample.graph_id, rule_payload))
        node_features: dict[str, list[float]] = {}
        for node in sample.node_records:
            bus_entity_id = build_entity_id('Bus', node.node_id)
            bus_entity = entity_map.get(bus_entity_id)
            attributes = bus_entity.attributes if bus_entity is not None else {}
            azimuth_mean = 0.0
            if incident_line_azimuth_counts.get(bus_entity_id, 0) > 0:
                azimuth_mean = incident_line_azimuth_sums[bus_entity_id] / float(incident_line_azimuth_counts[bus_entity_id])
            node_features[node.node_id] = [
                1.0,
                float(connected_line_counts.get(bus_entity_id, 0)),
                float(connected_transformer_counts.get(bus_entity_id, 0)),
                float(bool(attributes.get('grounding_assumed'))),
                float(bool(attributes.get('included_in_solver', True))),
                float(len(assumptions)),
                float(len(quality_flags)),
                float(incident_line_length_sums.get(bus_entity_id, 0.0)),
                float(incident_line_resistance_sums.get(bus_entity_id, 0.0)),
                float(azimuth_mean),
                float(transformer_resistance_sums.get(bus_entity_id, 0.0)),
                float(len(neighbor_bus_sets.get(bus_entity_id, set()))),
            ]
        provenance_global = {
            'kg.global.assumption_count': ['sample.metadata.assumptions'],
            'kg.global.quality_flag_count': ['sample.metadata.quality_flags'],
            'kg.global.signal_manifest_available': ['sample.metadata.signal_manifest_path'],
            'kg.global.scenario_is_timeseries': ['sample.scenario_id'],
            'kg.global.scenario_is_sweep': ['sample.scenario_id'],
            'kg.global.scenario_sample_count': ['scenario.observation_count'],
            'kg.global.scenario_position': ['observation.time_index'],
            'kg.global.scenario_progress': ['observation.time_index'],
            'kg.global.time_minutes_from_start': ['observation.time_index'],
            'kg.global.bus_count': ['entities:Bus'],
            'kg.global.line_count': ['entities:TransmissionLine'],
            'kg.global.transformer_count': ['entities:Transformer'],
        }
        if include_rule_features:
            provenance_global.update({
                'kg.rule.hit_count': ['rules.graph_rules'],
                'kg.rule.warning_count': ['rules.graph_rules.severity'],
                'kg.rule.info_count': ['rules.graph_rules.severity'],
                'kg.rule.assumption_present': ['rules.graph_rules.assumption_present'],
                'kg.rule.quality_flags_present': ['rules.graph_rules.quality_flags_present'],
                'kg.rule.signal_context_available': ['rules.graph_rules.signal_context_available'],
                'kg.rule.missing_physics_case': ['rules.graph_rules.missing_physics_case'],
            })
        graph_features[sample.graph_id] = {
            'graph_id': sample.graph_id,
            'sample_id': sample.sample_id,
            'scenario_id': sample.scenario_id,
            'global_feature_names': list(global_feature_names),
            'global_features': global_values,
            'node_feature_names': list(NODE_FEATURE_NAMES),
            'node_features': node_features,
            'provenance': {
                'global': provenance_global,
                'node': {
                    'kg.node.connected_line_count': ['relations:connected_to'],
                    'kg.node.connected_transformer_count': ['relations:connected_to'],
                    'kg.node.grounding_assumed': ['entity.attributes.grounding_assumed'],
                    'kg.node.in_solver': ['entity.attributes.included_in_solver'],
                    'kg.node.sample_assumption_count': ['sample.metadata.assumptions'],
                    'kg.node.sample_quality_flag_count': ['sample.metadata.quality_flags'],
                    'kg.node.incident_line_length_km_sum': ['entity.attributes.length_km'],
                    'kg.node.incident_line_resistance_ohm_sum': ['entity.attributes.resistance_ohm'],
                    'kg.node.incident_line_azimuth_abs_mean': ['entity.attributes.azimuth_deg'],
                    'kg.node.transformer_resistance_sum': ['entity.attributes.effective_resistance_ohm'],
                    'kg.node.neighbor_bus_count': ['relations:connected_to', 'entity.attributes.from_bus', 'entity.attributes.to_bus'],
                },
            },
        }
    return {
        'dataset_name': graph_samples[0].metadata.get('source_case_id', 'unknown') if graph_samples else 'unknown',
        'graph_count': len(graph_features),
        'global_feature_names': list(global_feature_names),
        'node_feature_names': list(NODE_FEATURE_NAMES),
        'graph_features': graph_features,
    }
