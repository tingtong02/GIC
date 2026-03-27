from __future__ import annotations

from gic.data.loaders.timeseries_loader import TimeSeriesLoader
from gic.data.registry import RegistryStore
from gic.signal.methods.lowfreq_frontend import LowFrequencyFrontend
from gic.signal.preprocess import build_signal_sample_from_timeseries
from gic.signal.schema import FrontendConfig


def test_lowfreq_frontend_smooths_fixture(project_root) -> None:
    registry = RegistryStore(project_root=project_root, registry_root="data/registry")
    dataset = registry.get_dataset("sample_geomagnetic_storm_day")
    source = registry.get_source(dataset.source_name)
    series, _ = TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)
    sample = build_signal_sample_from_timeseries(series, {"synthetic_noise": {"enabled": False}})
    result = LowFrequencyFrontend().run(
        sample,
        FrontendConfig(
            method_name="lowfreq_baseline",
            method_version="1.0",
            parameters={"smoothing_window": 3},
        ),
    )
    assert result.method_name == "lowfreq_baseline"
    assert "bx_nT.mean" in result.feature_set.summary_statistics
