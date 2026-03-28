from __future__ import annotations

import torch

from gic.models import MainModelInputBundle, build_main_model


def test_phase5_main_model_forward_returns_regression_and_hotspot_outputs() -> None:
    config = {
        'model': {
            'graph_backbone': 'graphsage',
            'graph_layers': 2,
            'hidden_dim': 16,
            'dropout': 0.0,
            'temporal_encoder': 'gru',
            'physics_fusion': 'residual',
            'use_signal_features': True,
            'use_physics_features': True,
            'use_kg_features': True,
            'use_residual': True,
        },
        'tasks': {
            'hotspot': True,
            'risk_score': False,
            'uncertainty': False,
        },
    }
    model = build_main_model(
        config,
        node_input_dim=6,
        global_signal_dim=4,
        node_physics_dim=3,
        global_physics_dim=5,
        node_kg_dim=2,
        global_kg_dim=3,
    )
    batch = MainModelInputBundle(
        sequence_node_features=torch.randn(2, 3, 4, 6),
        sequence_global_signal_features=torch.randn(2, 3, 4),
        sequence_node_kg_features=torch.randn(2, 3, 4, 2),
        sequence_global_kg_features=torch.randn(2, 3, 3),
        node_physics_features=torch.randn(2, 4, 3),
        global_physics_features=torch.randn(2, 5),
        physics_quality_mask=torch.tensor([[1.0, 0.5, 1.0, 0.0], [1.0, 1.0, 0.5, 1.0]], dtype=torch.float32),
        adjacency=torch.eye(4).repeat(2, 1, 1),
        regression_targets=torch.randn(2, 4),
        hotspot_targets=torch.randint(0, 2, (2, 4), dtype=torch.float32),
        observed_mask=torch.tensor([[True, False, True, False], [False, True, False, True]]),
        physics_baseline=torch.randn(2, 4),
        metadata=[[{'node_id': str(i)} for i in range(4)] for _ in range(2)],
    )
    output = model(batch)
    assert output.regression_prediction.shape == (2, 4)
    assert output.hotspot_logits is not None
    assert output.hotspot_logits.shape == (2, 4)
