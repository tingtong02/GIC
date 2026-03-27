from __future__ import annotations

from datetime import datetime, timezone

from gic.data.schema import DatasetManifest, GeomagneticTimeSeries


def _to_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _sampling_interval_seconds(time_index: list[str]) -> str:
    if len(time_index) < 2:
        return "unknown"
    first = datetime.fromisoformat(time_index[0].replace("Z", "+00:00"))
    second = datetime.fromisoformat(time_index[1].replace("Z", "+00:00"))
    delta = second - first
    return f"{int(delta.total_seconds())}s"


def convert_geomagnetic_rows(
    rows: list[dict[str, str]],
    *,
    dataset_name: str,
    source_name: str,
    raw_input_path: str,
) -> tuple[GeomagneticTimeSeries, DatasetManifest]:
    if not rows:
        raise ValueError("Time series rows must not be empty")
    value_columns = [key for key in rows[0].keys() if key not in {"timestamp", "station_id", "quality_flag"}]
    time_index = [row["timestamp"] for row in rows]
    station_id = rows[0]["station_id"]
    values = {column: [_to_float(row.get(column)) for row in rows] for column in value_columns}
    total_cells = max(len(rows) * max(len(value_columns), 1), 1)
    missing_cells = sum(1 for column in value_columns for value in values[column] if value is None)
    missing_ratio = missing_cells / total_cells
    quality_flags = sorted({row.get("quality_flag", "") for row in rows if row.get("quality_flag", "")})
    series = GeomagneticTimeSeries(
        series_id=dataset_name,
        source_name=source_name,
        station_id=station_id,
        time_index=time_index,
        value_columns=value_columns,
        values=values,
        units={column: "nT" for column in value_columns},
        sampling_interval=_sampling_interval_seconds(time_index),
        timezone="UTC",
        missing_ratio=missing_ratio,
        quality_flags=quality_flags,
        notes="Converted from a CSV geomagnetic sample during Phase 1.",
    )
    manifest = DatasetManifest(
        dataset_name=dataset_name,
        source_name=source_name,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        raw_input_paths=[raw_input_path],
        converter_name="convert_geomagnetic_rows",
        schema_version=series.version,
        record_count=len(rows),
        missing_stats={"missing_ratio": missing_ratio},
        notes="Geomagnetic time series manifest generated in Phase 1.",
    )
    return series, manifest
