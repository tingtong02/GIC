from __future__ import annotations

import torch
from torch import nn


class InputEncoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, dropout: float = 0.0) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(float(dropout)) if dropout > 0 else nn.Identity(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(features)
