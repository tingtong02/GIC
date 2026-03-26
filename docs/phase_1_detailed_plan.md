# Phase 1 Detailed Plan  
## 数据资源接入与标准化数据管线建设（Detailed Execution Plan v1）

## 1. 文档元信息

- 文档名称：`phase_1_detailed_plan.md`
- 阶段名称：Phase 1 — 数据资源接入与标准化数据管线建设
- 版本：v1
- 文档角色：**直接执行计划**
- 执行对象：Codex / 开发者
- 上位参考文档：
  - `GIC_project_planning_and_technical_route_v1.md`
  - `GIC_project_phase_roadmap_v1.md`
  - `phase_0_detailed_plan.md`

本文件用于约束 Phase 1 的开发行为。  
在 Phase 1 中，重点是建立**统一数据接入层、标准化 schema、数据注册表和可复用数据管线**，而不是提前实现复杂模型训练。

---

## 2. 本阶段的核心目标

Phase 1 的唯一核心目标是：

> 把项目中准备使用的数据源、测试系统和原始文件纳入统一的数据标准化框架，形成后续物理仿真、信号处理、图建模和训练都能直接复用的数据基础设施。

这意味着本阶段要解决的是：

- 数据放哪里
- 怎么命名
- 怎么读
- 怎么转换
- 怎么注册
- 怎么描述元数据
- 怎么做版本化
- 怎么输出统一中间格式

而不是：

- 追求模型效果
- 实现复杂训练流程
- 过早绑定某个具体算法结构

---

## 3. 非目标（本阶段明确不做的事情）

为了防止 Phase 1 范围失控，本阶段明确**不做**以下内容：

### 3.1 不实现完整 GIC forward solver

本阶段可以为 solver 未来需要的数据准备字段，但**不实现**：

- 线路地电场积分
- Norton 等效注入
- DC 网络求解
- 真值批量生成

这些属于 Phase 2。

### 3.2 不实现完整信号处理算法

本阶段不实现：

- FastICA 主体
- 稀疏表示去噪主体
- 滤波器设计主逻辑
- 时序增强与特征工程实验

这些属于 Phase 3。

### 3.3 不实现图模型或训练流程

本阶段不实现：

- 图数据集训练版封装
- GCN/GAT/Temporal GNN
- 训练脚本
- 损失函数设计
- 模型评估主逻辑

这些属于 Phase 4 / Phase 5。

### 3.4 不实现 KG 推理或复杂语义融合

本阶段可以为 KG 未来使用的数据关系保留字段，但**不实现**：

- 实体对齐主引擎
- 图数据库
- KG 嵌入训练
- relation-aware 学习

这些属于 Phase 6。

### 3.5 不追求“大而全”下载系统

本阶段可以实现基础下载/导入脚本，但不要求：

- 做通用网页抓取系统
- 做复杂鉴权管理
- 做所有公开数据源的自动化接入
- 做大规模增量同步机制

---

## 4. 本阶段完成后应具备的能力

Phase 1 完成后，项目至少应具备以下能力：

1. 可以把一个或多个测试系统纳入统一数据目录；
2. 可以把至少一种地磁/地电场相关时序数据纳入统一标准；
3. 可以为每个数据源生成元数据注册信息；
4. 可以把原始数据转换为统一 schema；
5. 可以做最基本的数据质量检查；
6. 可以输出供 Phase 2/3/4 后续复用的中间数据文件；
7. 可以清楚回答“当前项目有哪些数据、这些数据有什么用、准备不准备使用”。

---

## 5. 本阶段总体策略

Phase 1 应采用“**少量高价值数据源先跑通，再逐步扩展**”的策略。

建议优先顺序如下：

1. 先打通本地文件组织与数据注册表
2. 再打通一个基础测试系统
3. 再打通一种时序驱动数据
4. 再统一输出标准 schema
5. 再做质量检查和索引
6. 最后补充更多数据源占位与说明

不要一开始试图把全部数据源一次性自动化。

---

## 6. 本阶段必须参考的数据清单

本阶段必须以总体技术路线文档中已经明确的高价值数据/系统为准。  
当前建议纳入优先视野的数据分为四类。

## 6.1 电网测试系统类（高优先级）

### 6.1.1 MATPOWER case118
用途：

- 作为标准 IEEE 118-bus 测试系统基线
- 用于验证数据管线能否读入经典 power system case
- 作为后续图结构构建和物理 solver 的基础网络之一

