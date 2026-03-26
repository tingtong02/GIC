# Phase 6 Detailed Plan  
## 知识图谱（KG）建模与图学习增强（Detailed Execution Plan v1）

## 1. 文档元信息

- 文档名称：`phase_6_detailed_plan.md`
- 阶段名称：Phase 6 — 知识图谱（KG）建模与图学习增强
- 版本：v1
- 文档角色：**直接执行计划**
- 执行对象：Codex / 开发者
- 上位参考文档：
  - `GIC_project_planning_and_technical_route_v1.md`
  - `GIC_project_phase_roadmap_v1.md`
  - `phase_0_detailed_plan.md`
  - `phase_1_detailed_plan.md`
  - `phase_2_detailed_plan.md`
  - `phase_3_detailed_plan.md`
  - `phase_4_detailed_plan.md`
  - `phase_5_detailed_plan.md`

本文件用于约束 Phase 6 的开发行为。  
在 Phase 6 中，核心任务是把知识图谱从“文档里的目标”落实为**正式的数据与模型增强层**，使其在设备关系组织、规则表达、缺失信息管理和模型可解释性方面发挥明确作用，并通过可量化实验验证 KG 是否真正带来增益。

---

## 2. 本阶段的核心目标

Phase 6 的唯一核心目标是：

> 建立与 GIC 网络级重建任务相匹配的知识图谱 schema、构建管线和融合机制，并证明 KG 能在至少一个明确场景下提升模型表现、数据组织能力或结果可解释性。

这意味着本阶段必须解决的问题包括：

- KG 中到底有哪些实体与关系
- KG 从哪些数据层构建
- KG 如何与电网图、物理层和时序层共存
- KG 进入主模型时，是当作特征增强、关系增强还是规则约束
- KG 是否真能解决缺失属性、异构数据对齐和解释性问题
- 如何避免把 KG 做成与主模型脱节的独立项目

---

## 3. 非目标（本阶段明确不做的事情）

为了防止 Phase 6 范围失控，本阶段明确**不做**以下内容：

### 3.1 不重写主模型主干

本阶段不推翻 Phase 5 的主模型。  
KG 必须作为增强层进入，而不是重新发明一个全新模型体系。

### 3.2 不做大型图数据库平台工程

本阶段不实现：

- 企业级知识图谱服务
- 在线图数据库集群
- 复杂查询平台
- 大规模权限和图服务架构

本阶段目标是研究型、工程可控的 KG 层。

### 3.3 不追求百科全书式 KG

本阶段不应把所有可能实体、规则和领域知识都纳入 KG。  
必须围绕项目主目标，仅纳入对 GIC 重建与解释真正有帮助的知识。

### 3.4 不把 KG 当作替代物理与图学习的核心预测器

KG 不能替代：

- Phase 2 的物理标签来源
- Phase 4 的图学习基础
- Phase 5 的主模型主干

KG 应是增强层，而不是替代层。

### 3.5 不做脱离任务的知识嵌入实验

本阶段不允许为了“做 KG”而单独做一堆与主任务无关的 embedding 实验。  
任何 KG 设计都必须回答：它对主项目有什么具体作用。

---

## 4. 本阶段完成后应具备的能力

Phase 6 完成后，项目至少应具备以下能力：

1. 能构建与项目数据结构匹配的 KG schema；
2. 能从现有数据与元数据中抽取实体与关系；
3. 能把 KG 与主模型通过至少一种方式稳定融合；
4. 能在缺失属性、异构关系或解释性场景下使用 KG；
5. 能通过对比实验证明 KG 的价值边界；
6. 能为最终系统交付提供一层语义组织与可解释支撑；
7. 能清楚说明“KG 带来了什么，不带来什么”。

---

## 5. 本阶段总体策略

Phase 6 必须采用“**先把 KG 做小做实，再做融合与验证**”的策略。

建议推进顺序如下：

1. 先固定 KG 的目标范围
2. 再定义最小实体-关系 schema
3. 再从现有数据层抽取实体与关系
4. 再建立 KG 存储与导出格式
5. 再实现与主模型的最小融合路径
6. 再做 KG 增益实验
7. 最后形成默认 KG 增强方案与边界说明

不要一开始就做一个过大的 KG，然后再寻找用途。

---

## 6. 本阶段必须依赖的输入

## 6.1 上位文档与阶段文档

