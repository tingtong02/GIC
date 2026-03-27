from __future__ import annotations

import json
from pathlib import Path

from gic.data.converters.intermagnet_converter import convert_intermagnet_station_archive
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
        if source.raw_file_type == 'csv' or raw_path.suffix.lower() == '.csv':
            rows = parse_csv_file(raw_path)
            return convert_geomagnetic_rows(
                rows,
                dataset_name=dataset.dataset_name,
                source_name=source.source_name,
                raw_input_path=str(raw_path),
            )
        if source.raw_file_type == 'intermagnet_bin_dir' and raw_path.is_dir():
            return convert_intermagnet_station_archive(
                station_root=raw_path,
                dataset_name=dataset.dataset_name,
                source_name=source.source_name,
                time_range=dataset.time_range,
            )
        if raw_path.suffix.lower() == '.json':
            payload = json.loads(raw_path.read_text(encoding='utf-8'))
            series_payload = payload.get('series', payload)
            manifest_payload = payload.get('manifest', {
                'dataset_name': dataset.dataset_name,
                'source_name': source.source_name,
                'generated_at_utc': '',
                'raw_input_paths': [str(raw_path)],
                'converter_name': 'json_passthrough',
                'schema_version': series_payload.get('version', '1.0'),
                'record_count': len(series_payload.get('time_index', [])),
                'missing_stats': {'missing_ratio': series_payload.get('missing_ratio', 0.0)},
                'notes': 'Loaded from standardized JSON payload.',
            })
            return GeomagneticTimeSeries(**series_payload), DatasetManifest(**manifest_payload)
        raise ValueError(f'Unsupported geomagnetic dataset format: {raw_path}')
