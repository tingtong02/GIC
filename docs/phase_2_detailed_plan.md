# Phase 2 Detailed Plan  
## GIC 物理仿真与合成标签生成框架（Detailed Execution Plan v1）

## 1. 文档元信息

- 文档名称：`phase_2_detailed_plan.md`
- 阶段名称：Phase 2 — GIC 物理仿真与合成标签生成框架
- 版本：v1
- 文档角色：**直接执行计划**
- 执行对象：Codex / 开发者
- 上位参考文档：
  - `GIC_project_planning_and_technical_route_v1.md`
  - `GIC_project_phase_roadmap_v1.md`
  - `phase_0_detailed_plan.md`
  - `phase_1_detailed_plan.md`

本文件用于约束 Phase 2 的开发行为。  
在 Phase 2 中，核心任务是建立**可复用、可检查、可扩展的 GIC forward solver 与合成标签生成框架**，为后续图模型与时序模型提供可信的训练标签与物理 baseline。

---

## 2. 本阶段的核心目标

Phase 2 的唯一核心目标是：

> 基于标准化电网测试系统、地电场/地磁驱动和设备参数，建立一个模块化 GIC 物理仿真框架，能够生成 transformer-level / line-level / node-level 的合成标签与基线输出。

这意味着本阶段必须解决以下问题：

- 电网如何从数据层映射到 GIC 计算层
- 地电场输入如何作用到线路
- 线路感应量如何转为注入量
- DC 网络如何求解
- 如何输出后续模型可直接使用的标签文件
- 如何批量生成不同事件、不同参数扰动、不同观测稀疏率的训练样本

这也是整个项目里最关键的“标签来源阶段”。  
如果 Phase 2 做不好，后续 Phase 4 / Phase 5 的学习过程就会失去稳固基础。

---

## 3. 非目标（本阶段明确不做的事情）

为了防止 Phase 2 范围失控，本阶段明确**不做**以下内容：

### 3.1 不实现真正的学习模型

本阶段不实现：

- GCN / GraphSAGE / GAT
- Temporal GNN
- Hetero-GNN
- Physics-informed trainable model
- ranking head / hotspot head 等学习式输出头

这些属于 Phase 4 / Phase 5。

### 3.2 不实现复杂信号前端算法

本阶段可以接收来自 Phase 1 的标准化时序输入，但**不负责**：

- FastICA
- 自适应稀疏表示去噪
- 时序前端融合
- 前端性能对比实验

这些属于 Phase 3。

### 3.3 不实现 KG 语义建模

本阶段可以保留一些关系字段供未来 KG 使用，但不实现：

- KG schema 主体
- 知识抽取
- 关系推理
- KG 融合到模型

这些属于 Phase 6。

### 3.4 不追求真实世界极高精度物理拟合

本阶段目标是建立**合理、可控、可复现、可扩展**的物理近似框架，而不是：

- 完全复刻复杂工业级 GIC 仿真平台
- 覆盖所有电网设备特殊结构
- 依赖大量难以获得的真实参数

### 3.5 不做模型评价驱动的物理层污染

本阶段不能为了后续模型效果方便而篡改物理标签定义，例如：

- 把标签直接做成模型容易学的形式而失去物理意义
- 用后验统计修正掩盖 solver 问题
- 在没有记录的情况下手工改值

---

## 4. 本阶段完成后应具备的能力

Phase 2 完成后，项目至少应具备以下能力：

1. 能读取 Phase 1 输出的标准化 `GridCase`
2. 能接收一种或多种地电场驱动表示
3. 能对线路计算 GIC 相关感应输入
4. 能建立 DC conductance network 或等效求解结构
5. 能输出 transformer-level / line-level / node-level 结果
6. 能批量生成多场景合成样本
7. 能为后续模型提供稳定物理 baseline 和标签数据
8. 能记录哪些字段是真实给定、哪些是推断/补全的

---

## 5. 本阶段总体策略

Phase 2 必须采用“**从简单、清晰、可检查的 solver 开始，再逐渐增加复杂度**”的策略。

建议推进顺序如下：

1. 先固定物理计算接口与对象表示
2. 再实现单时刻、简化均匀场的 solver
3. 再加入线路方向、长度与地电场投影
4. 再加入 transformer-level 汇总输出
5. 再扩展到时序驱动与批量样本
6. 再加入参数扰动、场景生成与标签导出
7. 最后补充 sanity check、可视化与报告

