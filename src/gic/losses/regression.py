from __future__ import annotations

import torch
from torch import nn


class RegressionLoss(nn.Module):
    def __init__(self, mode: str = 'huber', delta: float = 1.0) -> None:
        super().__init__()
        if mode == 'mae':
            self.loss = nn.L1Loss()
        elif mode == 'mse':
            self.loss = nn.MSELoss()
        elif mode == 'huber':
            self.loss = nn.HuberLoss(delta=float(delta))
        else:
            raise ValueError(f'Unsupported regression loss mode: {mode}')

    def forward(self, prediction: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        return self.loss(prediction, target)
