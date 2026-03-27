from __future__ import annotations

from pathlib import Path

from gic.data.loaders.timeseries_loader import TimeSeriesLoader
from gic.data.registry import RegistryStore
from gic.signal.export import export_frontend_result
from gic.signal.methods.raw_baseline import RawBaselineFrontend
from gic.signal.preprocess import build_signal_sample_from_timeseries
from gic.signal.schema import FrontendConfig


def test_export_frontend_result_writes_manifest(project_root, tmp_path: Path) -> None:
    registry = RegistryStore(project_root=project_root, registry_root="data/registry")
    dataset = registry.get_dataset("sample_geomagnetic_storm_day")
    source = registry.get_source(dataset.source_name)
    series, _ = TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)
    sample = build_signal_sample_from_timeseries(series, {"synthetic_noise": {"enabled": False}})
    result = RawBaselineFrontend().run(
        sample,
        FrontendConfig(method_name="raw_baseline", method_version="1.0", parameters={}),
    )
    paths = export_frontend_result(
        project_root=tmp_path,
        signal_config={"output_root": "signal_ready"},
        signal_sample=sample,
        result=result,
    )
    assert Path(paths["timeseries"]).exists()
    assert Path(paths["manifest"]).exists()
