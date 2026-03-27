from __future__ import annotations

from gic.data.converters.timeseries_converter import convert_geomagnetic_rows
from gic.data.loaders.base_loader import BaseLoader
from gic.data.parsers.csv_parser import parse_csv_file
from gic.data.schema import DatasetManifest, DatasetRecord, GeomagneticTimeSeries, SourceRecord


class TimeSeriesLoader(BaseLoader):
    def load_geomagnetic(
        self,
        dataset: DatasetRecord,
        source: SourceRecord,
    ) -> tuple[GeomagneticTimeSeries, DatasetManifest]:
        raw_path = (self.project_root / dataset.relative_path).resolve()
        rows = parse_csv_file(raw_path)
        return convert_geomagnetic_rows(
            rows,
            dataset_name=dataset.dataset_name,
            source_name=source.source_name,
            raw_input_path=str(raw_path),
        )
