from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gic.graph.schema import (
    EdgeRecord,
    GraphFeatureBundle,
    GraphLabelBundle,
    GraphManifest,
    GraphSample,
    MaskBundle,
    NodeRecord,
)


@dataclass(slots=True)
class GraphDataset:
    dataset_name: str
    manifest_path: str
    graph_paths: list[str]
    split_assignments: dict[str, list[str]]
    metadata: dict[str, Any]

    @classmethod
    def from_path(cls, dataset_path: str | Path) -> 'GraphDataset':
        payload = json.loads(Path(dataset_path).read_text(encoding='utf-8'))
        return cls(
            dataset_name=str(payload['dataset_name']),
            manifest_path=str(payload['manifest_path']),
            graph_paths=[str(item) for item in payload.get('graph_paths', [])],
            split_assignments={str(key): [str(item) for item in value] for key, value in payload.get('split_assignments', {}).items()},
            metadata=dict(payload.get('metadata', {})),
        )

    def __len__(self) -> int:
        return len(self.graph_paths)

    def graph_ids(self) -> list[str]:
        return [Path(path).stem for path in self.graph_paths]

    def paths_for_split(self, split: str | None = None) -> list[str]:
        if split is None:
            return list(self.graph_paths)
        allowed = set(self.split_assignments.get(split, []))
        return [path for path in self.graph_paths if Path(path).stem in allowed]

    def load_samples(self, split: str | None = None) -> list[GraphSample]:
        return [load_graph_sample(path) for path in self.paths_for_split(split)]

    def load_all_samples(self) -> list[GraphSample]:
        return [load_graph_sample(path) for path in self.graph_paths]


@dataclass(slots=True)
class NodeRegressionExample:
    graph_id: str
    node_id: str
    features: list[float]
    target: float
    observed: bool
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GraphRegressionExample:
    graph_id: str
    node_ids: list[str]
    features: list[list[float]]
    targets: list[float]
    observed_mask: list[bool]
    adjacency: list[list[float]]
    metadata: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class TemporalGraphSequenceExample:
    target_graph_id: str
    sequence_graph_ids: list[str]
    node_ids: list[str]
    node_feature_names: list[str] = field(default_factory=list)
    node_physics_feature_names: list[str] = field(default_factory=list)
    global_signal_feature_names: list[str] = field(default_factory=list)
    global_physics_feature_names: list[str] = field(default_factory=list)
    node_kg_feature_names: list[str] = field(default_factory=list)
    global_kg_feature_names: list[str] = field(default_factory=list)
    sequence_node_features: list[list[list[float]]] = field(default_factory=list)
    sequence_global_signal_features: list[list[float]] = field(default_factory=list)
    sequence_node_kg_features: list[list[list[float]]] = field(default_factory=list)
    sequence_global_kg_features: list[list[float]] = field(default_factory=list)
    node_physics_features: list[list[float]] = field(default_factory=list)
    global_physics_features: list[float] = field(default_factory=list)
    adjacency: list[list[float]] = field(default_factory=list)
    regression_targets: list[float] = field(default_factory=list)
    hotspot_targets: list[float] = field(default_factory=list)
    observed_mask: list[bool] = field(default_factory=list)
    physics_baseline: list[float] = field(default_factory=list)
    physics_quality_mask: list[float] = field(default_factory=list)
    quality_flags: list[str] = field(default_factory=list)
    metadata: list[dict[str, Any]] = field(default_factory=list)



def _node_record_from_dict(payload: dict[str, Any]) -> NodeRecord:
    return NodeRecord(
        node_id=str(payload['node_id']),
        node_type=str(payload['node_type']),
        index=int(payload['index']),
        bus_id=str(payload['bus_id']) if payload.get('bus_id') is not None else None,
        metadata=dict(payload.get('metadata', {})),
    )



def _edge_record_from_dict(payload: dict[str, Any]) -> EdgeRecord:
    return EdgeRecord(
        edge_id=str(payload['edge_id']),
        edge_type=str(payload['edge_type']),
        source_node=str(payload['source_node']),
        target_node=str(payload['target_node']),
        features={str(key): float(value) for key, value in payload.get('features', {}).items()},
        metadata=dict(payload.get('metadata', {})),
    )



