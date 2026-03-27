from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


GRAPH_SCHEMA_VERSION = "1.0"


@dataclass(slots=True)
class NodeRecord:
    node_id: str
    node_type: str
    index: int
    bus_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EdgeRecord:
    edge_id: str
    edge_type: str
    source_node: str
    target_node: str
    features: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GraphFeatureBundle:
    node_feature_names: list[str]
    node_features: dict[str, list[float]]
    global_feature_names: list[str] = field(default_factory=list)
    global_features: list[float] = field(default_factory=list)
    quality_flags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GraphLabelBundle:
    target_level: str
    objective: str
    target_names: list[str]
    node_targets: dict[str, float] = field(default_factory=dict)
    transformer_targets: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MaskBundle:
    sparsity_rate: float
    observed_nodes: list[str]
    target_nodes: list[str]
    observed_mask: dict[str, bool]
    target_mask: dict[str, bool]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GraphSample:
    graph_id: str
    sample_id: str
    scenario_id: str
    time_index: list[str]
    node_records: list[NodeRecord]
    edge_records: list[EdgeRecord]
    feature_bundle: GraphFeatureBundle
    label_bundle: GraphLabelBundle
    mask_bundle: MaskBundle
    metadata: dict[str, Any] = field(default_factory=dict)
    version: str = GRAPH_SCHEMA_VERSION


@dataclass(slots=True)
class GraphBatch:
    batch_id: str
    graph_ids: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReconstructionTaskConfig:
    target_level: str
    objective: str
    node_type: str
    sparsity_rate: float
    include_signal_features: bool = False
    include_physics_baseline: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GraphManifest:
    dataset_name: str
    source_case_id: str
    scenario_id: str
    graph_count: int
    node_count: int
    edge_count: int
    generated_at_utc: str
    graph_paths: list[str]
    split_assignments: dict[str, list[str]]
    sparsity_rate: float
    task: dict[str, Any]
    notes: str = ''
    paths: dict[str, str] = field(default_factory=dict)
    version: str = GRAPH_SCHEMA_VERSION


def graph_to_dict(value: Any) -> Any:
    if hasattr(value, '__dataclass_fields__'):
        return asdict(value)
    if isinstance(value, list):
        return [graph_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: graph_to_dict(item) for key, item in value.items()}
    return value
