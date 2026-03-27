from __future__ import annotations

from typing import Any

from gic.physics.schema import GICSolution, PhysicsGridCase


def validate_physics_case(physics_case: PhysicsGridCase) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not physics_case.buses:
        errors.append("PhysicsGridCase contains no buses")
    if not physics_case.lines:
        errors.append("PhysicsGridCase contains no lines")
    if physics_case.missing_required_fields:
        warnings.append("Missing required fields tracked: " + ", ".join(physics_case.missing_required_fields))
    if not physics_case.available_for_solver:
        warnings.append("PhysicsGridCase contains excluded lines")
    return {
        "asset_type": "physics_case",
        "asset_id": physics_case.case_id,
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def validate_solution(solution: GICSolution) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if solution.solver_status != "ok":
        errors.append(f"Solver status is not ok: {solution.solver_status}")
    if not solution.transformer_gic:
        warnings.append("Transformer-level outputs are empty")
    if not solution.line_inputs:
        warnings.append("Line-level outputs are empty")
    return {
        "asset_type": "physics_solution",
        "asset_id": solution.solution_id,
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }
