from __future__ import annotations

from gic.data.loaders.timeseries_loader import TimeSeriesLoader
from gic.data.registry import RegistryStore
from gic.signal.preprocess import build_signal_sample_from_timeseries


def test_build_signal_sample_from_registry_fixture(project_root) -> None:
    registry = RegistryStore(project_root=project_root, registry_root="data/registry")
    dataset = registry.get_dataset("sample_geomagnetic_storm_day")
    source = registry.get_source(dataset.source_name)
    series, _ = TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)
    signal_sample = build_signal_sample_from_timeseries(
        series,
        {
            "synthetic_noise": {
                "enabled": True,
                "gaussian_std": 1.0,
                "sinusoid_amplitude": 2.0,
                "sinusoid_cycles": 1.0,
                "reference_lowfreq_window": 3,
                "random_seed": 7,
            }
        },
    )
    assert signal_sample.sample_id.startswith("signal_")
    assert len(signal_sample.channels) == 3
    assert signal_sample.metadata["reference_available"] is True