不要一开始就尝试实现所有复杂变压器结构和所有现实电场模型。

---

## 6. 本阶段必须依赖的输入

## 6.1 上位文档与阶段文档

必须参考：

- `GIC_project_planning_and_technical_route_v1.md`
- `GIC_project_phase_roadmap_v1.md`
- `phase_0_detailed_plan.md`
- `phase_1_detailed_plan.md`

## 6.2 Phase 1 的数据接口

必须复用以下能力：

- `GridCase` 标准对象
- 标准化线路、母线、变压器、站点记录
- 标准化时序对象
- manifest 与 registry 查询能力
- 数据校验接口

## 6.3 当前项目中优先使用的数据输入类型

### 6.3.1 测试系统输入
优先使用：

- MATPOWER case118 或等价基础电网 case
- UIUC 150-bus / TAMU 相关可扩展测试系统

### 6.3.2 场输入
优先支持：

- 均匀地电场（最简单 baseline）
- 区域常值或分片地电场
- 来自标准时序对象的简化驱动
- 未来真实 geoelectric input 的占位接口

### 6.3.3 设备参数输入
本阶段允许部分字段缺失，但必须显式标记，例如：

- 线路长度缺失
- 线路方向缺失
- 接地参数不全
- 变压器类型未完全区分

这些缺失不能静默忽略，必须通过 metadata 或报告记下来。

---

## 7. 本阶段输出

Phase 2 的输出应是**可供学习模型和后续阶段直接消费的物理基线与标签资产**。

至少包括：

- 单时刻 solver 结果
- 时序 solver 结果
- 线路级感应输入
- 设备级 GIC 输出
- 物理 baseline 数据集
- 场景生成配置
- 样本 manifest
- 质量检查与 sanity check 报告

---

## 8. 物理层对象设计要求

本阶段要在 Phase 1 的数据对象之上，再建立面向求解的物理对象表示。

## 8.1 最低需要定义的物理对象

至少应定义：

1. `PhysicsGridCase`
2. `PhysicsLine`
3. `PhysicsBus`
4. `PhysicsTransformer`
5. `GroundingRecord`
6. `ElectricFieldSnapshot`
7. `ElectricFieldSeries`
8. `GICSolution`
9. `ScenarioConfig`
10. `LabelManifest`

## 8.2 `PhysicsGridCase` 最低职责

`PhysicsGridCase` 不是对 `GridCase` 的简单复制，而应是：

- 已筛选出对 GIC 求解可用的设备集合
- 已补充或显式标注关键缺失字段
- 可建立 DC conductance network
- 可与场输入和求解器直接交互

最低字段建议：

- `case_id`
- `source_case_id`
- `buses`
- `lines`
- `transformers`
- `grounding`
- `gic_ready`
- `available_for_solver`
- `missing_required_fields`
- `assumptions`
- `version`

## 8.3 `ElectricFieldSnapshot` 最低字段建议

- `snapshot_id`
- `time`
- `field_mode`
- `reference_frame`
- `global_ex`
- `global_ey`
- `regional_fields`（可选）
- `units`
- `notes`

说明：

- 本阶段必须优先支持简化字段表示
- 不要求一开始就做复杂空间网格场

## 8.4 `GICSolution` 最低字段建议

至少包括：

- `solution_id`
- `case_id`
- `time`
- `scenario_id`
- `line_inputs`
- `bus_quantities`
- `transformer_gic`
- `solver_status`
- `solver_metadata`
- `assumptions`
- `quality_flags`

---

## 9. Solver 分层设计要求

这是本阶段最重要的工程边界。  
Codex 必须按“输入层 -> 组网层 -> 求解层 -> 输出层”的分层方式实现。

## 9.1 输入层（Input Layer）

职责：

- 接收 `PhysicsGridCase`
- 接收 `ElectricFieldSnapshot` / `ElectricFieldSeries`
- 接收场景配置
- 做基础字段检查

禁止在这一层掺入复杂数值求解。

## 9.2 组网层（Network Assembly Layer）

职责：

- 从物理对象构建求解需要的网络表示
- 形成导纳/电导矩阵或等价结构
- 建立线路到节点、变压器到节点映射
- 记录哪些设备被纳入/剔除