是否准备使用：

- **是，准备使用**
- 但需要注意其原始形式主要服务于 power flow，不天然具备完整 GIC 所需字段

### 6.1.2 UIUC 150-bus / TAMU 相关测试系统
用途：

- 作为更适合扩展 GIC benchmark 的测试系统来源
- 用于后续构建更贴近实际的网络案例
- 用于多拓扑、多参数场景实验

是否准备使用：

- **是，优先准备使用**
- 因为它们比纯经典 IEEE case 更有潜力支持 GIC 扩展

### 6.1.3 TAMU Electric Grid Test Case Repository 其他候选案例
用途：

- 作为后续扩展系统来源
- 用于跨拓扑泛化实验

是否准备使用：

- **暂定作为候选**
- 本阶段不要求全部纳入，只要求预留注册能力

## 6.2 地磁与时序驱动类（高优先级）

### 6.2.1 SuperMAG
用途：

- 获取地磁台站观测数据
- 构建 geomagnetic storm 驱动
- 为后续事件级输入提供真实时序基础

是否准备使用：

- **是，准备使用**
- 本阶段不要求完成全自动大规模接入，但应为其建立数据源描述与接口占位

### 6.2.2 INTERMAGNET
用途：

- 作为官方地磁观测网络数据来源
- 补充和交叉验证 storm 事件驱动

是否准备使用：

- **是，准备使用**
- 本阶段至少应预留 parser / importer 接口与注册表项

### 6.2.3 NOAA 指数 / geomagnetic products
用途：

- 提供 storm 强度背景信息
- 作为事件筛选辅助
- 某些产品可作为地电场近似驱动输入

是否准备使用：

- **是，准备使用**
- 本阶段可以只整理目录与元数据，不要求全量自动化

## 6.3 地电场 / 电导率相关数据（中高优先级）

### 6.3.1 NOAA SWPC Geoelectric Field Models
用途：

- 作为外部地电场驱动参考
- 为 Phase 2 物理仿真提供更接近真实的输入可能性

是否准备使用：

- **是，准备使用**
- 本阶段应预留标准输入格式

### 6.3.2 USGS MT / geoelectric 相关数据
用途：

- 作为 conductivity / impedance / geoelectric 补充信息来源
- 可能支持更真实的地磁到地电场映射

是否准备使用：

- **候选使用**
- 本阶段只需在注册表中列明，不强制完成接入

## 6.4 真实 GIC 观测或参考数据（中优先级）

### 6.4.1 论文附带或可整理的局部 GIC 测量样例
用途：

- 用于后续事件级验证
- 用于趋势/峰值/相关性层面的外部对照

是否准备使用：

- **是，但以“验证用途”为主**
- 本阶段只要求为这类数据预留 schema，不要求大规模清洗完成

---

## 7. 本阶段输入

本阶段输入主要包括规划文档、目录骨架和有限数量的数据样本。

### 7.1 必须参考的输入

- `GIC_project_planning_and_technical_route_v1.md`
- `GIC_project_phase_roadmap_v1.md`
- `phase_0_detailed_plan.md`

### 7.2 Phase 0 产出的工程接口

必须复用以下接口与规范：

- 配置加载接口
- 路径管理接口
- run 管理接口
- logging 接口
- docs/ 与 data/ 目录骨架
- artifacts 保存规范

### 7.3 数据输入来源

允许使用以下输入形式：

- 仓库中的本地原始文件
- 手动下载后放入 `data/raw/` 的公开数据
- 手工整理的测试系统文件
- CSV / JSON / MATPOWER case / 文本配置等文件

本阶段不依赖在线接口必须可用。

---

## 8. 本阶段输出

Phase 1 的输出应是**可被后续阶段稳定消费的数据层**。

至少包括：

- 标准化数据 schema
- 数据注册表
- 原始到中间格式转换器
- 数据加载器
- 数据质量检查器
- 数据索引与清单文档
- 至少一个测试系统样例
- 至少一种时序驱动样例

---

## 9. 目录与文件级设计要求

## 9.1 `data/` 目录进一步细化

建议在现有 Phase 0 基础上补充如下结构：

```text
data/
├── raw/
│   ├── grid_cases/
│   ├── geomagnetic/
│   ├── geoelectric/
│   ├── gic_observations/
│   └── external_docs/
├── interim/
│   ├── grid_cases/
│   ├── timeseries/
│   ├── mappings/
│   └── merged/
├── processed/
│   ├── datasets/
│   ├── graph_ready/
│   ├── physics_ready/
│   └── signal_ready/
└── registry/
    ├── data_sources.yaml
    ├── datasets.yaml
    └── README.md
```

