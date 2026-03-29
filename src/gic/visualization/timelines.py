from __future__ import annotations

from pathlib import Path
from typing import Any

from gic.visualization.final_figures import line_chart_body, write_svg


def export_timeline_svg(generalization_summary: dict[str, Any], destination_root: str | Path) -> str:
    destination = Path(destination_root)
    destination.mkdir(parents=True, exist_ok=True)
    grouped = dict(generalization_summary.get('grouped_metrics', {}))
    labels = [label for label in ['main', 'generalization', 'boundary'] if label in grouped]
    series = {
        'mean_hidden_mae_proxy': [float(grouped[label].get('mean_hidden_mae_proxy') or 0.0) for label in labels],
        'mean_trend_corr_shifted': [float(grouped[label].get('mean_trend_correlation') or 0.0) + 100.0 for label in labels],
    }
    path = destination / 'timeline_generalization.svg'
    write_svg(path, 920, 460, line_chart_body(labels, series), title='Generalization Surface Summary')
    return str(path)
