from __future__ import annotations

import numpy as np

from gic.physics.projections import induced_voltage, project_field_onto_line
from gic.physics.schema import (
    BusSolutionRecord,
    ElectricFieldSeries,
    ElectricFieldSnapshot,
    GICSolution,
    LineSolutionRecord,
    PhysicsGridCase,
    TransformerSolutionRecord,
)


class SolverError(ValueError):
    """Raised when the physics solver cannot produce a stable solution."""


def solve_snapshot(physics_case: PhysicsGridCase, snapshot: ElectricFieldSnapshot, scenario_id: str) -> GICSolution:
    if not physics_case.gic_ready:
        raise SolverError("PhysicsGridCase is not marked as gic_ready")

    bus_index = {bus.bus_id: index for index, bus in enumerate(physics_case.buses)}
    size = len(physics_case.buses)
    conductance = np.zeros((size, size), dtype=float)
    injections = np.zeros(size, dtype=float)
    line_results: list[LineSolutionRecord] = []
    line_currents: dict[str, float] = {}

    for line in physics_case.lines:
        if not line.included_in_solver or line.length_km is None or line.azimuth_deg is None:
            line_results.append(
                LineSolutionRecord(
                    line_id=line.line_id,
                    projected_field=0.0,
                    induced_quantity=0.0,
                    included_in_solver=False,
                    notes="Excluded from solver due to missing required fields.",
                )
            )
            continue

        i = bus_index[line.from_bus]
        j = bus_index[line.to_bus]
        g = 0.0 if line.resistance_ohm == 0 else 1.0 / line.resistance_ohm
        projected = project_field_onto_line(snapshot.global_ex, snapshot.global_ey, line.azimuth_deg)
        induced = induced_voltage(projected, line.length_km)

        conductance[i, i] += g
        conductance[j, j] += g
        conductance[i, j] -= g
        conductance[j, i] -= g
        injections[i] += g * induced
        injections[j] -= g * induced

        line_results.append(
            LineSolutionRecord(
                line_id=line.line_id,
                projected_field=projected,
                induced_quantity=induced,
                included_in_solver=True,
                notes="Projected field and induced quantity computed with uniform-field baseline.",
            )
        )
        line_currents[line.line_id] = induced

    for bus in physics_case.buses:
        index = bus_index[bus.bus_id]
        conductance[index, index] += bus.grounding.conductance_siemens

    try:
        potentials = np.linalg.solve(conductance, injections)
    except np.linalg.LinAlgError as exc:
        raise SolverError(f"Linear solve failed: {exc}") from exc

    bus_results = [
        BusSolutionRecord(
            bus_id=bus.bus_id,
            solved_quantity=float(potentials[bus_index[bus.bus_id]]),
            connected_components_info="single_component",
            quality_flag="ok",
        )
        for bus in physics_case.buses
    ]

    transformer_results: list[TransformerSolutionRecord] = []
    for transformer in physics_case.transformers:
        i = bus_index[transformer.from_bus]
        j = bus_index[transformer.to_bus]
        delta_v = float(potentials[i] - potentials[j])
        gic_value = delta_v / transformer.effective_resistance_ohm
        transformer_results.append(
            TransformerSolutionRecord(
                transformer_id=transformer.transformer_id,
                gic_value=float(gic_value),
                associated_bus_ids=[transformer.from_bus, transformer.to_bus],
                voltage_level=None,
                quality_flag="ok",
                included_in_risk_output=True,
            )
        )

    return GICSolution(
        solution_id=f"{scenario_id}_{snapshot.snapshot_id}",
        case_id=physics_case.case_id,
        time=snapshot.time,
        scenario_id=scenario_id,
        line_inputs=line_results,
        bus_quantities=bus_results,
        transformer_gic=transformer_results,
        solver_status="ok",
        solver_metadata={
            "matrix_size": size,
            "included_line_count": sum(1 for line in physics_case.lines if line.included_in_solver),
            "field_units": snapshot.units,
        },
        assumptions=list(physics_case.assumptions),
        quality_flags=[],
    )


def solve_series(physics_case: PhysicsGridCase, field_series: ElectricFieldSeries, scenario_id: str) -> list[GICSolution]:
    return [solve_snapshot(physics_case, snapshot, scenario_id) for snapshot in field_series.snapshots]
