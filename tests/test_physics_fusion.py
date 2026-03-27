from __future__ import annotations

import torch

from gic.models.fusion import PhysicsFusion


def test_physics_fusion_residual_mode_uses_physics_baseline() -> None:
    fusion = PhysicsFusion(hidden_dim=8, mode='residual', use_physics_features=True)
    state = torch.randn(2, 3, 8)
    baseline = torch.randn(2, 3)
    output = fusion(state, baseline)
    assert output.fused_features.shape == (2, 3, 8)
    assert torch.allclose(output.residual_base, baseline)


def test_physics_fusion_can_disable_physics_features() -> None:
    fusion = PhysicsFusion(hidden_dim=4, mode='residual', use_physics_features=False)
    state = torch.randn(1, 2, 4)
    baseline = torch.randn(1, 2)
    output = fusion(state, baseline)
    assert output.fused_features.shape == (1, 2, 4)
    assert torch.equal(output.residual_base, torch.zeros_like(baseline))
