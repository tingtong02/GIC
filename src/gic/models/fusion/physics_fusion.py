from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


@dataclass(slots=True)
class PhysicsFusionOutput:
    fused_features: torch.Tensor
    residual_base: torch.Tensor


class PhysicsFusion(nn.Module):
    def __init__(self, hidden_dim: int, *, mode: str = 'residual', use_physics_features: bool = True) -> None:
        super().__init__()
        self.mode = str(mode)
        self.use_physics_features = bool(use_physics_features)
        self.fusion_layer = nn.Linear(hidden_dim + 1, hidden_dim) if self.use_physics_features else nn.Identity()

    def _normalize_physics(self, physics_baseline: torch.Tensor) -> torch.Tensor:
        centered = physics_baseline - physics_baseline.mean(dim=-1, keepdim=True)
        scale = centered.std(dim=-1, keepdim=True).clamp(min=1e-6)
        return centered / scale

    def forward(self, node_state: torch.Tensor, physics_baseline: torch.Tensor) -> PhysicsFusionOutput:
        if self.use_physics_features:
            normalized_physics = self._normalize_physics(physics_baseline)
            fused = torch.relu(self.fusion_layer(torch.cat([node_state, normalized_physics.unsqueeze(-1)], dim=-1)))
        else:
            fused = node_state
        residual_base = physics_baseline if self.mode == 'residual' and self.use_physics_features else torch.zeros_like(physics_baseline)
        return PhysicsFusionOutput(fused_features=fused, residual_base=residual_base)
