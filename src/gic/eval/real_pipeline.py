from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from gic.config import load_config
from gic.data import RegistryStore, to_dict
from gic.data.converters.grid_to_physics import convert_grid_case_to_physics
from gic.data.loaders.matpower_loader import MatpowerLoader
from gic.data.loaders.timeseries_loader import TimeSeriesLoader
from gic.data.validation.reports import summarize_validation_results
from gic.eval.case_studies import build_case_studies
from gic.eval.evidence import ValidationEvidenceBundle, build_evidence_summary, evidence_to_dict
from gic.eval.generalization import GeneralizationSplitConfig, build_generalization_summary
from gic.eval.real_events import (
    RealEventAsset,
    RealEventBuildResult,
    RealEventDataset,
    RealEventManifest,
    export_real_event_manifest,
    flatten_event_records,
    real_event_to_dict,
)
from gic.eval.reporting import write_json_report, write_markdown_report
from gic.eval.reports import build_phase7_report_markdown
from gic.eval.robustness import RobustnessScenarioConfig, build_robustness_summary
from gic.eval.trustworthiness import build_trustworthiness_summary
from gic.graph import build_graph_samples_from_config, export_graph_dataset, export_graph_samples
from gic.physics.export import export_label_bundle
from gic.physics.field import build_series_from_timeseries
from gic.physics.schema import ScenarioConfig
from gic.physics.solver import solve_series
from gic.signal import (
    FrontendConfig,
    build_comparison_report,
    build_frontend,
    build_signal_sample_from_timeseries,
    export_comparison_report,
    export_frontend_result,
    signal_to_dict,
    validate_frontend_result,
    validate_signal_sample,
)
from gic.training import evaluate_baseline_model, evaluate_main_model
from gic.utils.paths import ensure_directory


@dataclass(slots=True)
class Phase7Paths:
    output_root: Path
    event_root: Path
    signal_root: Path
    physics_root: Path
    graph_root: Path
    manifest_root: Path


@dataclass(slots=True)
class ModelSpec:
    model_id: str
    model_family: str
    config_path: Path
    checkpoint_path: Path
    model_type: str | None = None


def _resolve_path(project_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (project_root / path).resolve()


def _load_mapping_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError(f'Phase 7 mapping file must contain an object: {path}')
    return payload



def _phase7_paths(project_root: Path, config: dict[str, Any], event_id: str) -> Phase7Paths:
    real_cfg = dict(config.get('real_eval', {}))
    output_root = ensure_directory(project_root / str(real_cfg.get('output_root', 'data/processed/real_event')))
    event_root = ensure_directory(output_root / event_id)
    return Phase7Paths(
        output_root=output_root,
        event_root=event_root,
        signal_root=ensure_directory(event_root / 'signal_ready'),
        physics_root=ensure_directory(event_root / 'physics_ready'),
        graph_root=ensure_directory(event_root / 'graph_ready'),
        manifest_root=ensure_directory(event_root / 'manifests'),
    )



def _load_event_sets(project_root: Path, config: dict[str, Any]) -> tuple[RealEventDataset, RealEventDataset]:
    real_cfg = dict(config.get('real_eval', {}))
    main_payload = _load_mapping_file(_resolve_path(project_root, str(real_cfg['event_set'])))
    generalization_payload = _load_mapping_file(_resolve_path(project_root, str(real_cfg['generalization_set'])))
    return flatten_event_records(main_payload), flatten_event_records(generalization_payload)



def load_all_real_event_records(project_root: Path, config: dict[str, Any]) -> RealEventDataset:
    main_set, generalization_set = _load_event_sets(project_root, config)
    return RealEventDataset(
        event_set_name=f"{main_set.event_set_name}+{generalization_set.event_set_name}",
        records=[*main_set.records, *generalization_set.records],
        notes='Combined Phase 7 event set.',
    )



def _load_geomagnetic_series(project_root: Path, registry: RegistryStore, dataset_name: str):
    dataset = registry.get_dataset(dataset_name)
    source = registry.get_source(dataset.source_name)
    return TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)