## 9.2 `src/gic/data/` 模块结构建议

```text
src/gic/data/
├── __init__.py
├── registry.py
├── schema.py
├── loaders/
│   ├── __init__.py
│   ├── base_loader.py
│   ├── matpower_loader.py
│   ├── timeseries_loader.py
│   └── metadata_loader.py
├── parsers/
│   ├── __init__.py
│   ├── matpower_parser.py
│   ├── csv_parser.py
│   └── json_parser.py
├── converters/
│   ├── __init__.py
│   ├── grid_converter.py
│   ├── timeseries_converter.py
│   └── id_mapping.py
├── validation/
│   ├── __init__.py
│   ├── checks.py
│   └── reports.py
└── catalog/
    ├── __init__.py
    └── dataset_catalog.py
```

说明：

- `parsers/` 负责读原始格式
- `converters/` 负责转标准格式
- `loaders/` 负责面向下游加载
- `validation/` 负责检查
- `registry.py` / `catalog/` 负责管理已知数据资产

---

## 10. 数据 schema 设计要求

本阶段的最关键设计之一是 schema。  
必须定义统一、明确、后续可扩展的数据结构。

## 10.1 最低需要定义的对象类型

至少定义以下对象的 schema：

1. `GridCase`
2. `BusRecord`
3. `LineRecord`
4. `TransformerRecord`
5. `SubstationRecord`（如暂时缺失可为可选）
6. `SensorRecord`
7. `GeomagneticTimeSeries`
8. `GeoelectricTimeSeries`
9. `GICObservationSeries`
10. `StormEventRecord`
11. `DatasetManifest`
12. `SourceRecord`

## 10.2 `GridCase` 最低字段建议

- `case_id`
- `source_name`
- `case_name`
- `base_mva`（若适用）
- `buses`
- `lines`
- `transformers`
- `substations`（可为空）
- `coordinate_system`
- `notes`
- `available_fields`
- `missing_fields`
- `version`

## 10.3 线路记录最低字段建议

由于后续 GIC 仿真需要线路空间信息和物理信息，因此至少预留：

- `line_id`
- `from_bus`
- `to_bus`
- `resistance`
- `reactance`（可选）
- `length_km`（允许缺失）
- `azimuth_deg`（允许缺失）
- `voltage_level_kv`（可选）
- `series_compensated`（布尔或未知）
- `available_for_gic`（布尔）

即便部分字段现在没有，也必须在 schema 中明确占位。

## 10.4 时序数据 schema 最低字段建议

统一包含：

- `series_id`
- `source_name`
- `station_id` / `sensor_id`
- `time_index`
- `value_columns`
- `units`
- `sampling_interval`
- `timezone`
- `missing_ratio`
- `quality_flags`

## 10.5 数据 manifest 要求

每个标准化后数据集都应带一个 manifest，至少记录：

- 数据集名称
- 来源
- 生成时间
- 原始输入路径
- 转换脚本版本
- schema 版本
- 行数/时间长度
- 缺失值统计
- 备注

---

## 11. 数据注册表要求

## 11.1 目标

建立“项目知道自己有哪些数据”的能力。

## 11.2 必须维护两层注册

### 11.2.1 数据源注册（Source Registry）

记录数据源级信息，例如：

- 数据源名称
- 官网/论文/来源说明
- 使用许可
- 原始文件类型
- 用途
- 当前状态（已接入/候选/仅参考）
- 是否准备使用

### 11.2.2 数据集注册（Dataset Registry）

记录项目内实际生成或接入的数据集，例如：

- 数据集名
- 对应数据源
- 本地路径
- schema 版本
- 时间范围
- 空间范围
- 是否可训练
- 是否仅验证
- 生成方式

## 11.3 注册表文件形式

建议至少维护：

- `data/registry/data_sources.yaml`
- `data/registry/datasets.yaml`

并补充一个说明文件：

- `data/registry/README.md`

---

## 12. 数据接入优先级要求

Codex 在本阶段必须按优先级推进，不允许到处平均发力。

## 12.1 第一优先级：测试系统基础接入

最先打通：

- MATPOWER case118 或等价基础 case
- 至少一个更适合后续扩展的候选测试系统占位信息

目标：

