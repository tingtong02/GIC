# Data Inventory

## 当前已知数据源清单

### 已接入并可加载

- `matpower_case118`
  - 类型：grid_case
  - 当前样例：`data/raw/grid_cases/matpower_case118_sample.m`
  - 用途：Phase 1 基础 grid case 接入；Phase 2 物理求解输入基础；Phase 4 图结构构建基础
  - 当前状态：active
  - 是否准备使用：是

- `sample_geomagnetic_series`
  - 类型：geomagnetic_timeseries
  - 当前样例：`data/raw/geomagnetic/sample_geomagnetic_series.csv`
  - 用途：Phase 1 时序 schema / parser / validation 验证；Phase 3 前端输入占位
  - 当前状态：active
  - 是否准备使用：是

### 已登记但当前未打通

- `uiuc_150_bus_candidate`
  - 类型：grid_case
  - 用途：更大测试系统候选
  - 当前状态：candidate
  - 是否准备使用：是

- `supermag_reference`
  - 类型：geomagnetic_timeseries
  - 用途：真实地磁事件驱动来源
  - 当前状态：planned
  - 是否准备使用：是

- `intermagnet_reference`
  - 类型：geomagnetic_timeseries
  - 用途：官方地磁观测补充来源
  - 当前状态：planned
  - 是否准备使用：是

- `noaa_geoelectric_reference`
  - 类型：geoelectric_timeseries
  - 用途：未来地电场驱动输入参考
  - 当前状态：candidate
  - 是否准备使用：是

- `paper_gic_observation_reference`
  - 类型：gic_observation
  - 用途：未来外部验证占位
  - 当前状态：reference_only
  - 是否准备使用：是

## 路径组织方式

- `data/raw/grid_cases/`: 原始或原始形态保留的电网测试系统文件
- `data/raw/geomagnetic/`: 原始 geomagnetic 时序样例
- `data/interim/grid_cases/`: 标准化 `GridCase` JSON 输出与 manifest
- `data/interim/timeseries/`: 标准化时序 JSON 输出与 manifest
- `data/registry/`: 数据源注册表与数据集注册表

## 当前 Phase 1 已打通的最小样例

- grid case：`matpower_case118_sample`
- time series：`sample_geomagnetic_storm_day`
