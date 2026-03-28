from __future__ import annotations

import torch

from gic.models.fusion import PhysicsFusion


def test_physics_fusion_residual_mode_uses_physics_baseline() -> None:
    fusion = PhysicsFusion(hidden_dim=8, node_physics_dim=2, global_physics_dim=3, mode='residual', use_physics_features=True)
    state = torch.randn(2, 3, 8)
    baseline = torch.randn(2, 3)
    node_physics = torch.randn(2, 3, 2)
    global_physics = torch.randn(2, 3)
    quality_mask = torch.tensor([[1.0, 0.5, 1.0], [1.0, 1.0, 0.0]], dtype=torch.float32)
    output = fusion(state, baseline, node_physics, global_physics, quality_mask)
    assert output.fused_features.shape == (2, 3, 8)
    assert torch.allclose(output.residual_base, baseline)
    assert output.quality_gate.shape == (2, 3)


def test_physics_fusion_can_disable_physics_features() -> None:
    fusion = PhysicsFusion(hidden_dim=4, mode='residual', use_physics_features=False)
    state = torch.randn(1, 2, 4)
    baseline = torch.randn(1, 2)
    output = fusion(state, baseline)
    assert output.fused_features.shape == (1, 2, 4)
    assert torch.equal(output.residual_base, torch.zeros_like(baseline))