- 让项目能读入一个标准电网 case
- 输出统一 `GridCase`

## 12.2 第二优先级：时序驱动基础接入

至少打通一种时序数据格式，例如：

- 地磁站 CSV/文本
- 指数型时序
- 简化 geoelectric 时序输入

目标：

- 让项目能读入一个标准化时序对象

## 12.3 第三优先级：事件与观测占位接入

建立：

- `StormEventRecord`
- `GICObservationSeries` schema
- 对应样例与注册表项

目标：

- 为未来真实验证预留格式

## 12.4 第四优先级：扩展数据源说明完善

将暂未真正接入的数据源写入注册表和文档，并清楚标记状态：

- planned
- candidate
- reference_only
- active

---

## 13. 解析与转换要求

## 13.1 解析器（Parser）职责

Parser 负责：

- 从原始文件中读取数据
- 保留原始字段语义
- 不做过重推断
- 输出中间原始对象

例如：

- MATPOWER case parser
- CSV parser
- JSON parser

## 13.2 转换器（Converter）职责

Converter 负责：

- 字段名标准化
- 单位标准化
- id 映射
- 时间索引标准化
- 输出统一 schema 对象

### 13.2.1 重要原则

- Parser 不要承担太多标准化逻辑
- Converter 不要依赖特定模型需求
- 标准化应面向后续多个阶段，而非某个单一模型

## 13.3 映射逻辑要求

必须建立基础映射能力：

- `raw_bus_id -> standardized_bus_id`
- `raw_line_id -> standardized_line_id`
- `raw_station_id -> standardized_station_id`

如果无法自动映射，应允许：

- 规则映射
- 手工映射表
- 显式缺失标记

---

## 14. 单位、时间与坐标标准化要求

这是数据层最容易出错的地方，必须明确规则。

## 14.1 单位标准化

必须明确并记录：

- 电阻单位
- 长度单位
- 磁场单位
- 地电场单位
- 时间采样单位

如果原始单位不统一，必须在转换阶段写入标准单位字段。

## 14.2 时间标准化

必须处理：

- 时间戳格式统一
- 时区统一
- 采样间隔记录
- 缺失时间点识别
- 重采样或对齐时的策略记录

禁止无记录地静默重采样。

## 14.3 空间与坐标标准化

如果存在地理信息，必须记录：

- 坐标系类型
- 经纬度是否可用
- 是否有线路方向/长度
- 是否仅有相对位置而无绝对坐标

如果缺失，也必须显式写入 metadata。

---

## 15. 数据质量检查要求

Phase 1 必须实现最基本的数据质量检查功能。

## 15.1 Grid case 检查

至少检查：

- 节点 id 是否唯一
- 线路起止节点是否存在
- 是否有孤立记录
- 是否有重复线路 id
- 关键字段缺失率

## 15.2 时序数据检查

至少检查：

- 时间索引是否单调
- 是否有重复时间戳
- 缺失比例
- 采样间隔是否一致
- 数值列是否存在明显非法值

## 15.3 注册表一致性检查

至少检查：

- 注册的数据路径是否存在
- 数据集名是否唯一
- schema 版本是否填写
- active 数据集是否可加载

## 15.4 报告输出要求

检查结果必须能输出：

- 控制台摘要
- 文件报告（json 或 markdown）

---

## 16. Phase 1 的 CLI 要求

在复用 Phase 0 CLI 结构的基础上，建议为 Phase 1 增加最小数据相关命令。

至少应支持：

- `data-list-sources`
- `data-list-datasets`
- `data-validate`
- `data-build-manifest`
- `data-convert-sample`

### 16.1 约束

- 命令必须复用统一配置
- 不要求一次性支持所有数据源
- 错误消息必须说明数据文件缺失、schema 不匹配或注册表未配置等原因

---

## 17. 配置文件要求

Phase 1 必须新增专用配置文件，例如：

```text
configs/phase1/
  phase1_dev.yaml
  data_sources.yaml
```

## 17.1 配置域建议

至少包括：

```yaml
stage:
  current: phase1

data:
  raw_root: data/raw
  interim_root: data/interim
  processed_root: data/processed
  registry_root: data/registry

  active_grid_sources:
    - matpower_case118

  active_timeseries_sources:
    - sample_geomagnetic_series

  validation:
    run_on_startup: true
    fail_on_missing_required_fields: true

  conversion:
    write_manifest: true
    overwrite_existing: false
```

---

## 18. 文档要求

