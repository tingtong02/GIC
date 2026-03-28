from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from gic.graph.features import build_feature_bundle
from gic.graph.labels import build_label_bundle
from gic.graph.masks import build_observation_mask
from gic.graph.schema import EdgeRecord, GraphSample, NodeRecord, ReconstructionTaskConfig



def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))



def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace('Z', '+00:00'))



def load_signal_feature_assets(manifest_path: Path | None) -> dict[str, Any] | None:
    if manifest_path is None or not manifest_path.exists():
        return None
    manifest = _read_json(manifest_path)
    paths = manifest.get('paths', {})
    features_path = Path(paths.get('features', ''))
    timeseries_path = Path(paths.get('timeseries', ''))
    if not features_path.exists():
        raise ValueError(f'Signal feature file missing: {features_path}')
    if not timeseries_path.exists():
        raise ValueError(f'Signal timeseries file missing: {timeseries_path}')
    return {
        'manifest_path': str(manifest_path),
        'manifest': manifest,
        'features_payload': _read_json(features_path),
        'timeseries_payload': _read_json(timeseries_path),
    }



def _resolve_solution_paths(graph_config: dict[str, Any], project_root: Path) -> list[Path]:
    solution_paths_value = graph_config.get('solution_paths')
    if isinstance(solution_paths_value, list) and solution_paths_value:
        resolved: list[Path] = []
        for item in solution_paths_value:
            if not isinstance(item, str) or not item:
                raise ValueError(f'Invalid graph.solution_paths entry: {item}')
            resolved.append((project_root / item).resolve())
        return resolved
    solution_path = graph_config.get('solution_path')
    if not isinstance(solution_path, str) or not solution_path:
        raise ValueError('Phase 4 graph config requires graph.solution_path or graph.solution_paths')
    return [(project_root / solution_path).resolve()]



def _mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0



def _std(values: list[float]) -> float:
    if not values:
        return 0.0
    mean_value = _mean(values)
    return math.sqrt(sum((value - mean_value) ** 2 for value in values) / len(values))



def _max_abs_index(values: list[float]) -> int:
    if not values:
        return 0
    return max(range(len(values)), key=lambda index: abs(values[index]))



def _prefix_signal_payload(signal_assets: dict[str, Any] | None, target_time: str) -> dict[str, Any] | None:
    if not isinstance(signal_assets, dict):
        return None
    timeseries_payload = signal_assets.get('timeseries_payload', {})
    features_payload = signal_assets.get('features_payload', {})
    quasi_series = timeseries_payload.get('quasi_dc_series', {})
    denoised_series = timeseries_payload.get('denoised_series', {})
    time_index = [str(item) for item in quasi_series.get('time_index', [])]
    if not time_index:
        return None
    target_dt = _parse_time(target_time)
    candidate_indices = [index for index, item in enumerate(time_index) if _parse_time(item) <= target_dt]
    if not candidate_indices:
        raise ValueError(f'Signal timeseries has no causal window for target time {target_time}')
    end_index = candidate_indices[-1]
    channels = [str(item) for item in quasi_series.get('channels', [])]
    quasi_values = {str(channel): [float(value) for value in quasi_series.get('values', {}).get(channel, [])[: end_index + 1]] for channel in channels}
    denoised_values = {str(channel): [float(value) for value in denoised_series.get('values', {}).get(channel, [])[: end_index + 1]] for channel in channels}

    summary_statistics: dict[str, float] = {}
    peak_features: dict[str, float] = {}
    trend_features: dict[str, float] = {}
    spectral_features: dict[str, float] = {}
    for channel in channels:
        quasi_channel = quasi_values.get(channel, [])
        denoised_channel = denoised_values.get(channel, quasi_channel)
        if not quasi_channel:
            continue
        summary_statistics[f'{channel}.mean'] = _mean(quasi_channel)
        summary_statistics[f'{channel}.std'] = _std(quasi_channel)
        summary_statistics[f'{channel}.max'] = float(max(quasi_channel))
        summary_statistics[f'{channel}.min'] = float(min(quasi_channel))
        summary_statistics[f'{channel}.peak_to_peak'] = float(max(quasi_channel) - min(quasi_channel))
        peak_features[f'{channel}.abs_peak'] = float(max(abs(value) for value in quasi_channel))
        peak_features[f'{channel}.peak_index'] = float(_max_abs_index(quasi_channel))
        trend_features[f'{channel}.start_end_delta'] = float(quasi_channel[-1] - quasi_channel[0])
        trend_features[f'{channel}.slope'] = float((quasi_channel[-1] - quasi_channel[0]) / max(len(quasi_channel) - 1, 1))
        residual = [denoised - quasi for denoised, quasi in zip(denoised_channel, quasi_channel)]
        base_energy = float(sum(value * value for value in denoised_channel) + 1e-9)
        spectral_features[f'{channel}.residual_energy_ratio'] = float(sum(value * value for value in residual) / base_energy)

    quality_flags = [str(item) for item in features_payload.get('quality_flags', []) if isinstance(item, str)]
    if end_index + 1 < 8 and 'short_sequence' not in quality_flags:
        quality_flags.append('short_sequence')
    return {
        'summary_statistics': summary_statistics,
        'peak_features': peak_features,
        'trend_features': trend_features,
        'spectral_features': spectral_features,
        'quality_flags': quality_flags,
        'window_definition': {
            'enabled': True,
            'size': end_index + 1,
            'stride': end_index + 1,
            'observed_points': end_index + 1,
            'target_time': target_time,
        },
    }



