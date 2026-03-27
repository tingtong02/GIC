# Phase 1 Completion Note

## 已打通的数据源

- `matpower_case118` -> `matpower_case118_sample`
- `sample_geomagnetic_series` -> `sample_geomagnetic_storm_day`

## 已登记但未打通的数据源

- `uiuc_150_bus_candidate`
- `supermag_reference`
- `intermagnet_reference`
- `noaa_geoelectric_reference`
- `paper_gic_observation_reference`

## 当前 schema 覆盖范围

- grid: `GridCase`, `BusRecord`, `LineRecord`, `TransformerRecord`, `SubstationRecord`
- time series: `GeomagneticTimeSeries`, `GeoelectricTimeSeries`, `GICObservationSeries`
- event / registry: `StormEventRecord`, `SourceRecord`, `DatasetRecord`, `DatasetManifest`

## 已具备进入 Phase 2 的字段与接口

- 统一 `GridCase` 加载接口
- 统一 geomagnetic time series 加载接口
- registry 查询接口
- manifest 输出接口
- validation 报告接口

## 当前仍缺失并留待 Phase 2/3 继续补充

- 线路长度、方位角、接地参数等更完整 GIC 所需字段
- 更真实的 geoelectric 输入
- 真实 GIC observation 清洗接入

## 当前已知数据质量问题

- MATPOWER 样例不包含完整 GIC 所需空间字段，因此这些字段在 schema 中被显式标记为缺失
- 当前 geomagnetic 样例是本地小样本，只用于 Phase 1 管线验证，不代表真实 storm 复杂性