这是“结构化准备层”。

## 9.3 求解层（Solver Layer）

职责：

- 根据线路投影场输入计算感应量
- 形成注入项
- 解线性系统
- 计算设备级 GIC 相关输出

这层只做求解，不做数据存储逻辑，不做模型逻辑。

## 9.4 输出层（Postprocess Layer）

职责：

- 把求解结果转成标准 `GICSolution`
- 生成 line-level / transformer-level / node-level 输出
- 保存 manifest
- 写 sanity check 摘要

---

## 10. 物理计算最小路径要求

Phase 2 必须先打通一条最小可运行物理路径。

## 10.1 最小路径定义

最低要求是：

1. 读取一个 `GridCase`
2. 转换成 `PhysicsGridCase`
3. 输入一个均匀 `ElectricFieldSnapshot`
4. 计算线路等效输入
5. 建立 DC network
6. 求解节点/设备结果
7. 输出 `GICSolution`

### 10.1.1 这条最小路径的意义

它是整个物理层的“dry run + baseline solver”  
后续所有扩展都必须建立在这条路径已经稳定的前提下。

---

## 11. 线路输入建模要求

## 11.1 必须实现的最低能力

至少实现线路在给定电场下的感应输入计算框架。

最低需支持：

- 线路长度
- 线路方向或等价几何信息
- 电场沿线路方向的投影
- 形成等效线路输入量

## 11.2 对字段缺失的处理要求

如果线路长度或方向缺失，不允许直接继续假装正常求解。  
必须选择以下策略之一，并明确记录：

- 明确报错
- 标记该线路不参与 GIC 求解
- 使用显式的简化假设补全
- 使用外部映射表补全

### 11.2.1 必须记录 assumptions

任何字段补全或简化都必须写入：

- 解决方案 metadata
- 场景说明
- manifest

---

## 12. 网络求解要求

## 12.1 求解目标

从线路输入与网络参数出发，得到：

- 节点级等效量
- 变压器级 GIC 输出
- 其他可导出辅助量

## 12.2 最低实现要求

至少需要：

- 建立线性系统
- 能求解单时刻结果
- 能处理合理的稀疏或中等规模测试系统
- 出现不可解或病态情况时能给出清晰报错

## 12.3 稳定性要求

必须考虑：

- 数值稳定性检查
- 矩阵维度检查
- 设备映射一致性检查
- 输入异常时报错机制

## 12.4 物理简化要求

允许在本阶段使用简化，但必须满足：

- 简化路径清楚
- 简化不与总体路线冲突
- 简化可在未来扩展替换
- 简化的适用范围有文档说明

---

## 13. 结果输出层级要求

Phase 2 不能只输出一个单一数值数组。  
必须至少支持以下三层输出。

## 13.1 Line-level 输出

用途：

- 作为线路感应驱动诊断信息
- 作为后续图模型边特征候选
- 作为 sanity check 依据

最低字段建议：

- `line_id`
- `projected_field`
- `induced_quantity`
- `included_in_solver`
- `notes`

## 13.2 Bus/node-level 输出

用途：

- 作为网络内部状态的辅助结果
- 作为后续图模型节点级 baseline 特征

最低字段建议：

- `bus_id`
- `solved_quantity`
- `connected_components_info`
- `quality_flag`

## 13.3 Transformer-level 输出

用途：

- 作为本项目最重要的标签层之一
- 作为热点与风险分析的核心输出

最低字段建议：

- `transformer_id`
- `gic_value`
- `associated_bus_ids`
- `voltage_level`
- `quality_flag`
- `included_in_risk_output`

---

## 14. 时序与批量样本生成要求

Phase 2 不应停留在单时刻 solver。  
必须进一步支持批量标签生成。

## 14.1 时序输入支持要求

至少支持：

- 一段 `ElectricFieldSeries`
- 多时刻连续求解
- 输出按时间索引组织的结果

## 14.2 场景配置要求

必须定义 `ScenarioConfig`，至少支持以下维度：

- 场强幅值
- 场方向
- 场时间长度
- 使用的测试系统
- 参数扰动开关
- 稀疏观测配置
- 噪声配置（仅 metadata，可不实际注入）
- 输出标签层级

