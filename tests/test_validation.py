from __future__ import annotations

from pathlib import Path

from gic.data.loaders.matpower_loader import MatpowerLoader
from gic.data.loaders.timeseries_loader import TimeSeriesLoader
from gic.data.registry import RegistryStore
from gic.data.validation.checks import (
    validate_geomagnetic_timeseries,
    validate_grid_case,
    validate_registry_consistency,
)


ROOT = Path(__file__).resolve().parents[1]


def test_registry_validation_passes_for_phase1_registry() -> None:
    registry = RegistryStore(project_root=ROOT, registry_root="data/registry")
    report = validate_registry_consistency(registry)
    assert report["ok"] is True
    assert report["errors"] == []


def test_grid_case_validation_returns_warning_for_missing_fields() -> None:
    registry = RegistryStore(project_root=ROOT, registry_root="data/registry")
    dataset = registry.get_dataset("matpower_case118_sample")
    source = registry.get_source(dataset.source_name)
    grid_case, _ = MatpowerLoader(ROOT).load(dataset, source)
    report = validate_grid_case(grid_case)
    assert report["ok"] is True
    assert report["warnings"]


def test_timeseries_validation_passes_for_sample_fixture() -> None:
    registry = RegistryStore(project_root=ROOT, registry_root="data/registry")
    dataset = registry.get_dataset("sample_geomagnetic_storm_day")
    source = registry.get_source(dataset.source_name)
    series, _ = TimeSeriesLoader(ROOT).load_geomagnetic(dataset, source)
    report = validate_geomagnetic_timeseries(series)
    assert report["ok"] is True
