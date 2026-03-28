from __future__ import annotations

from pathlib import Path

from gic.config import load_config
from gic.kg.builder import build_kg_bundle


ROOT = Path(__file__).resolve().parents[1]
PHASE6_CONFIG = ROOT / 'configs/phase6/phase6_dev.yaml'


def test_feature_payload_exports_graph_and_node_features() -> None:
    config = load_config(ROOT / 'configs/phase6/models/kg_default_full.yaml')
    result = build_kg_bundle(dataset_path=config['graph']['dataset_path'], project_root=ROOT, kg_config=config['kg'])
    graph_id = 'timeseries_matpower_case118_sample_20240101_000400'
    graph_features = result.feature_payload['graph_features'][graph_id]
    assert 'kg.global.assumption_count' in graph_features['global_feature_names']
    assert 'kg.rule.hit_count' in graph_features['global_feature_names']
    assert 'kg.rel.global.connected_to_count' in graph_features['global_feature_names']
    assert 'kg.node.connected_line_count' in graph_features['node_feature_names']
    assert 'kg.rel.node.relation_degree' in graph_features['node_feature_names']
    assert graph_features['feature_groups']['global']['kg.global.bus_count'] == 'topology_context'
    assert 'bus_2' in graph_features['node_features']
    assert graph_features['node_features']['bus_2'][1] >= 1.0
