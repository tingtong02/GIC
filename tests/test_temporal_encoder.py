from __future__ import annotations

import torch

from gic.models.encoders import TemporalEncoder


def test_temporal_encoder_gru_returns_last_state_per_node() -> None:
    encoder = TemporalEncoder(input_dim=4, hidden_dim=8, mode='gru')
    features = torch.randn(2, 3, 5, 4)
    output = encoder(features)
    assert output.shape == (2, 5, 8)


def test_temporal_encoder_none_projects_last_time_step() -> None:
    encoder = TemporalEncoder(input_dim=4, hidden_dim=6, mode='none')
    features = torch.randn(1, 4, 3, 4)
    output = encoder(features)
    assert output.shape == (1, 3, 6)
