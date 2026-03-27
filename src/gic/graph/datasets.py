from __future__ import annotations

import json
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



def load_node_regression_examples(dataset_path: str | Path, split: str | None = None, target_level: str = 'bus') -> list[NodeRegressionExample]:
    dataset = GraphDataset.from_path(dataset_path)
    return build_node_regression_examples(dataset.load_samples(split=split), target_level=target_level)



def load_graph_regression_examples(dataset_path: str | Path, split: str | None = None, target_level: str = 'bus') -> list[GraphRegressionExample]:
    dataset = GraphDataset.from_path(dataset_path)
    return build_graph_regression_examples(dataset.load_samples(split=split), target_level=target_level)



def build_split_assignments(graph_ids: list[str], split_config: dict[str, float]) -> dict[str, list[str]]:
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



def load_graph_manifest(path: str | Path) -> GraphManifest:
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    return GraphManifest(**payload)
