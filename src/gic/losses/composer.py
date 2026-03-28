from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from torch import nn

from gic.losses.hotspot import HotspotLoss
from gic.losses.physics_penalty import PhysicsPenaltyLoss
from gic.losses.regression import RegressionLoss
from gic.models.main_model import MainModelOutputBundle


@dataclass(slots=True)
class LossComputation:
    total: torch.Tensor
    components: dict[str, torch.Tensor]


class LossComposer(nn.Module):
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        loss_cfg = dict(config.get('loss', {}))
        tasks_cfg = dict(config.get('tasks', {}))
        self.regression_weight = float(loss_cfg.get('regression_weight', 1.0))
        self.hotspot_weight = float(loss_cfg.get('hotspot_weight', 0.5))
        self.physics_penalty_weight = float(loss_cfg.get('physics_penalty_weight', 0.1))
        self.physics_penalty_warmup_epochs = max(0, int(loss_cfg.get('physics_penalty_warmup_epochs', 0)))
        self.current_epoch = 1
        self.use_hotspot = bool(tasks_cfg.get('hotspot', True))
        self.use_physics_penalty = bool(loss_cfg.get('use_physics_penalty', True))
        self.regression_loss = RegressionLoss(mode=str(loss_cfg.get('regression_mode', 'huber')), delta=float(loss_cfg.get('huber_delta', 1.0)))
        self.hotspot_loss = HotspotLoss()
        self.physics_penalty = PhysicsPenaltyLoss(mode=str(loss_cfg.get('physics_penalty_mode', 'mae')))

    def set_epoch(self, epoch: int) -> None:
        self.current_epoch = max(1, int(epoch))

    def _physics_penalty_scale(self) -> float:
        if self.physics_penalty_warmup_epochs <= 0:
            return 1.0
        return 0.0 if self.current_epoch <= self.physics_penalty_warmup_epochs else 1.0

    def forward(self, output: MainModelOutputBundle) -> LossComputation:
        regression_component = self.regression_loss(output.regression_prediction, output.regression_target)
        total = self.regression_weight * regression_component
        components: dict[str, torch.Tensor] = {
            'regression': regression_component,
        }
        if self.use_hotspot and output.hotspot_logits is not None and output.hotspot_target is not None:
            hotspot_component = self.hotspot_loss(output.hotspot_logits, output.hotspot_target)
            total = total + self.hotspot_weight * hotspot_component
            components['hotspot'] = hotspot_component
        if self.use_physics_penalty and self.physics_penalty_weight > 0:
            penalty_scale = self._physics_penalty_scale()
            if penalty_scale > 0:
                physics_component = self.physics_penalty(output.regression_prediction, output.physics_baseline)
                total = total + (self.physics_penalty_weight * penalty_scale) * physics_component
                components['physics_penalty'] = physics_component
        components['total'] = total
        return LossComputation(total=total, components=components)
