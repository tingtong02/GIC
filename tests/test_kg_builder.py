from __future__ import annotations

from pathlib import Path

from gic.config import load_config
from gic.kg.builder import build_kg_bundle


ROOT = Path(__file__).resolve().parents[1]
PHASE6_CONFIG = ROOT / 'configs/phase6/phase6_dev.yaml'


def test_build_kg_bundle_contains_required_entities_and_relations() -> None:
    config = load_config(PHASE6_CONFIG)
    result = build_kg_bundle(dataset_path=config['graph']['dataset_path'], project_root=ROOT, kg_config=config['kg'])
    assert result.dataset_name == 'case118_graph_broader'
    assert result.validation['entity_counts']['Grid'] == 1
    assert result.validation['entity_counts']['Bus'] == 3
    assert result.validation['entity_counts']['Observation'] == 14
    assert result.validation['entity_counts']['Scenario'] == 10
    assert result.validation['relation_counts']['connected_to'] == 6
    assert result.validation['relation_counts']['derived_under_scenario'] == 14
    assert result.validation['relation_counts']['has_sensor'] == 1
    assert result.feature_payload['graph_count'] == 14
