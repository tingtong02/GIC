from __future__ import annotations

import math
from typing import Any

import numpy as np

from gic.signal.preprocess import channel_values_to_matrix
from gic.signal.schema import SignalSample


def _safe_correlation(left: np.ndarray, right: np.ndarray) -> float:
    mask = np.isfinite(left) & np.isfinite(right)
    if int(mask.sum()) < 2:
        return 0.0
    safe_left = left[mask]
    safe_right = right[mask]
    if np.allclose(np.std(safe_left), 0.0) or np.allclose(np.std(safe_right), 0.0):
        return 0.0
    return float(np.corrcoef(safe_left, safe_right)[0, 1])


def _safe_snr_db(reference: np.ndarray, estimate: np.ndarray) -> float:
    mask = np.isfinite(reference) & np.isfinite(estimate)
    safe_reference = reference[mask]
    safe_estimate = estimate[mask]
    signal_power = float(np.sum(np.square(safe_reference)) + 1e-9)
    noise_power = float(np.sum(np.square(safe_reference - safe_estimate)) + 1e-9)
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
    observed_energy = float(np.nansum(np.square(observed)) + 1e-9)
    common_metrics: dict[str, Any] = {
        'runtime_ms': float(runtime_ms),
        'channel_count': len(channels),
        'point_count': observed.shape[0],
        'residual_highfreq_ratio': float(np.nansum(np.square(denoised - quasi)) / observed_energy),
        'smoothing_strength': float(np.nansum(np.square(observed - quasi)) / observed_energy),
        'peak_preservation_ratio': float(np.nanmax(np.abs(quasi)) / (np.nanmax(np.abs(observed)) + 1e-9)),
    }
    synthetic_reference_metrics: dict[str, Any] = {}
    reference_absent_metrics: dict[str, Any] = {
        'trend_alignment_to_observed': _safe_correlation(np.nanmean(observed, axis=1), np.nanmean(quasi, axis=1)),
        'denoised_observed_correlation': _safe_correlation(observed.ravel(), denoised.ravel()),
        'quasi_dc_variance_ratio': float(np.nanvar(quasi) / (np.nanvar(observed) + 1e-9)),
        'peak_preservation_ratio': common_metrics['peak_preservation_ratio'],
        'stability_score': float(1.0 / (1.0 + np.nanmean(np.nanstd(denoised - quasi, axis=0)))),
    }
    metrics: dict[str, Any] = {
        **common_metrics,
        'synthetic_reference_metrics': synthetic_reference_metrics,
        'reference_absent_metrics': reference_absent_metrics,
        'reference_available': False,
        'benchmark_type': signal_sample.metadata.get('benchmark_type', 'real_event'),
        'mae_to_reference': None,
        'rmse_to_reference': None,
        'correlation_to_reference': None,
        'peak_error': None,
        'snr_input_db': None,
        'snr_output_db': None,
        'snr_improvement_db': None,
        'quasi_dc_correlation': None,
        'trend_consistency': None,
    }

    reference_clean = signal_sample.metadata.get('reference_clean_values')
    reference_quasi = signal_sample.metadata.get('reference_quasi_dc_values')
    if isinstance(reference_clean, dict):
        reference_clean_matrix = channel_values_to_matrix(reference_clean, channels)
        diff = denoised - reference_clean_matrix
        input_snr = _safe_snr_db(reference_clean_matrix, observed)
        output_snr = _safe_snr_db(reference_clean_matrix, denoised)
        synthetic_reference_metrics.update(
            {
                'mae_to_reference': float(np.nanmean(np.abs(diff))),
                'rmse_to_reference': float(np.sqrt(np.nanmean(np.square(diff)))),
                'correlation_to_reference': _safe_correlation(reference_clean_matrix.ravel(), denoised.ravel()),
                'peak_error': float(abs(np.nanmax(np.abs(denoised)) - np.nanmax(np.abs(reference_clean_matrix)))),
                'snr_input_db': float(input_snr),
                'snr_output_db': float(output_snr),
                'snr_improvement_db': float(output_snr - input_snr),
            }
        )
        metrics.update(synthetic_reference_metrics)
        metrics['reference_available'] = True
        metrics['benchmark_type'] = 'synthetic'
    if isinstance(reference_quasi, dict):
        reference_quasi_matrix = channel_values_to_matrix(reference_quasi, channels)
        quasi_dc_correlation = _safe_correlation(reference_quasi_matrix.ravel(), quasi.ravel())
        trend_consistency = _safe_correlation(np.nanmean(reference_quasi_matrix, axis=1), np.nanmean(quasi, axis=1))
        metrics['quasi_dc_correlation'] = quasi_dc_correlation
        metrics['trend_consistency'] = trend_consistency
        synthetic_reference_metrics['quasi_dc_correlation'] = quasi_dc_correlation
        synthetic_reference_metrics['trend_consistency'] = trend_consistency
        metrics['reference_available'] = True
        metrics['benchmark_type'] = 'synthetic'
    return metrics
