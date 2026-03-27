from __future__ import annotations

from typing import Any

import numpy as np

from gic.signal.preprocess import channel_values_to_matrix
from gic.signal.schema import SignalFeatureSet, SignalSample


def extract_signal_feature_set(
    *,
    signal_sample: SignalSample,
    method_name: str,
    quasi_dc_values: dict[str, list[float]],
    denoised_values: dict[str, list[float]],
    parameters: dict[str, Any],
) -> SignalFeatureSet:
    channels = list(signal_sample.channels)
    quasi = channel_values_to_matrix(quasi_dc_values, channels)
    denoised = channel_values_to_matrix(denoised_values, channels)
    observed = channel_values_to_matrix(signal_sample.values, channels)
    summary_statistics: dict[str, float] = {}
    peak_features: dict[str, float] = {}
    trend_features: dict[str, float] = {}
    spectral_features: dict[str, float] = {}
    quality_flags: list[str] = []

    for column, channel in enumerate(channels):
        series = quasi[:, column]
        summary_statistics[f"{channel}.mean"] = float(np.mean(series))
        summary_statistics[f"{channel}.std"] = float(np.std(series))
        summary_statistics[f"{channel}.max"] = float(np.max(series))
        summary_statistics[f"{channel}.min"] = float(np.min(series))
        summary_statistics[f"{channel}.peak_to_peak"] = float(np.ptp(series))
        peak_features[f"{channel}.abs_peak"] = float(np.max(np.abs(series)))
        peak_features[f"{channel}.peak_index"] = float(np.argmax(np.abs(series)))
        trend_features[f"{channel}.start_end_delta"] = float(series[-1] - series[0])
        trend_features[f"{channel}.slope"] = float((series[-1] - series[0]) / max(len(series) - 1, 1))
        residual = denoised[:, column] - quasi[:, column]
        base_energy = float(np.sum(np.square(observed[:, column])) + 1e-9)
        spectral_features[f"{channel}.residual_energy_ratio"] = float(np.sum(np.square(residual)) / base_energy)

    if quasi.shape[0] < 8:
        quality_flags.append("short_sequence")
    if signal_sample.metadata.get("reference_available"):
        quality_flags.append("reference_available")

    return SignalFeatureSet(
        feature_id=f"{signal_sample.sample_id}_{method_name}_features",
        window_definition={
            "enabled": bool(parameters.get("window_enabled", True)),
            "size": int(parameters.get("window_size", quasi.shape[0])),
            "stride": int(parameters.get("window_stride", max(quasi.shape[0], 1))),
            "observed_points": quasi.shape[0],
        },
        summary_statistics=summary_statistics,
        peak_features=peak_features,
        trend_features=trend_features,
        spectral_features=spectral_features,
        quality_flags=quality_flags,
    )
