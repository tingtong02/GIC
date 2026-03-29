from __future__ import annotations

from pathlib import Path
from typing import Any

from gic.visualization.final_figures import write_svg


def export_network_map_svg(active_eval: dict[str, Any], destination_root: str | Path) -> str:
    destination = Path(destination_root)
    destination.mkdir(parents=True, exist_ok=True)
    studies = list(active_eval.get('case_studies', []))
    study = studies[0] if studies else {'graph_id': 'no_case', 'top_error_nodes': []}
    nodes = list(study.get('top_error_nodes', []))[:5]
    body_parts = []
    cx = 140
    cy = 220
    for index, node in enumerate(nodes):
        radius = 22 + min(26.0, float(node.get('absolute_error', 0.0)) * 0.8)
        x = cx + index * 150
        color = '#dc2626' if float(node.get('prediction', 0.0)) < 0 else '#2563eb'
        body_parts.append(f'<circle cx="{x:.2f}" cy="{cy:.2f}" r="{radius:.2f}" fill="{color}" opacity="0.78"/>')
        body_parts.append(f'<text x="{x:.2f}" y="{cy - radius - 10:.2f}" text-anchor="middle" font-size="12" font-family="monospace" fill="#0f172a">{node.get("node_id", "node")}</text>')
        body_parts.append(f'<text x="{x:.2f}" y="{cy + 4:.2f}" text-anchor="middle" font-size="11" font-family="monospace" fill="#ffffff">err={float(node.get("absolute_error", 0.0)):.2f}</text>')
        if index > 0:
            prev_x = cx + (index - 1) * 150
            body_parts.append(f'<line x1="{prev_x:.2f}" y1="{cy:.2f}" x2="{x:.2f}" y2="{cy:.2f}" stroke="#94a3b8" stroke-width="3"/>')
    body_parts.append(f'<text x="40" y="390" font-size="12" font-family="monospace" fill="#334155">graph_id={study.get("graph_id", "")}</text>')
    path = destination / 'network_state_map.svg'
    write_svg(path, 900, 460, ''.join(body_parts), title='Active Synthetic Case Network View')
    return str(path)
