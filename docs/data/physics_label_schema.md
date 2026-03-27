# Physics Label Schema

## Line-level 字段

- `line_id`
- `projected_field`
- `induced_quantity`
- `included_in_solver`
- `notes`

## Bus-level 字段

- `bus_id`
- `solved_quantity`
- `connected_components_info`
- `quality_flag`

## Transformer-level 字段

- `transformer_id`
- `gic_value`
- `associated_bus_ids`
- `voltage_level`
- `quality_flag`
- `included_in_risk_output`

## Manifest 字段

- `dataset_name`
- `sample_count`
- `time_length`
- `case_source`
- `scenario_type`
- `solver_version`
- `schema_version`
- `assumptions`
- `generated_at_utc`
- `paths`

## 标识规则

- `solution_id = scenario_id + snapshot_id`
- `scenario_id` 来源于场景配置生成器
- `dataset_name` 与导出 bundle 使用同一 scenario id