def _load_grid_case(project_root: Path, registry: RegistryStore, dataset_name: str):
    dataset = registry.get_dataset(dataset_name)
    source = registry.get_source(dataset.source_name)
    return MatpowerLoader(project_root).load(dataset, source)



def _phase3_methods(project_root: Path, config: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    phase3_config = load_config(_resolve_path(project_root, str(config['real_eval']['phase3_config'])))
    signal_cfg = dict(phase3_config.get('signal', {}))
    comparison_cfg = dict(signal_cfg.get('comparison', {}))
    active_methods = [str(item) for item in comparison_cfg.get('active_methods', [])]
    if not active_methods:
        raise ValueError('Phase 7 requires Phase 3 active methods to export real-event signal assets')
    return phase3_config, active_methods



def _build_frontend_config(config: dict[str, Any], method_name: str) -> FrontendConfig:
    signal_cfg = dict(config.get('signal', {}))
    methods_cfg = dict(signal_cfg.get('methods', {}))
    method_cfg = dict(methods_cfg.get(method_name, {}))
    parameters = dict(method_cfg.get('parameters', {}))
    return FrontendConfig(
        method_name=method_name,
        method_version=str(method_cfg.get('method_version', '1.0')),
        parameters=parameters,
    )



def ensure_signal_assets(
    *,
    project_root: Path,
    registry: RegistryStore,
    config: dict[str, Any],
    dataset_name: str,
    signal_method: str,
) -> tuple[Path, Path | None]:
    phase3_config, method_names = _phase3_methods(project_root, config)
    signal_cfg = dict(phase3_config.get('signal', {}))
    manifest_path = project_root / 'data/processed/signal_ready/manifests' / f'signal_{dataset_name}_{signal_method}.manifest.json'
    comparison_path = project_root / 'data/processed/signal_ready/comparisons' / f'signal_{dataset_name}_comparison.json'
    if manifest_path.exists() and comparison_path.exists():
        return manifest_path.resolve(), comparison_path.resolve()

    sample = build_signal_sample_from_timeseries(_load_geomagnetic_series(project_root, registry, dataset_name)[0], signal_cfg)
    sample_validation = validate_signal_sample(sample)
    validations = [sample_validation]
    results = []
    for method_name in method_names:
        frontend = build_frontend(method_name)
        frontend_config = _build_frontend_config(phase3_config, method_name)
        result = frontend.run(sample, frontend_config)
        validations.append(validate_frontend_result(result))
        results.append(result)
        export_frontend_result(project_root=project_root, signal_config=signal_cfg, signal_sample=sample, result=result)
    summary = summarize_validation_results(validations)
    if summary['error_count'] > 0:
        raise ValueError(f'真实事件数据缺失或信号前端导出失败: {dataset_name}')
    comparison_report = build_comparison_report(
        sample_id=sample.sample_id,
        results=results,
        comparison_config=signal_cfg.get('comparison', {}),
        benchmark_type=str(sample.metadata.get('benchmark_type', 'real_event')),
        default_scope='real_event_benchmark',
        promotion_status='provisional',
        promotion_reason='Phase 7 reuses Phase 3 real-event benchmark logic as input evidence only.',
    )
    export_comparison_report(project_root=project_root, signal_config=signal_cfg, comparison_report=comparison_report)
    if not manifest_path.exists():
        raise FileNotFoundError(f'真实事件信号资产缺失: {manifest_path}')
    return manifest_path.resolve(), comparison_path.resolve() if comparison_path.exists() else None



def _physics_outputs(paths: Phase7Paths) -> dict[str, str]:
    return {
        'physics_ready_root': str(paths.physics_root.relative_to(paths.output_root.parent)),
        'datasets_root': str((paths.event_root / 'physics_datasets').relative_to(paths.output_root.parent)),
        'manifests_root': str((paths.event_root / 'physics_manifests').relative_to(paths.output_root.parent)),
    }



def build_real_physics_solution(
    *,
    project_root: Path,
    registry: RegistryStore,
    config: dict[str, Any],
    event_id: str,
    dataset_name: str,
    time_stride_minutes: int,
) -> tuple[Path, Path]:
    paths = _phase7_paths(project_root, config, event_id)
    real_cfg = dict(config.get('real_eval', {}))
    phase2_config = load_config(_resolve_path(project_root, str(real_cfg['phase2_config'])))
    case_dataset = str(real_cfg.get('case_dataset', 'matpower_case118_sample'))
    scenario_id = f'realevent_{dataset_name}_{case_dataset}'
    solution_path = paths.physics_root / f'{scenario_id}_solutions.json'
    physics_case_path = paths.physics_root / f'physics_{case_dataset}.json'
    if solution_path.exists() and physics_case_path.exists():
        return physics_case_path.resolve(), solution_path.resolve()

    grid_case, _ = _load_grid_case(project_root, registry, case_dataset)
    physics_case = convert_grid_case_to_physics(grid_case, phase2_config['physics'])
    physics_case_path.write_text(json.dumps(to_dict(physics_case), indent=2, sort_keys=True) + '\n', encoding='utf-8')

    series, _ = _load_geomagnetic_series(project_root, registry, dataset_name)
    scenario = ScenarioConfig(
        scenario_id=scenario_id,
        scenario_type='timeseries_field',
        case_dataset=case_dataset,
        field_units=str(phase2_config['physics']['field'].get('default_units', 'V_per_km')),
        time_interval_seconds=int(phase2_config['scenario'].get('time_interval_seconds', 60)),
        timeseries_dataset=dataset_name,
        output_levels=list(phase2_config['scenario'].get('output_levels', ['line', 'bus', 'transformer'])),
        assumptions=[
            'Real-event electric field series derived from local geomagnetic station via Phase 2 linear scale assumption.',
            f'Real-event source dataset={dataset_name}',
        ],
    )
    field_series = build_series_from_timeseries(
        scenario,
        series,
        float(phase2_config['physics']['field'].get('geomagnetic_scale_v_per_km_per_nt', 0.01)),
    )
    solutions = solve_series(physics_case, field_series, scenario_id)
    stride = max(1, int(time_stride_minutes))
    if stride > 1:
        solutions = [item for index, item in enumerate(solutions) if index % stride == 0]
    outputs_config = {
        'physics_ready_root': str(paths.physics_root.relative_to(project_root)),
        'datasets_root': str((paths.event_root / 'physics_datasets').relative_to(project_root)),
        'manifests_root': str((paths.event_root / 'physics_manifests').relative_to(project_root)),
    }
    export_label_bundle(project_root=project_root, outputs_config=outputs_config, scenario=scenario, solutions=solutions)
    return physics_case_path.resolve(), solution_path.resolve()



def build_real_graph_dataset(
    *,
    project_root: Path,
    config: dict[str, Any],
    event_id: str,
    dataset_name: str,
    physics_case_path: Path,
    solution_path: Path,
    signal_manifest_path: Path | None,
    sparsity_rate: float,
    mask_seed: int,
) -> Path:
    paths = _phase7_paths(project_root, config, event_id)
    dataset_slug = f'real_{dataset_name}_s{int(round(sparsity_rate * 100)):02d}'
    dataset_path = paths.graph_root / 'datasets' / f'{dataset_slug}.json'
    if dataset_path.exists():
        return dataset_path.resolve()

    phase4_config = load_config(_resolve_path(project_root, str(config['real_eval']['phase4_config'])))
    graph_config = json.loads(json.dumps(phase4_config))
    graph_config['graph']['output_root'] = str(paths.graph_root.relative_to(project_root))
    graph_config['graph']['dataset_name'] = dataset_slug
    graph_config['graph']['physics_case_path'] = str(physics_case_path)
    graph_config['graph']['solution_path'] = str(solution_path)
    graph_config['graph']['signal_manifest_path'] = str(signal_manifest_path) if signal_manifest_path else None
    graph_config['graph']['sparsity_rate'] = float(sparsity_rate)
    graph_config['graph']['mask_seed'] = int(mask_seed)
    task, build_context, graph_samples = build_graph_samples_from_config(project_root, graph_config)
    split_assignments = {'train': [], 'val': [], 'test': [sample.graph_id for sample in graph_samples]}
    manifest, _ = export_graph_samples(
        project_root=project_root,
        graph_config=graph_config['graph'],
        dataset_name=build_context['dataset_name'],
        source_case_id=build_context['source_case_id'],
        scenario_id=build_context['scenario_id'],
        task_payload=build_context['task'],
        graph_samples=graph_samples,
        split_assignments=split_assignments,
    )
    export_graph_dataset(project_root=project_root, graph_config=graph_config['graph'], manifest=manifest)
    return dataset_path.resolve()



def build_real_event_set(
    *,
    project_root: Path,
    registry: RegistryStore,
    config: dict[str, Any],
) -> RealEventBuildResult:
    dataset = load_all_real_event_records(project_root, config)
    real_cfg = dict(config.get('real_eval', {}))
    signal_method = str(real_cfg.get('signal_method', 'raw_baseline'))
    sparsity_rate = float(real_cfg.get('sparsity_rate', 0.7))
    mask_seed = int(real_cfg.get('mask_seed', 42))
    time_stride_minutes = int(real_cfg.get('time_stride_minutes', 5))
    assets: list[RealEventAsset] = []
    for record in dataset.records:
        for dataset_name in record.available_geomagnetic_inputs:
            interim_path = project_root / 'data/interim/timeseries' / f'{dataset_name}.json'
            interim_manifest_path = project_root / 'data/interim/timeseries' / f'{dataset_name}.manifest.json'
            if not interim_path.exists() or not interim_manifest_path.exists():
                raise FileNotFoundError(f'真实事件数据缺失: {dataset_name}')
            signal_manifest_path, comparison_path = ensure_signal_assets(
                project_root=project_root,
                registry=registry,
                config=config,
                dataset_name=dataset_name,
                signal_method=signal_method,
            )
            physics_case_path, solution_path = build_real_physics_solution(
                project_root=project_root,
                registry=registry,
                config=config,
                event_id=record.event_id,
                dataset_name=dataset_name,
                time_stride_minutes=time_stride_minutes,
            )
            graph_dataset_path = build_real_graph_dataset(
                project_root=project_root,
                config=config,
                event_id=record.event_id,
                dataset_name=dataset_name,
                physics_case_path=physics_case_path,
                solution_path=solution_path,
                signal_manifest_path=signal_manifest_path,
                sparsity_rate=sparsity_rate,
                mask_seed=mask_seed,
            )
            series_payload = json.loads(interim_path.read_text(encoding='utf-8'))
            assets.append(
                RealEventAsset(
                    event_id=record.event_id,
                    dataset_name=dataset_name,
                    station_id=str(series_payload.get('station_id', dataset_name)),
                    time_range=record.time_range,
                    evidence_level=record.evidence.normalized_level(),
                    interim_timeseries_path=str(interim_path.resolve()),
                    interim_manifest_path=str(interim_manifest_path.resolve()),
                    signal_manifest_path=str(signal_manifest_path.resolve()),
                    signal_comparison_path=str(comparison_path.resolve()) if comparison_path else None,
                    physics_solution_path=str(solution_path.resolve()),
                    graph_dataset_path=str(graph_dataset_path.resolve()),
                    notes=[*record.quality_notes],
                )
            )
    manifest = RealEventManifest(
        event_set_name=dataset.event_set_name,
        record_count=len(dataset.records),
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        records=real_event_to_dict(dataset.records),
        notes=dataset.notes,
    )
    destination = project_root / str(real_cfg.get('output_root', 'data/processed/real_event')) / 'real_event_manifest.json'
    export_real_event_manifest(RealEventBuildResult(dataset=dataset, manifest=manifest, assets=assets), destination)
    return RealEventBuildResult(dataset=dataset, manifest=manifest, assets=assets)



def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace('Z', '+00:00'))



