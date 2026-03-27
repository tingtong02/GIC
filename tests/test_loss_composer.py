from __future__ import annotations

import torch

from gic.losses import LossComposer
from gic.models.main_model import MainModelOutputBundle


def test_loss_composer_returns_named_components() -> None:
    composer = LossComposer(
        {
            'tasks': {'hotspot': True},
            'loss': {
                'regression_mode': 'huber',
                'regression_weight': 1.0,
                'hotspot_weight': 0.5,
                'use_physics_penalty': True,
                'physics_penalty_weight': 0.1,
            },
        }
    )
    output = MainModelOutputBundle(
        regression_prediction=torch.tensor([[1.0, 2.0]], dtype=torch.float32),
        regression_target=torch.tensor([[1.5, 1.5]], dtype=torch.float32),
        hotspot_logits=torch.tensor([[0.1, -0.2]], dtype=torch.float32),
        hotspot_target=torch.tensor([[1.0, 0.0]], dtype=torch.float32),
        risk_score=None,
        uncertainty=None,
        observed_mask=torch.tensor([[True, False]]),
        physics_baseline=torch.tensor([[1.2, 1.7]], dtype=torch.float32),
        metadata=[[{'node_id': 'a'}, {'node_id': 'b'}]],
    )
    payload = composer(output)
    assert payload.total.item() >= 0.0
    assert {'regression', 'hotspot', 'physics_penalty', 'total'} <= set(payload.components)
