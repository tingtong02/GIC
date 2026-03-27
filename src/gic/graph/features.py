from __future__ import annotations

from typing import Any

from gic.graph.schema import GraphFeatureBundle, MaskBundle



def _signal_feature_vector(signal_payload: dict[str, Any] | None) -> tuple[list[str], list[float]]:
    if not isinstance(signal_payload, dict):
        return [], []
    numeric_items: list[tuple[str, float]] = []
    for section_name in ('summary_statistics', 'trend_features', 'spectral_features', 'peak_features'):
        section = signal_payload.get(section_name)
        if not isinstance(section, dict):
            continue
        for key in sorted(section):
            value = section[key]
            if isinstance(value, (int, float)):
                numeric_items.append((f'signal.{section_name}.{key}', float(value)))
    names = [item[0] for item in numeric_items]
    values = [item[1] for item in numeric_items]
    return names, values



def build_feature_bundle(
    *,
    node_ids: list[str],
    bus_records: list[dict[str, Any]],
    adjacency_counts: dict[str, int],
    line_feature_totals: dict[str, float],
    observed_values: dict[str, float],
    mask_bundle: MaskBundle,
    signal_payload: dict[str, Any] | None,
    include_signal_features: bool,
    include_physics_baseline: bool,
) -> GraphFeatureBundle:
    signal_names, signal_values = _signal_feature_vector(signal_payload if include_signal_features else None)
    feature_names = [
        'static.base_kv',
        'static.grounding_resistance_ohm',
        'static.grounding_conductance_siemens',
        'static.degree',
        'observed.bus_quantity',
        'observed.mask',
    ]
    if include_physics_baseline:
        feature_names.extend([
            'physics.adjacent_induced_abs_sum',
            'physics.adjacent_edge_count',
        ])
    feature_names.extend(signal_names)

    bus_index = {str(item['bus_id']): item for item in bus_records}
    node_features: dict[str, list[float]] = {}
    for node_id in node_ids:
        bus = bus_index[node_id]
        grounding = bus.get('grounding', {})
        values = [
            float(bus.get('base_kv') or 0.0),
            float(grounding.get('grounding_resistance_ohm') or 0.0),
            float(grounding.get('conductance_siemens') or 0.0),
            float(adjacency_counts.get(node_id, 0)),
            float(observed_values.get(node_id, 0.0)),
            1.0 if mask_bundle.observed_mask.get(node_id, False) else 0.0,
        ]
        if include_physics_baseline:
            values.extend([
                float(line_feature_totals.get(node_id, 0.0)),
                float(adjacency_counts.get(node_id, 0)),
            ])
        values.extend(signal_values)
        node_features[node_id] = values

    return GraphFeatureBundle(
        node_feature_names=feature_names,
        node_features=node_features,
        global_feature_names=signal_names,
        global_features=signal_values,
        quality_flags=['signal_features_included' if include_signal_features and signal_names else 'signal_features_absent'],
    )
