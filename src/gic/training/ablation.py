from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

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


def _resolve_variant_config_path(
    config_path_text: str,
    *,
    base_config_path: str | Path,
    project_root: str | Path | None,
    phase_subdirs: tuple[str, ...] = ('phase5',),
) -> Path:
    requested = Path(config_path_text)
    candidates: list[Path] = []
    if requested.is_absolute():
        candidates.append(requested)
    else:
        base_config_dir = Path(base_config_path).resolve().parent
        candidates.append((base_config_dir / requested).resolve())
        if project_root is not None:
            project_root_path = Path(project_root).resolve()
            candidates.append((project_root_path / requested).resolve())
            for phase_subdir in phase_subdirs:
                candidates.append((project_root_path / 'configs' / phase_subdir / requested).resolve())
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _phase5_control_summary(report_path: str | Path | None) -> dict[str, Any] | None:
    if not report_path:
        return None
    path = Path(report_path).resolve()
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding='utf-8'))
    metrics = dict(payload.get('default_run', {}).get('metrics', {}))
    return {
        'report_path': str(path),
        'hidden_mae': hidden_mae_from_metrics(metrics) if metrics else None,
        'metrics': metrics,
    }


def _surface_specs_from_config(config: dict[str, Any], *, project_root: str | Path | None) -> list[dict[str, str]]:
    evaluation_cfg = dict(config.get('evaluation', {}))
    payload: dict[str, Any] = {}
    config_path_text = str(evaluation_cfg.get('multi_surface_config_path', '')).strip()
    if config_path_text:
        resolved = Path(config_path_text)
        if not resolved.is_absolute() and project_root is not None:
            resolved = (Path(project_root).resolve() / config_path_text).resolve()
        text = resolved.read_text(encoding='utf-8')
        if yaml is not None:
            parsed = yaml.safe_load(text) or {}
        else:
            parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError(f'Invalid multi-surface payload: {resolved}')
        payload = parsed
    else:
        payload = dict(evaluation_cfg.get('multi_surface', {}))
    surfaces = payload.get('surfaces', []) if isinstance(payload, dict) else []
    resolved_specs: list[dict[str, str]] = []
    for item in surfaces:
        if not isinstance(item, dict):
            continue
        name = str(item.get('name', '')).strip()
        dataset_path = str(item.get('dataset_path', '')).strip()
        if not name or not dataset_path:
            continue
        resolved_dataset_path = Path(dataset_path)
        if not resolved_dataset_path.is_absolute() and project_root is not None:
            resolved_dataset_path = (Path(project_root).resolve() / dataset_path).resolve()
        resolved_specs.append({'name': name, 'dataset_path': str(resolved_dataset_path)})
    return resolved_specs


