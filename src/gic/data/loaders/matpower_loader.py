from __future__ import annotations

from pathlib import Path

from gic.data.converters.grid_converter import convert_matpower_to_grid_case
from gic.data.loaders.base_loader import BaseLoader
from gic.data.parsers.matpower_parser import parse_matpower_case
from gic.data.schema import DatasetManifest, DatasetRecord, GridCase, SourceRecord


class MatpowerLoader(BaseLoader):
    def load(
        self,
        dataset: DatasetRecord,
        source: SourceRecord,
    ) -> tuple[GridCase, DatasetManifest]:
        raw_path = (self.project_root / dataset.relative_path).resolve()
        raw_case = parse_matpower_case(raw_path)
        return convert_matpower_to_grid_case(
            raw_case,
            dataset_name=dataset.dataset_name,
            source_name=source.source_name,
            raw_input_path=str(raw_path),
        )
