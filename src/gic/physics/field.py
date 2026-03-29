from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from gic.data.schema import GeomagneticTimeSeries
from gic.physics.schema import ElectricFieldSeries, ElectricFieldSnapshot, ScenarioConfig


def _timestamp_at(index: int, interval_seconds: int) -> str:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return (base + timedelta(seconds=index * interval_seconds)).isoformat().replace("+00:00", "Z")



def _channel_aliases(channel_name: str) -> list[str]:
    normalized = str(channel_name).lower()
    if normalized in {"bx", "bx_nt", "x"}:
        return ["bx_nT", "BX_NT", "Bx_nT", "X", "x"]
    if normalized in {"by", "by_nt", "y"}:
        return ["by_nT", "BY_NT", "By_nT", "Y", "y"]
    if normalized in {"bz", "bz_nt", "z"}:
        return ["bz_nT", "BZ_NT", "Bz_nT", "Z", "z"]
    return [channel_name]



def _resolve_channel_values(geomagnetic_series: GeomagneticTimeSeries, channel_name: str) -> list[float | None]:
    values = dict(geomagnetic_series.values)
    for alias in _channel_aliases(channel_name):
        series = values.get(alias)
        if isinstance(series, list):
            return list(series)
    return [0.0 for _ in geomagnetic_series.time_index]



def _value_at(series: list[float | None], index: int) -> float:
    if index >= len(series):
        return 0.0
    raw = series[index]
    return float(raw) if raw is not None else 0.0



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
    bx_values = _resolve_channel_values(geomagnetic_series, "bx_nT")
    by_values = _resolve_channel_values(geomagnetic_series, "by_nT")
    for index, timestamp in enumerate(geomagnetic_series.time_index):
        ex = _value_at(bx_values, index) * scale_v_per_km_per_nt
        ey = _value_at(by_values, index) * scale_v_per_km_per_nt
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
