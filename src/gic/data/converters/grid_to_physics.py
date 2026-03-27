from __future__ import annotations

from gic.data.schema import GridCase
from gic.physics.builder import build_physics_case
from gic.physics.schema import PhysicsGridCase


def convert_grid_case_to_physics(grid_case: GridCase, physics_config: dict) -> PhysicsGridCase:
    return build_physics_case(grid_case, physics_config)
