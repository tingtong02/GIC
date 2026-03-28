from __future__ import annotations

from typing import Any

from gic.kg.schema import build_entity_id


def query_sample(
    *,
    identifier: str,
    sample_index: dict[str, dict[str, Any]],
    feature_payload: dict[str, Any],
    rule_payload: dict[str, Any],
) -> dict[str, Any]:
    key = identifier
    summary = sample_index.get(key)
    if summary is None:
        for item in sample_index.values():
            if item.get('sample_id') == identifier:
                summary = item
                key = str(item['graph_id'])
                break
    if summary is None:
        raise KeyError(f'Unknown graph_id or sample_id: {identifier}')
    graph_features = feature_payload['graph_features'].get(key, {})
    node_summaries = []
    node_feature_names = graph_features.get('node_feature_names', [])
    for node_id, values in list(graph_features.get('node_features', {}).items())[:3]:
        node_summaries.append(
            {
                'node_id': node_id,
                'entity_id': build_entity_id('Bus', node_id),
                'features': {name: values[index] for index, name in enumerate(node_feature_names)},
            }
        )
    return {
        'graph_id': key,
        'sample_id': summary.get('sample_id'),
        'scenario_id': summary.get('scenario_id'),
        'time_index': summary.get('time_index'),
        'source_case_id': summary.get('source_case_id'),
        'quality_flags': summary.get('quality_flags', []),
        'assumptions': summary.get('assumptions', []),
        'signal_manifest_path': summary.get('signal_manifest_path'),
        'global_features': {
            name: graph_features.get('global_features', [])[index]
            for index, name in enumerate(graph_features.get('global_feature_names', []))
        },
        'rule_findings': rule_payload.get('graph_rules', {}).get(key, []),
        'node_summaries': node_summaries,
    }
