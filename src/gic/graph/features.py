from __future__ import annotations

from typing import Any

from gic.graph.schema import GraphFeatureBundle, MaskBundle


def _signal_feature_vector(signal_payload: dict[str, Any] | None) -> tuple[list[str], list[float], list[str]]:
    if not isinstance(signal_payload, dict):
        return [], [], []
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
    quality_flags = [str(item) for item in signal_payload.get('quality_flags', []) if isinstance(item, str)]
    return names, values, quality_flags


def _physics_global_vector(
    *,
    line_feature_totals: dict[str, float],
    projected_field_totals: dict[str, float],
    adjacency_counts: dict[str, int],
    solution_quality_flags: list[str],
    solution_assumptions: list[str],
    solver_status: str,
) -> tuple[list[str], list[float]]:
    induced_values = [float(value) for value in line_feature_totals.values()]
    projected_values = [float(value) for value in projected_field_totals.values()]
    degree_values = [float(value) for value in adjacency_counts.values()]
    solver_ok = 1.0 if str(solver_status).lower() == 'ok' else 0.0
    return (
        [
            'physics.global.total_induced_abs_sum',
            'physics.global.mean_induced_abs_sum',
            'physics.global.max_induced_abs_sum',
            'physics.global.total_projected_field_abs_sum',
            'physics.global.mean_projected_field_abs_sum',
            'physics.global.max_projected_field_abs_sum',
            'physics.global.mean_adjacent_edge_count',
            'physics.global.max_adjacent_edge_count',
            'physics.global.solver_ok',
            'physics.global.quality_flag_count',
            'physics.global.assumption_count',
        ],
        [
            float(sum(induced_values)),
            float(sum(induced_values) / len(induced_values)) if induced_values else 0.0,
            float(max(induced_values)) if induced_values else 0.0,
            float(sum(projected_values)),
            float(sum(projected_values) / len(projected_values)) if projected_values else 0.0,
            float(max(projected_values)) if projected_values else 0.0,
            float(sum(degree_values) / len(degree_values)) if degree_values else 0.0,
            float(max(degree_values)) if degree_values else 0.0,
            solver_ok,
            float(len(solution_quality_flags)),
            float(len(solution_assumptions)),
        ],
    )


def build_feature_bundle(
    *,
    node_ids: list[str],
    bus_records: list[dict[str, Any]],
    adjacency_counts: dict[str, int],
    line_feature_totals: dict[str, float],
    projected_field_totals: dict[str, float],
    observed_values: dict[str, float],
    mask_bundle: MaskBundle,
    signal_payload: dict[str, Any] | None,
    include_signal_features: bool,
    include_physics_baseline: bool,
    solution_quality_flags: list[str],
    solution_assumptions: list[str],
    solver_status: str,
) -> GraphFeatureBundle:
    signal_names, signal_values, signal_quality_flags = _signal_feature_vector(signal_payload if include_signal_features else None)
    feature_names = [
        'static.base_kv',
        'static.grounding_resistance_ohm',
        'static.grounding_conductance_siemens',
        'static.degree',
        'observed.bus_quantity',
        'observed.mask',
    ]
    global_feature_names: list[str] = list(signal_names)
    global_features: list[float] = list(signal_values)
    if include_physics_baseline:
        feature_names.extend(
            [
                'physics.adjacent_induced_abs_sum',
                'physics.adjacent_projected_field_abs_sum',
                'physics.adjacent_edge_count',
                'physics.solver_ok',
                'physics.quality_flag_count',
                'physics.assumption_count',
            ]
        )
        physics_global_names, physics_global_values = _physics_global_vector(
            line_feature_totals=line_feature_totals,
            projected_field_totals=projected_field_totals,
            adjacency_counts=adjacency_counts,
            solution_quality_flags=solution_quality_flags,
            solution_assumptions=solution_assumptions,
            solver_status=solver_status,
        )
        global_feature_names.extend(physics_global_names)
        global_features.extend(physics_global_values)

    feature_names.extend(signal_names)

    bus_index = {str(item['bus_id']): item for item in bus_records}
    solver_ok_value = 1.0 if str(solver_status).lower() == 'ok' else 0.0
    quality_count = float(len(solution_quality_flags))
    assumption_count = float(len(solution_assumptions))
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
            values.extend(
                [
                    float(line_feature_totals.get(node_id, 0.0)),
                    float(projected_field_totals.get(node_id, 0.0)),
                    float(adjacency_counts.get(node_id, 0)),
                    solver_ok_value,
                    quality_count,
                    assumption_count,
                ]
            )
        values.extend(signal_values)
        node_features[node_id] = values

    quality_flags = ['signal_features_included' if include_signal_features and signal_names else 'signal_features_absent']
    quality_flags.extend(signal_quality_flags)
    if include_physics_baseline:
        quality_flags.append(f'physics_solver_status:{solver_status}')
        quality_flags.extend(f'physics_quality:{item}' for item in solution_quality_flags)
        quality_flags.extend(f'physics_assumption:{item}' for item in solution_assumptions)

    return GraphFeatureBundle(
        node_feature_names=feature_names,
        node_features=node_features,
        global_feature_names=global_feature_names,
        global_features=global_features,
        quality_flags=quality_flags,
    )
