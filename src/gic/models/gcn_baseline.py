from __future__ import annotations

from typing import Any

import torch
from torch import nn

from gic.models.base import BaselineModel


class GCNLayer(nn.Module):
    def __init__(self, input_dim: int, output_dim: int) -> None:
        super().__init__()
        self.linear = nn.Linear(input_dim, output_dim)

    def forward(self, features: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        degree = adjacency.sum(dim=-1).clamp(min=1.0)
        degree_inv_sqrt = degree.pow(-0.5)
        normalized = degree_inv_sqrt.unsqueeze(-1) * adjacency * degree_inv_sqrt.unsqueeze(0)
        return normalized @ self.linear(features)


class GCNBaseline(BaselineModel):
    model_name = 'gcn'

    def __init__(self, input_dim: int, hidden_dim: int, layers: int = 2, dropout: float = 0.0) -> None:
        super().__init__()
        if input_dim <= 0:
            raise ValueError('GCNBaseline input_dim must be positive')
        if layers < 1:
            raise ValueError('GCNBaseline requires at least one layer')
        self.dropout = nn.Dropout(float(dropout)) if dropout > 0 else nn.Identity()
        hidden_layers: list[nn.Module] = []
        previous_dim = input_dim
        for _ in range(max(1, layers - 1)):
            hidden_layers.append(GCNLayer(previous_dim, hidden_dim))
            previous_dim = hidden_dim
        self.hidden_layers = nn.ModuleList(hidden_layers)
        self.output_layer = GCNLayer(previous_dim, 1)

    def forward(
        self,
        features: torch.Tensor,
        *,
        adjacency: torch.Tensor | None = None,
        graph_index: torch.Tensor | None = None,
    ) -> torch.Tensor:
        if adjacency is None:
            raise ValueError('GCNBaseline requires adjacency information')
        hidden = features
        for layer in self.hidden_layers:
            hidden = torch.relu(layer(hidden, adjacency))
            hidden = self.dropout(hidden)
        return self.output_layer(hidden, adjacency).squeeze(-1)



def build_gcn_baseline(model_config: dict[str, Any], input_dim: int) -> GCNBaseline:
    return GCNBaseline(
        input_dim=input_dim,
        hidden_dim=int(model_config.get('hidden_dim', 32)),
        layers=int(model_config.get('layers', 2)),
        dropout=float(model_config.get('dropout', 0.0)),
    )
