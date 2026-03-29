from __future__ import annotations

from pathlib import Path
from typing import Any


def _resolve_path(project_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (project_root / path).resolve()


def _mean(values: list[float]) -> float | None:
    return float(sum(values) / len(values)) if values else None


def collect_final_versions(project_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    final_cfg = dict(config.get('final', {}))
    assets_cfg = dict(final_cfg.get('assets', {}))
    freeze_cfg = dict(final_cfg.get('freeze', {}))
    resolved_assets = {key: str(_resolve_path(project_root, value)) for key, value in assets_cfg.items()}
    return {
        'freeze': freeze_cfg,
        'assets': resolved_assets,
        'default_variant': str(final_cfg.get('default_variant', 'without_kg')),
    }


def _real_model_summary(rows: list[dict[str, Any]], model_id: str) -> dict[str, Any]:
    selected = [row for row in rows if str(row.get('model_id')) == model_id]
    maes = [float(row['proxy_hidden_mae']) for row in selected if row.get('proxy_hidden_mae') is not None]
    trends = [float(row['trend_correlation']) for row in selected if row.get('trend_correlation') is not None]
    peaks = [float(row['peak_timing_error_minutes']) for row in selected if row.get('peak_timing_error_minutes') is not None]
    return {
        'row_count': len(selected),
        'mean_proxy_hidden_mae': _mean(maes),
        'mean_trend_correlation': _mean(trends),
        'mean_peak_timing_error_minutes': _mean(peaks),
    }


def build_final_report_payload(
    project_root: Path,
    config: dict[str, Any],
    *,
    active_variant: str,
    phase5_report: dict[str, Any],
    phase6_report: dict[str, Any],
    phase7_report: dict[str, Any],
    active_eval: dict[str, Any] | None = None,
) -> dict[str, Any]:
    versions = collect_final_versions(project_root, config)
    phase5_hidden = float(phase5_report.get('comparison_with_phase4', {}).get('phase5_hidden_mae', 0.0))
    phase4_graph_hidden = float(phase5_report.get('comparison_with_phase4', {}).get('phase4_default_graph_hidden_mae', 0.0))
    phase4_best_hidden = float(phase5_report.get('comparison_with_phase4', {}).get('phase4_best_hidden_mae', 0.0))
    phase6_hidden = float(phase6_report.get('best_run', {}).get('metrics', {}).get('hidden_only', {}).get('mae', 0.0))
    phase7_rows = list(phase7_report.get('evaluation', {}).get('rows', []))
    model_ids = ['phase4_best_graph', 'phase5_default', 'phase6_feature_only']
    real_summary = {model_id: _real_model_summary(phase7_rows, model_id) for model_id in model_ids}
    kg_in_default = active_variant == 'with_kg'
    default_model_id = 'phase6_feature_only' if kg_in_default else 'phase5_default'
    return {
        'default_variant': active_variant,
        'kg_in_default': kg_in_default,
        'default_model_id': default_model_id,
        'phase7_default_promotion_decision': str(phase7_report.get('default_promotion_decision', '')),
        'frozen_versions': versions,
        'synthetic_summary': {
            'dataset_name': str(phase5_report.get('dataset_name', '')),
            'phase4_best_hidden_mae': phase4_best_hidden,
            'phase4_graph_hidden_mae': phase4_graph_hidden,
            'phase5_default_hidden_mae': phase5_hidden,
            'phase6_feature_only_hidden_mae': phase6_hidden,
        },
        'real_event_summary': {
            'event_asset_count': int(phase7_report.get('event_asset_count', 0)),
            'result_row_count': int(phase7_report.get('result_row_count', 0)),
            'decision': str(phase7_report.get('default_promotion_decision', '')),
            'model_summary': real_summary,
            'evidence_summary': dict(phase7_report.get('evidence_summary', {})),
        },
        'phase5_report_path': versions['assets']['phase5_report_path'],
        'phase6_report_path': versions['assets']['phase6_report_path'],
        'phase7_report_path': versions['assets']['phase7_report_path'],
        'active_eval': active_eval or {},
        'limitations': [
            'Final default remains evidence-bounded and is not a production deployment claim.',
            'Real-event validation still relies on station-local disturbance references rather than full-network truth.',
            'KG remains available as an optional final variant even when it is not promoted to the default path.',
        ],
    }


def build_final_report_markdown(report: dict[str, Any]) -> str:
    synthetic = dict(report.get('synthetic_summary', {}))
    real_event = dict(report.get('real_event_summary', {}))
    model_summary = dict(real_event.get('model_summary', {}))
    lines = [
        '# Final System Summary',
        '',
        '## Default Path',
        f"- Default variant: `{report.get('default_variant', '')}`",
        f"- KG in default: `{bool(report.get('kg_in_default', False))}`",
        f"- Default model id: `{report.get('default_model_id', '')}`",
        f"- Phase 7 promotion decision: `{report.get('phase7_default_promotion_decision', '')}`",
        '',
        '## Synthetic Benchmark Summary',
        f"- Dataset: `{synthetic.get('dataset_name', '')}`",
        f"- Phase 4 best hidden-node MAE: `{float(synthetic.get('phase4_best_hidden_mae', 0.0)):.6f}`",
        f"- Phase 4 graph hidden-node MAE: `{float(synthetic.get('phase4_graph_hidden_mae', 0.0)):.6f}`",
        f"- Phase 5 default hidden-node MAE: `{float(synthetic.get('phase5_default_hidden_mae', 0.0)):.6f}`",
        f"- Phase 6 feature_only hidden-node MAE: `{float(synthetic.get('phase6_feature_only_hidden_mae', 0.0)):.6f}`",
        '',
        '## Real Event Summary',
        f"- Event assets: `{int(real_event.get('event_asset_count', 0))}`",
        f"- Evaluation rows: `{int(real_event.get('result_row_count', 0))}`",
        f"- Decision: `{real_event.get('decision', '')}`",
    ]
    for model_id, metrics in model_summary.items():
        lines.append(
            f"- {model_id}: mean proxy hidden MAE `{float(metrics.get('mean_proxy_hidden_mae') or 0.0):.6f}`, "
            f"mean trend correlation `{float(metrics.get('mean_trend_correlation') or 0.0):.6f}`"
        )
    lines.extend(['', '## Limitations'])
    for line in report.get('limitations', []):
        lines.append(f'- {line}')
    return '\n'.join(lines).rstrip() + '\n'
