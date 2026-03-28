from __future__ import annotations

from typing import Any


def build_kg_report_payload(
    *,
    dataset_name: str,
    dataset_path: str,
    manifest: dict[str, Any],
    validation: dict[str, Any],
    feature_payload: dict[str, Any],
    rule_payload: dict[str, Any],
    query_examples: list[dict[str, Any]],
    phase5_report_path: str | None,
) -> dict[str, Any]:
    return {
        'dataset_name': dataset_name,
        'dataset_path': dataset_path,
        'manifest': manifest,
        'validation': validation,
        'feature_summary': {
            'graph_count': feature_payload.get('graph_count', 0),
            'global_feature_count': len(feature_payload.get('global_feature_names', [])),
            'node_feature_count': len(feature_payload.get('node_feature_names', [])),
        },
        'rule_summary': {
            'graph_count': rule_payload.get('graph_count', 0),
            'rule_counts': rule_payload.get('rule_counts', {}),
        },
        'query_examples': query_examples,
        'phase5_control_report_path': phase5_report_path,
    }


def build_kg_report_markdown(payload: dict[str, Any]) -> str:
    manifest = payload['manifest']
    feature_summary = payload['feature_summary']
    rule_summary = payload['rule_summary']
    lines = [
        '# Phase 6 KG Report',
        '',
        f"- dataset: `{payload['dataset_name']}`",
        f"- entity count: `{manifest['entity_count']}`",
        f"- relation count: `{manifest['relation_count']}`",
        f"- global feature count: `{feature_summary['global_feature_count']}`",
        f"- node feature count: `{feature_summary['node_feature_count']}`",
        f"- rule graph count: `{rule_summary['graph_count']}`",
        f"- phase5 control report: `{payload['phase5_control_report_path'] or ''}`",
        '',
        '## Entity Types',
    ]
    for key, value in sorted(payload['validation']['entity_counts'].items()):
        lines.append(f'- `{key}`: `{value}`')
    lines.extend(['', '## Relation Types'])
    for key, value in sorted(payload['validation']['relation_counts'].items()):
        lines.append(f'- `{key}`: `{value}`')
    lines.extend(['', '## Rule Counts'])
    for key, value in sorted(rule_summary['rule_counts'].items()):
        lines.append(f'- `{key}`: `{value}`')
    lines.extend(['', '## Query Examples'])
    for example in payload['query_examples']:
        lines.append(
            f"- `{example['graph_id']}` -> scenario `{example['scenario_id']}` with `{len(example['rule_findings'])}` rule findings"
        )
    return '\n'.join(lines)
