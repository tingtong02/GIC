from __future__ import annotations

from gic.data.schema import GridCase
from gic.physics.schema import GroundingRecord, PhysicsBus, PhysicsGridCase, PhysicsLine, PhysicsTransformer


class PhysicsBuildError(ValueError):
    """Raised when a GridCase cannot be converted into a physics-ready case."""


def build_physics_case(grid_case: GridCase, physics_config: dict) -> PhysicsGridCase:
    solver_cfg = physics_config["solver"]
    assumptions_cfg = physics_config.get("assumptions", {})
    line_overrides = assumptions_cfg.get("line_overrides", {})
    allow_assumption_fill = bool(solver_cfg.get("allow_assumption_fill", False))

    grounding_records: list[GroundingRecord] = []
    buses: list[PhysicsBus] = []
    assumptions: list[str] = []
    missing_required_fields: list[str] = []

    grounding_resistance = float(solver_cfg.get("grounding_resistance_ohm", 1.0))
    conductance = 0.0 if grounding_resistance == 0 else 1.0 / grounding_resistance

    for bus in grid_case.buses:
        grounding = GroundingRecord(
            bus_id=bus.bus_id,
            grounding_resistance_ohm=grounding_resistance,
            conductance_siemens=conductance,
            assumed=True,
            notes="Uniform grounding assumption from Phase 2 config.",
        )
        grounding_records.append(grounding)
        buses.append(
            PhysicsBus(
                bus_id=bus.bus_id,
                base_kv=bus.base_kv,
                grounding=grounding,
                included_in_solver=True,
            )
        )
    assumptions.append(f"All buses use grounding_resistance_ohm={grounding_resistance}.")

    lines: list[PhysicsLine] = []
    for line in grid_case.lines:
        line_assumptions: list[str] = []
        line_missing: list[str] = []
        override = line_overrides.get(line.line_id, {})
        length_km = line.length_km
        azimuth_deg = line.azimuth_deg
        included = True

        if length_km is None:
            if "length_km" in override and allow_assumption_fill:
                length_km = float(override["length_km"])
                line_assumptions.append(f"length_km filled from config override: {length_km}")
            else:
                line_missing.append("length_km")
                included = False
        if azimuth_deg is None:
            if "azimuth_deg" in override and allow_assumption_fill:
                azimuth_deg = float(override["azimuth_deg"])
                line_assumptions.append(f"azimuth_deg filled from config override: {azimuth_deg}")
            else:
                line_missing.append("azimuth_deg")
                included = False
        if line_missing:
            missing_required_fields.extend([f"{line.line_id}:{item}" for item in line_missing])

        lines.append(
            PhysicsLine(
                line_id=line.line_id,
                from_bus=line.from_bus,
                to_bus=line.to_bus,
                resistance_ohm=float(line.resistance if line.resistance is not None else 1.0),
                length_km=length_km,
                azimuth_deg=azimuth_deg,
                voltage_level_kv=line.voltage_level_kv,
                included_in_solver=included,
                available_for_solver=included,
                assumptions=line_assumptions,
                source_missing_fields=line_missing,
                notes=line.notes,
            )
        )
        assumptions.extend([f"{line.line_id}: {item}" for item in line_assumptions])

    transformers: list[PhysicsTransformer] = []
    for transformer in grid_case.transformers:
        effective_resistance = float(
            solver_cfg.get("default_transformer_resistance_ohm", 0.5)
        )
        transformer_assumptions = [f"effective_resistance_ohm set to {effective_resistance}"]
        transformers.append(
            PhysicsTransformer(
                transformer_id=transformer.transformer_id,
                from_bus=transformer.from_bus,
                to_bus=transformer.to_bus,
                effective_resistance_ohm=effective_resistance,
                associated_line_id=transformer.raw_transformer_id,
                available_for_solver=True,
                assumptions=transformer_assumptions,
                notes=transformer.notes,
            )
        )
        assumptions.extend([f"{transformer.transformer_id}: {item}" for item in transformer_assumptions])

    available = all(line.available_for_solver for line in lines)
    gic_ready = available and len(lines) > 0 and len(buses) > 0
    if solver_cfg.get("fail_on_missing_required_fields", True) and missing_required_fields and not allow_assumption_fill:
        raise PhysicsBuildError(
            "Cannot build physics case because required fields are missing: " + ", ".join(missing_required_fields)
        )

    return PhysicsGridCase(
        case_id=f"physics_{grid_case.case_id}",
        source_case_id=grid_case.case_id,
        buses=buses,
        lines=lines,
        transformers=transformers,
        grounding=grounding_records,
        gic_ready=gic_ready,
        available_for_solver=available,
        missing_required_fields=sorted(set(missing_required_fields)),
        assumptions=assumptions,
    )