## 14.3 样本批量生成要求

必须支持：

- 给定一组 scenario 配置，批量生成标签
- 为每个样本生成唯一 sample_id
- 写入 manifest
- 保持结果可回溯到源 case 与源场景

---

## 15. 场景生成器设计要求

这是后续训练数据多样性的来源。  
但本阶段只做物理标签生成，不做复杂数据增强。

## 15.1 最低需要支持的场景类型

### 15.1.1 Uniform Field Scenario
用途：

- 最基础 solver 验证
- 最容易做 sanity check

### 15.1.2 Multi-Direction Field Sweep
用途：

- 分析方向敏感性
- 形成更丰富的训练样本

### 15.1.3 Multi-Amplitude Sweep
用途：

- 分析响应非线性/尺度变化
- 检查 solver 输出稳定性

### 15.1.4 Time-Series Scenario
用途：

- 构造连续时间样本
- 为 Phase 3 / Phase 5 预留接口

### 15.1.5 Parameter Perturbation Scenario
用途：

- 模拟接地参数、线路参数不确定性
- 增强样本多样性

## 15.2 场景元数据要求

每个场景必须记录：

- `scenario_id`
- 场景类型
- 基础 case
- 输入场参数
- 使用的 assumptions
- 参数扰动说明
- 输出位置

---

## 16. 标签导出要求

Phase 2 的产出必须真正可被后续模型训练复用。

## 16.1 标签导出层级

至少应导出：

- `physics_ready/`
- `datasets/`
- `manifests/`

## 16.2 标签格式要求

建议导出为结构清晰、易读、易版本化的格式，例如：

- JSON
- CSV
- Parquet（若环境允许）
- NumPy / tensor 存储（作为附加层）

但不能只保留在内存或 notebook 中。

## 16.3 每个标签集必须带 manifest

manifest 至少记录：

- 样本数量
- 时间长度
- case 来源
- 场景类型
- solver 版本
- schema 版本
- assumptions
- 生成时间
- 路径

---

## 17. Phase 2 的 CLI 要求

在复用 Phase 0 / Phase 1 CLI 结构的基础上，建议增加最小物理相关命令。

至少应支持：

- `physics-build-case`
- `physics-solve-snapshot`
- `physics-solve-series`
- `physics-generate-scenarios`
- `physics-export-labels`
- `physics-validate-solution`

### 17.1 命令要求

- 每个命令都必须使用统一配置系统
- 不允许把 case 路径硬编码在脚本里
- 错误提示必须说明是：
  - 字段缺失
  - 网络不可构建
  - 数值求解失败
  - 输出写入失败
  - manifest 缺失

---

## 18. 配置文件要求

Phase 2 必须新增专用配置文件，例如：

```text
configs/phase2/
  phase2_dev.yaml
  scenarios/
    uniform_field.yaml
    sweep_field.yaml
    timeseries_field.yaml
```

## 18.1 配置域建议

至少包括：

```yaml
stage:
  current: phase2

physics:
  solver:
    mode: dc_baseline
    fail_on_missing_required_fields: true
    allow_assumption_fill: false

  field:
    default_units: V_per_km
    representation: uniform_xy

  outputs:
    export_line_level: true
    export_bus_level: true
    export_transformer_level: true
    write_manifest: true

scenario:
  type: uniform_field
  case_id: ieee118
  amplitude: 1.0
  direction_deg: 0.0

export:
  physics_ready_root: data/processed/physics_ready
```

---

## 19. 文档要求

Phase 2 必须新增一组物理层文档，避免后续模型阶段遗忘 assumptions。

至少新增：

- `docs/models/physics_solver_overview.md`
- `docs/data/physics_label_schema.md`
- `docs/decisions/0002_phase2_solver_assumptions.md`

## 19.1 `physics_solver_overview.md` 应包含

- solver 分层结构
- 当前物理简化
- 输入输出说明
- 适用范围
- 已知局限

## 19.2 `physics_label_schema.md` 应包含

- line-level / bus-level / transformer-level 标签字段
- manifest 字段
- sample_id / scenario_id 规则

## 19.3 决策记录应包含

至少记录：

- 为什么先做简化 baseline solver
- 哪些字段允许缺失
- 哪些字段缺失时必须报错
- 为什么采用当前标签组织方式

