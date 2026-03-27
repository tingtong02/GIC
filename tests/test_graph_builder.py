from __future__ import annotations

from pathlib import Path

from gic.config import load_config
from gic.graph import build_graph_samples_from_config, validate_graph_sample


ROOT = Path(__file__).resolve().parents[1]
PHASE4_CONFIG = ROOT / 'configs/phase4/phase4_dev.yaml'


def test_graph_builder_creates_bus_graph_samples() -> None:
    config = load_config(PHASE4_CONFIG)
    task, build_context, samples = build_graph_samples_from_config(ROOT, config)
    assert task.node_type == 'bus'
    assert build_context['dataset_name'] == 'timeseries_case118_graph_default'
    assert len(samples) == 5
    first = samples[0]
    assert len(first.node_records) == 3
    assert len(first.edge_records) >= 4
    assert first.mask_bundle.sparsity_rate == 0.7
    assert first.label_bundle.node_targets['bus_1'] != 0.0
    assert 'signal.summary_statistics.bx_nT.max' in first.feature_bundle.node_feature_names


def test_graph_builder_validation_passes_for_exportable_sample() -> None:
    config = load_config(PHASE4_CONFIG)
    _, _, samples = build_graph_samples_from_config(ROOT, config)
    report = validate_graph_sample(samples[0])
    assert report['ok'] is True