def evaluate_phase6_surface_runs(
    *,
    base_config: dict[str, Any],
    runs: list[dict[str, Any]],
    compare_split: str,
    project_root: str | Path | None,
) -> dict[str, Any]:
    surface_specs = _surface_specs_from_config(base_config, project_root=project_root)
    if not surface_specs:
        return {}
    results: dict[str, Any] = {}
    for run in runs:
        variant_name = str(run.get('variant_name', ''))
        config_path = str(run.get('config_path', ''))
        checkpoint_path = str(run.get('checkpoint_path', ''))
        if not variant_name or not config_path or not checkpoint_path:
            continue
        variant_config = load_config(config_path)
        variant_results: dict[str, Any] = {}
        for surface in surface_specs:
            evaluation = evaluate_main_model(
                config=variant_config,
                dataset_path=surface['dataset_path'],
                checkpoint_path=checkpoint_path,
                split=compare_split,
                project_root=project_root,
            )
            variant_results[surface['name']] = {
                'dataset_path': surface['dataset_path'],
                'hidden_mae': hidden_mae_from_metrics(evaluation['metrics']),
                'overall_mae': float(evaluation['metrics'].get('overall', {}).get('mae', 0.0)),
                'metrics': evaluation['metrics'],
                'kg_summary': evaluation.get('kg_summary', {}),
            }
        results[variant_name] = variant_results
    return results


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
            phase_subdirs=('phase5',),
        )
        variant_config = load_config(variant_config_path)
        variant_config = _clone_config(variant_config)
        variant_config.setdefault('training', {})['epochs'] = training_epochs
        variant_root = ensure_directory(Path(output_root) / variant_name)
        train_result = train_main_model(config=variant_config, dataset_path=dataset_path, output_dir=variant_root, project_root=project_root)
        evaluation = evaluate_main_model(
            config=variant_config,
            dataset_path=dataset_path,
            checkpoint_path=train_result.checkpoint_path,
            split=compare_split,
            project_root=project_root,
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
                'feature_summary': evaluation['feature_summary'],
                'signal_summary': evaluation['signal_summary'],
                'kg_summary': evaluation.get('kg_summary', {}),
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


def run_phase6_ablation_suite(
    *,
    base_config: dict[str, Any],
    base_config_path: str | Path,
    dataset_path: str | Path,
    output_root: str | Path,
    compare_split: str = 'test',
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    ablation_cfg = dict(base_config.get('ablation', {}))
    evaluation_cfg = dict(base_config.get('evaluation', {}))
    variants = ablation_cfg.get('variants', [])
    if not isinstance(variants, list) or not variants:
        raise ValueError('Phase 6 config requires ablation.variants')
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
            phase_subdirs=('phase6', 'phase5'),
        )
        variant_config = load_config(variant_config_path)
        variant_config = _clone_config(variant_config)
        variant_config.setdefault('training', {})['epochs'] = training_epochs
        variant_root = ensure_directory(Path(output_root) / variant_name)
        train_result = train_main_model(config=variant_config, dataset_path=dataset_path, output_dir=variant_root, project_root=project_root)
        evaluation = evaluate_main_model(
            config=variant_config,
            dataset_path=dataset_path,
            checkpoint_path=train_result.checkpoint_path,
            split=compare_split,
            project_root=project_root,
        )
        row = _variant_summary(variant_name, str(variant_config_path), evaluation)
        row['overall_mae'] = float(evaluation['metrics'].get('overall', {}).get('mae', 0.0))
        row['kg_enabled'] = bool(evaluation.get('kg_summary', {}).get('enabled', False))
        row['kg_rule_feature_count'] = int(evaluation.get('kg_summary', {}).get('rule_feature_count', 0))
        row['relation_feature_count'] = int(evaluation.get('kg_summary', {}).get('active_relation_global_feature_count', 0)) + int(evaluation.get('kg_summary', {}).get('active_relation_node_feature_count', 0))
        rows.append(row)
        full_runs.append(
            {
                'variant_name': variant_name,
                'config_path': str(variant_config_path),
                'checkpoint_path': train_result.checkpoint_path,
                'history_path': train_result.history_path,
                'metrics': evaluation['metrics'],
                'hotspot_metrics': evaluation['hotspot_metrics'],
                'feature_summary': evaluation['feature_summary'],
                'signal_summary': evaluation['signal_summary'],
                'kg_summary': evaluation.get('kg_summary', {}),
                'dataset_summary': evaluation['dataset_summary'],
            }
        )
    rows.sort(key=lambda item: (float(item['hidden_mae']), str(item['variant_name'])))
    runs_by_name = {item['variant_name']: item for item in full_runs}
    no_kg_run = runs_by_name.get('no_kg') or (full_runs[0] if full_runs else None)
    best_run = next((item for item in full_runs if item['variant_name'] == rows[0]['variant_name']), None) if rows else None
    recommended_variant = 'no_kg'
    if no_kg_run is not None and best_run is not None:
        if hidden_mae_from_metrics(best_run['metrics']) < hidden_mae_from_metrics(no_kg_run['metrics']):
            recommended_variant = str(best_run['variant_name'])
    phase5_control = _phase5_control_summary(
        str(evaluation_cfg.get('phase5_report_path', '')) if evaluation_cfg.get('compare_with_phase5_default', False) else None
    )
    return {
        'compare_split': compare_split,
        'phase5_control': phase5_control,
        'default_run': runs_by_name.get('kg_default', best_run),
        'no_kg_run': no_kg_run,
        'best_run': best_run,
        'recommended_variant': recommended_variant,
        'ablations': rows,
        'runs': full_runs,
    }
