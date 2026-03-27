from __future__ import annotations

import torch
from torch import nn


class HotspotHead(nn.Module):
    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        self.projection = nn.Linear(hidden_dim, 1)

    def forward(self, node_state: torch.Tensor) -> torch.Tensor:
        return self.projection(node_state).squeeze(-1)
