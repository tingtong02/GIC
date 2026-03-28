from __future__ import annotations

from pathlib import Path

from gic.config import load_config
from gic.kg.builder import build_kg_bundle
from gic.models.fusion.kg_fusion import build_kg_fusion_bundle, merge_feature_names


ROOT = Path(__file__).resolve().parents[1]
PHASE6_CONFIG = ROOT / 'configs/phase6/phase6_dev.yaml'


def test_build_kg_fusion_bundle_and_merge_feature_names() -> None:
    config = load_config(PHASE6_CONFIG)
    result = build_kg_bundle(dataset_path=config['graph']['dataset_path'], project_root=ROOT, kg_config=config['kg'])
    bundle = build_kg_fusion_bundle('timeseries_matpower_case118_sample_20240101_000400', result.feature_payload)
    assert bundle.source_graph_id == 'timeseries_matpower_case118_sample_20240101_000400'
    assert 'kg.global.assumption_count' in bundle.global_feature_names
    merged = merge_feature_names(['signal.a'], ['kg.global.assumption_count', 'signal.a'])
    assert merged == ['signal.a', 'kg.global.assumption_count']