def load_graph_sample(path: str | Path) -> GraphSample:
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    feature_bundle = payload['feature_bundle']
    label_bundle = payload['label_bundle']
    mask_bundle = payload['mask_bundle']
    return GraphSample(
        graph_id=str(payload['graph_id']),
        sample_id=str(payload['sample_id']),
        scenario_id=str(payload['scenario_id']),
        time_index=[str(item) for item in payload.get('time_index', [])],
        node_records=[_node_record_from_dict(item) for item in payload.get('node_records', [])],
        edge_records=[_edge_record_from_dict(item) for item in payload.get('edge_records', [])],
        feature_bundle=GraphFeatureBundle(
            node_feature_names=[str(item) for item in feature_bundle.get('node_feature_names', [])],
            node_features={str(key): [float(value) for value in values] for key, values in feature_bundle.get('node_features', {}).items()},
            global_feature_names=[str(item) for item in feature_bundle.get('global_feature_names', [])],
            global_features=[float(item) for item in feature_bundle.get('global_features', [])],
            quality_flags=[str(item) for item in feature_bundle.get('quality_flags', [])],
        ),
        label_bundle=GraphLabelBundle(
            target_level=str(label_bundle.get('target_level', 'bus')),
            objective=str(label_bundle.get('objective', 'regression')),
            target_names=[str(item) for item in label_bundle.get('target_names', [])],
            node_targets={str(key): float(value) for key, value in label_bundle.get('node_targets', {}).items()},
            transformer_targets={str(key): float(value) for key, value in label_bundle.get('transformer_targets', {}).items()},
            metadata=dict(label_bundle.get('metadata', {})),
        ),
        mask_bundle=MaskBundle(
            sparsity_rate=float(mask_bundle.get('sparsity_rate', 0.0)),
            observed_nodes=[str(item) for item in mask_bundle.get('observed_nodes', [])],
            target_nodes=[str(item) for item in mask_bundle.get('target_nodes', [])],
            observed_mask={str(key): bool(value) for key, value in mask_bundle.get('observed_mask', {}).items()},
            target_mask={str(key): bool(value) for key, value in mask_bundle.get('target_mask', {}).items()},
            metadata=dict(mask_bundle.get('metadata', {})),
        ),
        metadata=dict(payload.get('metadata', {})),
        version=str(payload.get('version', '1.0')),
    )



def _node_metadata(sample: GraphSample, node_id: str) -> dict[str, Any]:
    return {
        'graph_id': sample.graph_id,
        'node_id': node_id,
        'sample_id': sample.sample_id,
        'scenario_id': sample.scenario_id,
        'time_index': sample.time_index[0] if sample.time_index else None,
        'source_case_id': sample.metadata.get('source_case_id'),
    }



def _build_adjacency_matrix(sample: GraphSample, include_self_loops: bool = True) -> list[list[float]]:
    node_ids = [item.node_id for item in sample.node_records]
    index = {node_id: position for position, node_id in enumerate(node_ids)}
    adjacency = [[0.0 for _ in node_ids] for _ in node_ids]
    for edge in sample.edge_records:
        source_index = index[edge.source_node]
        target_index = index[edge.target_node]
        adjacency[source_index][target_index] += 1.0
    if include_self_loops:
        for position in range(len(node_ids)):
            adjacency[position][position] += 1.0
    return adjacency



def build_node_regression_examples(samples: list[GraphSample], target_level: str = 'bus') -> list[NodeRegressionExample]:
    if target_level != 'bus':
        raise NotImplementedError(f'Only bus-level node regression is implemented in the current Phase 4 pass: {target_level}')
    examples: list[NodeRegressionExample] = []
    for sample in samples:
        for node in sample.node_records:
            node_id = node.node_id
            examples.append(
                NodeRegressionExample(
                    graph_id=sample.graph_id,
                    node_id=node_id,
                    features=list(sample.feature_bundle.node_features[node_id]),
                    target=float(sample.label_bundle.node_targets[node_id]),
                    observed=bool(sample.mask_bundle.observed_mask.get(node_id, False)),
                    metadata=_node_metadata(sample, node_id),
                )
            )
    return examples



def build_graph_regression_examples(samples: list[GraphSample], target_level: str = 'bus') -> list[GraphRegressionExample]:
    if target_level != 'bus':
        raise NotImplementedError(f'Only bus-level graph regression is implemented in the current Phase 4 pass: {target_level}')
    examples: list[GraphRegressionExample] = []
    for sample in samples:
        node_ids = [item.node_id for item in sample.node_records]
        examples.append(
            GraphRegressionExample(
                graph_id=sample.graph_id,
                node_ids=node_ids,
                features=[list(sample.feature_bundle.node_features[node_id]) for node_id in node_ids],
                targets=[float(sample.label_bundle.node_targets[node_id]) for node_id in node_ids],
                observed_mask=[bool(sample.mask_bundle.observed_mask.get(node_id, False)) for node_id in node_ids],
                adjacency=_build_adjacency_matrix(sample),
                metadata=[_node_metadata(sample, node_id) for node_id in node_ids],
            )
        )
    return examples



