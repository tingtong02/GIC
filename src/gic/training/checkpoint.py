from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.optim import Optimizer


def save_checkpoint(
    destination: str | Path,
    *,
    model: nn.Module,
    optimizer: Optimizer | None,
    epoch: int,
    metadata: dict[str, Any],
) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'epoch': int(epoch),
        'model_state': model.state_dict(),
        'optimizer_state': optimizer.state_dict() if optimizer is not None else None,
        'metadata': metadata,
    }
    torch.save(payload, path)
    return path


def load_checkpoint(
    source: str | Path,
    *,
    model: nn.Module,
    optimizer: Optimizer | None = None,
    map_location: str = 'cpu',
) -> dict[str, Any]:
    payload = torch.load(Path(source), map_location=map_location)
    model.load_state_dict(payload['model_state'])
    optimizer_state = payload.get('optimizer_state')
    if optimizer is not None and optimizer_state is not None:
        optimizer.load_state_dict(optimizer_state)
    return payload
