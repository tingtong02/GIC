import json
from pathlib import Path

from gic.graph.datasets import load_graph_regression_examples


def test_real_event_phase4_alignment_maps_legacy_signal_names(tmp_path: Path) -> None:
    sample_path = tmp_path / 'graph_sample.json'
    dataset_path = tmp_path / 'dataset.json'
    sample_payload = {
        'graph_id': 'graph_001',
        'sample_id': 'sample_001',
        'scenario_id': 'real_demo',
        'time_index': ['2020-09-01T00:00:00+00:00'],
        'node_records': [
            {'node_id': 'bus_1', 'node_type': 'bus', 'index': 0, 'bus_id': '1', 'metadata': {}},
            {'node_id': 'bus_2', 'node_type': 'bus', 'index': 1, 'bus_id': '2', 'metadata': {}},
        ],
        'edge_records': [
            {'edge_id': 'line_1', 'edge_type': 'line', 'source_node': 'bus_1', 'target_node': 'bus_2', 'features': {}, 'metadata': {}},
        ],
        'feature_bundle': {
            'node_feature_names': [
                'static.base_kv',
                'observed.bus_quantity',
                'physics.adjacent_induced_abs_sum',
                'physics.adjacent_edge_count',
                'signal.summary_statistics.X.max',
                'signal.summary_statistics.Y.max',
                'signal.summary_statistics.Z.max',
            ],
            'node_features': {
                'bus_1': [230.0, 1.5, 0.2, 1.0, 10.0, 20.0, 30.0],
                'bus_2': [115.0, 0.5, 0.1, 1.0, 11.0, 21.0, 31.0],
            },
            'global_feature_names': [],
            'global_features': [],
            'quality_flags': [],
        },
        'label_bundle': {
            'target_level': 'bus',
            'objective': 'regression',
            'target_names': ['gic'],
            'node_targets': {'bus_1': 1.0, 'bus_2': 2.0},
            'transformer_targets': {},
            'metadata': {},
        },
        'mask_bundle': {
            'sparsity_rate': 0.7,
            'observed_nodes': ['bus_1'],
            'target_nodes': ['bus_2'],
            'observed_mask': {'bus_1': True, 'bus_2': False},
            'target_mask': {'bus_1': False, 'bus_2': True},
            'metadata': {},
        },
        'metadata': {'source_case_id': 'matpower_case118_sample'},
        'version': '1.0',
    }
    dataset_payload = {
        'dataset_name': 'demo',
        'manifest_path': str(tmp_path / 'manifest.json'),
        'graph_paths': [str(sample_path)],
        'split_assignments': {'train': [], 'val': [], 'test': ['graph_sample']},
        'metadata': {},
    }
    sample_path.write_text(json.dumps(sample_payload), encoding='utf-8')
    dataset_path.write_text(json.dumps(dataset_payload), encoding='utf-8')

    feature_names = [
        'static.base_kv',
        'physics.adjacent_induced_abs_sum',
        'signal.summary_statistics.bx_nT.max',
        'signal.summary_statistics.by_nT.max',
        'signal.summary_statistics.bz_nT.max',
    ]
    feature_aliases = {
        'signal.summary_statistics.bx_nT.max': 'signal.summary_statistics.X.max',
        'signal.summary_statistics.by_nT.max': 'signal.summary_statistics.Y.max',
        'signal.summary_statistics.bz_nT.max': 'signal.summary_statistics.Z.max',
    }

    examples = load_graph_regression_examples(
        dataset_path,
        split='test',
        target_level='bus',
        feature_names=feature_names,
        feature_aliases=feature_aliases,
    )

    assert len(examples) == 1
    assert examples[0].features[0] == [230.0, 0.2, 10.0, 20.0, 30.0]
    assert examples[0].features[1] == [115.0, 0.1, 11.0, 21.0, 31.0]
