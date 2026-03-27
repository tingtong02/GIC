from __future__ import annotations

import hashlib
import json
from typing import Any

from gic.signal.features import extract_signal_feature_set
from gic.signal.metrics import compute_frontend_metrics
from gic.signal.schema import FrontendConfig, FrontendResult, QuasiDCSeries, SignalQualityReport, SignalSample


def _config_hash(frontend_config: FrontendConfig) -> str:
    payload = {
        "method_name": frontend_config.method_name,
        "method_version": frontend_config.method_version,
        "parameters": frontend_config.parameters,
        "use_reference_if_available": frontend_config.use_reference_if_available,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def build_frontend_result(
    *,
    signal_sample: SignalSample,
    frontend_config: FrontendConfig,
    denoised_values: dict[str, list[float]],
    quasi_dc_values: dict[str, list[float]],
    runtime_ms: float,
    status: str,
    notes: str,
    metadata: dict[str, Any],
) -> FrontendResult:
    config_hash = _config_hash(frontend_config)
    denoised_series = QuasiDCSeries(
        series_id=f"{signal_sample.sample_id}_{frontend_config.method_name}_denoised",
        channels=list(signal_sample.channels),
        time_index=list(signal_sample.time_index),
        values=denoised_values,
        metadata={"kind": "denoised_series"},
    )
    quasi_dc_series = QuasiDCSeries(
        series_id=f"{signal_sample.sample_id}_{frontend_config.method_name}_quasi_dc",
        channels=list(signal_sample.channels),
        time_index=list(signal_sample.time_index),
        values=quasi_dc_values,
        metadata={"kind": "quasi_dc_series"},
    )
    feature_set = extract_signal_feature_set(
        signal_sample=signal_sample,
        method_name=frontend_config.method_name,
        quasi_dc_values=quasi_dc_values,
        denoised_values=denoised_values,
        parameters=frontend_config.parameters,
    )
    quality_metrics = compute_frontend_metrics(
        signal_sample=signal_sample,
        denoised_values=denoised_values,
        quasi_dc_values=quasi_dc_values,
        runtime_ms=runtime_ms,
    )
    quality_metrics["status"] = status
    return FrontendResult(
        result_id=f"{signal_sample.sample_id}_{frontend_config.method_name}_{config_hash}",
        sample_id=signal_sample.sample_id,
        method_name=frontend_config.method_name,
        method_version=frontend_config.method_version,
        config_hash=config_hash,
        denoised_series=denoised_series,
        quasi_dc_series=quasi_dc_series,
        feature_set=feature_set,
        quality_metrics=quality_metrics,
        status=status,
        notes=notes,
        metadata=metadata,
    )


def build_quality_report(result: FrontendResult) -> SignalQualityReport:
    warnings: list[str] = []
    if result.status != "ok":
        warnings.append(f"Frontend status is {result.status}")
    if result.quality_metrics.get("correlation_to_reference") is None:
        warnings.append("Reference metrics unavailable")
    return SignalQualityReport(
        report_id=f"{result.result_id}_quality",
        sample_id=result.sample_id,
        result_id=result.result_id,
        metrics=dict(result.quality_metrics),
        warnings=warnings,
        status=result.status,
    )