---

## 20. 推荐文件级实现清单

以下是 Phase 2 推荐实现的文件级清单。Codex 应以此为主要目标。

```text
configs/
  phase2/
    phase2_dev.yaml
    scenarios/
      uniform_field.yaml
      sweep_field.yaml
      timeseries_field.yaml

docs/
  models/
    physics_solver_overview.md
  data/
    physics_label_schema.md
  decisions/
    0002_phase2_solver_assumptions.md

src/
  gic/
    physics/
      __init__.py
      schema.py
      builder.py
      field.py
      projections.py
      solver.py
      postprocess.py
      scenarios.py
      export.py
      validation.py
    data/
      converters/
        grid_to_physics.py

tests/
  test_physics_schema.py
  test_physics_builder.py
  test_field_projection.py
  test_solver_snapshot.py
  test_scenario_generation.py
```

说明：

- 不要求一开始就把每个文件写得很复杂
- 但物理层边界必须清楚
- `solver.py`、`field.py`、`postprocess.py`、`scenarios.py` 是本阶段最核心文件

---

## 21. Codex 在本阶段的实现顺序要求

Codex 必须按以下顺序推进，不允许直接跳到大批量生成或复杂实验。

### Step 1：建立物理层 schema 与 `GridCase -> PhysicsGridCase` 转换

先实现：

- `PhysicsGridCase`
- `ElectricFieldSnapshot`
- `GICSolution`
- 基础转换器

### Step 2：实现最小 uniform field solver 路径

先打通：

- 单 case
- 单 snapshot
- 单次求解
- 单次输出

### Step 3：实现 line/bus/transformer 三层结果输出

确保：

- 结果可读
- 字段明确
- metadata 完整

### Step 4：实现 series 求解与 scenario 配置

支持：

- 时间序列输入
- 多场景配置
- batch 生成

### Step 5：实现标签导出与 manifest

确保：

- 标签可落盘
- 可被后续读取
- 样本可追踪

### Step 6：实现 validation / sanity check / 报告

至少覆盖：

- 输入字段检查
- 求解结果检查
- 场景输出摘要

### Step 7：补齐文档与测试

完成：

- 物理层文档
- 决策记录
- 核心测试

---

## 22. Phase 2 的验收标准

只有满足以下条件，Phase 2 才算完成。

### 22.1 物理层对象完成

- `PhysicsGridCase`
- `ElectricFieldSnapshot`
- `GICSolution`
- `ScenarioConfig`

至少都已定义并可用。

### 22.2 最小 solver 路径完成

- 能读取一个标准测试系统
- 能输入一个 uniform field snapshot
- 能输出求解结果
- 能写出三层标签

### 22.3 批量标签生成能力完成

- 能基于场景配置批量生成样本
- 每个样本有唯一 id
- 有 manifest

### 22.4 输出与导出能力完成

- line-level
- bus-level
- transformer-level

三层结果均可导出并带 metadata。

### 22.5 验证与 sanity check 完成

- 能检测明显输入问题
- 能给出 solver 失败原因
- 能输出最基础质量报告

### 22.6 文档完成

- solver 概述文档存在
- label schema 文档存在
- assumptions 决策记录存在

---

## 23. 最低可接受标准（Minimum Acceptable Outcome）

如果时间有限，Phase 2 至少必须达到以下底线：

1. 可以把一个 `GridCase` 转为 `PhysicsGridCase`
2. 可以对一个 uniform field snapshot 完成单次求解
3. 可以输出 transformer-level 结果
4. 可以导出至少一个标签文件和一个 manifest
5. 可以跑最基础的求解测试

如果连这个底线都达不到，则 Phase 2 不能结束。

---

## 24. 风险与回退策略

## 24.1 风险：测试系统缺少关键 GIC 字段

### 对策

- 显式记录缺失
- 用 `assumptions` 字段追踪补全
- 对关键字段区分“可补全”和“不可补全”

## 24.2 风险：求解公式或实现细节有歧义

### 对策

- 保持 solver 模块化
- 把公式来源与简化记录到文档
- 先保证最小一致性，再逐步细化

## 24.3 风险：数值不稳定或求解失败

### 对策

- 加矩阵与输入检查
- 在 validation 中输出清晰错误信息
- 不要静默 fallback 到无意义结果

