from __future__ import annotations

from collections import defaultdict
from typing import Any

from gic.models.base import BaselinePrediction



def prediction_rows_from_output(output: BaselinePrediction) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    prediction_values = output.prediction.detach().cpu().tolist()
    target_values = output.target.detach().cpu().tolist()
    observed_values = output.observed_mask.detach().cpu().tolist()
    for index, metadata in enumerate(output.metadata):
        row = dict(metadata)
        row.update(
            {
                'prediction': float(prediction_values[index]),
                'target': float(target_values[index]),
                'observed': bool(observed_values[index]),
            }
        )
        rows.append(row)
    return rows



def prediction_rows_from_outputs(outputs: list[BaselinePrediction]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for output in outputs:
        rows.extend(prediction_rows_from_output(output))
    return rows



def build_reconstruction_maps(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get('graph_id', '')), row.get('time_index'))].append(row)
    maps: list[dict[str, Any]] = []
    for (graph_id, time_index), group_rows in grouped.items():
        maps.append(
            {
                'graph_id': graph_id,
                'time_index': time_index,
                'node_predictions': [
                    {
                        'node_id': str(item.get('node_id', '')),
                        'prediction': float(item['prediction']),
                        'target': float(item['target']),
                        'observed': bool(item['observed']),
                    }
                    for item in sorted(group_rows, key=lambda value: str(value.get('node_id', '')))
                ],
            }
        )
    maps.sort(key=lambda item: (str(item['graph_id']), str(item.get('time_index'))))
    return maps