必须参考：

- `GIC_project_planning_and_technical_route_v1.md`
- `GIC_project_phase_roadmap_v1.md`
- `phase_0_detailed_plan.md`
- `phase_1_detailed_plan.md`
- `phase_2_detailed_plan.md`
- `phase_3_detailed_plan.md`
- `phase_4_detailed_plan.md`
- `phase_5_detailed_plan.md`

## 6.2 前置阶段提供的关键输入

必须复用：

- Phase 1 的数据 registry、schema 和 source metadata
- Phase 2 的物理对象、assumptions、quality flags、scenario metadata
- Phase 3 的 signal-ready 特征 metadata
- Phase 4 的 graph-ready schema 与图对象
- Phase 5 的主模型输入 bundle、默认配置和输出结果

## 6.3 本阶段允许抽取的知识来源

至少包括以下几类：

1. 电网拓扑与设备关系
2. 设备属性与参数层次
3. 传感器与设备的观测关系
4. 地理区域与站点归属关系
5. storm event 与样本关系
6. assumptions / quality / missingness 信息
7. 工程规则与约束性知识

---

## 7. 本阶段输出

Phase 6 的输出应是**可被主模型和最终系统共同消费的 KG 增强资产**。

至少包括：

- KG schema
- 实体与关系抽取管线
- KG 数据文件或序列化结果
- KG-to-model 融合模块
- KG 驱动的对比实验结果
- KG 查询/解释示例
- 默认 KG 增强配置
- 阶段性收益与边界报告

---

## 8. KG 的角色定位要求

本阶段必须先回答一个问题：KG 在本项目中到底扮演什么角色。  
必须至少明确以下四种角色中的哪些被启用。

## 8.1 角色 A：异构数据组织层

作用：

- 统一设备、线路、传感器、站点、事件、区域等对象
- 管理不同数据层之间的关系映射
- 使项目对“实体是谁、怎么关联”的表达更清晰

这是 KG 最基础、最稳妥的作用。

## 8.2 角色 B：模型增强层

作用：

- 为主模型提供关系增强特征
- 提供 relation embedding
- 提供额外边类型或语义权重

这是 KG 进入预测模型的主要路径之一。

## 8.3 角色 C：规则与约束表达层

作用：

- 表达设备层级关系
- 表达观测有效性规则
- 表达区域归属和物理适用范围
- 表达 assumptions 与缺失属性补全规则

这是 KG 区别于普通 metadata 的关键部分。

## 8.4 角色 D：解释与查询层

作用：

- 支持结果解释
- 支持回答“为什么该设备被判为高风险”
- 支持定位输入缺失、规则冲突和关系来源

## 8.5 本阶段建议角色组合

建议至少启用：

- 角色 A：异构数据组织层
- 角色 B：模型增强层
- 角色 D：解释与查询层

角色 C 可以以轻量规则层方式实现，不必一开始做复杂推理引擎。

---

## 9. KG schema 设计要求

KG schema 必须小而明确，不允许无限膨胀。

## 9.1 最低实体集合要求

至少定义以下实体类型：

1. `Grid`
2. `Region`
3. `Substation`
4. `Bus`
5. `Transformer`
6. `TransmissionLine`
7. `Sensor`
8. `MagnetometerStation`
9. `StormEvent`
10. `Scenario`
11. `Observation`
12. `RiskState`（可选）
13. `AssumptionRecord`（可选但推荐）

## 9.2 最低关系集合要求

至少定义以下关系类型：

- `connected_to`
- `located_in`
- `belongs_to`
- `contains`
- `observes`
- `influenced_by`
- `has_sensor`
- `has_voltage_level`
- `mapped_to`
- `generated_from`
- `associated_with_event`
- `derived_under_scenario`
- `constrained_by`
- `has_quality_flag`

## 9.3 实体字段设计要求

每个实体至少应具有：

- `entity_id`
- `entity_type`
- `name`（如适用）
- `source`
- `attributes`
- `version`
- `status`

## 9.4 关系字段设计要求

每条关系至少应具有：

- `relation_id`
- `head_entity_id`
- `relation_type`
- `tail_entity_id`
- `source`
- `confidence`（可选）
- `attributes`
- `version`

---

## 10. KG 构建范围约束

本阶段必须明确 KG 的范围，避免无限扩展。

## 10.1 必须纳入 KG 的关系

