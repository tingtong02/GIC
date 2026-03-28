from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


@dataclass(slots=True)
class PhysicsFusionOutput:
    fused_features: torch.Tensor
    residual_base: torch.Tensor
    quality_gate: torch.Tensor


class PhysicsFusion(nn.Module):
    def __init__(
        self,
        hidden_dim: int,
        *,
        node_physics_dim: int = 0,
        global_physics_dim: int = 0,
        mode: str = 'residual',
        use_physics_features: bool = True,
    ) -> None:
        super().__init__()
        self.hidden_dim = int(hidden_dim)
        self.mode = str(mode)
        self.use_physics_features = bool(use_physics_features)
        self.node_physics_dim = max(0, int(node_physics_dim))
        self.global_physics_dim = max(0, int(global_physics_dim))
        self.node_physics_encoder = self._physics_encoder(self.node_physics_dim)
        self.global_physics_encoder = self._physics_encoder(self.global_physics_dim)
        fusion_input_dim = self.hidden_dim + 1 + 1
        if self.node_physics_encoder is not None:
            fusion_input_dim += self.hidden_dim
        if self.global_physics_encoder is not None:
            fusion_input_dim += self.hidden_dim
        self.fusion_layer = nn.Sequential(
            nn.Linear(fusion_input_dim, self.hidden_dim),
            nn.ReLU(),
        ) if self.use_physics_features else nn.Identity()

    def _physics_encoder(self, input_dim: int) -> nn.Module | None:
        if not self.use_physics_features or input_dim <= 0:
            return None
        return nn.Sequential(
            nn.Linear(input_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.ReLU(),
        )

    def _normalize_physics(self, values: torch.Tensor) -> torch.Tensor:
        centered = values - values.mean(dim=-1, keepdim=True)
        scale = centered.std(dim=-1, keepdim=True).clamp(min=1e-6)
        return centered / scale

    def forward(
        self,
        node_state: torch.Tensor,
        physics_baseline: torch.Tensor,
        node_physics_features: torch.Tensor | None = None,
        global_physics_features: torch.Tensor | None = None,
        physics_quality_mask: torch.Tensor | None = None,
    ) -> PhysicsFusionOutput:
        if not self.use_physics_features:
            return PhysicsFusionOutput(
                fused_features=node_state,
                residual_base=torch.zeros_like(physics_baseline),
                quality_gate=torch.ones_like(physics_baseline),
            )

        normalized_baseline = self._normalize_physics(physics_baseline).unsqueeze(-1)
        if physics_quality_mask is None:
            quality_gate = torch.ones_like(physics_baseline).unsqueeze(-1)
        else:
            quality_gate = physics_quality_mask.unsqueeze(-1).clamp(0.0, 1.0)
        features = [node_state, normalized_baseline, quality_gate]
        if self.node_physics_encoder is not None and node_physics_features is not None and node_physics_features.shape[-1] > 0:
            features.append(self.node_physics_encoder(node_physics_features))
        if self.global_physics_encoder is not None and global_physics_features is not None and global_physics_features.shape[-1] > 0:
            encoded_global = self.global_physics_encoder(global_physics_features).unsqueeze(1)
            features.append(encoded_global.expand(-1, node_state.shape[1], -1))
        fused_candidate = self.fusion_layer(torch.cat(features, dim=-1))
        fused = quality_gate * fused_candidate + (1.0 - quality_gate) * node_state
        residual_base = physics_baseline if self.mode == 'residual' else torch.zeros_like(physics_baseline)
        return PhysicsFusionOutput(
            fused_features=fused,
            residual_base=residual_base,
            quality_gate=quality_gate.squeeze(-1),
        )
