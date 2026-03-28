from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gic.config import load_config
from gic.eval import hidden_mae_from_metrics
from gic.training import evaluate_main_model, evaluate_phase6_surface_runs, train_main_model


def _clone_config(config: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(config))


def _resolve_config_path(config_path_text: str, *, base_config_path: Path, project_root: Path) -> Path:
    requested = Path(config_path_text)
    candidates: list[Path] = []
    if requested.is_absolute():
        candidates.append(requested)
    else:
        candidates.append((base_config_path.parent / requested).resolve())
        candidates.append((project_root / requested).resolve())
        candidates.append((project_root / 'configs' / 'phase6' / requested).resolve())
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _dataset_path_from_config(config: dict[str, Any], *, project_root: Path, override: str | None) -> Path:
    if override:
        return Path(override).resolve()
    graph_cfg = dict(config.get('graph', {}))
    dataset_path = str(graph_cfg.get('dataset_path', '')).strip()
    if dataset_path:
        resolved = Path(dataset_path)
        if not resolved.is_absolute():
            resolved = (project_root / dataset_path).resolve()
        return resolved
    output_root = str(graph_cfg.get('output_root', '')).strip()
    dataset_name = str(graph_cfg.get('dataset_name', '')).strip()
    if not output_root or not dataset_name:
        raise ValueError('Phase 6 optimization requires graph.dataset_path or graph.output_root + graph.dataset_name')
    return (project_root / output_root / 'datasets' / f'{dataset_name}.json').resolve()


def _train_and_eval_variant(
    *,
    variant_name: str,
    config_path: Path,
    dataset_path: Path,
    output_root: Path,
    compare_split: str,
    project_root: Path,
) -> dict[str, Any]:
    config = _clone_config(load_config(config_path))
    variant_root = output_root / variant_name
    train_result = train_main_model(
        config=config,
        dataset_path=dataset_path,
        output_dir=variant_root,
        project_root=project_root,
    )
    evaluation = evaluate_main_model(
        config=config,
        dataset_path=dataset_path,
        checkpoint_path=train_result.checkpoint_path,
        split=compare_split,
        project_root=project_root,
    )
    return {
        'variant_name': variant_name,
        'config_path': str(config_path),
        'checkpoint_path': train_result.checkpoint_path,
        'history_path': train_result.history_path,
        'hidden_mae': hidden_mae_from_metrics(evaluation['metrics']),
        'overall_mae': float(evaluation['metrics'].get('overall', {}).get('mae', 0.0)),
        'metrics': evaluation['metrics'],
        'hotspot_metrics': evaluation['hotspot_metrics'],
        'kg_summary': evaluation.get('kg_summary', {}),
        'dataset_summary': evaluation.get('dataset_summary', {}),
    }


def _degraded_surfaces(
    *,
    candidate_variant: str,
    current_default_variant: str,
    surface_results: dict[str, Any],
    primary_surface: str,
    tolerance: float,
) -> list[str]:
    current_payload = dict(surface_results.get(current_default_variant, {}))
    candidate_payload = dict(surface_results.get(candidate_variant, {}))
    degraded: list[str] = []
    for surface_name, current_metrics in sorted(current_payload.items()):
        if surface_name == primary_surface or not isinstance(current_metrics, dict):
            continue
        candidate_metrics = dict(candidate_payload.get(surface_name, {}))
        current_hidden = current_metrics.get('hidden_mae')
        candidate_hidden = candidate_metrics.get('hidden_mae')
        if current_hidden is None or candidate_hidden is None:
            continue
        current_value = float(current_hidden)
        candidate_value = float(candidate_hidden)
        if current_value <= 0.0:
            continue
        if candidate_value > current_value * (1.0 + tolerance):
            degraded.append(surface_name)
    return degraded


