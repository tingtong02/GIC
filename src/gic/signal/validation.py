from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from gic.signal.schema import FrontendResult, SignalSample


def validate_signal_sample(signal_sample: SignalSample) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not signal_sample.channels:
        errors.append("SignalSample must contain at least one channel")
    counts = Counter(signal_sample.time_index)
    duplicates = [stamp for stamp, count in counts.items() if count > 1]
    if duplicates:
        errors.append(f"Duplicate timestamps detected: {duplicates}")
    try:
        parsed = [datetime.fromisoformat(item.replace("Z", "+00:00")) for item in signal_sample.time_index]
        if parsed != sorted(parsed):
            errors.append("SignalSample time index must be monotonic")
    except Exception:
        warnings.append("Failed to parse time index timestamps")
    expected = len(signal_sample.time_index)
    for channel in signal_sample.channels:
        values = signal_sample.values.get(channel)
        if values is None:
            errors.append(f"Missing values for channel {channel}")
            continue
        if len(values) != expected:
            errors.append(f"Channel {channel} length mismatch")
    return {
        "asset_type": "signal_sample",
        "asset_id": signal_sample.sample_id,
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "channel_count": len(signal_sample.channels),
            "point_count": len(signal_sample.time_index),
        },
    }


def validate_frontend_result(result: FrontendResult) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if result.status == "failed":
        warnings.append("Frontend marked as failed")
    denoised_points = len(result.denoised_series.time_index)
    quasi_points = len(result.quasi_dc_series.time_index)
    if denoised_points != quasi_points:
        errors.append("Denoised and quasi-DC series must have the same time length")
    if not result.method_name:
        errors.append("method_name must not be empty")
    if not result.feature_set.summary_statistics:
        warnings.append("Feature set summary statistics are empty")
    return {
        "asset_type": "frontend_result",
        "asset_id": result.result_id,
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "method_name": result.method_name,
            "status": result.status,
            "point_count": denoised_points,
        },
    }
