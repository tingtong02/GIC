from __future__ import annotations

from typing import Any


def _hidden_mae(run: dict[str, Any] | None) -> float | None:
    if not run:
        return None
    metrics = dict(run.get('metrics', {}))
    hidden_only = dict(metrics.get('hidden_only', {}))
    overall = dict(metrics.get('overall', {}))
    if metrics.get('hidden_row_count', 0):
        return float(hidden_only.get('mae', 0.0))
    if overall:
        return float(overall.get('mae', 0.0))
    return None


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
    ablation_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
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
    if ablation_payload is not None:
        no_kg_run = ablation_payload.get('no_kg_run')
        best_run = ablation_payload.get('best_run')
        payload['model_comparison'] = {
            'compare_split': ablation_payload.get('compare_split', 'test'),
            'phase5_control': ablation_payload.get('phase5_control'),
            'recommended_variant': ablation_payload.get('recommended_variant'),
            'best_variant': best_run.get('variant_name') if isinstance(best_run, dict) else None,
            'best_hidden_mae': _hidden_mae(best_run),
            'no_kg_hidden_mae': _hidden_mae(no_kg_run),
            'kg_beats_no_kg': (
                _hidden_mae(best_run) is not None
                and _hidden_mae(no_kg_run) is not None
                and float(_hidden_mae(best_run)) < float(_hidden_mae(no_kg_run))
            ),
            'ablations': [
                {
                    'variant_name': row.get('variant_name'),
                    'hidden_mae': row.get('hidden_mae'),
                    'overall_mae': row.get('overall_mae'),
                    'kg_enabled': row.get('kg_enabled'),
                    'kg_rule_feature_count': row.get('kg_rule_feature_count', 0),
                }
                for row in ablation_payload.get('ablations', [])
            ],
        }
    return payload


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
    model_comparison = payload.get('model_comparison')
    if isinstance(model_comparison, dict):
        lines.extend(['', '## Model Comparison'])
        lines.append(f"- compare split: `{model_comparison.get('compare_split', '')}`")
        lines.append(f"- recommended variant: `{model_comparison.get('recommended_variant', '')}`")
        lines.append(f"- best variant: `{model_comparison.get('best_variant', '')}`")
        lines.append(f"- best hidden MAE: `{model_comparison.get('best_hidden_mae', '')}`")
        lines.append(f"- no KG hidden MAE: `{model_comparison.get('no_kg_hidden_mae', '')}`")
        lines.append(f"- KG beats no KG: `{model_comparison.get('kg_beats_no_kg', False)}`")
        phase5_control = model_comparison.get('phase5_control')
        if isinstance(phase5_control, dict):
            lines.append(f"- frozen phase5 hidden MAE: `{phase5_control.get('hidden_mae', '')}`")
        lines.extend(['', '## KG Ablations'])
        for row in model_comparison.get('ablations', []):
            lines.append(
                f"- `{row['variant_name']}`: hidden MAE `{row['hidden_mae']}`, overall MAE `{row['overall_mae']}`, "
                f"kg enabled `{row['kg_enabled']}`, rule features `{row['kg_rule_feature_count']}`"
            )
    lines.extend(['', '## Query Examples'])
    for example in payload['query_examples']:
        lines.append(
            f"- `{example['graph_id']}` -> scenario `{example['scenario_id']}` with `{len(example['rule_findings'])}` rule findings"
        )
    return '\n'.join(lines)
