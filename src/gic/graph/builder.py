from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gic.graph.features import build_feature_bundle
from gic.graph.labels import build_label_bundle
from gic.graph.masks import build_observation_mask
from gic.graph.schema import EdgeRecord, GraphSample, NodeRecord, ReconstructionTaskConfig



def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))



def load_signal_feature_payload(manifest_path: Path | None) -> dict[str, Any] | None:
    if manifest_path is None or not manifest_path.exists():
        return None
    manifest = _read_json(manifest_path)
    features_path = Path(manifest.get('paths', {}).get('features', ''))
    if not features_path.exists():
        raise ValueError(f'Signal feature file missing: {features_path}')
    payload = _read_json(features_path)
    payload['_manifest_path'] = str(manifest_path)
    return payload



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



def _line_totals(solution: dict[str, Any], adjacency_lines: dict[str, list[str]]) -> dict[str, float]:
    line_values = {str(item['line_id']): abs(float(item.get('induced_quantity') or 0.0)) for item in solution.get('line_inputs', [])}
    return {
        node_id: float(sum(line_values.get(line_id, 0.0) for line_id in line_ids))
        for node_id, line_ids in adjacency_lines.items()
    }



def build_graph_samples_from_config(project_root: Path, config: dict[str, Any]) -> tuple[ReconstructionTaskConfig, dict[str, Any], list[GraphSample]]:
    graph_config = dict(config.get('graph', {}))
    task_config = dict(config.get('task', {}))
    physics_case_path = (project_root / graph_config['physics_case_path']).resolve()
    solution_path = (project_root / graph_config['solution_path']).resolve()
    signal_manifest_value = graph_config.get('signal_manifest_path')
    signal_manifest_path = (project_root / signal_manifest_value).resolve() if isinstance(signal_manifest_value, str) and signal_manifest_value else None

    physics_case = _read_json(physics_case_path)
    solutions = _read_json(solution_path)
    signal_payload = load_signal_feature_payload(signal_manifest_path)

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
        feature_bundle = build_feature_bundle(
            node_ids=node_ids,
            bus_records=list(physics_case.get('buses', [])),
            adjacency_counts=adjacency_counts,
            line_feature_totals=_line_totals(solution, adjacency_lines),
            observed_values=observed_values,
            mask_bundle=mask_bundle,
            signal_payload=signal_payload,
            include_signal_features=task.include_signal_features,
            include_physics_baseline=task.include_physics_baseline,
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
                    'solution_path': str(solution_path),
                    'signal_manifest_path': str(signal_manifest_path) if signal_manifest_path else None,
                },
            )
        )

    build_context = {
        'dataset_name': str(graph_config.get('dataset_name', 'graph_dataset_default')),
        'source_case_id': str(physics_case.get('source_case_id', physics_case.get('case_id', ''))),
        'scenario_id': str(solutions[0].get('scenario_id', 'graph_scenario')) if solutions else 'graph_scenario',
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
