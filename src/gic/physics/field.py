from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from gic.data.schema import GeomagneticTimeSeries
from gic.physics.schema import ElectricFieldSeries, ElectricFieldSnapshot, ScenarioConfig


def _timestamp_at(index: int, interval_seconds: int) -> str:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return (base + timedelta(seconds=index * interval_seconds)).isoformat().replace("+00:00", "Z")


def uniform_field_from_scenario(scenario: ScenarioConfig) -> ElectricFieldSnapshot:
    amplitude = float(scenario.amplitude or 0.0)
    direction = math.radians(float(scenario.direction_deg or 0.0))
    return ElectricFieldSnapshot(
        snapshot_id=f"{scenario.scenario_id}_snapshot_000",
        time=_timestamp_at(0, scenario.time_interval_seconds),
        field_mode="uniform_xy",
        reference_frame="global_xy",
        global_ex=amplitude * math.cos(direction),
        global_ey=amplitude * math.sin(direction),
        units=scenario.field_units,
        notes="Uniform field snapshot generated from ScenarioConfig.",
    )


def build_series_from_timeseries(
    scenario: ScenarioConfig,
    geomagnetic_series: GeomagneticTimeSeries,
    scale_v_per_km_per_nt: float,
) -> ElectricFieldSeries:
    snapshots: list[ElectricFieldSnapshot] = []
    bx_values = geomagnetic_series.values.get("bx_nT", [])
    by_values = geomagnetic_series.values.get("by_nT", [])
    for index, timestamp in enumerate(geomagnetic_series.time_index):
        ex = float(bx_values[index] or 0.0) * scale_v_per_km_per_nt
        ey = float(by_values[index] or 0.0) * scale_v_per_km_per_nt
        snapshots.append(
            ElectricFieldSnapshot(
                snapshot_id=f"{scenario.scenario_id}_snapshot_{index:03d}",
                time=timestamp,
                field_mode="timeseries_xy",
                reference_frame="global_xy",
                global_ex=ex,
                global_ey=ey,
                units=scenario.field_units,
                notes="Built from geomagnetic series using linear scaling assumption.",
            )
        )
    return ElectricFieldSeries(
        series_id=f"{scenario.scenario_id}_series",
        source_name=geomagnetic_series.source_name,
        snapshots=snapshots,
        notes="Electric field series derived from geomagnetic series with explicit Phase 2 scaling assumption.",
    )