至少纳入以下四类关系：

### 10.1.1 电网结构关系
例如：

- bus 与 line 的连接关系
- transformer 与 bus/substation 的从属关系

### 10.1.2 观测关系
例如：

- sensor 观测哪个设备
- station 对哪个区域或样本有影响

### 10.1.3 场景关系
例如：

- sample 属于哪个 scenario
- scenario 属于哪个 storm event

### 10.1.4 质量与假设关系
例如：

- 某字段缺失
- 某参数由 assumption 补全
- 某样本存在质量风险

## 10.2 可选纳入 KG 的关系

可选纳入：

- 区域邻接关系
- 设备类别层级
- 电压等级层级
- 规则模板关系

## 10.3 本阶段不必纳入的内容

不要求：

- 完整外部领域本体
- 所有文献中的知识条目
- 所有自然语言规则
- 大规模知识推理链

---

## 11. KG 构建管线要求

KG 不能手工散乱拼装。  
必须建立正式构建管线。

## 11.1 最低需要的构建步骤

至少包括：

1. 实体抽取
2. 关系抽取
3. id 规范化
4. 属性挂载
5. 冲突检查
6. 序列化导出
7. manifest 生成

## 11.2 实体抽取来源要求

实体至少可从以下来源抽取：

- Phase 1 的标准数据对象
- Phase 2 的物理对象与 scenario
- Phase 3 的前端结果 metadata
- Phase 4/5 的 graph/sample/model metadata

## 11.3 关系抽取来源要求

关系至少可从以下来源抽取：

- 拓扑连接
- 所属关系
- 观测映射
- 时间/场景归属
- assumptions / quality flags

## 11.4 id 统一要求

必须建立：

- `entity_id` 统一命名规则
- `relation_id` 统一命名规则
- 与现有 `bus_id`、`line_id`、`sample_id`、`scenario_id` 的映射规则

禁止不同层使用冲突 id 而不记录映射。

---

## 12. KG 数据格式与存储要求

本阶段不要求复杂图数据库，但必须有稳定存储格式。

## 12.1 最低存储形式

至少支持以下一种或多种：

- JSON / JSONL
- CSV triples
- Parquet（可选）
- NetworkX / in-memory graph 序列化（作为辅助）

## 12.2 必须导出的内容

至少导出：

- entities
- relations
- KG manifest
- schema version
- source provenance

## 12.3 存储目录建议

建议导出到：

```text
data/processed/kg/
```

并包含：

```text
data/processed/kg/
├── entities/
├── relations/
├── manifests/
└── exports/
```

---

## 13. KG 与主模型的融合方式要求

这是本阶段最关键的验证点之一。  
KG 不能只构建出来，而必须进入模型或结果解释流程。

## 13.1 至少支持以下一种最小融合路径

### 路径 A：KG 派生特征增强
方式：

- 从 KG 中导出设备层级、区域关系、观测关系等特征
- 挂载到 graph-ready 或 model input bundle 中

优点：

- 最稳定
- 最易与 Phase 5 可比
- 实现门槛最低

### 路径 B：KG 派生关系增强
方式：

- 根据 KG 关系生成额外边、边类型或关系 embedding
- 进入主模型图结构

优点：

- 更直接利用语义关系
- 但复杂度更高

### 路径 C：KG 驱动规则增强
方式：

- 基于 KG 规则对输入、缺失属性或质量标记做约束
- 影响训练或后处理

优点：

- 更适合解释与治理
- 可以不直接改变主干网络

## 13.2 本阶段建议融合路径

建议最小主路径为：

- **路径 A：KG 派生特征增强**
- 路径 C 作为辅助解释与规则检查层
- 路径 B 作为扩展实验，不要求第一时间成为默认方案

## 13.3 融合约束

- KG 增强必须可开关
- 必须能做“无 KG / 有 KG”公平比较
- 不得把 KG 信息偷偷混进 baseline 特征而不记录
- 所有 KG 派生特征必须能追踪来源关系

---

## 14. KG 派生特征要求

如果走路径 A，本阶段必须明确哪些特征来自 KG。

## 14.1 建议优先派生的特征类型

至少考虑以下类型：

1. 节点类型与设备层级编码
2. 所属区域编码
3. 观测覆盖关系特征
4. 场景/事件上下文特征
5. 缺失字段与 assumption 标记
6. 质量与可靠性标记
7. 邻近关键设备统计量（如可定义）

