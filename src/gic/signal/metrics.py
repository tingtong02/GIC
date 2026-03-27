from __future__ import annotations

import math
from typing import Any

import numpy as np

from gic.signal.preprocess import channel_values_to_matrix
from gic.signal.schema import SignalSample


def _safe_correlation(left: np.ndarray, right: np.ndarray) -> float:
    if left.size == 0 or right.size == 0:
        return 0.0
    if np.allclose(np.std(left), 0.0) or np.allclose(np.std(right), 0.0):
        return 0.0
    return float(np.corrcoef(left, right)[0, 1])


def _safe_snr_db(reference: np.ndarray, estimate: np.ndarray) -> float:
    signal_power = float(np.sum(np.square(reference)) + 1e-9)
    noise_power = float(np.sum(np.square(reference - estimate)) + 1e-9)
    return float(10.0 * math.log10(signal_power / noise_power))


def compute_frontend_metrics(
    *,
    signal_sample: SignalSample,
    denoised_values: dict[str, list[float]],
    quasi_dc_values: dict[str, list[float]],
    runtime_ms: float,
) -> dict[str, Any]:
    channels = list(signal_sample.channels)
    observed = channel_values_to_matrix(signal_sample.values, channels)
    denoised = channel_values_to_matrix(denoised_values, channels)
    quasi = channel_values_to_matrix(quasi_dc_values, channels)
    metrics: dict[str, Any] = {
        "runtime_ms": float(runtime_ms),
        "channel_count": len(channels),
        "point_count": observed.shape[0],
    }
    observed_energy = float(np.sum(np.square(observed)) + 1e-9)
    metrics["residual_highfreq_ratio"] = float(np.sum(np.square(denoised - quasi)) / observed_energy)
    metrics["smoothing_strength"] = float(np.sum(np.square(observed - quasi)) / observed_energy)
    metrics["peak_preservation_ratio"] = float(np.max(np.abs(quasi)) / (np.max(np.abs(observed)) + 1e-9))

    reference_clean = signal_sample.metadata.get("reference_clean_values")
    reference_quasi = signal_sample.metadata.get("reference_quasi_dc_values")
    if isinstance(reference_clean, dict):
        reference_clean_matrix = channel_values_to_matrix(reference_clean, channels)
        diff = denoised - reference_clean_matrix
        metrics["mae_to_reference"] = float(np.mean(np.abs(diff)))
        metrics["rmse_to_reference"] = float(np.sqrt(np.mean(np.square(diff))))
        metrics["correlation_to_reference"] = _safe_correlation(reference_clean_matrix.ravel(), denoised.ravel())
        metrics["peak_error"] = float(abs(np.max(np.abs(denoised)) - np.max(np.abs(reference_clean_matrix))))
        input_snr = _safe_snr_db(reference_clean_matrix, observed)
        output_snr = _safe_snr_db(reference_clean_matrix, denoised)
        metrics["snr_input_db"] = float(input_snr)
        metrics["snr_output_db"] = float(output_snr)
        metrics["snr_improvement_db"] = float(output_snr - input_snr)
    else:
        metrics["mae_to_reference"] = None
        metrics["rmse_to_reference"] = None
        metrics["correlation_to_reference"] = None
        metrics["peak_error"] = None
        metrics["snr_input_db"] = None
        metrics["snr_output_db"] = None
        metrics["snr_improvement_db"] = None

    if isinstance(reference_quasi, dict):
        reference_quasi_matrix = channel_values_to_matrix(reference_quasi, channels)
        metrics["quasi_dc_correlation"] = _safe_correlation(reference_quasi_matrix.ravel(), quasi.ravel())
        metrics["trend_consistency"] = _safe_correlation(
            np.mean(reference_quasi_matrix, axis=1),
            np.mean(quasi, axis=1),
        )
    else:
        metrics["quasi_dc_correlation"] = None
        metrics["trend_consistency"] = None

    return metrics
