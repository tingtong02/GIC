from __future__ import annotations

from gic.physics.schema import ScenarioConfig


def build_uniform_scenario(config: dict) -> list[ScenarioConfig]:
    scenario_cfg = config["scenario"]
    return [
        ScenarioConfig(
            scenario_id=f"uniform_{scenario_cfg['case_dataset']}",
            scenario_type="uniform_field",
            case_dataset=scenario_cfg["case_dataset"],
            amplitude=float(scenario_cfg.get("amplitude", 1.0)),
            direction_deg=float(scenario_cfg.get("direction_deg", 0.0)),
            field_units=config["physics"]["field"]["default_units"],
            time_interval_seconds=int(scenario_cfg.get("time_interval_seconds", 60)),
            output_levels=list(scenario_cfg.get("output_levels", ["line", "bus", "transformer"])),
            assumptions=["Uniform electric field scenario."],
        )
    ]


def build_sweep_scenarios(config: dict) -> list[ScenarioConfig]:
    scenario_cfg = config["scenario"]
    scenarios: list[ScenarioConfig] = []
    for amplitude in scenario_cfg.get("amplitude_sweep", []):
        for direction in scenario_cfg.get("direction_sweep", []):
            scenarios.append(
                ScenarioConfig(
                    scenario_id=f"sweep_{scenario_cfg['case_dataset']}_{str(amplitude).replace('.', 'p')}_{int(direction)}",
                    scenario_type="uniform_field",
                    case_dataset=scenario_cfg["case_dataset"],
                    amplitude=float(amplitude),
                    direction_deg=float(direction),
                    field_units=config["physics"]["field"]["default_units"],
                    time_interval_seconds=int(scenario_cfg.get("time_interval_seconds", 60)),
                    output_levels=list(scenario_cfg.get("output_levels", ["line", "bus", "transformer"])),
                    assumptions=["Generated from amplitude/direction sweep."],
                )
            )
    return scenarios


def build_timeseries_scenario(config: dict) -> list[ScenarioConfig]:
    scenario_cfg = config["scenario"]
    return [
        ScenarioConfig(
            scenario_id=f"timeseries_{scenario_cfg['case_dataset']}",
            scenario_type="timeseries_field",
            case_dataset=scenario_cfg["case_dataset"],
            field_units=config["physics"]["field"]["default_units"],
            time_interval_seconds=int(scenario_cfg.get("time_interval_seconds", 60)),
            timeseries_dataset=scenario_cfg["timeseries_dataset"],
            output_levels=list(scenario_cfg.get("output_levels", ["line", "bus", "transformer"])),
            assumptions=["Electric field series derived from geomagnetic sample via linear scale assumption."],
        )
    ]


def generate_scenarios(config: dict, scenario_mode: str | None = None) -> list[ScenarioConfig]:
    mode = scenario_mode or config["scenario"].get("type", "uniform_field")
    if mode == "uniform_field":
        return build_uniform_scenario(config)
    if mode == "sweep_field":
        return build_sweep_scenarios(config)
    if mode == "timeseries_field":
        return build_timeseries_scenario(config)
    raise ValueError(f"Unsupported scenario mode: {mode}")
