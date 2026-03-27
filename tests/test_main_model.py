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
            'use_physics_features': True,
            'use_residual': True,
        },
        'tasks': {
            'hotspot': True,
            'risk_score': False,
            'uncertainty': False,
        },
    }
    model = build_main_model(config, input_dim=6)
    batch = MainModelInputBundle(
        sequence_features=torch.randn(2, 3, 4, 6),
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
