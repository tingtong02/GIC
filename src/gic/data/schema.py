from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SCHEMA_VERSION = "1.0"


@dataclass(slots=True)
class BusRecord:
    bus_id: str
    raw_bus_id: str
    bus_type: int | None = None
    base_kv: float | None = None
    vm_pu: float | None = None
    va_deg: float | None = None
    notes: str = ""


@dataclass(slots=True)
class LineRecord:
    line_id: str
    raw_line_id: str
    from_bus: str
    to_bus: str
    resistance: float | None
    reactance: float | None = None
    length_km: float | None = None
    azimuth_deg: float | None = None
    voltage_level_kv: float | None = None
    series_compensated: bool | None = None
    available_for_gic: bool = False
    notes: str = ""


@dataclass(slots=True)
class TransformerRecord:
    transformer_id: str
    raw_transformer_id: str
    from_bus: str
    to_bus: str
    tap_ratio: float | None = None
    phase_shift_deg: float | None = None
    available_for_gic: bool = False
    notes: str = ""


@dataclass(slots=True)
class SubstationRecord:
    substation_id: str
    name: str = ""
    latitude: float | None = None
    longitude: float | None = None
    notes: str = ""


@dataclass(slots=True)
class SensorRecord:
    sensor_id: str
    source_name: str
    station_id: str
    sensor_type: str
    units: str
    notes: str = ""


@dataclass(slots=True)
class GridCase:
    case_id: str
    source_name: str
    case_name: str
    base_mva: float | None
    buses: list[BusRecord]
    lines: list[LineRecord]
    transformers: list[TransformerRecord]
    substations: list[SubstationRecord] = field(default_factory=list)
    coordinate_system: str = "unknown"
    notes: str = ""
    available_fields: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    version: str = SCHEMA_VERSION


@dataclass(slots=True)
class GeomagneticTimeSeries:
    series_id: str
    source_name: str
    station_id: str
    time_index: list[str]
    value_columns: list[str]
    values: dict[str, list[float | None]]
    units: dict[str, str]
    sampling_interval: str
    timezone: str
    missing_ratio: float
    quality_flags: list[str]
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    version: str = SCHEMA_VERSION


@dataclass(slots=True)
class GeoelectricTimeSeries:
    series_id: str
    source_name: str
    station_id: str
    time_index: list[str]
    value_columns: list[str]
    values: dict[str, list[float | None]]
    units: dict[str, str]
    sampling_interval: str
    timezone: str
    missing_ratio: float
    quality_flags: list[str]
    notes: str = ""
    version: str = SCHEMA_VERSION


@dataclass(slots=True)
class GICObservationSeries:
    series_id: str
    source_name: str
    sensor_id: str
    time_index: list[str]
    value_columns: list[str]
    values: dict[str, list[float | None]]
    units: dict[str, str]
    sampling_interval: str
    timezone: str
    missing_ratio: float
    quality_flags: list[str]
    notes: str = ""
    version: str = SCHEMA_VERSION


@dataclass(slots=True)
class StormEventRecord:
    event_id: str
    source_name: str
    start_time: str
    end_time: str
    storm_level: str | None = None
    notes: str = ""
    version: str = SCHEMA_VERSION


@dataclass(slots=True)
class SourceRecord:
    source_name: str
    source_type: str
    origin: str
    description: str
    license: str
    raw_file_type: str
    status: str
    intended_use: bool
    phases: list[str]
    purpose: str
    homepage: str = ""
    notes: str = ""


@dataclass(slots=True)
class DatasetRecord:
    dataset_name: str
    source_name: str
    relative_path: str
    schema_version: str
    time_range: str | None
    spatial_scope: str | None
    trainable: bool
    validation_only: bool
    generation_method: str
    status: str
    description: str
    notes: str = ""


@dataclass(slots=True)
class DatasetManifest:
    dataset_name: str
    source_name: str
    generated_at_utc: str
    raw_input_paths: list[str]
    converter_name: str
    schema_version: str
    record_count: int
    missing_stats: dict[str, Any]
    notes: str = ""


def to_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, list):
        return [to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    return value