def _adjacency_from_case(physics_case: dict[str, Any]) -> tuple[dict[str, int], list[EdgeRecord], dict[str, list[str]]]:
    adjacency_counts: dict[str, int] = {str(item['bus_id']): 0 for item in physics_case.get('buses', [])}
    adjacency_lines: dict[str, list[str]] = {str(item['bus_id']): [] for item in physics_case.get('buses', [])}
    edges: list[EdgeRecord] = []
    for line in physics_case.get('lines', []):
        from_bus = str(line['from_bus'])
        to_bus = str(line['to_bus'])
        adjacency_counts[from_bus] += 1
        adjacency_counts[to_bus] += 1
        adjacency_lines[from_bus].append(str(line['line_id']))
        adjacency_lines[to_bus].append(str(line['line_id']))
        features = {
            'resistance_ohm': float(line.get('resistance_ohm') or 0.0),
            'length_km': float(line.get('length_km') or 0.0),
            'azimuth_deg': float(line.get('azimuth_deg') or 0.0),
        }
        edges.append(EdgeRecord(edge_id=f"{line['line_id']}:fwd", edge_type='electrical_connectivity', source_node=from_bus, target_node=to_bus, features=features, metadata={'component_type': 'line', 'component_id': str(line['line_id'])}))
        edges.append(EdgeRecord(edge_id=f"{line['line_id']}:rev", edge_type='electrical_connectivity', source_node=to_bus, target_node=from_bus, features=features, metadata={'component_type': 'line', 'component_id': str(line['line_id'])}))
    for transformer in physics_case.get('transformers', []):
        from_bus = str(transformer['from_bus'])
        to_bus = str(transformer['to_bus'])
        adjacency_counts[from_bus] += 1
        adjacency_counts[to_bus] += 1
        features = {
            'effective_resistance_ohm': float(transformer.get('effective_resistance_ohm') or 0.0),
        }
        edges.append(EdgeRecord(edge_id=f"{transformer['transformer_id']}:fwd", edge_type='electrical_connectivity', source_node=from_bus, target_node=to_bus, features=features, metadata={'component_type': 'transformer', 'component_id': str(transformer['transformer_id'])}))
        edges.append(EdgeRecord(edge_id=f"{transformer['transformer_id']}:rev", edge_type='electrical_connectivity', source_node=to_bus, target_node=from_bus, features=features, metadata={'component_type': 'transformer', 'component_id': str(transformer['transformer_id'])}))
    return adjacency_counts, edges, adjacency_lines



def _line_totals(solution: dict[str, Any], adjacency_lines: dict[str, list[str]], *, field_name: str) -> dict[str, float]:
    line_values = {str(item['line_id']): abs(float(item.get(field_name) or 0.0)) for item in solution.get('line_inputs', [])}
    return {
        node_id: float(sum(line_values.get(line_id, 0.0) for line_id in line_ids))
        for node_id, line_ids in adjacency_lines.items()
    }