def _build_promotion_decision(
    *,
    current_default_variant: str,
    current_default_hidden_mae: float,
    current_default_control_run: dict[str, Any],
    top_runs: list[dict[str, Any]],
    surface_results: dict[str, Any],
    primary_surface: str,
    tolerance: float,
    failure_limit: int,
) -> dict[str, Any]:
    decisions: list[dict[str, Any]] = []
    for run in top_runs:
        degraded = _degraded_surfaces(
            candidate_variant=str(run['variant_name']),
            current_default_variant=current_default_variant,
            surface_results=surface_results,
            primary_surface=primary_surface,
            tolerance=tolerance,
        )
        primary_hidden = float(run['hidden_mae'])
        eligible = primary_hidden < float(current_default_hidden_mae) and len(degraded) <= failure_limit
        decisions.append(
            {
                'variant_name': str(run['variant_name']),
                'hidden_mae': primary_hidden,
                'beats_frozen_primary_threshold': primary_hidden < float(current_default_hidden_mae),
                'degraded_surface_count': len(degraded),
                'degraded_surfaces': degraded,
                'eligible_for_promotion': eligible,
            }
        )
    promoted = next((item for item in decisions if item['eligible_for_promotion']), None)
    return {
        'primary_surface': primary_surface,
        'current_default_variant': current_default_variant,
        'current_default_hidden_mae': float(current_default_hidden_mae),
        'current_default_control_hidden_mae': float(current_default_control_run['hidden_mae']),
        'risk_surface_degradation_tolerance': float(tolerance),
        'risk_surface_failure_limit': int(failure_limit),
        'candidate_decisions': decisions,
        'promote_new_default': promoted is not None,
        'promoted_variant': promoted['variant_name'] if promoted is not None else current_default_variant,
        'summary': 'promote_candidate' if promoted is not None else 'keep_current_default',
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run the Phase 6 KG optimization matrix')
    parser.add_argument('--config', default='configs/phase6/ablations/kg_optimization_matrix.yaml')
    parser.add_argument('--project-root', default='/home/user/projects/GIC')
    parser.add_argument('--dataset-path', default=None)
    parser.add_argument('--output', default=None)
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve()
    base_config = load_config(config_path)
    optimization_cfg = dict(base_config.get('optimization', {}))
    compare_split = str(optimization_cfg.get('compare_split', 'test'))
    primary_surface = str(optimization_cfg.get('primary_surface', 'case118_graph_broader'))
    current_default_variant = str(optimization_cfg.get('current_default_variant', 'feature_only'))
    current_default_hidden_mae = float(optimization_cfg.get('current_default_hidden_mae', 5.947530508041382))
    current_default_config_path = _resolve_config_path(
        str(optimization_cfg.get('current_default_config_path', 'configs/phase6/models/feature_only_full.yaml')),
        base_config_path=config_path,
        project_root=project_root,
    )
    tolerance = float(optimization_cfg.get('risk_surface_degradation_tolerance', 0.15))
    failure_limit = int(optimization_cfg.get('risk_surface_failure_limit', 1))
    top_k = int(optimization_cfg.get('top_k', 3))
    variants = list(optimization_cfg.get('variants', []))
    dataset_path = _dataset_path_from_config(base_config, project_root=project_root, override=args.dataset_path)

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output_path = Path(args.output).resolve() if args.output else (project_root / 'reports' / f'phase6_optimization_matrix_{timestamp}.json')
    output_root = project_root / 'artifacts' / 'runs' / f'phase6_optimization_matrix_{timestamp}'
    output_root.mkdir(parents=True, exist_ok=True)

    current_default_control_run = _train_and_eval_variant(
        variant_name=current_default_variant,
        config_path=current_default_config_path,
        dataset_path=dataset_path,
        output_root=output_root / 'control',
        compare_split=compare_split,
        project_root=project_root,
    )

    candidate_runs: list[dict[str, Any]] = []
    for item in variants:
        if not isinstance(item, dict):
            continue
        variant_name = str(item.get('name', '')).strip()
        config_path_text = str(item.get('config_path', '')).strip()
        if not variant_name or not config_path_text:
            continue
        variant_config_path = _resolve_config_path(config_path_text, base_config_path=config_path, project_root=project_root)
        candidate_runs.append(
            _train_and_eval_variant(
                variant_name=variant_name,
                config_path=variant_config_path,
                dataset_path=dataset_path,
                output_root=output_root / 'candidates',
                compare_split=compare_split,
                project_root=project_root,
            )
        )

    candidate_runs.sort(key=lambda item: (float(item['hidden_mae']), str(item['variant_name'])))
    top_runs = candidate_runs[: max(1, top_k)]
    surface_results = evaluate_phase6_surface_runs(
        base_config=base_config,
        runs=[current_default_control_run, *top_runs],
        compare_split=compare_split,
        project_root=project_root,
    )
    decision = _build_promotion_decision(
        current_default_variant=current_default_variant,
        current_default_hidden_mae=current_default_hidden_mae,
        current_default_control_run=current_default_control_run,
        top_runs=top_runs,
        surface_results=surface_results,
        primary_surface=primary_surface,
        tolerance=tolerance,
        failure_limit=failure_limit,
    )

    payload = {
        'config_path': str(config_path),
        'project_root': str(project_root),
        'dataset_path': str(dataset_path),
        'compare_split': compare_split,
        'primary_surface': primary_surface,
        'current_default_control_run': current_default_control_run,
        'candidate_runs': candidate_runs,
        'top_runs': top_runs,
        'surface_results': surface_results,
        'default_promotion_decision': decision,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({
        'output_path': str(output_path),
        'best_candidate': top_runs[0]['variant_name'] if top_runs else current_default_variant,
        'best_hidden_mae': top_runs[0]['hidden_mae'] if top_runs else current_default_control_run['hidden_mae'],
        'promoted_variant': decision['promoted_variant'],
        'promote_new_default': decision['promote_new_default'],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
