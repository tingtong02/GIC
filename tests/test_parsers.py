from __future__ import annotations

from pathlib import Path

from gic.data.loaders.matpower_loader import MatpowerLoader
from gic.data.loaders.timeseries_loader import TimeSeriesLoader
from gic.data.parsers.csv_parser import parse_csv_file
from gic.data.parsers.matpower_parser import parse_matpower_case
from gic.data.registry import RegistryStore


ROOT = Path(__file__).resolve().parents[1]


def test_parse_matpower_case_fixture() -> None:
    payload = parse_matpower_case(ROOT / "data/raw/grid_cases/matpower_case118_sample.m")
    assert payload["baseMVA"] == 100.0
    assert len(payload["bus"]) == 3
    assert len(payload["branch"]) == 2


def test_parse_csv_fixture() -> None:
    rows = parse_csv_file(ROOT / "data/raw/geomagnetic/sample_geomagnetic_series.csv")
    assert len(rows) == 5
    assert rows[0]["station_id"] == "AAA"


def test_loaders_convert_registry_datasets() -> None:
    registry = RegistryStore(project_root=ROOT, registry_root="data/registry")
    grid_dataset = registry.get_dataset("matpower_case118_sample")
    grid_source = registry.get_source(grid_dataset.source_name)
    grid_case, _ = MatpowerLoader(ROOT).load(grid_dataset, grid_source)
    assert len(grid_case.buses) == 3

    ts_dataset = registry.get_dataset("sample_geomagnetic_storm_day")
    ts_source = registry.get_source(ts_dataset.source_name)
    series, _ = TimeSeriesLoader(ROOT).load_geomagnetic(ts_dataset, ts_source)
    assert series.sampling_interval == "60s"
