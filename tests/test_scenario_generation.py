from __future__ import annotations

from pathlib import Path

from gic.config import load_config
from gic.physics.scenarios import generate_scenarios


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/phase2/phase2_dev.yaml"


def test_generate_sweep_scenarios() -> None:
    config = load_config(CONFIG)
    scenarios = generate_scenarios(config, "sweep_field")
    assert len(scenarios) == 9


def test_generate_timeseries_scenario() -> None:
    config = load_config(CONFIG)
    scenarios = generate_scenarios(config, "timeseries_field")
    assert scenarios[0].timeseries_dataset == "sample_geomagnetic_storm_day"
