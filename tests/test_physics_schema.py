from __future__ import annotations

from gic.physics.schema import ElectricFieldSnapshot, PhysicsGridCase, ScenarioConfig, physics_to_dict


def test_physics_schema_serializes_snapshot() -> None:
    snapshot = ElectricFieldSnapshot(
        snapshot_id="snap_1",
        time="2024-01-01T00:00:00Z",
        field_mode="uniform_xy",
        reference_frame="global_xy",
        global_ex=1.0,
        global_ey=0.0,
        units="V_per_km",
    )
    payload = physics_to_dict(snapshot)
    assert payload["global_ex"] == 1.0


def test_scenario_config_defaults() -> None:
    scenario = ScenarioConfig(scenario_id="s1", scenario_type="uniform_field", case_dataset="matpower_case118_sample")
    assert scenario.output_levels == ["line", "bus", "transformer"]
