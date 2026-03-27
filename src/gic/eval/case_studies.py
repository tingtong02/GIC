from __future__ import annotations

from collections import defaultdict
from typing import Any



def build_case_studies(rows: list[dict[str, Any]], top_k: int = 3) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get('graph_id', '')), row.get('time_index'))].append(row)
    studies: list[dict[str, Any]] = []
    for (graph_id, time_index), group_rows in grouped.items():
        ranked = sorted(group_rows, key=lambda item: float(item.get('absolute_error', 0.0)), reverse=True)
        studies.append(
            {
                'graph_id': graph_id,
                'time_index': time_index,
                'node_count': len(group_rows),
                'hidden_node_count': sum(1 for item in group_rows if not bool(item.get('observed', False))),
                'top_error_nodes': [
                    {
                        'node_id': str(item.get('node_id', '')),
                        'prediction': float(item.get('prediction', 0.0)),
                        'target': float(item.get('target', 0.0)),
                        'absolute_error': float(item.get('absolute_error', 0.0)),
                        'observed': bool(item.get('observed', False)),
                        'hotspot_target': float(item.get('hotspot_target', 0.0)) if item.get('hotspot_target') is not None else None,
                        'hotspot_probability': float(item.get('hotspot_probability', 0.0)) if item.get('hotspot_probability') is not None else None,
                    }
                    for item in ranked[:max(1, top_k)]
                ],
            }
        )
    studies.sort(key=lambda item: (str(item['graph_id']), str(item.get('time_index'))))
    return studies