Phase 1 不仅要写代码，还必须把“当前项目有哪些数据”写清楚。

至少新增以下文档：

- `docs/data/data_inventory.md`
- `docs/data/schema_overview.md`
- `docs/data/source_usage_matrix.md`

## 18.1 `data_inventory.md` 应包含

- 当前已知数据源清单
- 每个数据源的说明
- 路径组织方式
- 当前状态
- 是否准备使用

## 18.2 `source_usage_matrix.md` 应包含

建议用表格式列出：

- 数据源名称
- 类型
- 用途
- 是否准备使用
- 当前状态
- 计划用于哪个阶段
- 备注

## 18.3 `schema_overview.md` 应包含

- 所有标准对象概览
- 字段说明
- 必填与可选字段
- 示例

---

## 19. 推荐文件级实现清单

以下是 Phase 1 推荐实现的文件级清单。Codex 应以此为主要目标。

```text
configs/
  phase1/
    phase1_dev.yaml
    data_sources.yaml

data/
  registry/
    data_sources.yaml
    datasets.yaml
    README.md

docs/
  data/
    data_inventory.md
    schema_overview.md
    source_usage_matrix.md

src/
  gic/
    data/
      registry.py
      schema.py
      catalog/
        dataset_catalog.py
      loaders/
        base_loader.py
        matpower_loader.py
        timeseries_loader.py
      parsers/
        matpower_parser.py
        csv_parser.py
        json_parser.py
      converters/
        grid_converter.py
        timeseries_converter.py
        id_mapping.py
      validation/
        checks.py
        reports.py

tests/
  test_data_schema.py
  test_registry.py
  test_parsers.py
  test_validation.py
```

说明：

- 不要求一次性全部完整实现
- 但文件骨架与核心对象必须建立
- `matpower_loader.py` 和至少一种 `timeseries_loader.py` 应可工作

---

## 20. Codex 在本阶段的实现顺序要求

Codex 必须按以下顺序推进，不允许直接跳到复杂自动化。

### Step 1：补充数据目录和注册表文件骨架

先确保：

- `data/raw/...`
- `data/interim/...`
- `data/processed/...`
- `data/registry/...`

结构稳定。

### Step 2：实现 schema 与 registry 基础

先写：

- `SourceRecord`
- `DatasetManifest`
- `GridCase`
- `GeomagneticTimeSeries`
- `StormEventRecord`
- registry 读写逻辑

### Step 3：实现最小 parser / converter

至少打通：

- MATPOWER case 读入 -> `GridCase`
- 一种简单时序文件 -> `GeomagneticTimeSeries`

### Step 4：实现 validation 检查逻辑

至少覆盖：

- grid case 基础检查
- timeseries 基础检查
- registry 一致性检查

### Step 5：实现数据 CLI 子命令

支持：

- 列表查看
- 简单转换
- 基础验证

### Step 6：补齐文档清单

- data inventory
- source usage matrix
- schema overview

### Step 7：补齐测试

测试应覆盖：

- schema
- parser
- registry
- validation

---

## 21. Phase 1 的验收标准

只有满足以下条件，Phase 1 才算完成。

### 21.1 数据组织完成

- 数据目录结构明确
- 原始 / 中间 / 处理后目录职责清晰
- registry 文件存在

### 21.2 schema 完成

- 至少定义了核心 grid / timeseries / observation / event 对象
- 可区分必填与可选字段
- 支持 manifest

### 21.3 至少两个最小接入样例打通

必须至少打通：

1. 一个电网测试系统样例
2. 一种时序驱动样例

### 21.4 数据校验能力完成

- 可运行基础数据检查
- 可生成检查摘要
- 可识别明显格式问题

### 21.5 注册表能力完成

- 可列出已知数据源
- 可列出实际数据集
- 可清楚标记哪些“准备使用”、哪些只是候选

### 21.6 文档完成

- `data_inventory.md`
- `source_usage_matrix.md`
- `schema_overview.md`

均存在且信息基本完整。

---

## 22. 最低可接受标准（Minimum Acceptable Outcome）

如果时间有限，Phase 1 至少必须达到以下底线：

1. 有统一数据 schema
2. 有 registry
3. 能读入一个测试系统
4. 能读入一个时序样例
5. 能做最基础 validation
6. 能输出一份“数据清单 + 用途 + 是否准备使用”的文档

如果连这个底线都达不到，则 Phase 1 不能结束。

---

## 23. 风险与回退策略

