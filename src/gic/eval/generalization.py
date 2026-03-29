from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class GeneralizationSplitConfig:
    main_event_ids: list[str] = field(default_factory=list)
    generalization_event_ids: list[str] = field(default_factory=list)
    boundary_event_ids: list[str] = field(default_factory=list)



def build_generalization_summary(results: list[dict[str, Any]], split_config: GeneralizationSplitConfig) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {
        'main': [],
        'generalization': [],
        'boundary': [],
        'unassigned': [],
    }
    main = set(split_config.main_event_ids)
    generalization = set(split_config.generalization_event_ids)
    boundary = set(split_config.boundary_event_ids)
    for item in results:
        event_id = str(item.get('event_id', ''))
        if event_id in main:
            grouped['main'].append(item)
        elif event_id in generalization:
            grouped['generalization'].append(item)
        elif event_id in boundary:
            grouped['boundary'].append(item)
        else:
            grouped['unassigned'].append(item)

    def _metric_mean(rows: list[dict[str, Any]], key: str) -> float | None:
        values = [float(row[key]) for row in rows if row.get(key) is not None]
        if not values:
            return None
        return float(sum(values) / len(values))

    return {
        'split_config': asdict(split_config),
        'group_counts': {key: len(value) for key, value in grouped.items()},
        'grouped_metrics': {
            key: {
                'mean_hidden_mae_proxy': _metric_mean(value, 'proxy_hidden_mae'),
                'mean_trend_correlation': _metric_mean(value, 'trend_correlation'),
                'mean_peak_timing_error_minutes': _metric_mean(value, 'peak_timing_error_minutes'),
            }
            for key, value in grouped.items()
        },
        'rows': grouped,
    }