def _sorted_solutions(solution_collections: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for collection in solution_collections:
        merged.extend(collection)
    return sorted(merged, key=lambda item: (str(item.get('scenario_id', '')), _parse_time(str(item.get('time', '1970-01-01T00:00:00Z'))), str(item.get('solution_id', ''))))



def build_graph_samples_from_config(project_root: Path, config: dict[str, Any]) -> tuple[ReconstructionTaskConfig, dict[str, Any], list[GraphSample]]:
    graph_config = dict(config.get('graph', {}))
    task_config = dict(config.get('task', {}))
    physics_case_path = (project_root / graph_config['physics_case_path']).resolve()
    solution_paths = _resolve_solution_paths(graph_config, project_root)
    signal_manifest_value = graph_config.get('signal_manifest_path')
    signal_manifest_path = (project_root / signal_manifest_value).resolve() if isinstance(signal_manifest_value, str) and signal_manifest_value else None

    physics_case = _read_json(physics_case_path)
    solutions = _sorted_solutions([_read_json(path) for path in solution_paths])
    signal_assets = load_signal_feature_assets(signal_manifest_path)

    task = ReconstructionTaskConfig(
        target_level=str(task_config.get('target_level', 'bus')),
        objective=str(task_config.get('objective', 'regression')),
        node_type=str(graph_config.get('node_type', 'bus')),
        sparsity_rate=float(graph_config.get('sparsity_rate', 0.7)),
        include_signal_features=bool(graph_config.get('include_signal_features', False)),
        include_physics_baseline=bool(graph_config.get('include_physics_baseline', False)),
        metadata={'dataset_name': str(graph_config.get('dataset_name', 'graph_dataset_default'))},
    )

    node_records = [
        NodeRecord(node_id=str(item['bus_id']), node_type=task.node_type, index=index, bus_id=str(item['bus_id']), metadata={'base_kv': float(item.get('base_kv') or 0.0)})
        for index, item in enumerate(physics_case.get('buses', []))
    ]
    node_ids = [item.node_id for item in node_records]
    adjacency_counts, edge_records, adjacency_lines = _adjacency_from_case(physics_case)

    graph_samples: list[GraphSample] = []
    for solution in solutions:
        graph_id = f"{solution['scenario_id']}_{solution['time'].replace(':', '').replace('-', '').replace('T', '_').replace('Z', '')}"
        mask_bundle = build_observation_mask(node_ids, task.sparsity_rate, int(graph_config.get('mask_seed', 42)), graph_id)
        label_bundle = build_label_bundle(solution, task)
        observed_values = {
            node_id: label_bundle.node_targets[node_id]
            for node_id in node_ids
            if mask_bundle.observed_mask.get(node_id, False)
        }
        signal_payload = _prefix_signal_payload(signal_assets, str(solution.get('time', ''))) if task.include_signal_features else None
        quality_flags = [str(item) for item in solution.get('quality_flags', []) if isinstance(item, str)]
        assumptions = [str(item) for item in solution.get('assumptions', []) if isinstance(item, str)]
        solver_status = str(solution.get('solver_status', 'unknown'))
        feature_bundle = build_feature_bundle(
            node_ids=node_ids,
            bus_records=list(physics_case.get('buses', [])),
            adjacency_counts=adjacency_counts,
            line_feature_totals=_line_totals(solution, adjacency_lines, field_name='induced_quantity'),
            projected_field_totals=_line_totals(solution, adjacency_lines, field_name='projected_field'),
            observed_values=observed_values,
            mask_bundle=mask_bundle,
            signal_payload=signal_payload,
            include_signal_features=task.include_signal_features,
            include_physics_baseline=task.include_physics_baseline,
            solution_quality_flags=quality_flags,
            solution_assumptions=assumptions,
            solver_status=solver_status,
        )
        graph_samples.append(
            GraphSample(
                graph_id=graph_id,
                sample_id=str(solution.get('solution_id')),
                scenario_id=str(solution.get('scenario_id')),
                time_index=[str(solution.get('time'))],
                node_records=node_records,
                edge_records=edge_records,
                feature_bundle=feature_bundle,
                label_bundle=label_bundle,
                mask_bundle=mask_bundle,
                metadata={
                    'source_case_id': str(physics_case.get('source_case_id', physics_case.get('case_id', ''))),
                    'physics_case_path': str(physics_case_path),
                    'solution_paths': [str(path) for path in solution_paths],
                    'signal_manifest_path': str(signal_manifest_path) if signal_manifest_path else None,
                    'solver_status': solver_status,
                    'quality_flags': quality_flags,
                    'assumptions': assumptions,
                    'solver_metadata': dict(solution.get('solver_metadata', {})),
                },
            )
        )

    scenario_ids = sorted({str(item.get('scenario_id', '')) for item in solutions})
    build_context = {
        'dataset_name': str(graph_config.get('dataset_name', 'graph_dataset_default')),
        'source_case_id': str(physics_case.get('source_case_id', physics_case.get('case_id', ''))),
        'scenario_id': scenario_ids[0] if len(scenario_ids) == 1 else 'combined_scenarios',
        'scenario_ids': scenario_ids,
        'solution_paths': [str(path) for path in solution_paths],
        'graph_config': graph_config,
        'task': {
            'target_level': task.target_level,
            'objective': task.objective,
            'node_type': task.node_type,
            'sparsity_rate': task.sparsity_rate,
            'include_signal_features': task.include_signal_features,
            'include_physics_baseline': task.include_physics_baseline,
        },
    }
    return task, build_context, graph_samples
