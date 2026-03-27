from __future__ import annotations

from typing import Any

import torch
from torch import nn

from gic.models.base import BaselineModel


class MLPBaseline(BaselineModel):
    model_name = 'mlp'

    def __init__(self, input_dim: int, hidden_dims: list[int], dropout: float = 0.0) -> None:
        super().__init__()
        if input_dim <= 0:
            raise ValueError('MLPBaseline input_dim must be positive')
        if not hidden_dims:
            raise ValueError('MLPBaseline requires at least one hidden layer')
        layers: list[nn.Module] = []
        previous_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(previous_dim, int(hidden_dim)))
            layers.append(nn.ReLU())
            if dropout > 0:
                layers.append(nn.Dropout(float(dropout)))
            previous_dim = int(hidden_dim)
        layers.append(nn.Linear(previous_dim, 1))
        self.network = nn.Sequential(*layers)

    def forward(
        self,
        features: torch.Tensor,
        *,
        adjacency: torch.Tensor | None = None,
        graph_index: torch.Tensor | None = None,
    ) -> torch.Tensor:
        return self.network(features).squeeze(-1)



def build_mlp_baseline(model_config: dict[str, Any], input_dim: int) -> MLPBaseline:
    hidden_dims = [int(item) for item in model_config.get('hidden_dims', [32, 32])]
    dropout = float(model_config.get('dropout', 0.0))
    return MLPBaseline(input_dim=input_dim, hidden_dims=hidden_dims, dropout=dropout)
