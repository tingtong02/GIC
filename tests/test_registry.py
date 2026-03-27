from __future__ import annotations

from pathlib import Path

from gic.data.registry import RegistryStore


ROOT = Path(__file__).resolve().parents[1]


def test_registry_lists_sources_and_datasets() -> None:
    registry = RegistryStore(project_root=ROOT, registry_root="data/registry")
    assert len(registry.list_sources()) >= 2
    assert len(registry.list_datasets()) >= 2


def test_registry_resolves_active_dataset_path() -> None:
    registry = RegistryStore(project_root=ROOT, registry_root="data/registry")
    path = registry.resolve_dataset_path("matpower_case118_sample")
    assert path.exists()
    assert path.name == "matpower_case118_sample.m"