def _iso_time_key(sample: GraphSample) -> str:
    return sample.time_index[0] if sample.time_index else sample.graph_id



def _quantile_threshold(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = min(max(int(round((len(ordered) - 1) * quantile)), 0), len(ordered) - 1)
    return float(ordered[position])



def _prefix_indices(names: list[str], prefix: str) -> list[int]:
    return [index for index, name in enumerate(names) if name.startswith(prefix)]



def _feature_values_for_indices(row: list[float], indices: list[int]) -> list[float]:
    return [float(row[index]) for index in indices]



def _sequence_values_for_indices(sequence_rows: list[list[float]], indices: list[int]) -> list[list[float]]:
    return [_feature_values_for_indices(row, indices) for row in sequence_rows]



def _align_named_values(names: list[str], value_names: list[str], values: list[float]) -> list[float]:
    if not names:
        return []
    lookup = {str(name): float(values[index]) for index, name in enumerate(value_names) if index < len(values)}
    return [float(lookup.get(name, 0.0)) for name in names]



def _kg_graph_feature_view(
    graph_id: str,
    *,
    node_ids: list[str],
    kg_feature_payload: dict[str, Any] | None,
) -> tuple[list[str], list[str], list[float], dict[str, list[float]]]:
    if not kg_feature_payload:
        return [], [], [], {node_id: [] for node_id in node_ids}
    global_feature_names = [str(item) for item in kg_feature_payload.get('global_feature_names', [])]
    node_feature_names = [str(item) for item in kg_feature_payload.get('node_feature_names', [])]
    graph_payload = dict(kg_feature_payload.get('graph_features', {}).get(graph_id, {}))
    graph_global_names = [str(item) for item in graph_payload.get('global_feature_names', global_feature_names)]
    graph_global_values = [float(item) for item in graph_payload.get('global_features', [])]
    aligned_global_values = _align_named_values(global_feature_names, graph_global_names, graph_global_values)
    graph_node_names = [str(item) for item in graph_payload.get('node_feature_names', node_feature_names)]
    raw_node_features = dict(graph_payload.get('node_features', {}))
    aligned_node_features: dict[str, list[float]] = {}
    for node_id in node_ids:
        raw_values = [float(item) for item in raw_node_features.get(node_id, [])]
        aligned_node_features[node_id] = _align_named_values(node_feature_names, graph_node_names, raw_values)
    return node_feature_names, global_feature_names, aligned_global_values, aligned_node_features



def _physics_quality_mask(node_physics_features: list[list[float]], node_physics_feature_names: list[str]) -> list[float]:
    if not node_physics_features:
        return []
    solver_index = node_physics_feature_names.index('physics.solver_ok') if 'physics.solver_ok' in node_physics_feature_names else None
    quality_index = node_physics_feature_names.index('physics.quality_flag_count') if 'physics.quality_flag_count' in node_physics_feature_names else None
    assumption_index = node_physics_feature_names.index('physics.assumption_count') if 'physics.assumption_count' in node_physics_feature_names else None
    mask: list[float] = []
    for row in node_physics_features:
        solver_ok = float(row[solver_index]) if solver_index is not None else 1.0
        quality_penalty = float(row[quality_index]) if quality_index is not None else 0.0
        assumption_penalty = float(row[assumption_index]) if assumption_index is not None else 0.0
        quality_value = max(0.0, solver_ok) / (1.0 + quality_penalty + 0.25 * assumption_penalty)
        mask.append(float(quality_value))
    return mask



def build_temporal_graph_examples(
    dataset: GraphDataset,
    *,
    split: str,
    target_level: str = 'bus',
    window_size: int = 3,
    hotspot_quantile: float = 0.75,
    physics_feature_name: str = 'physics.adjacent_induced_abs_sum',
    kg_feature_payload: dict[str, Any] | None = None,
) -> list[TemporalGraphSequenceExample]:
    if target_level != 'bus':
        raise NotImplementedError(f'Only bus-level temporal regression is implemented in the current Phase 5 pass: {target_level}')
    if window_size < 1:
        raise ValueError(f'window_size must be positive: {window_size}')
    target_graph_ids = set(dataset.split_assignments.get(split, []))
    if not target_graph_ids:
        return []
    samples = dataset.load_all_samples()
    by_scenario: dict[str, list[GraphSample]] = {}
    for sample in samples:
        by_scenario.setdefault(sample.scenario_id, []).append(sample)
    examples: list[TemporalGraphSequenceExample] = []
    for scenario_samples in by_scenario.values():
        ordered_samples = sorted(scenario_samples, key=_iso_time_key)
        for end_index in range(len(ordered_samples)):
            target_sample = ordered_samples[end_index]
            if target_sample.graph_id not in target_graph_ids:
                continue
            history_start = max(0, end_index - window_size + 1)
            window = ordered_samples[history_start:end_index + 1]
            if len(window) < window_size:
                window = [window[0]] * (window_size - len(window)) + window
            node_ids = [item.node_id for item in target_sample.node_records]
            all_feature_names = list(target_sample.feature_bundle.node_feature_names)
            local_feature_indices = [
                index for index, name in enumerate(all_feature_names)
                if not name.startswith('signal.') and not name.startswith('physics.')
            ]
            node_physics_feature_indices = _prefix_indices(all_feature_names, 'physics.')
            node_feature_names = [all_feature_names[index] for index in local_feature_indices]
            node_physics_feature_names = [all_feature_names[index] for index in node_physics_feature_indices]
            if physics_feature_name in all_feature_names:
                physics_feature_index = all_feature_names.index(physics_feature_name)
                physics_baseline = [float(target_sample.feature_bundle.node_features[node_id][physics_feature_index]) for node_id in node_ids]
            else:
                physics_baseline = [0.0 for _ in node_ids]
            global_feature_names = list(target_sample.feature_bundle.global_feature_names)
            global_signal_indices = _prefix_indices(global_feature_names, 'signal.')
            global_physics_indices = _prefix_indices(global_feature_names, 'physics.global.')
            global_signal_feature_names = [global_feature_names[index] for index in global_signal_indices]
            global_physics_feature_names = [global_feature_names[index] for index in global_physics_indices]
            target_node_kg_feature_names, target_global_kg_feature_names, target_global_kg_values, target_node_kg_values = _kg_graph_feature_view(
                target_sample.graph_id,
                node_ids=node_ids,
                kg_feature_payload=kg_feature_payload,
            )
            abs_targets = [abs(float(target_sample.label_bundle.node_targets[node_id])) for node_id in node_ids]
            hotspot_threshold = _quantile_threshold(abs_targets, hotspot_quantile)
            metadata: list[dict[str, Any]] = []
            for node_id in node_ids:
                row = _node_metadata(target_sample, node_id)
                row['hotspot_threshold'] = hotspot_threshold
                row['physics_feature_name'] = physics_feature_name
                row['quality_flags'] = list(target_sample.metadata.get('quality_flags', []))
                row['assumptions'] = list(target_sample.metadata.get('assumptions', []))
                row['solver_status'] = target_sample.metadata.get('solver_status')
                metadata.append(row)
            node_physics_features = [
                _feature_values_for_indices(target_sample.feature_bundle.node_features[node_id], node_physics_feature_indices)
                for node_id in node_ids
            ]
            sequence_node_kg_features: list[list[list[float]]] = []
            sequence_global_kg_features: list[list[float]] = []
            for sample in window:
                _, _, step_global_kg_values, step_node_kg_values = _kg_graph_feature_view(
                    sample.graph_id,
                    node_ids=node_ids,
                    kg_feature_payload=kg_feature_payload,
                )
                sequence_global_kg_features.append(step_global_kg_values)
                sequence_node_kg_features.append([list(step_node_kg_values[node_id]) for node_id in node_ids])
            examples.append(
                TemporalGraphSequenceExample(
                    target_graph_id=target_sample.graph_id,
                    sequence_graph_ids=[sample.graph_id for sample in window],
                    node_ids=node_ids,
                    node_feature_names=node_feature_names,
                    node_physics_feature_names=node_physics_feature_names,
                    global_signal_feature_names=global_signal_feature_names,
                    global_physics_feature_names=global_physics_feature_names,
                    node_kg_feature_names=target_node_kg_feature_names,
                    global_kg_feature_names=target_global_kg_feature_names,
                    sequence_node_features=[
                        [_feature_values_for_indices(sample.feature_bundle.node_features[node_id], local_feature_indices) for node_id in node_ids]
                        for sample in window
                    ],
                    sequence_global_signal_features=[
                        _feature_values_for_indices(sample.feature_bundle.global_features, global_signal_indices)
                        for sample in window
                    ],
                    sequence_node_kg_features=sequence_node_kg_features,
                    sequence_global_kg_features=sequence_global_kg_features,
                    node_physics_features=node_physics_features,
                    global_physics_features=_feature_values_for_indices(target_sample.feature_bundle.global_features, global_physics_indices),
                    adjacency=_build_adjacency_matrix(target_sample),
                    regression_targets=[float(target_sample.label_bundle.node_targets[node_id]) for node_id in node_ids],
                    hotspot_targets=[1.0 if abs(float(target_sample.label_bundle.node_targets[node_id])) >= hotspot_threshold else 0.0 for node_id in node_ids],
                    observed_mask=[bool(target_sample.mask_bundle.observed_mask.get(node_id, False)) for node_id in node_ids],
                    physics_baseline=physics_baseline,
                    physics_quality_mask=_physics_quality_mask(node_physics_features, node_physics_feature_names),
                    quality_flags=list(target_sample.feature_bundle.quality_flags),
                    metadata=metadata,
                )
            )
    return examples



def load_node_regression_examples(dataset_path: str | Path, split: str | None = None, target_level: str = 'bus') -> list[NodeRegressionExample]:
    dataset = GraphDataset.from_path(dataset_path)
    return build_node_regression_examples(dataset.load_samples(split=split), target_level=target_level)



def load_graph_regression_examples(dataset_path: str | Path, split: str | None = None, target_level: str = 'bus') -> list[GraphRegressionExample]:
    dataset = GraphDataset.from_path(dataset_path)
    return build_graph_regression_examples(dataset.load_samples(split=split), target_level=target_level)



def load_temporal_graph_examples(
    dataset_path: str | Path,
    *,
    split: str,
    target_level: str = 'bus',
    window_size: int = 3,
    hotspot_quantile: float = 0.75,
    physics_feature_name: str = 'physics.adjacent_induced_abs_sum',
    kg_feature_payload: dict[str, Any] | None = None,
) -> list[TemporalGraphSequenceExample]:
    dataset = GraphDataset.from_path(dataset_path)
    return build_temporal_graph_examples(
        dataset,
        split=split,
        target_level=target_level,
        window_size=window_size,
        hotspot_quantile=hotspot_quantile,
        physics_feature_name=physics_feature_name,
        kg_feature_payload=kg_feature_payload,
    )



def _basic_split_assignments(graph_ids: list[str], split_config: dict[str, float]) -> dict[str, list[str]]:
    ordered = list(graph_ids)
    total = len(ordered)
    if total == 0:
        return {'train': [], 'val': [], 'test': []}
    train_ratio = float(split_config.get('train', 0.6))
    val_ratio = float(split_config.get('val', 0.2))
    train_count = max(1, int(total * train_ratio))
    val_count = max(1, int(total * val_ratio)) if total >= 3 else max(0, total - train_count - 1)
    if train_count + val_count >= total:
        val_count = max(0, total - train_count - 1)
    test_count = max(0, total - train_count - val_count)
    if test_count == 0 and total >= 3:
        test_count = 1
        if train_count > 1:
            train_count -= 1
        elif val_count > 0:
            val_count -= 1
    return {
        'train': ordered[:train_count],
        'val': ordered[train_count:train_count + val_count],
        'test': ordered[train_count + val_count:train_count + val_count + test_count],
    }



def build_split_assignments(
    graph_ids: list[str],
    split_config: dict[str, float],
    group_assignments: dict[str, str] | None = None,
) -> dict[str, list[str]]:
    if not group_assignments:
        return _basic_split_assignments(graph_ids, split_config)
    ordered_group_ids: list[str] = []
    group_to_graph_ids: dict[str, list[str]] = {}
    for graph_id in graph_ids:
        group_id = str(group_assignments.get(graph_id, graph_id))
        if group_id not in group_to_graph_ids:
            ordered_group_ids.append(group_id)
            group_to_graph_ids[group_id] = []
        group_to_graph_ids[group_id].append(graph_id)
    shuffled_group_ids = list(ordered_group_ids)
    if len(shuffled_group_ids) > 1:
        rng = random.Random(int(split_config.get('seed', 42)))
        rng.shuffle(shuffled_group_ids)
    grouped = _basic_split_assignments(shuffled_group_ids, split_config)
    return {
        split_name: [graph_id for group_id in grouped[split_name] for graph_id in group_to_graph_ids.get(group_id, [])]
        for split_name in ('train', 'val', 'test')
    }



def load_graph_manifest(path: str | Path) -> GraphManifest:
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    return GraphManifest(**payload)