## 14.2 特征约束

- 特征必须稳定可重复生成
- 特征不能依赖测试标签本身
- 特征必须写入 schema 与 manifest
- 特征必须可做独立 ablation

---

## 15. KG 驱动的规则与解释要求

即便默认主路径是特征增强，也必须让 KG 在解释层有实际作用。

## 15.1 规则层最低要求

至少支持以下一类轻量规则：

- 某设备/样本是否使用了 assumption
- 某设备是否缺少关键参数
- 某观测是否由间接映射而来
- 某高风险输出是否与区域或观测稀疏性有关

## 15.2 解释层最低要求

至少支持回答类似问题：

- 某高风险设备属于哪个区域、哪个变电站
- 该设备有哪些直接观测或相邻设备关系
- 该样本用了哪些 assumptions
- 该结果依赖哪些 KG 派生特征

## 15.3 本阶段不要求的解释能力

不要求：

- 完整自然语言问答系统
- 图数据库可视化平台
- 复杂推理解释引擎

---

## 16. KG 增益评估要求

KG 阶段不能只说“图谱建好了”。  
必须证明它的价值。

## 16.1 必做对比

至少比较：

1. Phase 5 默认主模型（无 KG）
2. + KG 派生特征
3. + KG 规则/解释辅助（如实现）

## 16.2 应重点观察的场景

至少重点分析以下一种或多种：

- 属性缺失较多的样本
- 观测稀疏率高的场景
- 需要跨层级关系理解的设备
- explanation / traceability 要求高的案例

## 16.3 评估维度

至少包括：

- 主任务数值指标变化
- 热点识别变化
- 特定困难样本的改善
- 缺失属性场景鲁棒性
- 可解释性与可追踪性提升

## 16.4 结果要求

必须输出：

- 哪些场景下 KG 有帮助
- 哪些场景下帮助有限
- KG 带来的复杂度成本
- 是否推荐纳入默认主流程

---

## 17. 默认 KG 增强方案要求

本阶段结束时，不能只给“KG 做过了”。  
必须明确是否存在默认推荐方案。

## 17.1 默认方案至少应明确以下内容

- 启用哪些实体/关系
- 哪些 KG 派生特征进入模型
- 是否启用规则层
- 是否启用关系增强
- 默认适用的数据版本
- 默认适用的主模型版本

## 17.2 推荐输出形式

建议最终给出：

- `kg_default.yaml`
- 一份 KG 增强说明文档
- 一份相对于无 KG 主模型的收益摘要

---

## 18. Phase 6 的 CLI 要求

在复用既有 CLI 结构的基础上，建议增加 KG 相关命令。

至少应支持：

- `kg-build-schema`
- `kg-build-graph`
- `kg-export-features`
- `kg-run-ablation`
- `kg-build-report`
- `kg-query-sample`（轻量查询即可）

### 18.1 命令要求

- 使用统一配置系统
- 必须能指定输入数据版本和主模型版本
- 错误信息必须区分：
  - schema 缺失
  - entity/relation 构建失败
  - id 映射冲突
  - KG 导出失败
  - KG 特征与主模型输入不匹配

---

## 19. 配置文件要求

Phase 6 必须新增专用配置文件，例如：

```text
configs/phase6/
  phase6_dev.yaml
  kg/
    schema_default.yaml
    kg_default.yaml
    feature_only.yaml
    rules_only.yaml
  ablations/
    kg_ablation.yaml
```

## 19.1 配置域建议

至少包括：

```yaml
stage:
  current: phase6

kg:
  enabled: true
  schema_version: v1
  use_feature_enhancement: true
  use_relation_enhancement: false
  use_rule_layer: true

  entities:
    - grid
    - region
    - substation
    - bus
    - transformer
    - line
    - sensor
    - station
    - event
    - scenario

  relations:
    - connected_to
    - located_in
    - observes
    - influenced_by
    - derived_under_scenario
    - has_quality_flag

fusion:
  inject_into_main_model: true
  export_kg_features: true

evaluation:
  compare_with_phase5_default: true
  export_queries: true
```

---

## 20. 文档要求

Phase 6 必须新增一组 KG 文档，明确记录 KG 范围、作用和边界。

至少新增：

