from __future__ import annotations

from gic.signal.schema import FrontendConfig, SignalFeatureSet, SignalSample, signal_to_dict


def test_signal_sample_serializes() -> None:
    sample = SignalSample(
        sample_id="sample_a",
        source_name="fixture",
        sensor_id="AAA",
        time_index=["2024-01-01T00:00:00Z"],
        channels=["bx"],
        values={"bx": [1.0]},
        units={"bx": "nT"},
        sampling_interval="60s",
    )
    payload = signal_to_dict(sample)
    assert payload["sample_id"] == "sample_a"
    assert payload["channels"] == ["bx"]


def test_frontend_config_and_feature_set() -> None:
    config = FrontendConfig(method_name="raw_baseline", method_version="1.0", parameters={})
    feature_set = SignalFeatureSet(
        feature_id="feature_a",
        window_definition={"enabled": True},
        summary_statistics={"bx.mean": 1.0},
        peak_features={"bx.abs_peak": 1.0},
        trend_features={"bx.slope": 0.0},
    )
    assert config.method_name == "raw_baseline"
    assert feature_set.summary_statistics["bx.mean"] == 1.0
