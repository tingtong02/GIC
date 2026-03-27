from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from gic.data.converters.timeseries_converter import _sampling_interval_seconds
from gic.data.parsers.intermagnet_parser import parse_intermagnet_station_archive
from gic.data.schema import DatasetManifest, GeomagneticTimeSeries


def _slice_range(time_index: list[str], values: dict[str, list[float | None]], time_range: str | None):
    if not time_range:
        return time_index, values
    start_text, end_text = time_range.split('/', 1)
    start = pd.Timestamp(start_text)
    end = pd.Timestamp(end_text)
    stamps = pd.to_datetime(time_index, utc=True)
    mask = (stamps >= start) & (stamps < end)
    selected_index = [stamp.strftime('%Y-%m-%dT%H:%M:%SZ') for stamp in stamps[mask]]
    selected_values = {
        key: [value for value, keep in zip(column, mask, strict=False) if bool(keep)]
        for key, column in values.items()
    }
    return selected_index, selected_values


def convert_intermagnet_station_archive(
    *,
    station_root: Path,
    dataset_name: str,
    source_name: str,
    time_range: str | None,
) -> tuple[GeomagneticTimeSeries, DatasetManifest]:
    parsed = parse_intermagnet_station_archive(station_root)
    time_index, values = _slice_range(parsed['time_index'], parsed['values'], time_range)
    value_columns = list(parsed['value_columns'])
    total_cells = max(len(time_index) * max(len(value_columns), 1), 1)
    missing_cells = sum(
        1 for column in value_columns for value in values[column] if value is None
    )
    missing_ratio = missing_cells / total_cells
    quality_flags = ['intermagnet_bin_v1', 'reference_absent']
    if missing_cells > 0:
        quality_flags.append('missing_values_present')
    metadata = dict(parsed['metadata'])
    metadata['dataset_time_range'] = time_range
    series = GeomagneticTimeSeries(
        series_id=dataset_name,
        source_name=source_name,
        station_id=parsed['station_id'],
        time_index=time_index,
        value_columns=value_columns,
        values=values,
        units=dict(parsed['units']),
        sampling_interval=_sampling_interval_seconds(time_index),
        timezone='UTC',
        missing_ratio=missing_ratio,
        quality_flags=quality_flags,
        notes='Converted from INTERMAGNET annual raw archive during Phase 3 hardening.',
        metadata=metadata,
    )
    manifest = DatasetManifest(
        dataset_name=dataset_name,
        source_name=source_name,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        raw_input_paths=[str(station_root), *metadata.get('raw_monthly_paths', [])],
        converter_name='convert_intermagnet_station_archive',
        schema_version=series.version,
        record_count=len(time_index),
        missing_stats={
            'missing_ratio': missing_ratio,
            'missing_cells': missing_cells,
            'time_range': time_range,
        },
        notes='INTERMAGNET .bin parsed as primary numeric input; .blv/.dka kept as provenance only.',
    )
    return series, manifest
