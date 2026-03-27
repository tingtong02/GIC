from __future__ import annotations

import torch

from gic.models import build_gat_baseline, build_gcn_baseline, build_graphsage_baseline


def test_graph_baselines_forward_shape() -> None:
    features = torch.tensor(
        [
            [1.0, 0.0, 0.5],
            [0.5, 1.0, 0.0],
            [0.0, 0.5, 1.0],
        ],
        dtype=torch.float32,
    )
    adjacency = torch.tensor(
        [
            [1.0, 1.0, 0.0],
            [1.0, 1.0, 1.0],
            [0.0, 1.0, 1.0],
        ],
        dtype=torch.float32,
    )
    builders = [
        build_gcn_baseline({"hidden_dim": 8, "layers": 2, "dropout": 0.0}, input_dim=3),
        build_graphsage_baseline({"hidden_dim": 8, "layers": 2, "dropout": 0.0}, input_dim=3),
        build_gat_baseline({"hidden_dim": 8, "layers": 2, "heads": 2, "dropout": 0.0}, input_dim=3),
    ]
    for model in builders:
        prediction = model(features, adjacency=adjacency)
        assert prediction.shape == (3,)
        assert torch.isfinite(prediction).all()
