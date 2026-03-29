from __future__ import annotations

from pathlib import Path
from typing import Any

from gic.visualization.final_figures import info_cards_body, write_svg


def export_kg_view_svg(phase6_report: dict[str, Any], destination_root: str | Path) -> str:
    destination = Path(destination_root)
    destination.mkdir(parents=True, exist_ok=True)
    best_run = dict(phase6_report.get('best_run', {}))
    kg_summary = dict(best_run.get('kg_summary', {}))
    items = [
        ('recommended_variant', str(phase6_report.get('recommended_variant', 'feature_only'))),
        ('active_global_kg', str(len(kg_summary.get('active_global_feature_names', [])))),
        ('active_node_kg', str(len(kg_summary.get('active_node_feature_names', [])))),
    ]
    path = destination / 'kg_view.svg'
    write_svg(path, 860, 220, info_cards_body(items), title='KG Final Variant Summary')
    return str(path)
