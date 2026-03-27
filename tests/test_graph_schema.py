from __future__ import annotations

from gic.graph.schema import GraphFeatureBundle, GraphLabelBundle, GraphSample, MaskBundle, NodeRecord, EdgeRecord


def test_graph_sample_schema_holds_minimum_fields() -> None:
    sample = GraphSample(
        graph_id='graph_001',
        sample_id='sample_001',
        scenario_id='scenario_001',
        time_index=['2024-01-01T00:00:00Z'],
        node_records=[NodeRecord(node_id='bus_1', node_type='bus', index=0, bus_id='bus_1')],
        edge_records=[EdgeRecord(edge_id='edge_1', edge_type='electrical_connectivity', source_node='bus_1', target_node='bus_1')],
        feature_bundle=GraphFeatureBundle(node_feature_names=['f0'], node_features={'bus_1': [1.0]}),
        label_bundle=GraphLabelBundle(target_level='bus', objective='regression', target_names=['gic'], node_targets={'bus_1': 1.0}),
        mask_bundle=MaskBundle(sparsity_rate=0.7, observed_nodes=['bus_1'], target_nodes=['bus_1'], observed_mask={'bus_1': True}, target_mask={'bus_1': True}),
    )
    assert sample.graph_id == 'graph_001'
    assert sample.feature_bundle.node_features['bus_1'] == [1.0]
    assert sample.label_bundle.node_targets['bus_1'] == 1.0
