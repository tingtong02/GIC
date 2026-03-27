from __future__ import annotations

from gic.data.registry import RegistryStore
from gic.data.schema import DatasetRecord


class DatasetCatalog:
    def __init__(self, registry: RegistryStore):
        self.registry = registry

    def list_active_grid_datasets(self) -> list[DatasetRecord]:
        datasets = []
        for dataset in self.registry.active_datasets():
            source = self.registry.get_source(dataset.source_name)
            if source.source_type == "grid_case":
                datasets.append(dataset)
        return datasets

    def list_active_timeseries_datasets(self) -> list[DatasetRecord]:
        datasets = []
        for dataset in self.registry.active_datasets():
            source = self.registry.get_source(dataset.source_name)
            if source.source_type in {"geomagnetic_timeseries", "geoelectric_timeseries", "gic_observation"}:
                datasets.append(dataset)
        return datasets