## 24.4 风险：标签组织方式过早绑定后续模型

### 对策

- 导出保持物理语义
- 不为某个模型专门 reshape 成训练格式
- graph-ready 格式延后到 Phase 4

## 24.5 风险：场景生成过度复杂

### 对策

- 只做有限几类场景
- 先 uniform，再 sweep，再 series
- 不做庞大随机参数空间搜索

---

## 25. 明确禁止事项

Codex 在本阶段**禁止**做以下事情：

1. 不得实现 GNN、Temporal GNN、Hetero-GNN
2. 不得实现训练脚本和损失函数体系
3. 不得为了下游模型方便而破坏物理标签含义
4. 不得在字段缺失时无记录地自动补值
5. 不得把复杂物理逻辑写进 notebook 而不进入正式模块
6. 不得把 solver 和导出逻辑混成一个巨大脚本
7. 不得跳过 manifest 与 assumptions 记录
8. 不得把求解失败样本伪装成成功输出
9. 不得把场景生成器写成不可复现的随机黑盒
10. 不得省略测试与基础 sanity check

---

## 26. 建议提交粒度

建议本阶段按以下粒度逐步提交，方便回溯。

### Commit 1
建立 `physics/` 模块骨架与 schema

### Commit 2
实现 `GridCase -> PhysicsGridCase` 转换器

### Commit 3
实现 uniform field 单时刻 solver

### Commit 4
实现 line/bus/transformer 输出层

### Commit 5
实现 series 求解与 scenario 配置

### Commit 6
实现标签导出与 manifest

### Commit 7
补齐 validation、测试与文档

---

## 27. 本阶段完成后的交接要求

Phase 2 完成后，应额外输出一份交接摘要，说明：

- 当前 solver 支持哪些输入模式
- 当前 solver 做了哪些物理简化
- 哪些字段必须具备才能求解
- 哪些字段可以通过 assumption 补全
- 当前可导出的标签层级有哪些
- 后续 Phase 3 / 4 / 5 将如何消费这些结果
- 当前 solver 的已知局限是什么

建议存放于：

- `reports/phase2_summary.md`
  或
- `docs/phases/phase2_completion_note.md`

---

## 28. Phase 3 / Phase 4 的前置接口要求

为了让后续阶段顺利开始，Phase 2 完成后至少应保证以下接口稳定：

### 28.1 给 Phase 3 的接口
- 标准化时序场输入接口
- series 求解输出接口
- 基础时间索引一致性

### 28.2 给 Phase 4 的接口
- transformer-level 标签导出接口
- line-level / bus-level baseline 输出
- manifest 与 sample_id 查询接口

### 28.3 给 Phase 5 的接口
- 物理 baseline 结果接口
- assumptions / quality flag 接口
- scenario metadata 接口

如果这些接口不稳定，则不应进入后续主模型阶段。

---

## 29. 最终执行指令（给 Codex 的摘要版）

下面这段可直接作为对 Codex 的高层执行约束摘要：

> 你正在执行 GIC 项目的 Phase 2。你的目标是建立一个简化但可信、模块化且可扩展的 GIC 物理仿真与标签生成框架。你必须先打通从标准 `GridCase` 到 `PhysicsGridCase`，再到 uniform field 单时刻 solver，最后到时序场景与批量标签导出的最小路径。你必须保持物理层语义清晰，显式记录 assumptions、缺失字段和 solver 状态。你不得提前实现学习模型，不得为了后续模型便利而扭曲物理标签定义，不得在字段缺失时静默补值，不得省略 manifest、validation 和文档。

---

## 30. 结论

Phase 2 是整个项目里“从数据层进入物理层”的关键阶段。  
它的核心价值不在于实现最复杂的物理系统，而在于：

- 为后续学习模型建立可信标签来源；
- 为后续 physics-informed 方法提供 baseline；
- 让整个项目不沦为纯黑箱重建。

如果 Phase 2 做得好，后续 Phase 4 / Phase 5 将能够围绕一个清楚、稳定、可解释的物理基线来设计。  
如果 Phase 2 做得差，后续模型阶段就会不断被标签定义不清、场景不可追踪和 assumptions 不透明的问题拖住。

Phase 2 完成并验收后，下一步应开始：

- `phase_3_detailed_plan.md`
