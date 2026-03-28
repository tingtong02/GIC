from __future__ import annotations

from pathlib import Path

from gic.config import load_config
from gic.kg.builder import build_kg_bundle
from gic.kg.query import query_sample


ROOT = Path(__file__).resolve().parents[1]
PHASE6_CONFIG = ROOT / 'configs/phase6/phase6_dev.yaml'


def test_query_sample_includes_rules_and_global_features() -> None:
    config = load_config(PHASE6_CONFIG)
    result = build_kg_bundle(dataset_path=config['graph']['dataset_path'], project_root=ROOT, kg_config=config['kg'])
    payload = query_sample(
        identifier='timeseries_matpower_case118_sample_20240101_000400',
        sample_index=result.sample_index,
        feature_payload=result.feature_payload,
        rule_payload=result.rule_payload,
    )
    assert payload['scenario_id'] == 'timeseries_matpower_case118_sample'
    assert payload['global_features']['kg.global.scenario_is_timeseries'] == 1.0
    assert any(item['rule_name'] == 'assumption_present' for item in payload['rule_findings'])
