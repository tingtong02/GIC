from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from gic.graph.datasets import GraphSample
from gic.kg.schema import KGEntity, KGRelation, build_entity_id


GLOBAL_FEATURE_SPECS: list[tuple[str, str]] = [
    ('kg.global.assumption_count', 'reliability_context'),
    ('kg.global.assumption_density_per_bus', 'reliability_context'),
    ('kg.global.quality_flag_count', 'reliability_context'),
    ('kg.global.quality_flag_density_per_bus', 'reliability_context'),
    ('kg.global.signal_manifest_available', 'reliability_context'),
    ('kg.global.observed_fraction', 'reliability_context'),
    ('kg.global.hidden_fraction', 'reliability_context'),
    ('kg.global.scenario_is_timeseries', 'scenario_context'),
    ('kg.global.scenario_is_sweep', 'scenario_context'),
    ('kg.global.scenario_sample_count', 'scenario_context'),
    ('kg.global.scenario_position', 'scenario_context'),
    ('kg.global.scenario_progress', 'scenario_context'),
    ('kg.global.time_minutes_from_start', 'scenario_context'),
    ('kg.global.bus_count', 'topology_context'),
    ('kg.global.line_count', 'topology_context'),
    ('kg.global.transformer_count', 'topology_context'),
    ('kg.global.line_per_bus_ratio', 'topology_context'),
    ('kg.global.transformer_per_bus_ratio', 'topology_context'),
]

RULE_GLOBAL_FEATURE_SPECS: list[tuple[str, str]] = [
    ('kg.rule.hit_count', 'rule_context'),
    ('kg.rule.hit_density_per_bus', 'rule_context'),
    ('kg.rule.warning_count', 'rule_context'),
    ('kg.rule.info_count', 'rule_context'),
    ('kg.rule.assumption_present', 'rule_context'),
    ('kg.rule.quality_flags_present', 'rule_context'),
    ('kg.rule.signal_context_available', 'rule_context'),
    ('kg.rule.missing_physics_case', 'rule_context'),
    ('kg.rule.assumption_pressure', 'rule_context'),
    ('kg.rule.quality_pressure', 'rule_context'),
    ('kg.rule.observed_fraction', 'rule_context'),
    ('kg.rule.hidden_fraction', 'rule_context'),
    ('kg.rule.scenario_progress', 'rule_context'),
    ('kg.rule.time_minutes_from_start', 'rule_context'),
]

RELATION_GLOBAL_FEATURE_SPECS: list[tuple[str, str]] = [
    ('kg.rel.global.connected_to_count', 'relation_context'),
    ('kg.rel.global.connected_to_per_bus', 'relation_context'),
    ('kg.rel.global.constrained_by_count', 'relation_context'),
    ('kg.rel.global.constrained_by_per_bus', 'relation_context'),
    ('kg.rel.global.generated_from_count', 'relation_context'),
    ('kg.rel.global.derived_under_scenario_count', 'relation_context'),
    ('kg.rel.global.relation_count', 'relation_context'),
    ('kg.rel.global.relation_per_entity', 'relation_context'),
]

NODE_FEATURE_SPECS: list[tuple[str, str]] = [
    ('kg.node.is_bus', 'topology_context'),
    ('kg.node.connected_line_count', 'topology_context'),
    ('kg.node.connected_transformer_count', 'topology_context'),
    ('kg.node.incident_line_length_km_sum', 'topology_context'),
    ('kg.node.incident_line_resistance_ohm_sum', 'topology_context'),
    ('kg.node.incident_line_azimuth_abs_mean', 'topology_context'),
    ('kg.node.transformer_resistance_sum', 'topology_context'),
    ('kg.node.neighbor_bus_count', 'topology_context'),
    ('kg.node.grounding_assumed', 'reliability_context'),
    ('kg.node.in_solver', 'reliability_context'),
    ('kg.node.sample_assumption_count', 'reliability_context'),
    ('kg.node.sample_quality_flag_count', 'reliability_context'),
    ('kg.node.is_observed', 'reliability_context'),
    ('kg.node.is_target', 'reliability_context'),
    ('kg.node.sample_observed_fraction', 'reliability_context'),
    ('kg.node.sample_hidden_fraction', 'reliability_context'),
    ('kg.node.assumption_pressure', 'reliability_context'),
    ('kg.node.quality_pressure', 'reliability_context'),
]

