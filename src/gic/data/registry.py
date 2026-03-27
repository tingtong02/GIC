from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

from gic.data.schema import DatasetRecord, SourceRecord


class RegistryError(ValueError):
    """Raised when registry content is missing or malformed."""


def _read_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RegistryError(f"Registry file does not exist: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        payload = yaml.safe_load(text) if yaml is not None else json.loads(text)
    except Exception as exc:  # pragma: no cover
        raise RegistryError(f"Failed to parse registry file {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RegistryError(f"Registry payload must be a mapping: {path}")
    return payload


class RegistryStore:
    def __init__(self, project_root: str | Path, registry_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.registry_root = (self.project_root / registry_root).resolve()
        self.sources_path = self.registry_root / "data_sources.yaml"
        self.datasets_path = self.registry_root / "datasets.yaml"
        self._sources = self._load_sources()
        self._datasets = self._load_datasets()

    def _load_sources(self) -> list[SourceRecord]:
        payload = _read_mapping(self.sources_path)
        items = payload.get("sources", [])
        if not isinstance(items, list):
            raise RegistryError("Registry sources must be a list")
        return [SourceRecord(**item) for item in items]

    def _load_datasets(self) -> list[DatasetRecord]:
        payload = _read_mapping(self.datasets_path)
        items = payload.get("datasets", [])
        if not isinstance(items, list):
            raise RegistryError("Registry datasets must be a list")
        return [DatasetRecord(**item) for item in items]

    def list_sources(self) -> list[SourceRecord]:
        return list(self._sources)

    def list_datasets(self) -> list[DatasetRecord]:
        return list(self._datasets)

    def get_source(self, source_name: str) -> SourceRecord:
        for item in self._sources:
            if item.source_name == source_name:
                return item
        raise RegistryError(f"Unknown source: {source_name}")

    def get_dataset(self, dataset_name: str) -> DatasetRecord:
        for item in self._datasets:
            if item.dataset_name == dataset_name:
                return item
        raise RegistryError(f"Unknown dataset: {dataset_name}")

    def resolve_dataset_path(self, dataset_name: str) -> Path:
        dataset = self.get_dataset(dataset_name)
        return (self.project_root / dataset.relative_path).resolve()

    def active_datasets(self) -> list[DatasetRecord]:
        return [item for item in self._datasets if item.status == "active"]
