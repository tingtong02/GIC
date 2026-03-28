from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class KGFusionBundle:
    global_feature_names: list[str]
    global_features: list[float]
    node_feature_names: list[str]
    node_features: dict[str, list[float]]
    source_graph_id: str


def build_kg_fusion_bundle(graph_id: str, feature_payload: dict[str, Any]) -> KGFusionBundle:
    graph_features = feature_payload['graph_features'][graph_id]
    return KGFusionBundle(
        global_feature_names=[str(item) for item in graph_features.get('global_feature_names', [])],
        global_features=[float(item) for item in graph_features.get('global_features', [])],
        node_feature_names=[str(item) for item in graph_features.get('node_feature_names', [])],
        node_features={str(key): [float(value) for value in values] for key, values in graph_features.get('node_features', {}).items()},
        source_graph_id=graph_id,
    )


def merge_feature_names(base_feature_names: list[str], kg_feature_names: list[str]) -> list[str]:
    return list(base_feature_names) + [name for name in kg_feature_names if name not in base_feature_names]
