from __future__ import annotations

from typing import Any

import numpy as np

from gic.data.schema import GeomagneticTimeSeries
from gic.signal.schema import SignalSample


def build_signal_sample_from_timeseries(series: GeomagneticTimeSeries, signal_config: dict[str, Any]) -> SignalSample:
    channels = list(series.value_columns)
    clean_values = {
        channel: [None if value is None else float(value) for value in series.values[channel]]
        for channel in channels
    }
    observed_values = {channel: list(values) for channel, values in clean_values.items()}
    metadata: dict[str, Any] = {
        "origin_series_id": series.series_id,
        "origin_source_name": series.source_name,
        "reference_clean_values": clean_values,
        "reference_available": True,
    }

    synthetic_noise = signal_config.get("synthetic_noise", {})
    if synthetic_noise.get("enabled", False):
        clean_matrix = channel_values_to_matrix(clean_values, channels)
        noisy_matrix = inject_synthetic_noise(clean_matrix, synthetic_noise)
        observed_values = matrix_to_channel_values(noisy_matrix, channels)
        metadata["synthetic_noise"] = dict(synthetic_noise)
        reference_window = int(synthetic_noise.get("reference_lowfreq_window", 3))
        reference_quasi = moving_average(clean_matrix, reference_window)
        metadata["reference_quasi_dc_values"] = matrix_to_channel_values(reference_quasi, channels)
    else:
        metadata["reference_quasi_dc_values"] = {
            channel: list(values) for channel, values in clean_values.items()
        }

    return SignalSample(
        sample_id=f"signal_{series.series_id}",
        source_name=series.source_name,
        sensor_id=series.station_id,
        time_index=list(series.time_index),
        channels=channels,
        values=observed_values,
        units=dict(series.units),
        sampling_interval=series.sampling_interval,
        metadata=metadata,
    )


def channel_values_to_matrix(values: dict[str, list[float | None]], channels: list[str]) -> np.ndarray:
    rows: list[list[float]] = []
    length = len(values[channels[0]]) if channels else 0
    for index in range(length):
        row: list[float] = []
        for channel in channels:
            value = values[channel][index]
            row.append(float("nan") if value is None else float(value))
        rows.append(row)
    return np.asarray(rows, dtype=float)


def matrix_to_channel_values(matrix: np.ndarray, channels: list[str]) -> dict[str, list[float]]:
    values: dict[str, list[float]] = {}
    for column, channel in enumerate(channels):
        values[channel] = [float(item) for item in matrix[:, column].tolist()]
    return values


def inject_synthetic_noise(matrix: np.ndarray, config: dict[str, Any]) -> np.ndarray:
    gaussian_std = float(config.get("gaussian_std", 1.0))
    sinusoid_amplitude = float(config.get("sinusoid_amplitude", 0.0))
    sinusoid_cycles = float(config.get("sinusoid_cycles", 2.0))
    random_seed = int(config.get("random_seed", 7))
    rng = np.random.default_rng(random_seed)
    time_axis = np.linspace(0.0, 2.0 * np.pi * sinusoid_cycles, matrix.shape[0], endpoint=True)
    noisy = np.array(matrix, copy=True)
    for column in range(matrix.shape[1]):
        harmonic = sinusoid_amplitude * np.cos((column + 1) * time_axis)
        gaussian = rng.normal(0.0, gaussian_std, size=matrix.shape[0])
        noisy[:, column] = noisy[:, column] + harmonic + gaussian
    return noisy


def apply_missing_strategy(matrix: np.ndarray, strategy: str) -> np.ndarray:
    if not np.isnan(matrix).any():
        return np.array(matrix, copy=True)
    filled = np.array(matrix, copy=True)
    for column in range(filled.shape[1]):
        series = filled[:, column]
        mask = np.isnan(series)
        if not mask.any():
            continue
        valid = series[~mask]
        if strategy == "zero":
            fill_value = 0.0
            series[mask] = fill_value
        elif strategy == "forward_fill":
            last = valid[0] if valid.size else 0.0
            for index, item in enumerate(series):
                if np.isnan(item):
                    series[index] = last
                else:
                    last = item
        else:
            fill_value = float(valid.mean()) if valid.size else 0.0
            series[mask] = fill_value
        filled[:, column] = series
    return filled


def moving_average(matrix: np.ndarray, window: int) -> np.ndarray:
    if window <= 1:
        return np.array(matrix, copy=True)
    radius = max(window, 1)
    smoothed = np.zeros_like(matrix, dtype=float)
    kernel = np.ones(radius, dtype=float) / float(radius)
    for column in range(matrix.shape[1]):
        smoothed[:, column] = np.convolve(matrix[:, column], kernel, mode="same")
    return smoothed


def soft_threshold(matrix: np.ndarray, lam: float) -> np.ndarray:
    return np.sign(matrix) * np.maximum(np.abs(matrix) - lam, 0.0)


def prepare_matrix(signal_sample: SignalSample, parameters: dict[str, Any]) -> np.ndarray:
    strategy = str(parameters.get("missing_strategy", "mean"))
    matrix = channel_values_to_matrix(signal_sample.values, signal_sample.channels)
    return apply_missing_strategy(matrix, strategy)
