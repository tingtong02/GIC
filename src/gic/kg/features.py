from __future__ import annotations

from collections import defaultdict
from typing import Any

from gic.graph.datasets import GraphSample
from gic.kg.schema import KGEntity, KGRelation, build_entity_id


GLOBAL_FEATURE_NAMES = [
    'kg.global.assumption_count',
    'kg.global.quality_flag_count',
    'kg.global.signal_manifest_available',
    'kg.global.scenario_is_timeseries',
    'kg.global.scenario_is_sweep',
    'kg.global.bus_count',
    'kg.global.line_count',
    'kg.global.transformer_count',
    'kg.global.rule_hit_count',
]
NODE_FEATURE_NAMES = [
    'kg.node.is_bus',
    'kg.node.connected_line_count',
    'kg.node.connected_transformer_count',
    'kg.node.grounding_assumed',
    'kg.node.in_solver',
    'kg.node.sample_assumption_count',
    'kg.node.sample_quality_flag_count',
]


def derive_feature_payload(
    *,
    entities: list[KGEntity],
    relations: list[KGRelation],
    graph_samples: list[GraphSample],
    rule_payload: dict[str, Any],
) -> dict[str, Any]:
    entity_map = {entity.entity_id: entity for entity in entities}
    connected_line_counts: defaultdict[str, int] = defaultdict(int)
    connected_transformer_counts: defaultdict[str, int] = defaultdict(int)
    for relation in relations:
        if relation.relation_type != 'connected_to':
            continue
        head_entity = entity_map.get(relation.head_entity_id)
        if head_entity is None:
            continue
        if head_entity.entity_type == 'TransmissionLine':
            connected_line_counts[relation.tail_entity_id] += 1
        if head_entity.entity_type == 'Transformer':
            connected_transformer_counts[relation.tail_entity_id] += 1
    bus_entities = [entity for entity in entities if entity.entity_type == 'Bus']
    line_entities = [entity for entity in entities if entity.entity_type == 'TransmissionLine']
    transformer_entities = [entity for entity in entities if entity.entity_type == 'Transformer']
    graph_features: dict[str, Any] = {}
    for sample in graph_samples:
        assumptions = [str(item) for item in sample.metadata.get('assumptions', [])]
        quality_flags = [str(item) for item in sample.metadata.get('quality_flags', [])]
        global_values = [
            float(len(assumptions)),
            float(len(quality_flags)),
            float(bool(sample.metadata.get('signal_manifest_path'))),
            float(str(sample.scenario_id).startswith('timeseries')),
            float(str(sample.scenario_id).startswith('sweep')),
            float(len(bus_entities)),
            float(len(line_entities)),
            float(len(transformer_entities)),
            float(len(rule_payload.get('graph_rules', {}).get(sample.graph_id, []))),
        ]
        node_features: dict[str, list[float]] = {}
        for node in sample.node_records:
            bus_entity_id = build_entity_id('Bus', node.node_id)
            bus_entity = entity_map.get(bus_entity_id)
            attributes = bus_entity.attributes if bus_entity is not None else {}
            node_features[node.node_id] = [
                1.0,
                float(connected_line_counts.get(bus_entity_id, 0)),
                float(connected_transformer_counts.get(bus_entity_id, 0)),
                float(bool(attributes.get('grounding_assumed'))),
                float(bool(attributes.get('included_in_solver', True))),
                float(len(assumptions)),
                float(len(quality_flags)),
            ]
        graph_features[sample.graph_id] = {
            'graph_id': sample.graph_id,
            'sample_id': sample.sample_id,
            'scenario_id': sample.scenario_id,
            'global_feature_names': list(GLOBAL_FEATURE_NAMES),
            'global_features': global_values,
            'node_feature_names': list(NODE_FEATURE_NAMES),
            'node_features': node_features,
            'provenance': {
                'global': {
                    'kg.global.assumption_count': ['sample.metadata.assumptions'],
                    'kg.global.quality_flag_count': ['sample.metadata.quality_flags'],
                    'kg.global.signal_manifest_available': ['sample.metadata.signal_manifest_path'],
                    'kg.global.scenario_is_timeseries': ['sample.scenario_id'],
                    'kg.global.scenario_is_sweep': ['sample.scenario_id'],
                    'kg.global.bus_count': ['entities:Bus'],
                    'kg.global.line_count': ['entities:TransmissionLine'],
                    'kg.global.transformer_count': ['entities:Transformer'],
                    'kg.global.rule_hit_count': ['rules.graph_rules'],
                },
                'node': {
                    'kg.node.connected_line_count': ['relations:connected_to'],
                    'kg.node.connected_transformer_count': ['relations:connected_to'],
                    'kg.node.grounding_assumed': ['entity.attributes.grounding_assumed'],
                    'kg.node.in_solver': ['entity.attributes.included_in_solver'],
                    'kg.node.sample_assumption_count': ['sample.metadata.assumptions'],
                    'kg.node.sample_quality_flag_count': ['sample.metadata.quality_flags'],
                },
            },
        }
    return {
        'dataset_name': graph_samples[0].metadata.get('source_case_id', 'unknown') if graph_samples else 'unknown',
        'graph_count': len(graph_features),
        'global_feature_names': list(GLOBAL_FEATURE_NAMES),
        'node_feature_names': list(NODE_FEATURE_NAMES),
        'graph_features': graph_features,
    }
