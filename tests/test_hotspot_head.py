from __future__ import annotations

import torch

from gic.eval.hotspot_metrics import summarize_hotspot_rows
from gic.models.heads import HotspotHead


def test_hotspot_head_projects_node_logits() -> None:
    head = HotspotHead(hidden_dim=8)
    state = torch.randn(2, 3, 8)
    logits = head(state)
    assert logits.shape == (2, 3)


def test_hotspot_metrics_summary_reports_f1() -> None:
    summary = summarize_hotspot_rows(
        [
            {'hotspot_probability': 0.9, 'hotspot_target': 1.0},
            {'hotspot_probability': 0.1, 'hotspot_target': 0.0},
        ],
        threshold=0.5,
    )
    assert summary['row_count'] == 2
    assert summary['f1'] == 1.0