- `docs/models/kg_overview.md`
- `docs/data/kg_schema.md`
- `docs/decisions/0006_phase6_kg_design.md`

## 20.1 `kg_overview.md` 应包含

- KG 的角色定位
- KG 与主模型的关系
- 默认 KG 增强路径
- KG 的收益与边界
- 为什么 KG 在本项目中不是可选噱头，而是目标组成部分之一

## 20.2 `kg_schema.md` 应包含

- 实体类型
- 关系类型
- 实体字段
- 关系字段
- 导出格式
- id 规则

## 20.3 决策记录应包含

至少记录：

- 为什么 KG 采用当前最小 schema
- 为什么先做 feature-level 融合
- 为什么规则层做轻量实现
- 为什么不把 KG 做成独立预测器

---

## 21. 推荐文件级实现清单

以下是 Phase 6 推荐实现的文件级清单。Codex 应以此为主要目标。

```text
configs/
  phase6/
    phase6_dev.yaml
    kg/
      schema_default.yaml
      kg_default.yaml
      feature_only.yaml
      rules_only.yaml
    ablations/
      kg_ablation.yaml

docs/
  models/
    kg_overview.md
  data/
    kg_schema.md
  decisions/
    0006_phase6_kg_design.md

src/
  gic/
    kg/
      __init__.py
      schema.py
      builder.py
      extractors.py
      relations.py
      export.py
      features.py
      rules.py
      query.py
      validation.py
    models/
      fusion/
        kg_fusion.py
    eval/
      kg_reports.py
      kg_case_studies.py

tests/
  test_kg_schema.py
  test_kg_builder.py
  test_kg_export.py
  test_kg_feature_derivation.py
  test_kg_rules.py
  test_kg_fusion.py
```

说明：

- 不要求一开始做复杂图推理
- 但 `schema.py`、`builder.py`、`features.py`、`rules.py` 和 `kg_fusion.py` 是本阶段关键文件

---

## 22. Codex 在本阶段的实现顺序要求

Codex 必须按以下顺序推进，不允许先写融合逻辑再补 KG 基础。

### Step 1：固定 KG schema 与 id 规则

先实现：

- 实体类型
- 关系类型
- 实体/关系 schema
- id 命名规则

### Step 2：实现实体与关系构建管线

先打通：

- 从已有数据层抽取实体
- 从已有映射和 metadata 构建关系
- 导出 KG

### Step 3：实现 KG 派生特征

确保：

- 可从 KG 稳定导出特征
- 可写回主模型输入 bundle
- 可追踪来源

### Step 4：实现轻量规则与查询层

先做：

- assumption / quality / missingness 相关规则
- 简单查询接口

### Step 5：实现 KG 融合与 ablation

至少覆盖：

- 无 KG
- + KG 特征
- + 规则辅助（如启用）

### Step 6：实现报告、案例导出与默认 KG 配置

至少输出：

- KG 增益报告
- KG 查询示例
- 默认 KG 方案

### Step 7：补齐文档与测试

完成：

- KG 文档
- 决策记录
- 核心测试

---

## 23. Phase 6 的验收标准

只有满足以下条件，Phase 6 才算完成。

### 23.1 KG 基础完成

- 有明确 schema
- 有实体与关系导出
- 有 manifest 与版本记录

### 23.2 KG 管线完成

- 能从现有数据层构建 KG
- 能稳定导出 KG 文件
- 能处理 id 映射与冲突检查

### 23.3 KG 融合完成

- 至少有一种进入主模型的融合方式
- 推荐最少完成特征增强路径
- KG 增强可配置开关

### 23.4 KG 增益评估完成

- 与无 KG 主模型有明确比较
- 至少一个场景下能说明 KG 是否有帮助
- 能说明成本与收益

### 23.5 文档完成

- KG 概述文档存在
- KG schema 文档存在
- 决策记录存在

---

## 24. 最低可接受标准（Minimum Acceptable Outcome）

如果时间有限，Phase 6 至少必须达到以下底线：

1. 有一个最小 KG schema
2. 能构建并导出实体与关系
3. 能从 KG 派生特征
4. 能做“无 KG / 有 KG 特征”对比
5. 有一份默认 KG 配置
6. 有一份清楚说明 KG 价值边界的报告

如果连这个底线都达不到，则 Phase 6 不能结束。

---

## 25. 风险与回退策略

## 25.1 风险：KG 规模膨胀、收益有限

