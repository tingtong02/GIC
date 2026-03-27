from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def hidden_mae_from_metrics(metrics: dict[str, Any]) -> float:
    hidden_only = metrics.get('hidden_only', {})
    if int(metrics.get('hidden_row_count', 0)) > 0:
        return float(hidden_only.get('mae', metrics.get('overall', {}).get('mae', float('inf'))))
    return float(metrics.get('overall', {}).get('mae', float('inf')))


def compare_with_phase4_report(phase5_metrics: dict[str, Any], phase4_report_path: str | Path) -> dict[str, Any]:
    report_path = Path(phase4_report_path).resolve()
    payload = json.loads(report_path.read_text(encoding='utf-8'))
    comparison = payload.get('comparison', {})
    ranked_rows = comparison.get('rows', [])
    best_row = ranked_rows[0] if ranked_rows else {}
    default_graph_baseline = comparison.get('default_graph_baseline', '')
    default_graph_row = next((row for row in ranked_rows if str(row.get('model_type')) == str(default_graph_baseline)), {})
    phase5_hidden_mae = hidden_mae_from_metrics(phase5_metrics)
    phase4_best_hidden_mae = hidden_mae_from_metrics(best_row.get('metrics', {})) if best_row else float('inf')
    phase4_graph_hidden_mae = hidden_mae_from_metrics(default_graph_row.get('metrics', {})) if default_graph_row else float('inf')
    return {
        'phase4_report_path': str(report_path),
        'phase4_best_model': str(best_row.get('model_type', '')),
        'phase4_best_hidden_mae': phase4_best_hidden_mae,
        'phase4_default_graph_model': str(default_graph_baseline),
        'phase4_default_graph_hidden_mae': phase4_graph_hidden_mae,
        'phase5_hidden_mae': phase5_hidden_mae,
        'hidden_mae_gain_vs_phase4_best': phase4_best_hidden_mae - phase5_hidden_mae,
        'hidden_mae_gain_vs_phase4_graph': phase4_graph_hidden_mae - phase5_hidden_mae,
        'phase5_beats_phase4_best': phase5_hidden_mae < phase4_best_hidden_mae,
        'phase5_beats_phase4_graph': phase5_hidden_mae < phase4_graph_hidden_mae,
    }


def build_phase5_report_markdown(report: dict[str, Any]) -> str:
    comparison = report.get('comparison_with_phase4', {})
    lines = [
        '# Phase 5 Main Model Report',
        '',
        '## Default Main Model',
        f"- Dataset: `{report.get('dataset_name', '')}`",
        f"- Split: `{report.get('compare_split', 'test')}`",
        f"- Default config: `{report.get('default_config_path', '')}`",
        f"- Main hidden-node MAE: `{hidden_mae_from_metrics(report.get('default_run', {}).get('metrics', {})):.6f}`",
        f"- Main hotspot F1: `{float(report.get('default_run', {}).get('hotspot_metrics', {}).get('f1', 0.0)):.6f}`",
    ]
    if comparison:
        lines.extend(
            [
                '',
                '## Comparison With Phase 4',
                f"- Phase 4 best model: `{comparison.get('phase4_best_model', '')}`",
                f"- Phase 4 best hidden-node MAE: `{float(comparison.get('phase4_best_hidden_mae', 0.0)):.6f}`",
                f"- Hidden-node MAE gain vs Phase 4 best: `{float(comparison.get('hidden_mae_gain_vs_phase4_best', 0.0)):.6f}`",
                f"- Phase 5 beats Phase 4 best: `{bool(comparison.get('phase5_beats_phase4_best', False))}`",
                f"- Phase 5 beats Phase 4 default graph baseline: `{bool(comparison.get('phase5_beats_phase4_graph', False))}`",
            ]
        )
    lines.extend(['', '## Ablations'])
    for row in report.get('ablations', []):
        lines.append(
            f"- `{row['variant_name']}`: hidden_mae={float(row['metrics']['hidden_only']['mae'] if row['metrics'].get('hidden_row_count', 0) > 0 else row['metrics']['overall']['mae']):.6f}, hotspot_f1={float(row['hotspot_metrics'].get('f1', 0.0)):.6f}"
        )
    lines.extend(['', '## Acceptance Note'])
    if comparison.get('phase5_beats_phase4_best', False):
        lines.append('- The current Phase 5 default main model outperforms the Phase 4 best baseline on hidden-node MAE for the default comparison split.')
    else:
        lines.append('- The current Phase 5 default main model does not yet outperform the Phase 4 best baseline on hidden-node MAE for the default comparison split.')
    lines.append('- Phase 5 engineering scope is only considered complete together with training, evaluation, ablation, configuration, tests, and documentation coverage.')
    return '\n'.join(lines) + '\n'
