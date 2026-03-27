from __future__ import annotations

import torch
from torch import nn


class TemporalEncoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, mode: str = 'gru') -> None:
        super().__init__()
        self.mode = str(mode)
        self.hidden_dim = int(hidden_dim)
        if self.mode == 'gru':
            self.encoder = nn.GRU(input_size=input_dim, hidden_size=hidden_dim, batch_first=True)
        elif self.mode == 'none':
            self.encoder = nn.Linear(input_dim, hidden_dim)
        else:
            raise ValueError(f'Unsupported temporal encoder mode: {mode}')

    def forward(self, sequence_features: torch.Tensor) -> torch.Tensor:
        if sequence_features.ndim != 4:
            raise ValueError(f'TemporalEncoder expects [batch, steps, nodes, features], got {tuple(sequence_features.shape)}')
        batch_size, step_count, node_count, feature_dim = sequence_features.shape
        if self.mode == 'none':
            return self.encoder(sequence_features[:, -1, :, :])
        flattened = sequence_features.permute(0, 2, 1, 3).reshape(batch_size * node_count, step_count, feature_dim)
        _, hidden = self.encoder(flattened)
        return hidden[-1].reshape(batch_size, node_count, self.hidden_dim)
