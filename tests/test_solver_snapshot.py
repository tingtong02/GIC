from __future__ import annotations

from pathlib import Path

from gic.config import load_config
from gic.data.converters.grid_to_physics import convert_grid_case_to_physics
from gic.data.loaders.matpower_loader import MatpowerLoader
from gic.data.registry import RegistryStore
from gic.physics.field import uniform_field_from_scenario
from gic.physics.scenarios import generate_scenarios
from gic.physics.solver import solve_snapshot


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/phase2/phase2_dev.yaml"


def test_uniform_snapshot_solver_returns_transformer_outputs() -> None:
    config = load_config(CONFIG)
    registry = RegistryStore(project_root=ROOT, registry_root="data/registry")
    dataset = registry.get_dataset("matpower_case118_sample")
    source = registry.get_source(dataset.source_name)
    grid_case, _ = MatpowerLoader(ROOT).load(dataset, source)
    physics_case = convert_grid_case_to_physics(grid_case, config["physics"])
    scenario = generate_scenarios(config, "uniform_field")[0]
    snapshot = uniform_field_from_scenario(scenario)
    solution = solve_snapshot(physics_case, snapshot, scenario.scenario_id)
    assert solution.solver_status == "ok"
    assert len(solution.transformer_gic) >= 1
    assert len(solution.line_inputs) == len(physics_case.lines)
