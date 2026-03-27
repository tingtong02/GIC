from __future__ import annotations

from pathlib import Path

from gic.config import load_config
from gic.data.loaders.matpower_loader import MatpowerLoader
from gic.data.registry import RegistryStore
from gic.physics.builder import build_physics_case


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/phase2/phase2_dev.yaml"


def test_build_physics_case_applies_line_overrides() -> None:
    config = load_config(CONFIG)
    registry = RegistryStore(project_root=ROOT, registry_root="data/registry")
    dataset = registry.get_dataset("matpower_case118_sample")
    source = registry.get_source(dataset.source_name)
    grid_case, _ = MatpowerLoader(ROOT).load(dataset, source)
    physics_case = build_physics_case(grid_case, config["physics"])
    assert physics_case.gic_ready is True
    assert physics_case.lines[0].length_km == 80.0
    assert physics_case.lines[1].azimuth_deg == 45.0
