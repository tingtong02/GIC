from __future__ import annotations

from typing import Any

from gic.physics.schema import GICSolution, physics_to_dict


def summarize_solution(solution: GICSolution) -> dict[str, Any]:
    return {
        "solution_id": solution.solution_id,
        "scenario_id": solution.scenario_id,
        "solver_status": solution.solver_status,
        "line_count": len(solution.line_inputs),
        "bus_count": len(solution.bus_quantities),
        "transformer_count": len(solution.transformer_gic),
        "max_abs_transformer_gic": max((abs(item.gic_value) for item in solution.transformer_gic), default=0.0),
    }


def solution_to_dict(solution: GICSolution) -> dict[str, Any]:
    return physics_to_dict(solution)
