from __future__ import annotations

from pathlib import Path

from gic.data.loaders.timeseries_loader import TimeSeriesLoader
from gic.data.registry import RegistryStore


def test_intermagnet_station_archive_smoke_window(project_root) -> None:
    registry = RegistryStore(project_root=project_root, registry_root='data/registry')
    dataset = registry.get_dataset('intermagnet_bou_2020_sep01_smoke')
    source = registry.get_source(dataset.source_name)
    series, manifest = TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)
    assert series.station_id == 'BOU'
    assert len(series.time_index) == 1440
    assert series.time_index[0] == '2020-09-01T00:00:00Z'
    assert series.time_index[-1] == '2020-09-01T23:59:00Z'
    assert 'H' in series.value_columns or 'X' in series.value_columns
    assert manifest.converter_name == 'convert_intermagnet_station_archive'
    assert series.metadata['disable_synthetic_noise'] is True
