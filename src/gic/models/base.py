from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import torch
from torch import nn


@dataclass(slots=True)
class BaselineBatch:
    features: torch.Tensor
    targets: torch.Tensor
    observed_mask: torch.Tensor
    adjacency: torch.Tensor | None = None
    graph_index: torch.Tensor | None = None
    metadata: list[dict[str, Any]] = field(default_factory=list)

    def to(self, device: torch.device) -> 'BaselineBatch':
        return BaselineBatch(
            features=self.features.to(device),
            targets=self.targets.to(device),
            observed_mask=self.observed_mask.to(device),
            adjacency=self.adjacency.to(device) if self.adjacency is not None else None,
            graph_index=self.graph_index.to(device) if self.graph_index is not None else None,
            metadata=self.metadata,
        )


@dataclass(slots=True)
class BaselinePrediction:
    prediction: torch.Tensor
    target: torch.Tensor
    observed_mask: torch.Tensor
    metadata: list[dict[str, Any]] = field(default_factory=list)


class BaselineModel(nn.Module):
    model_name = 'baseline'

    def forward(
        self,
        features: torch.Tensor,
        *,
        adjacency: torch.Tensor | None = None,
        graph_index: torch.Tensor | None = None,
    ) -> torch.Tensor:
        raise NotImplementedError

    def predict_batch(self, batch: BaselineBatch) -> BaselinePrediction:
        prediction = self.forward(
            batch.features,
            adjacency=batch.adjacency,
            graph_index=batch.graph_index,
        )
        return BaselinePrediction(
            prediction=prediction,
            target=batch.targets,
            observed_mask=batch.observed_mask,
            metadata=batch.metadata,
        )
