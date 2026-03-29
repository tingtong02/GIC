from __future__ import annotations

from pathlib import Path
from typing import Any

from gic.visualization.final_figures import bar_chart_body, write_svg


def export_model_comparison_svgs(report: dict[str, Any], destination_root: str | Path) -> dict[str, str]:
    destination = Path(destination_root)
    destination.mkdir(parents=True, exist_ok=True)
    synthetic = dict(report.get('synthetic_summary', {}))
    synthetic_path = destination / 'model_comparison_synthetic.svg'
    synthetic_labels = ['phase4_graph', 'phase5_default', 'phase6_feature_only']
    synthetic_values = [
        float(synthetic.get('phase4_graph_hidden_mae', 0.0)),
        float(synthetic.get('phase5_default_hidden_mae', 0.0)),
        float(synthetic.get('phase6_feature_only_hidden_mae', 0.0)),
    ]
    write_svg(synthetic_path, 900, 460, bar_chart_body(synthetic_labels, synthetic_values, color='#2563eb'), title='Synthetic Hidden-Node MAE Comparison')

    real_summary = dict(report.get('real_event_summary', {}).get('model_summary', {}))
    real_path = destination / 'model_comparison_real.svg'
    real_labels = ['phase4_best_graph', 'phase5_default', 'phase6_feature_only']
    real_values = [
        float(real_summary.get('phase4_best_graph', {}).get('mean_proxy_hidden_mae') or 0.0),
        float(real_summary.get('phase5_default', {}).get('mean_proxy_hidden_mae') or 0.0),
        float(real_summary.get('phase6_feature_only', {}).get('mean_proxy_hidden_mae') or 0.0),
    ]
    write_svg(real_path, 900, 460, bar_chart_body(real_labels, real_values, color='#0f766e'), title='Real-Event Proxy Hidden MAE Comparison')
    return {
        'synthetic_model_comparison_svg': str(synthetic_path),
        'real_model_comparison_svg': str(real_path),
    }