### 对策

- 严格限制实体/关系集合
- 先围绕主任务选关系
- 如果收益不明显，也要如实记录，保持 KG 作为可选增强而非强制默认

## 25.2 风险：KG 与主模型接口混乱

### 对策

- 先做 feature-level 融合
- 所有 KG 派生特征进入显式 schema
- 不在模型内部隐式查 KG

## 25.3 风险：id 对齐复杂导致错误传播

### 对策

- 建立统一 id 规范
- 增加 validation 与冲突检查
- 所有映射必须有 manifest

## 25.4 风险：规则层过于复杂

### 对策

- 只做轻量规则
- 优先服务于 assumptions、quality、missingness
- 复杂推理延后

## 25.5 风险：做成“看起来很学术，但无实际帮助”的 KG

### 对策

- 强制要求 ablation
- 强制要求困难样本分析
- 强制要求解释与追踪示例

---

## 26. 明确禁止事项

Codex 在本阶段**禁止**做以下事情：

1. 不得推翻 Phase 5 主模型主干
2. 不得把 KG 做成独立且脱离主任务的子项目
3. 不得无限扩展实体与关系范围
4. 不得在没有 schema 的情况下手工散乱拼接 triples
5. 不得把 KG 特征偷偷混入主模型而不记录
6. 不得跳过“无 KG / 有 KG”公平比较
7. 不得省略 id 映射规则与 validation
8. 不得把规则层做成不可解释的黑盒
9. 不得只报告“KG 建好了”，不报告实际作用
10. 不得省略文档、测试和阶段报告

---

## 27. 建议提交粒度

建议本阶段按以下粒度逐步提交，方便回溯。

### Commit 1
建立 KG schema、id 规则与配置骨架

### Commit 2
实现实体/关系抽取与导出

### Commit 3
实现 KG 特征派生

### Commit 4
实现轻量规则与查询接口

### Commit 5
实现 KG 融合与 ablation

### Commit 6
实现 KG 报告、案例导出与默认配置

### Commit 7
补齐文档、测试与阶段总结

---

## 28. 本阶段完成后的交接要求

Phase 6 完成后，应额外输出一份交接摘要，说明：

- 当前 KG 包含哪些实体与关系
- 当前默认 KG 增强路径是什么
- 哪些场景下 KG 有明显帮助
- 哪些场景下 KG 增益有限
- 当前规则层支持什么
- 最终系统中 KG 应如何展示和使用
- 当前 KG 模块的已知局限是什么

建议存放于：

- `reports/phase6_summary.md`
  或
- `docs/phases/phase6_completion_note.md`

---

## 29. Phase 7 的前置接口要求

为了让后续阶段顺利开始，Phase 6 完成后至少应保证以下接口稳定：

- KG schema 与版本接口
- KG feature export 接口
- KG rule/query 接口
- 与主模型输入 bundle 的融合接口
- 无 KG / 有 KG 结果对比接口

如果这些接口不稳定，则不应进入 Phase 7。

---

## 30. 最终执行指令（给 Codex 的摘要版）

下面这段可直接作为对 Codex 的高层执行约束摘要：

> 你正在执行 GIC 项目的 Phase 6。你的目标是把知识图谱落实为正式的数据组织与模型增强层，而不是做一个独立的学术附加模块。你必须先定义最小 KG schema 和统一 id 规则，再从现有数据、物理、前端、图和主模型 metadata 中抽取实体与关系，随后实现 KG 派生特征、轻量规则与查询接口，并通过“无 KG / 有 KG”公平对比验证其价值。你不得推翻 Phase 5 主模型，不得无限扩展 KG 范围，不得在没有 schema 和 validation 的情况下随意拼接 triples，不得只报告 KG 构建而不报告实际收益。

---

## 31. 结论

Phase 6 的核心不是“项目里终于有了 KG”，而是：

- 让 KG 真正进入主项目主线；
- 让异构数据、关系语义、规则与解释性有统一归宿；
- 证明 KG 是正式目标组成部分，而不是附属噱头。

如果 Phase 6 做得好，项目将具备明显优于“只有物理+GNN”的结构表达和解释能力；  
如果 Phase 6 做得差，KG 会变成一层昂贵但边缘化的附加组件。

Phase 6 完成并验收后，下一步应开始：

- `phase_7_detailed_plan.md`
