# Schema Overview

## 核心对象

### `GridCase`

- 必填：`case_id`, `source_name`, `case_name`, `buses`, `lines`, `transformers`, `available_fields`, `missing_fields`, `version`
- 可选：`base_mva`, `substations`, `coordinate_system`, `notes`
- 说明：作为 Phase 2 物理求解与 Phase 4 图建模的统一网络输入对象

### `BusRecord`

- 必填：`bus_id`, `raw_bus_id`
- 可选：`bus_type`, `base_kv`, `vm_pu`, `va_deg`, `notes`

### `LineRecord`

- 必填：`line_id`, `raw_line_id`, `from_bus`, `to_bus`, `resistance`, `available_for_gic`
- 可选：`reactance`, `length_km`, `azimuth_deg`, `voltage_level_kv`, `series_compensated`, `notes`

### `TransformerRecord`

- 必填：`transformer_id`, `raw_transformer_id`, `from_bus`, `to_bus`
- 可选：`tap_ratio`, `phase_shift_deg`, `available_for_gic`, `notes`

### `GeomagneticTimeSeries`

- 必填：`series_id`, `source_name`, `station_id`, `time_index`, `value_columns`, `values`, `units`, `sampling_interval`, `timezone`, `missing_ratio`, `quality_flags`, `version`
- 可选：`notes`
- 说明：Phase 3 的时序前端和 Phase 7 的真实事件输入都应复用该接口

### `GeoelectricTimeSeries`

- 字段结构与 `GeomagneticTimeSeries` 一致
- 当前 Phase 1 只做 schema 占位

### `GICObservationSeries`

- 必填：`series_id`, `source_name`, `sensor_id`, `time_index`, `value_columns`, `values`, `units`, `sampling_interval`, `timezone`, `missing_ratio`, `quality_flags`, `version`
- 当前 Phase 1 只做 schema 占位

### `StormEventRecord`

- 必填：`event_id`, `source_name`, `start_time`, `end_time`, `version`
- 可选：`storm_level`, `notes`

### `SourceRecord`

- 必填：`source_name`, `source_type`, `origin`, `description`, `license`, `raw_file_type`, `status`, `intended_use`, `phases`, `purpose`
- 可选：`homepage`, `notes`

### `DatasetRecord`

- 必填：`dataset_name`, `source_name`, `relative_path`, `schema_version`, `trainable`, `validation_only`, `generation_method`, `status`, `description`
- 可选：`time_range`, `spatial_scope`, `notes`

### `DatasetManifest`

- 必填：`dataset_name`, `source_name`, `generated_at_utc`, `raw_input_paths`, `converter_name`, `schema_version`, `record_count`, `missing_stats`
- 可选：`notes`

## 示例

- `GridCase` 输出示例：`data/interim/grid_cases/matpower_case118_sample.json`
- `GeomagneticTimeSeries` 输出示例：`data/interim/timeseries/sample_geomagnetic_storm_day.json`
- Manifest 输出示例：`data/interim/grid_cases/matpower_case118_sample.manifest.json`