## 23.1 风险：尝试接入过多数据源导致失控

### 对策

- 严格按优先级只打通少量高价值源
- 其余先写进注册表和文档
- 不在 Phase 1 做全量自动化

## 23.2 风险：schema 设计过窄，后续无法扩展

### 对策

- 用“核心必填 + 可选扩展字段”结构
- 明确 `available_fields` 与 `missing_fields`
- 给 GIC 相关关键字段保留占位

## 23.3 风险：过早把 schema 绑定具体模型

### 对策

- schema 只面向数据层
- 不在字段命名中嵌入模型特定概念
- graph-ready / physics-ready 应放在 processed 层，而不是原始 schema 层

## 23.4 风险：测试系统缺少 GIC 必需字段

### 对策

- 明确标记缺失字段
- 使用 `available_for_gic` 或类似布尔标识
- 把字段补全逻辑延后到 Phase 2

## 23.5 风险：真实数据难获取或格式不稳定

### 对策

- 真实数据在本阶段只做 schema 占位和文档登记
- 不把项目主线绑定到必须实时抓取的源
- 优先使用本地可控样例文件

---

## 24. 明确禁止事项

Codex 在本阶段**禁止**做以下事情：

1. 不得实现 GIC forward solver 主逻辑
2. 不得实现 GNN 模型
3. 不得实现复杂训练流程
4. 不得为了某个模型硬改 schema
5. 不得把不同来源数据直接硬编码拼在一起
6. 不得绕开 registry 私自读取随机路径文件
7. 不得把 validation 省略为纯手工检查
8. 不得把所有候选数据源都做成“active”
9. 不得省略“用途”和“是否准备使用”的标记
10. 不得在缺失关键字段时静默忽略而不记录

---

## 25. 建议提交粒度

建议本阶段按以下粒度逐步提交，方便回溯。

### Commit 1
补充 `data/` 目录结构与 registry 文件骨架

### Commit 2
实现 schema 与 registry 基础对象

### Commit 3
实现最小 grid parser / converter

### Commit 4
实现最小时序 parser / converter

### Commit 5
实现 validation 与数据 CLI

### Commit 6
补齐数据文档与 source usage matrix

### Commit 7
补齐测试并做一次阶段性整理

---

## 26. 本阶段完成后的交接要求

Phase 1 完成后，应额外输出一份交接摘要，说明：

- 当前已打通了哪些数据源
- 哪些只是登记为候选
- 当前 schema 覆盖到什么程度
- 哪些字段已具备进入 Phase 2 的条件
- 哪些字段仍缺失，需要 Phase 2 继续补充
- 当前已知数据质量问题是什么

建议存放于：

- `reports/phase1_summary.md`
  或
- `docs/phases/phase1_completion_note.md`

---

## 27. Phase 2 的前置接口要求

为了让 Phase 2 能顺利开始，Phase 1 完成后至少应保证后续能直接使用以下能力：

- 统一 `GridCase` 加载接口
- 统一时序驱动加载接口
- manifest 与 registry 查询接口
- 数据质量检查接口
- 标准化中间格式输出
- 缺失字段显式标记机制

如果这些接口不稳定，Phase 2 不应开始。

---

## 28. 最终执行指令（给 Codex 的摘要版）

下面这段可直接作为对 Codex 的高层执行约束摘要：

> 你正在执行 GIC 项目的 Phase 1。你的目标不是实现物理求解或模型训练，而是建立统一、可追踪、可扩展的数据基础设施。你必须把测试系统、地磁/地电场时序数据和未来可能用到的观测数据纳入统一 schema、registry 和数据目录结构中。你必须优先打通少量高价值样例，而不是一次性接入所有数据源。你必须明确记录每个数据源的用途、当前状态和是否准备使用。你不得把 schema 绑定某个具体模型，不得绕开 registry 随意读取文件，不得省略 validation 和数据文档。

---

## 29. 结论

Phase 1 的本质不是“收集很多数据”，而是：

- 建立统一数据语言；
- 明确项目的数据资产边界；
- 为 Phase 2 物理仿真和后续学习模块提供稳定输入。

如果 Phase 1 做得好，后面无论是物理求解、时序前端、图建模还是 KG，都能在同一个标准化数据层上工作。  
如果 Phase 1 做得差，后续每个阶段都会重复为数据问题付出代价。

Phase 1 完成并验收后，下一步应开始：

- `phase_2_detailed_plan.md`
