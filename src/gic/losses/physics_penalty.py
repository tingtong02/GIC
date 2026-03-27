from __future__ import annotations

import torch
from torch import nn


class PhysicsPenaltyLoss(nn.Module):
    def __init__(self, mode: str = 'mae') -> None:
        super().__init__()
        if mode == 'mae':
            self.loss = nn.L1Loss()
        elif mode == 'mse':
            self.loss = nn.MSELoss()
        else:
            raise ValueError(f'Unsupported physics penalty mode: {mode}')

    def forward(self, prediction: torch.Tensor, physics_baseline: torch.Tensor) -> torch.Tensor:
        return self.loss(prediction, physics_baseline)