RELATION_NODE_FEATURE_SPECS: list[tuple[str, str]] = [
    ('kg.rel.node.relation_degree', 'relation_context'),
    ('kg.rel.node.connected_to_ratio', 'relation_context'),
    ('kg.rel.node.constraint_support_count', 'relation_context'),
    ('kg.rel.node.constraint_support_ratio', 'relation_context'),
    ('kg.rel.node.generated_support_count', 'relation_context'),
    ('kg.rel.node.generated_support_ratio', 'relation_context'),
]

GLOBAL_FEATURE_NAMES = [name for name, _group in GLOBAL_FEATURE_SPECS]
RULE_GLOBAL_FEATURE_NAMES = [name for name, _group in RULE_GLOBAL_FEATURE_SPECS]
RELATION_GLOBAL_FEATURE_NAMES = [name for name, _group in RELATION_GLOBAL_FEATURE_SPECS]
NODE_FEATURE_NAMES = [name for name, _group in NODE_FEATURE_SPECS]
RELATION_NODE_FEATURE_NAMES = [name for name, _group in RELATION_NODE_FEATURE_SPECS]


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


def _relation_count_map(relations: list[KGRelation]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for relation in relations:
        counts[str(relation.relation_type)] += 1
    return counts


def _rule_feature_values(
    sample: GraphSample,
    *,
    rule_payload: dict[str, Any],
    bus_count: int,
    observed_fraction: float,
    hidden_fraction: float,
    scenario_progress: float,
    time_minutes_from_start: float,
) -> list[float]:
    findings = [dict(item) for item in rule_payload.get('graph_rules', {}).get(sample.graph_id, [])]
    warning_count = sum(1 for item in findings if str(item.get('severity', '')) == 'warning')
    info_count = sum(1 for item in findings if str(item.get('severity', '')) == 'info')
    rule_names = {str(item.get('rule_name', '')) for item in findings}
    assumptions = [str(item) for item in sample.metadata.get('assumptions', [])]
    quality_flags = [str(item) for item in sample.metadata.get('quality_flags', [])]
    bus_denom = float(max(1, bus_count))
    return [
        float(len(findings)),
        float(len(findings)) / bus_denom,
        float(warning_count),
        float(info_count),
        float('assumption_present' in rule_names),
        float('quality_flags_present' in rule_names),
        float('signal_context_available' in rule_names),
        float('missing_physics_case' in rule_names),
        float(len(assumptions)) / bus_denom,
        float(len(quality_flags)) / bus_denom,
        float(observed_fraction),
        float(hidden_fraction),
        float(scenario_progress),
        float(time_minutes_from_start),
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
    relation_counts = _relation_count_map(relations)
    connected_line_counts: defaultdict[str, int] = defaultdict(int)
    connected_transformer_counts: defaultdict[str, int] = defaultdict(int)
    incident_line_length_sums: defaultdict[str, float] = defaultdict(float)
    incident_line_resistance_sums: defaultdict[str, float] = defaultdict(float)
    incident_line_azimuth_sums: defaultdict[str, float] = defaultdict(float)
    incident_line_azimuth_counts: defaultdict[str, int] = defaultdict(int)
    transformer_resistance_sums: defaultdict[str, float] = defaultdict(float)
    neighbor_bus_sets: defaultdict[str, set[str]] = defaultdict(set)
    relation_degree_counts: defaultdict[str, int] = defaultdict(int)
    constraint_support_counts: defaultdict[str, int] = defaultdict(int)
    generated_support_counts: defaultdict[str, int] = defaultdict(int)
    asset_to_bus_ids: defaultdict[str, set[str]] = defaultdict(set)

    for relation in relations:
        relation_degree_counts[str(relation.head_entity_id)] += 1
        relation_degree_counts[str(relation.tail_entity_id)] += 1
        if relation.relation_type != 'connected_to':
            continue
        head_entity = entity_map.get(relation.head_entity_id)
        if head_entity is None:
            continue
        asset_to_bus_ids[relation.head_entity_id].add(relation.tail_entity_id)
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

    for relation in relations:
        if relation.relation_type == 'constrained_by':
            for bus_id in asset_to_bus_ids.get(relation.head_entity_id, set()):
                constraint_support_counts[bus_id] += 1
        if relation.relation_type == 'generated_from':
            for bus_id in asset_to_bus_ids.get(relation.head_entity_id, set()):
                generated_support_counts[bus_id] += 1

    bus_entities = [entity for entity in entities if entity.entity_type == 'Bus']
    line_entities = [entity for entity in entities if entity.entity_type == 'TransmissionLine']
    transformer_entities = [entity for entity in entities if entity.entity_type == 'Transformer']
    scenario_context = _scenario_temporal_context(graph_samples)
    global_feature_names = list(GLOBAL_FEATURE_NAMES)
    if include_rule_features:
        global_feature_names.extend(RULE_GLOBAL_FEATURE_NAMES)
    global_feature_names.extend(RELATION_GLOBAL_FEATURE_NAMES)
    node_feature_names = list(NODE_FEATURE_NAMES) + list(RELATION_NODE_FEATURE_NAMES)
    graph_features: dict[str, Any] = {}
    global_group_map = {name: group for name, group in GLOBAL_FEATURE_SPECS}
    global_group_map.update({name: group for name, group in RULE_GLOBAL_FEATURE_SPECS})
    global_group_map.update({name: group for name, group in RELATION_GLOBAL_FEATURE_SPECS})
    node_group_map = {name: group for name, group in NODE_FEATURE_SPECS}
    node_group_map.update({name: group for name, group in RELATION_NODE_FEATURE_SPECS})
    bus_count = len(bus_entities)
    line_count = len(line_entities)
    transformer_count = len(transformer_entities)
    entity_count = max(1, len(entities))
    bus_denom = float(max(1, bus_count))
    line_per_bus_ratio = float(line_count) / bus_denom
    transformer_per_bus_ratio = float(transformer_count) / bus_denom

    for sample in graph_samples:
        assumptions = [str(item) for item in sample.metadata.get('assumptions', [])]
        quality_flags = [str(item) for item in sample.metadata.get('quality_flags', [])]
        temporal_context = scenario_context.get(sample.graph_id, {})
        observed_fraction = float(sample.mask_bundle.metadata.get('observed_fraction', 0.0) or 0.0)
        hidden_fraction = float(sample.mask_bundle.metadata.get('hidden_fraction', 0.0) or 0.0)
        global_values = [
            float(len(assumptions)),
            float(len(assumptions)) / bus_denom,
            float(len(quality_flags)),
            float(len(quality_flags)) / bus_denom,
            float(bool(sample.metadata.get('signal_manifest_path'))),
            observed_fraction,
            hidden_fraction,
            float(str(sample.scenario_id).startswith('timeseries')),
            float(str(sample.scenario_id).startswith('sweep')),
            float(temporal_context.get('scenario_sample_count', 1.0)),
            float(temporal_context.get('scenario_position', 0.0)),
            float(temporal_context.get('scenario_progress', 0.0)),
            float(temporal_context.get('time_minutes_from_start', 0.0)),
            float(bus_count),
            float(line_count),
            float(transformer_count),
            line_per_bus_ratio,
            transformer_per_bus_ratio,
        ]
        if include_rule_features:
            global_values.extend(
                _rule_feature_values(
                    sample,
                    rule_payload=rule_payload,
                    bus_count=bus_count,
                    observed_fraction=observed_fraction,
                    hidden_fraction=hidden_fraction,
                    scenario_progress=float(temporal_context.get('scenario_progress', 0.0)),
                    time_minutes_from_start=float(temporal_context.get('time_minutes_from_start', 0.0)),
                )
            )
        global_values.extend(
            [
                float(relation_counts.get('connected_to', 0)),
                float(relation_counts.get('connected_to', 0)) / bus_denom,
                float(relation_counts.get('constrained_by', 0)),
                float(relation_counts.get('constrained_by', 0)) / bus_denom,
                float(relation_counts.get('generated_from', 0)),
                float(relation_counts.get('derived_under_scenario', 0)),
                float(len(relations)),
                float(len(relations)) / float(entity_count),
            ]
        )
        node_features: dict[str, list[float]] = {}
        for node in sample.node_records:
            bus_entity_id = build_entity_id('Bus', node.node_id)
            bus_entity = entity_map.get(bus_entity_id)
            attributes = bus_entity.attributes if bus_entity is not None else {}
            azimuth_mean = 0.0
            if incident_line_azimuth_counts.get(bus_entity_id, 0) > 0:
                azimuth_mean = incident_line_azimuth_sums[bus_entity_id] / float(incident_line_azimuth_counts[bus_entity_id])
            connected_line_count = float(connected_line_counts.get(bus_entity_id, 0))
            relation_degree = float(relation_degree_counts.get(bus_entity_id, 0))
            node_features[node.node_id] = [
                1.0,
                connected_line_count,
                float(connected_transformer_counts.get(bus_entity_id, 0)),
                float(incident_line_length_sums.get(bus_entity_id, 0.0)),
                float(incident_line_resistance_sums.get(bus_entity_id, 0.0)),
                float(azimuth_mean),
                float(transformer_resistance_sums.get(bus_entity_id, 0.0)),
                float(len(neighbor_bus_sets.get(bus_entity_id, set()))),
                float(bool(attributes.get('grounding_assumed'))),
                float(bool(attributes.get('included_in_solver', True))),
                float(len(assumptions)),
                float(len(quality_flags)),
                float(bool(sample.mask_bundle.observed_mask.get(node.node_id, False))),
                float(bool(sample.mask_bundle.target_mask.get(node.node_id, False))),
                observed_fraction,
                hidden_fraction,
                float(len(assumptions)) / bus_denom,
                float(len(quality_flags)) / bus_denom,
                relation_degree,
                connected_line_count / float(max(1.0, relation_degree)),
                float(constraint_support_counts.get(bus_entity_id, 0)),
                float(constraint_support_counts.get(bus_entity_id, 0)) / float(max(1.0, relation_degree)),
                float(generated_support_counts.get(bus_entity_id, 0)),
                float(generated_support_counts.get(bus_entity_id, 0)) / float(max(1.0, relation_degree)),
            ]
        provenance_global = {
            'kg.global.assumption_count': ['sample.metadata.assumptions'],
            'kg.global.assumption_density_per_bus': ['sample.metadata.assumptions', 'entities:Bus'],
            'kg.global.quality_flag_count': ['sample.metadata.quality_flags'],
            'kg.global.quality_flag_density_per_bus': ['sample.metadata.quality_flags', 'entities:Bus'],
            'kg.global.signal_manifest_available': ['sample.metadata.signal_manifest_path'],
            'kg.global.observed_fraction': ['sample.mask_bundle.metadata.observed_fraction'],
            'kg.global.hidden_fraction': ['sample.mask_bundle.metadata.hidden_fraction'],
            'kg.global.scenario_is_timeseries': ['sample.scenario_id'],
            'kg.global.scenario_is_sweep': ['sample.scenario_id'],
            'kg.global.scenario_sample_count': ['scenario.observation_count'],
            'kg.global.scenario_position': ['observation.time_index'],
            'kg.global.scenario_progress': ['observation.time_index'],
            'kg.global.time_minutes_from_start': ['observation.time_index'],
            'kg.global.bus_count': ['entities:Bus'],
            'kg.global.line_count': ['entities:TransmissionLine'],
            'kg.global.transformer_count': ['entities:Transformer'],
            'kg.global.line_per_bus_ratio': ['entities:TransmissionLine', 'entities:Bus'],
            'kg.global.transformer_per_bus_ratio': ['entities:Transformer', 'entities:Bus'],
            'kg.rel.global.connected_to_count': ['relations:connected_to'],
            'kg.rel.global.connected_to_per_bus': ['relations:connected_to', 'entities:Bus'],
            'kg.rel.global.constrained_by_count': ['relations:constrained_by'],
            'kg.rel.global.constrained_by_per_bus': ['relations:constrained_by', 'entities:Bus'],
            'kg.rel.global.generated_from_count': ['relations:generated_from'],
            'kg.rel.global.derived_under_scenario_count': ['relations:derived_under_scenario'],
            'kg.rel.global.relation_count': ['relations:*'],
            'kg.rel.global.relation_per_entity': ['relations:*', 'entities:*'],
        }
        if include_rule_features:
            provenance_global.update({
                'kg.rule.hit_count': ['rules.graph_rules'],
                'kg.rule.hit_density_per_bus': ['rules.graph_rules', 'entities:Bus'],
                'kg.rule.warning_count': ['rules.graph_rules.severity'],
                'kg.rule.info_count': ['rules.graph_rules.severity'],
                'kg.rule.assumption_present': ['rules.graph_rules.assumption_present'],
                'kg.rule.quality_flags_present': ['rules.graph_rules.quality_flags_present'],
                'kg.rule.signal_context_available': ['rules.graph_rules.signal_context_available'],
                'kg.rule.missing_physics_case': ['rules.graph_rules.missing_physics_case'],
                'kg.rule.assumption_pressure': ['sample.metadata.assumptions', 'entities:Bus'],
                'kg.rule.quality_pressure': ['sample.metadata.quality_flags', 'entities:Bus'],
                'kg.rule.observed_fraction': ['sample.mask_bundle.metadata.observed_fraction'],
                'kg.rule.hidden_fraction': ['sample.mask_bundle.metadata.hidden_fraction'],
                'kg.rule.scenario_progress': ['observation.time_index'],
                'kg.rule.time_minutes_from_start': ['observation.time_index'],
            })
        graph_features[sample.graph_id] = {
            'graph_id': sample.graph_id,
            'sample_id': sample.sample_id,
            'scenario_id': sample.scenario_id,
            'global_feature_names': list(global_feature_names),
            'global_features': global_values,
            'node_feature_names': list(node_feature_names),
            'node_features': node_features,
            'feature_groups': {
                'global': dict(global_group_map),
                'node': dict(node_group_map),
            },
            'provenance': {
                'global': provenance_global,
                'node': {
                    'kg.node.connected_line_count': ['relations:connected_to'],
                    'kg.node.connected_transformer_count': ['relations:connected_to'],
                    'kg.node.grounding_assumed': ['entity.attributes.grounding_assumed'],
                    'kg.node.in_solver': ['entity.attributes.included_in_solver'],
                    'kg.node.sample_assumption_count': ['sample.metadata.assumptions'],
                    'kg.node.sample_quality_flag_count': ['sample.metadata.quality_flags'],
                    'kg.node.is_observed': ['sample.mask_bundle.observed_mask'],
                    'kg.node.is_target': ['sample.mask_bundle.target_mask'],
                    'kg.node.sample_observed_fraction': ['sample.mask_bundle.metadata.observed_fraction'],
                    'kg.node.sample_hidden_fraction': ['sample.mask_bundle.metadata.hidden_fraction'],
                    'kg.node.assumption_pressure': ['sample.metadata.assumptions', 'entities:Bus'],
                    'kg.node.quality_pressure': ['sample.metadata.quality_flags', 'entities:Bus'],
                    'kg.node.incident_line_length_km_sum': ['entity.attributes.length_km'],
                    'kg.node.incident_line_resistance_ohm_sum': ['entity.attributes.resistance_ohm'],
                    'kg.node.incident_line_azimuth_abs_mean': ['entity.attributes.azimuth_deg'],
                    'kg.node.transformer_resistance_sum': ['entity.attributes.effective_resistance_ohm'],
                    'kg.node.neighbor_bus_count': ['relations:connected_to', 'entity.attributes.from_bus', 'entity.attributes.to_bus'],
                    'kg.rel.node.relation_degree': ['relations:*'],
                    'kg.rel.node.connected_to_ratio': ['relations:connected_to', 'relations:*'],
                    'kg.rel.node.constraint_support_count': ['relations:constrained_by', 'relations:connected_to'],
                    'kg.rel.node.constraint_support_ratio': ['relations:constrained_by', 'relations:*'],
                    'kg.rel.node.generated_support_count': ['relations:generated_from', 'relations:connected_to'],
                    'kg.rel.node.generated_support_ratio': ['relations:generated_from', 'relations:*'],
                },
            },
        }
    return {
        'dataset_name': graph_samples[0].metadata.get('source_case_id', 'unknown') if graph_samples else 'unknown',
        'graph_count': len(graph_features),
        'global_feature_names': list(global_feature_names),
        'node_feature_names': list(node_feature_names),
        'feature_groups': {
            'global': dict(global_group_map),
            'node': dict(node_group_map),
        },
        'graph_features': graph_features,
    }
