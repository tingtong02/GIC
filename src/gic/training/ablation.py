from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gic.config import load_config
from gic.eval.comparison_reports import compare_with_phase4_report, hidden_mae_from_metrics
from gic.training.main_loops import evaluate_main_model, train_main_model
from gic.utils.paths import ensure_directory


def _clone_config(config: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(config))


def _variant_summary(variant_name: str, config_path: str, evaluation: dict[str, Any]) -> dict[str, Any]:
    return {
        'variant_name': variant_name,
        'config_path': config_path,
        'metrics': evaluation['metrics'],
        'hotspot_metrics': evaluation['hotspot_metrics'],
        'hidden_mae': hidden_mae_from_metrics(evaluation['metrics']),
    }


def _resolve_variant_config_path(config_path_text: str, *, base_config_path: str | Path, project_root: str | Path | None) -> Path:
    requested = Path(config_path_text)
    candidates: list[Path] = []
    if requested.is_absolute():
        candidates.append(requested)
    else:
        candidates.append((Path(base_config_path).resolve().parent / requested).resolve())
        if project_root is not None:
            project_root_path = Path(project_root).resolve()
            candidates.append((project_root_path / requested).resolve())
            candidates.append((project_root_path / 'configs' / 'phase5' / requested).resolve())
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def run_phase5_ablation_suite(
    *,
    base_config: dict[str, Any],
    base_config_path: str | Path,
    dataset_path: str | Path,
    output_root: str | Path,
    compare_split: str = 'test',
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    ablation_cfg = dict(base_config.get('ablation', {}))
    variants = ablation_cfg.get('variants', [])
    if not isinstance(variants, list) or not variants:
        raise ValueError('Phase 5 config requires ablation.variants')
    phase4_report_path = ablation_cfg.get('phase4_report_path') or base_config.get('graph', {}).get('phase4_report_path')
    if not isinstance(phase4_report_path, str) or not phase4_report_path:
        raise ValueError('Phase 5 ablation requires phase4_report_path')
    training_epochs = int(ablation_cfg.get('training_epochs', base_config.get('training', {}).get('epochs', 40)))
    rows: list[dict[str, Any]] = []
    full_runs: list[dict[str, Any]] = []
    for item in variants:
        if not isinstance(item, dict):
            raise ValueError(f'Invalid ablation variant entry: {item}')
        variant_name = str(item.get('name', '')).strip()
        config_path_text = str(item.get('config_path', '')).strip()
        if not variant_name or not config_path_text:
            raise ValueError(f'Invalid ablation variant entry: {item}')
        variant_config_path = _resolve_variant_config_path(
            config_path_text,
            base_config_path=base_config_path,
            project_root=project_root,
        )
        variant_config = load_config(variant_config_path)
        variant_config = _clone_config(variant_config)
        variant_config.setdefault('training', {})['epochs'] = training_epochs
        variant_root = ensure_directory(Path(output_root) / variant_name)
        train_result = train_main_model(config=variant_config, dataset_path=dataset_path, output_dir=variant_root)
        evaluation = evaluate_main_model(
            config=variant_config,
            dataset_path=dataset_path,
            checkpoint_path=train_result.checkpoint_path,
            split=compare_split,
        )
        comparison = compare_with_phase4_report(evaluation['metrics'], phase4_report_path)
        row = _variant_summary(variant_name, str(variant_config_path), evaluation)
        rows.append(row)
        full_runs.append(
            {
                'variant_name': variant_name,
                'config_path': str(variant_config_path),
                'checkpoint_path': train_result.checkpoint_path,
                'history_path': train_result.history_path,
                'metrics': evaluation['metrics'],
                'hotspot_metrics': evaluation['hotspot_metrics'],
                'comparison_with_phase4': comparison,
            }
        )
    rows.sort(key=lambda item: (float(item['hidden_mae']), str(item['variant_name'])))
    default_run = next((item for item in full_runs if item['variant_name'] == 'main_model_default'), full_runs[0] if full_runs else None)
    comparison = compare_with_phase4_report(default_run['metrics'], phase4_report_path) if default_run is not None else {}
    return {
        'compare_split': compare_split,
        'phase4_report_path': phase4_report_path,
        'default_run': default_run,
        'ablations': rows,
        'runs': full_runs,
        'comparison_with_phase4': comparison,
    }
