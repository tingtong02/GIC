from __future__ import annotations

import torch
from torch import nn


class InputEncoder(nn.Module):
    def __init__(
        self,
        node_input_dim: int,
        hidden_dim: int,
        *,
        global_signal_dim: int = 0,
        dropout: float = 0.0,
    ) -> None:
        super().__init__()
        if node_input_dim <= 0:
            raise ValueError('InputEncoder requires node_input_dim > 0')
        self.node_input_dim = int(node_input_dim)
        self.global_signal_dim = max(0, int(global_signal_dim))
        self.hidden_dim = int(hidden_dim)
        dropout_layer = nn.Dropout(float(dropout)) if float(dropout) > 0 else nn.Identity()
        self.node_network = nn.Sequential(
            nn.Linear(self.node_input_dim, self.hidden_dim),
            nn.ReLU(),
            dropout_layer,
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.ReLU(),
        )
        if self.global_signal_dim > 0:
            self.signal_network = nn.Sequential(
                nn.Linear(self.global_signal_dim, self.hidden_dim),
                nn.ReLU(),
                nn.Linear(self.hidden_dim, self.hidden_dim),
                nn.ReLU(),
            )
            self.fusion = nn.Sequential(
                nn.Linear(self.hidden_dim * 2, self.hidden_dim),
                nn.ReLU(),
            )
        else:
            self.signal_network = None
            self.fusion = nn.Identity()

    def forward(
        self,
        node_features: torch.Tensor,
        global_signal_features: torch.Tensor | None = None,
    ) -> torch.Tensor:
        if node_features.ndim != 4:
            raise ValueError(f'InputEncoder expects [batch, steps, nodes, features], got {tuple(node_features.shape)}')
        encoded_nodes = self.node_network(node_features)
        if self.signal_network is None or global_signal_features is None:
            return encoded_nodes
        if global_signal_features.ndim != 3:
            raise ValueError(
                'InputEncoder expects global signal features shaped [batch, steps, features], '
                f'got {tuple(global_signal_features.shape)}'
            )
        if global_signal_features.shape[:2] != node_features.shape[:2]:
            raise ValueError('Global signal sequence must align with node feature sequence steps')
        encoded_signal = self.signal_network(global_signal_features).unsqueeze(2)
        encoded_signal = encoded_signal.expand(-1, -1, node_features.shape[2], -1)
        return self.fusion(torch.cat([encoded_nodes, encoded_signal], dim=-1))
