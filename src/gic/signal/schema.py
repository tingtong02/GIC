from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SIGNAL_SCHEMA_VERSION = "1.0"


@dataclass(slots=True)
class SignalSample:
    sample_id: str
    source_name: str
    sensor_id: str
    time_index: list[str]
    channels: list[str]
    values: dict[str, list[float | None]]
    units: dict[str, str]
    sampling_interval: str
    scenario_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SignalBatch:
    batch_id: str
    sample_ids: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SignalWindow:
    window_id: str
    sample_id: str
    start_index: int
    end_index: int
    time_index: list[str]
    channels: list[str]
    values: dict[str, list[float | None]]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FrontendConfig:
    method_name: str
    method_version: str
    parameters: dict[str, Any]
    use_reference_if_available: bool = True


@dataclass(slots=True)
class QuasiDCSeries:
    series_id: str
    channels: list[str]
    time_index: list[str]
    values: dict[str, list[float | None]]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SignalFeatureSet:
    feature_id: str
    window_definition: dict[str, Any]
    summary_statistics: dict[str, float]
    peak_features: dict[str, float]
    trend_features: dict[str, float]
    spectral_features: dict[str, float] = field(default_factory=dict)
    quality_flags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SignalQualityReport:
    report_id: str
    sample_id: str
    result_id: str
    metrics: dict[str, Any]
    warnings: list[str]
    status: str


@dataclass(slots=True)
class FrontendResult:
    result_id: str
    sample_id: str
    method_name: str
    method_version: str
    config_hash: str
    denoised_series: QuasiDCSeries
    quasi_dc_series: QuasiDCSeries
    feature_set: SignalFeatureSet
    quality_metrics: dict[str, Any]
    status: str
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FrontendComparisonReport:
    comparison_id: str
    sample_id: str
    methods: list[str]
    ranking: list[str]
    default_method: str
    summary_table: list[dict[str, Any]]
    notes: str = ""


def signal_to_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, list):
        return [signal_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: signal_to_dict(item) for key, item in value.items()}
    return value
