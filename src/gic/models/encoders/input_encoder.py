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
        node_kg_dim: int = 0,
        global_kg_dim: int = 0,
        dropout: float = 0.0,
    ) -> None:
        super().__init__()
        if node_input_dim <= 0:
            raise ValueError('InputEncoder requires node_input_dim > 0')
        self.node_input_dim = int(node_input_dim)
        self.global_signal_dim = max(0, int(global_signal_dim))
        self.node_kg_dim = max(0, int(node_kg_dim))
        self.global_kg_dim = max(0, int(global_kg_dim))
        self.hidden_dim = int(hidden_dim)
        dropout_layer = nn.Dropout(float(dropout)) if float(dropout) > 0 else nn.Identity()
        self.node_network = nn.Sequential(
            nn.Linear(self.node_input_dim, self.hidden_dim),
            nn.ReLU(),
            dropout_layer,
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.ReLU(),
        )
        self.signal_network = self._branch(self.global_signal_dim)
        self.node_kg_network = self._branch(self.node_kg_dim)
        self.global_kg_network = self._branch(self.global_kg_dim)
        self.signal_fusion = (
            nn.Sequential(
                nn.Linear(self.hidden_dim * 2, self.hidden_dim),
                nn.ReLU(),
            )
            if self.signal_network is not None
            else nn.Identity()
        )
        self.node_kg_gate = nn.Parameter(torch.tensor(0.1, dtype=torch.float32)) if self.node_kg_network is not None else None
        self.global_kg_gate = nn.Parameter(torch.tensor(0.1, dtype=torch.float32)) if self.global_kg_network is not None else None

    def _branch(self, feature_dim: int) -> nn.Sequential | None:
        if feature_dim <= 0:
            return None
        return nn.Sequential(
            nn.Linear(feature_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.ReLU(),
        )

    def _expand_global_branch(self, network: nn.Sequential | None, values: torch.Tensor | None, *, node_features: torch.Tensor, branch_name: str) -> torch.Tensor | None:
        if network is None or values is None:
            return None
        if values.ndim != 3:
            raise ValueError(
                f'InputEncoder expects {branch_name} features shaped [batch, steps, features], got {tuple(values.shape)}'
            )
        if values.shape[:2] != node_features.shape[:2]:
            raise ValueError(f'{branch_name} sequence must align with node feature sequence steps')
        encoded = network(values).unsqueeze(2)
        return encoded.expand(-1, -1, node_features.shape[2], -1)

    def forward(
        self,
        node_features: torch.Tensor,
        global_signal_features: torch.Tensor | None = None,
        node_kg_features: torch.Tensor | None = None,
        global_kg_features: torch.Tensor | None = None,
    ) -> torch.Tensor:
        if node_features.ndim != 4:
            raise ValueError(f'InputEncoder expects [batch, steps, nodes, features], got {tuple(node_features.shape)}')
        encoded = self.node_network(node_features)
        signal_branch = self._expand_global_branch(
            self.signal_network,
            global_signal_features,
            node_features=node_features,
            branch_name='global signal',
        )
        if signal_branch is not None:
            encoded = self.signal_fusion(torch.cat([encoded, signal_branch], dim=-1))
        if self.node_kg_network is not None and node_kg_features is not None:
            if node_kg_features.ndim != 4:
                raise ValueError(
                    'InputEncoder expects node KG features shaped [batch, steps, nodes, features], '
                    f'got {tuple(node_kg_features.shape)}'
                )
            if node_kg_features.shape[:3] != node_features.shape[:3]:
                raise ValueError('Node KG features must align with node feature batch/step/node dimensions')
            encoded = encoded + torch.tanh(self.node_kg_gate) * self.node_kg_network(node_kg_features)
        global_kg_branch = self._expand_global_branch(
            self.global_kg_network,
            global_kg_features,
            node_features=node_features,
            branch_name='global KG',
        )
        if global_kg_branch is not None:
            encoded = encoded + torch.tanh(self.global_kg_gate) * global_kg_branch
        return encoded