def _mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0



def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = _mean(xs)
    mean_y = _mean(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x <= 1e-12 or den_y <= 1e-12:
        return None
    return float(num / (den_x * den_y))



def _rank(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    for rank, index in enumerate(order):
        ranks[index] = float(rank)
    return ranks



def _station_disturbance_curve(timeseries_payload: dict[str, Any]) -> tuple[list[str], list[float]]:
    time_index = [str(item) for item in timeseries_payload.get('time_index', [])]
    values = dict(timeseries_payload.get('values', {}))
    channels = [channel for channel in ['X', 'Y', 'Z'] if channel in values]
    if not channels:
        return time_index, [0.0 for _ in time_index]
    baselines: dict[str, float] = {}
    for channel in channels:
        series = values.get(channel, [])
        baseline = 0.0
        for value in series:
            if value is not None:
                baseline = float(value)
                break
        baselines[channel] = baseline
    curve: list[float] = []
    for index in range(len(time_index)):
        total = 0.0
        for channel in channels:
            series = values.get(channel, [])
            raw = series[index] if index < len(series) else None
            value = float(raw) if raw is not None else baselines[channel]
            total += abs(value - baselines[channel])
        curve.append(total)
    return time_index, curve



def _prediction_curve(rows: list[dict[str, Any]]) -> tuple[list[str], list[float]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = str(row.get('time_index') or row.get('graph_id') or row.get('sample_id') or '')
        grouped[key].append(row)
    ordered_keys = sorted(grouped.keys())
    curve: list[float] = []
    for key in ordered_keys:
        group_rows = grouped[key]
        hidden_rows = [item for item in group_rows if not bool(item.get('observed', False))]
        selected = hidden_rows or group_rows
        curve.append(max(abs(float(item.get('prediction', 0.0))) for item in selected))
    return ordered_keys, curve



def _peak_time(times: list[str], values: list[float]) -> str | None:
    if not times or not values:
        return None
    index = max(range(len(values)), key=lambda i: values[i])
    return str(times[index])



def _curve_metrics(reference_times: list[str], reference_values: list[float], pred_times: list[str], pred_values: list[float]) -> dict[str, Any]:
    length = min(len(reference_times), len(pred_times), len(reference_values), len(pred_values))
    if length == 0:
        return {'trend_correlation': None, 'ranking_correlation': None, 'peak_timing_error_minutes': None, 'peak_coincidence': None}
    ref_times = reference_times[:length]
    ref_values = reference_values[:length]
    model_times = pred_times[:length]
    model_values = pred_values[:length]
    ref_peak = _peak_time(ref_times, ref_values)
    model_peak = _peak_time(model_times, model_values)
    peak_error = None
    if ref_peak and model_peak:
        peak_error = abs((_parse_iso(model_peak) - _parse_iso(ref_peak)).total_seconds()) / 60.0
    return {
        'trend_correlation': _pearson(ref_values, model_values),
        'ranking_correlation': _pearson(_rank(ref_values), _rank(model_values)),
        'peak_timing_error_minutes': peak_error,
        'peak_coincidence': bool(peak_error is not None and peak_error <= 15.0),
    }



def _phase4_reference_feature_names(project_root: Path, config: dict[str, Any]) -> list[str]:
    real_cfg = dict(config.get('real_eval', {}))
    checkpoint_path = _resolve_path(project_root, str(real_cfg['phase4_best_graph_checkpoint']))
    checkpoint_payload = torch.load(checkpoint_path, map_location='cpu')
    checkpoint_metadata = dict(checkpoint_payload.get('metadata', {})) if isinstance(checkpoint_payload, dict) else {}
    expected_input_dim = int(checkpoint_metadata.get('input_dim', 0))

    run_name = checkpoint_path.parents[2].name
    candidate_paths = [
        _resolve_path(project_root, str(real_cfg['phase4_report_path'])),
        checkpoint_path.parents[2] / 'phase4_baseline_report.json',
        project_root / 'reports' / run_name / 'phase4_baseline_report.json',
    ]
    seen: set[Path] = set()
    for report_path in candidate_paths:
        if report_path in seen or not report_path.exists():
            continue
        seen.add(report_path)
        payload = json.loads(report_path.read_text(encoding='utf-8'))
        default_dataset = dict(payload.get('default_dataset', {}))
        graph_report = dict(default_dataset.get('graph_report', {}))
        feature_names = [str(item) for item in graph_report.get('feature_names', [])]
        if not feature_names:
            continue
        if expected_input_dim <= 0 or len(feature_names) == expected_input_dim:
            return feature_names

    raise ValueError(
        f'Phase 7 could not find Phase 4 reference features matching checkpoint input_dim={expected_input_dim}: {checkpoint_path}'
    )



def _phase4_real_feature_aliases(feature_names: list[str]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    replacements = {
        'bx_nT': 'X',
        'by_nT': 'Y',
        'bz_nT': 'Z',
    }
    for name in feature_names:
        alias = str(name)
        for old, new in replacements.items():
            alias = alias.replace(f'.{old}.', f'.{new}.')
        if alias != name:
            aliases[str(name)] = alias
    return aliases



def _model_specs(project_root: Path, config: dict[str, Any]) -> list[ModelSpec]:
    real_cfg = dict(config.get('real_eval', {}))
    specs = [
        ModelSpec(
            model_id='phase4_best_graph',
            model_family='phase4_baseline',
            config_path=_resolve_path(project_root, str(real_cfg['phase4_config'])),
            checkpoint_path=_resolve_path(project_root, str(real_cfg['phase4_best_graph_checkpoint'])),
            model_type='gat',
        ),
        ModelSpec(
            model_id='phase5_default',
            model_family='phase5_main',
            config_path=_resolve_path(project_root, str(real_cfg['phase5_config'])),
            checkpoint_path=_resolve_path(project_root, str(real_cfg['phase5_default_checkpoint'])),
        ),
        ModelSpec(
            model_id='phase6_feature_only',
            model_family='phase6_main',
            config_path=_resolve_path(project_root, str(real_cfg['phase6_config'])),
            checkpoint_path=_resolve_path(project_root, str(real_cfg['phase6_default_checkpoint'])),
        ),
    ]
    for spec in specs:
        if not spec.checkpoint_path.exists():
            raise FileNotFoundError(f'模型 checkpoint 缺失: {spec.checkpoint_path}')
    return specs



def run_real_event_eval(
    *,
    project_root: Path,
    registry: RegistryStore,
    config: dict[str, Any],
    build_result: RealEventBuildResult | None = None,
) -> dict[str, Any]:
    build_result = build_result or build_real_event_set(project_root=project_root, registry=registry, config=config)
    records_by_event = {record.event_id: record for record in build_result.dataset.records}
    model_specs = _model_specs(project_root, config)
    phase4_feature_names = _phase4_reference_feature_names(project_root, config)
    phase4_feature_aliases = _phase4_real_feature_aliases(phase4_feature_names)
    result_rows: list[dict[str, Any]] = []
    evidence_bundles = [record.evidence for record in build_result.dataset.records]
    for asset in build_result.assets:
        timeseries_payload = json.loads(Path(asset.interim_timeseries_path).read_text(encoding='utf-8'))
        reference_times, reference_curve = _station_disturbance_curve(timeseries_payload)
        for spec in model_specs:
            model_config = load_config(spec.config_path)
            if spec.model_family == 'phase4_baseline':
                evaluation = evaluate_baseline_model(
                    model_type=str(spec.model_type or 'gat'),
                    config=model_config,
                    dataset_path=asset.graph_dataset_path or '',
                    checkpoint_path=spec.checkpoint_path,
                    split='test',
                    feature_names_override=phase4_feature_names,
                    feature_aliases=phase4_feature_aliases,
                )
            else:
                evaluation = evaluate_main_model(
                    config=model_config,
                    dataset_path=asset.graph_dataset_path or '',
                    checkpoint_path=spec.checkpoint_path,
                    split='test',
                    project_root=project_root,
                )
            pred_times, pred_curve = _prediction_curve(list(evaluation.get('rows', [])))
            curve_metrics = _curve_metrics(reference_times, reference_curve, pred_times, pred_curve)
            hidden_metrics = dict(evaluation.get('metrics', {}).get('hidden_only', {}))
            result_rows.append(
                {
                    'event_id': asset.event_id,
                    'dataset_name': asset.dataset_name,
                    'station_id': asset.station_id,
                    'model_id': spec.model_id,
                    'model_family': spec.model_family,
                    'evidence_level': asset.evidence_level,
                    'proxy_hidden_mae': hidden_metrics.get('mae'),
                    'proxy_hidden_rmse': hidden_metrics.get('rmse'),
                    'trend_correlation': curve_metrics['trend_correlation'],
                    'ranking_correlation': curve_metrics['ranking_correlation'],
                    'peak_timing_error_minutes': curve_metrics['peak_timing_error_minutes'],
                    'peak_coincidence': curve_metrics['peak_coincidence'],
                    'row_count': int(evaluation.get('row_count', evaluation.get('metrics', {}).get('row_count', 0))),
                    'graph_dataset_path': asset.graph_dataset_path,
                    'checkpoint_path': str(spec.checkpoint_path),
                }
            )
    return {
        'event_set_name': build_result.dataset.event_set_name,
        'event_asset_count': len(build_result.assets),
        'result_row_count': len(result_rows),
        'evidence_summary': build_evidence_summary(evidence_bundles),
        'rows': result_rows,
    }



def run_real_generalization(eval_payload: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    grouping_cfg = dict(_load_mapping_file(_resolve_path(Path.cwd(), str(config['real_eval']['evaluation']))).get('real_eval', {}).get('event_grouping', {}))
    split_config = GeneralizationSplitConfig(
        main_event_ids=[str(item) for item in grouping_cfg.get('main', [])],
        generalization_event_ids=[str(item) for item in grouping_cfg.get('generalization', [])],
        boundary_event_ids=[str(item) for item in grouping_cfg.get('boundary', [])],
    )
    return build_generalization_summary(list(eval_payload.get('rows', [])), split_config)



def run_real_robustness(eval_payload: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    robustness_cfg = dict(_load_mapping_file(_resolve_path(Path.cwd(), str(config['real_eval']['robustness']))).get('robustness', {}))
    scenario = RobustnessScenarioConfig(
        sensor_dropout=[float(item) for item in robustness_cfg.get('sensor_dropout', [])],
        timing_shift_minutes=[int(item) for item in robustness_cfg.get('timing_shift_minutes', [])],
        noise_stress_std=[float(item) for item in robustness_cfg.get('noise_stress_std', [])],
    )
    rows: list[dict[str, Any]] = []
    for item in eval_payload.get('rows', []):
        for dropout in scenario.sensor_dropout:
            proxy = item.get('proxy_hidden_mae')
            degraded = None if proxy is None else float(proxy) * (1.0 + max(0.0, dropout - 0.7))
            rows.append({
                'event_id': item['event_id'],
                'dataset_name': item['dataset_name'],
                'model_id': item['model_id'],
                'scenario': 'sensor_dropout',
                'parameter': dropout,
                'proxy_hidden_mae_estimate': degraded,
            })
        for shift in scenario.timing_shift_minutes:
            peak_error = item.get('peak_timing_error_minutes')
            shifted = None if peak_error is None else abs(float(peak_error) + int(shift))
            rows.append({
                'event_id': item['event_id'],
                'dataset_name': item['dataset_name'],
                'model_id': item['model_id'],
                'scenario': 'timing_shift',
                'parameter': shift,
                'peak_timing_error_estimate': shifted,
            })
    return build_robustness_summary(rows, scenario)



def build_real_failure_cases(eval_payload: dict[str, Any], top_k: int = 5) -> list[dict[str, Any]]:
    rows = list(eval_payload.get('rows', []))
    ranked = sorted(
        rows,
        key=lambda item: (
            -float(item.get('peak_timing_error_minutes') or 0.0),
            float(item.get('trend_correlation') if item.get('trend_correlation') is not None else 1.0),
        ),
    )
    return ranked[:max(1, top_k)]



def build_real_event_report(
    *,
    project_root: Path,
    registry: RegistryStore,
    config: dict[str, Any],
) -> dict[str, Any]:
    build_result = build_real_event_set(project_root=project_root, registry=registry, config=config)
    eval_payload = run_real_event_eval(project_root=project_root, registry=registry, config=config, build_result=build_result)
    generalization_payload = run_real_generalization(eval_payload, config)
    robustness_payload = run_real_robustness(eval_payload, config)
    failure_cases = build_real_failure_cases(eval_payload)
    phase5_rows = [row for row in eval_payload['rows'] if row['model_id'] == 'phase5_default']
    phase6_rows = [row for row in eval_payload['rows'] if row['model_id'] == 'phase6_feature_only']

    def _mean_metric(rows: list[dict[str, Any]], key: str) -> float | None:
        values = [float(item[key]) for item in rows if item.get(key) is not None]
        return float(sum(values) / len(values)) if values else None

    phase5_trend = _mean_metric(phase5_rows, 'trend_correlation')
    phase6_trend = _mean_metric(phase6_rows, 'trend_correlation')
    decision = 'no_real_default_promotion'
    if phase5_trend is not None and phase6_trend is not None and phase6_trend > phase5_trend + 1e-6:
        decision = 'phase6_feature_only_real_event_leader'
    elif phase5_trend is not None and phase6_trend is not None and phase5_trend > phase6_trend + 1e-6:
        decision = 'phase5_default_real_event_leader'

    report = {
        'event_set_name': build_result.dataset.event_set_name,
        'event_asset_count': len(build_result.assets),
        'result_row_count': len(eval_payload['rows']),
        'evidence_summary': eval_payload['evidence_summary'],
        'evaluation': eval_payload,
        'generalization_summary': generalization_payload,
        'robustness_summary': robustness_payload,
        'failure_case_count': len(failure_cases),
        'failure_cases': failure_cases,
        'default_promotion_decision': decision,
    }
    report['trustworthiness_summary'] = build_trustworthiness_summary(report)
    return report



def export_real_event_report(project_root: Path, config: dict[str, Any], report: dict[str, Any], destination_root: Path) -> dict[str, str]:
    destination_root.mkdir(parents=True, exist_ok=True)
    report_path = write_json_report(report, destination_root / 'phase7_real_event_report.json')
    markdown_path = write_markdown_report(build_phase7_report_markdown(report), destination_root / 'phase7_real_event_report.md')
    case_study_path = write_json_report(report.get('failure_cases', []), destination_root / 'phase7_failure_cases.json')
    return {
        'report_path': str(report_path),
        'markdown_path': str(markdown_path),
        'case_study_path': str(case_study_path),
    }
