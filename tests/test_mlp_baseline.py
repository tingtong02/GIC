from __future__ import annotations

import torch

from gic.models import build_mlp_baseline


def test_mlp_baseline_forward_returns_node_predictions() -> None:
    model = build_mlp_baseline({'hidden_dims': [16, 8], 'dropout': 0.0}, input_dim=6)
    features = torch.randn(4, 6)
    predictions = model(features)
    assert predictions.shape == (4,)
