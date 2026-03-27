from __future__ import annotations

from pathlib import Path

from gic.data.registry import RegistryStore


ROOT = Path(__file__).resolve().parents[1]


def test_registry_lists_sources_and_datasets() -> None:
    registry = RegistryStore(project_root=ROOT, registry_root="data/registry")
    assert len(registry.list_sources()) >= 2
    assert len(registry.list_datasets()) >= 14


def test_registry_resolves_active_dataset_path() -> None:
    registry = RegistryStore(project_root=ROOT, registry_root="data/registry")
    path = registry.resolve_dataset_path("matpower_case118_sample")
    assert path.exists()
    assert path.name == "matpower_case118_sample.m"


def test_registry_contains_added_phase3_real_event_windows() -> None:
    registry = RegistryStore(project_root=ROOT, registry_root="data/registry")
    expected = {
        "intermagnet_bou_2020_oct01_smoke",
        "intermagnet_frd_2020_oct01_smoke",
        "intermagnet_ott_2020_oct01_smoke",
        "intermagnet_bou_2020_nov01_smoke",
        "intermagnet_frd_2020_nov01_smoke",
        "intermagnet_ott_2020_nov01_smoke",
    }
    dataset_names = {item.dataset_name for item in registry.list_datasets()}
    assert expected.issubset(dataset_names)
