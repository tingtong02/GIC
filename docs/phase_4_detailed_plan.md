# Phase 4 Detailed Plan  
## 图结构建模与基础 GNN 重建基线（Detailed Execution Plan v1）

## 1. 文档元信息

- 文档名称：`phase_4_detailed_plan.md`
- 阶段名称：Phase 4 — 图结构建模与基础 GNN 重建基线
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

本文件用于约束 Phase 4 的开发行为。  
在 Phase 4 中，核心任务是建立**标准图对象、图数据集构造流程和基础 GNN 重建基线**，用于验证“利用电网拓扑与局域关系进行网络级 GIC 重建”这条路线本身是否成立。

---

## 2. 本阶段的核心目标

Phase 4 的唯一核心目标是：

> 在不引入复杂 physics-informed 训练机制和 KG 语义增强的前提下，先建立一条干净、可复现、可比较的基础图学习重建链路，验证图结构是否明显优于非图结构 baseline。

这意味着本阶段必须解决的问题包括：

- 电网与观测如何转成图
- 图里的节点、边、特征和标签如何定义
- 如何构造适合训练/验证/测试的 graph-ready 数据
- 如何定义基础重建任务
- 哪些 baseline 必须存在
- 如何比较 non-graph 与 graph 方法
- 如何让后续 Phase 5 在此基础上继续，而不是推倒重来

---

## 3. 非目标（本阶段明确不做的事情）

为了防止 Phase 4 范围失控，本阶段明确**不做**以下内容：

### 3.1 不实现完整 physics-informed 主模型

本阶段不实现：

- 物理一致性损失主体系
- residual learning on solver outputs 的完整训练版
- physics-guided message passing
- 多物理量联合约束训练

这些属于 Phase 5。

### 3.2 不实现 KG 融合

本阶段不实现：

- KG schema 进入模型
- relation-aware graph learning
- 知识约束嵌入
- 语义实体图与电网图的融合

这些属于 Phase 6。

### 3.3 不把前端与模型端到端联训

本阶段可以读取 Phase 3 的 signal-ready 结果，但不实现：

- 前端和 GNN 联合训练
- 可学习信号前端模块
- end-to-end waveform-to-graph training

### 3.4 不追求最终主模型效果

本阶段的目标是“建立可信 baseline”，而不是：

- 打磨最终最强精度
- 做全部复杂 ablation
- 覆盖所有任务头
- 追求论文最终指标

### 3.5 不把图对象设计得过于复杂

本阶段可以预留异构图扩展接口，但不要求一开始就实现：

- full hetero-graph
- temporal graph transformer
- relation-specific attention
- large-scale distributed graph training

---

## 4. 本阶段完成后应具备的能力

Phase 4 完成后，项目至少应具备以下能力：

1. 能把标准化数据与物理标签转成 graph-ready 数据；
2. 能构建用于 GIC 重建的图对象；
3. 能在相同任务定义下训练 non-graph baseline 与 graph baseline；
4. 能输出网络级重建结果；
5. 能比较图模型与非图模型的差异；
6. 能为 Phase 5 提供稳定的图结构、数据集与训练脚手架；
7. 能明确指出哪些改进空间属于 physics-informed 阶段，而不是继续在 Phase 4 内堆复杂度。

---

## 5. 本阶段总体策略

Phase 4 必须采用“**先定义图对象与数据任务，再建立 baseline，再做最小 ablation**”的策略。

建议推进顺序如下：

1. 先固定图 schema 与 graph-ready 数据格式
2. 再固定训练任务定义与数据切分规则
3. 再实现 non-graph baseline
4. 再实现基础 graph baseline
5. 再建立训练/验证/评估流程
6. 再做最小必要 ablation
7. 最后形成阶段报告与默认 baseline

不要一开始就实现复杂的图网络变体，而没有清楚的任务定义。

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

## 6.2 前置阶段提供的关键接口

必须复用：

- Phase 1 的标准化 `GridCase`、时序与 manifest
- Phase 2 的物理标签、baseline 输出、scenario metadata
- Phase 3 的 signal-ready 特征与 quasi-DC 输出

## 6.3 本阶段允许消费的输入层级

至少支持以下输入组合：

1. 仅物理标签 + 基础拓扑
2. 基础拓扑 + 稀疏观测 mask
3. 拓扑 + Phase 3 signal-ready 特征
4. 拓扑 + Phase 2 baseline 结果
5. 上述组合的不同版本

---

## 7. 本阶段输出

Phase 4 的输出应是**可被后续主模型阶段直接继承的图学习基线资产**。

至少包括：

- graph-ready 数据格式
- 图对象构造器
- baseline 数据集类
- non-graph baseline 训练结果
- graph baseline 训练结果
- 重建结果导出
- baseline 比较报告
- 默认图基线建议

---

## 8. 图对象设计要求

这是本阶段最关键的设计之一。  
必须先定义清楚“图长什么样”，再写模型。

## 8.1 最低需要定义的图对象

至少应定义：

1. `GraphSample`
2. `GraphBatch`
3. `NodeRecord`
4. `EdgeRecord`
5. `GraphFeatureBundle`
6. `GraphLabelBundle`
7. `GraphManifest`
8. `ReconstructionTaskConfig`

## 8.2 `GraphSample` 最低字段建议

- `graph_id`
- `sample_id`
- `scenario_id`
- `time_index`（可选）
- `node_records`
- `edge_records`
- `feature_bundle`
- `label_bundle`
- `mask_bundle`
- `metadata`

## 8.3 节点类型建议

本阶段最小实现可以从单类型节点开始，但必须预留扩展能力。  
建议最小节点单位优先从以下二选一中固定：

### 方案 A：Bus 为主节点
优点：

- 与电网拓扑天然一致
- 图结构清晰
- 更容易对接线路连接关系

### 方案 B：Transformer 为主节点
优点：

- 与最终 GIC 风险输出更直接
- 标签更贴近任务目标

### 建议

本阶段优先采用：

- **Bus 为主节点**
- Transformer 标签通过附加映射或节点属性输出

理由：

- 更适合作为“基础图拓扑验证”的第一步
- 与后续异构图扩展更兼容

## 8.4 边类型建议

本阶段最小实现应至少支持：

- electrical connectivity edges

可选支持但不强制：

- sensor linkage edges
- geographic adjacency edges
- transformer association edges

本阶段不要求 full hetero edge system，但必须在 schema 中预留 `edge_type` 字段。

## 8.5 特征分类要求

节点特征至少可分为：

1. 静态拓扑与设备属性
2. 观测值或观测 mask
3. 前端 signal-ready 特征
4. 物理 baseline 特征
5. 质量或缺失标记

---

## 9. 图任务定义要求

本阶段不能在没有清楚任务定义的情况下写模型。  
必须先固定“我们到底在学什么”。

## 9.1 最低任务定义

本阶段至少应支持以下基础任务：

### 9.1.1 节点级重建任务
输入：

- 稀疏观测 + 图拓扑 + 可选额外特征

输出：

- 每个目标节点的 GIC 相关值或中间代理量

### 9.1.2 变压器级重建任务
输入：

- 图结构 + 节点特征 + 映射关系

输出：

- transformer-level GIC 标签

### 9.1.3 网络级态势图输出任务
输入：

- 单图或图序列

输出：

- 一次性网络级 GIC reconstruction map

## 9.2 本阶段建议主任务

建议把本阶段主任务固定为：

> **在给定稀疏观测与拓扑条件下，重建节点级或映射后的 transformer-level GIC 数值。**

原因：

- 易于比较 baseline
- 便于衡量 graph 是否有效
- 可为后续 Phase 5 的多任务扩展留空间

## 9.3 标签来源要求

标签必须明确来自：

- Phase 2 的物理求解结果
- 标准 manifest 可追踪的样本

禁止使用来源不清的手工标签。

---

## 10. Graph-ready 数据构造要求

Phase 4 必须建立正式的数据构造层，不能靠训练脚本临时拼装。

## 10.1 构造目标

输入：

- `GridCase` / `PhysicsGridCase`
- signal-ready 特征
- 物理标签
- 稀疏观测配置

输出：

- 标准 `GraphSample`

## 10.2 必须支持的构造能力

至少支持：

- 图节点索引构建
- 边索引构建
- 节点特征拼接
- 标签映射
- 观测 mask 注入
- train/val/test split 信息保留

## 10.3 稀疏观测机制要求

必须能够显式控制稀疏率，例如：

- 30%
- 50%
- 70%
- 90%

并且明确区分：

- 作为输入可见的观测节点
- 作为目标需要重建的节点
- 完全未使用的节点（如有）

禁止在训练脚本中隐式随机稀疏化却不记录。

---

## 11. baseline 模型范围要求

Phase 4 的核心是 baseline，不是最终方法。  
必须有最小而完整的 baseline 体系。

## 11.1 non-graph baseline 必须存在

至少实现以下一个或多个：

- mean / interpolation baseline（如适用）
- MLP baseline
- simple regression baseline

目的：

- 防止后续“图模型看起来有效”，但其实任何方法都能做到

## 11.2 graph baseline 必须存在

至少实现以下一个或多个：

- GCN baseline
- GraphSAGE baseline
- GAT baseline

### 建议

本阶段建议最少实现：

- 一个 non-graph baseline
- GCN
- GraphSAGE
- GAT

这样后续有明确比较梯度。

## 11.3 不要求的模型

本阶段不要求：

- Graph Transformer
- Hetero-GNN
- relation-aware message passing
- temporal graph architecture
- physics-informed hybrid architecture

这些属于 Phase 5 或更后。

---

## 12. 模型输入输出接口要求

## 12.1 统一模型输入接口

不管哪种 baseline，训练脚本都应消费统一数据对象，例如：

- `GraphSample`
- `GraphBatch`
- `GraphFeatureBundle`
- `GraphLabelBundle`

## 12.2 统一输出接口

每个模型至少应输出：

- `prediction`
- `target`
- `mask`
- `metadata`

以便统一评估。

## 12.3 禁止事项

禁止：

- 每个模型单独定义一套数据读取逻辑
- 某个模型只能读自己私有格式
- 训练时临时拼接字段而不回写 graph-ready 层

---

## 13. 训练与评估脚手架要求

本阶段必须建立基础训练与评估流程，但不追求过度复杂。

## 13.1 训练脚手架最低要求

至少应支持：

- 数据集加载
- 模型初始化
- train/val/test 循环
- checkpoint 保存
- 指标记录
- 配置快照保存

## 13.2 评估脚手架最低要求

至少应支持：

- MAE / RMSE
- correlation
- 稀疏率分组结果
- 样本级输出导出
- 网络级重建可视化导出（静态版即可）

## 13.3 结果保存要求

必须保存：

- 配置
- checkpoint
- 训练曲线
- 测试指标
- 预测与标签样例
- 最基本误差分析

---

## 14. 最小 ablation 要求

本阶段不能只报告一个模型结果。  
至少应完成最小 ablation。

## 14.1 必做对比

至少比较：

1. non-graph baseline vs graph baseline
2. 不同稀疏率
3. 是否使用 signal-ready 特征
4. 是否使用物理 baseline 特征

## 14.2 可选对比

可选但不强制：

- 不同节点定义
- 不同边定义
- 不同邻域深度
- 不同 feature bundle 组合

## 14.3 本阶段不必做的对比

不要求：

- 大规模 hyperparameter search
- 所有模型变体 exhaustive ablation
- 复杂多任务头比较
- 复杂时空模型比较

---

## 15. graph-ready 导出要求

本阶段必须把图数据正式导出，而不是让训练脚本动态临时创建。

## 15.1 导出目标

必须能够导出到标准位置，例如：

```text
data/processed/graph_ready/
```

## 15.2 导出内容

至少包括：

- 图结构
- 节点特征
- 边特征（如有）
- 标签
- mask
- manifest
- split 信息

## 15.3 导出要求

- 必须可回溯到原始 sample_id / scenario_id
- 必须可区分不同稀疏率版本
- 必须可被多个 baseline 复用
- 不得只存在于训练缓存中

---

## 16. Phase 4 的 CLI 要求

在复用既有 CLI 结构的基础上，建议增加最小图学习相关命令。

至少应支持：

- `graph-build-samples`
- `graph-export-dataset`
- `train-baseline`
- `eval-baseline`
- `graph-build-report`

### 16.1 命令要求

- 统一使用配置系统
- 必须能指定数据集、稀疏率和模型类型
- 错误信息必须区分：
  - graph-ready 数据缺失
  - 特征不匹配
  - 标签缺失
  - 模型初始化失败
  - checkpoint 缺失

---

## 17. 配置文件要求

Phase 4 必须新增专用配置文件，例如：

```text
configs/phase4/
  phase4_dev.yaml
  datasets/
    graph_dataset_default.yaml
  models/
    mlp_baseline.yaml
    gcn_baseline.yaml
    graphsage_baseline.yaml
    gat_baseline.yaml
  eval/
    baseline_eval.yaml
```

## 17.1 配置域建议

至少包括：

```yaml
stage:
  current: phase4

graph:
  node_type: bus
  include_edge_features: false
  include_signal_features: true
  include_physics_baseline: true
  sparsity_rate: 0.7

task:
  target_level: transformer
  objective: regression

training:
  batch_size: 16
  epochs: 50
  lr: 1e-3
  seed: 42

baseline:
  active_models:
    - mlp
    - gcn
    - graphsage
    - gat

evaluation:
  export_predictions: true
  export_reconstruction_maps: true
```

---

## 18. 文档要求

Phase 4 必须新增一组图学习基线文档，清楚记录图对象设计与 baseline 范围。

至少新增：

- `docs/models/graph_baseline_overview.md`
- `docs/data/graph_ready_schema.md`
- `docs/decisions/0004_phase4_graph_design.md`

## 18.1 `graph_baseline_overview.md` 应包含

- 图任务定义
- 节点与边设计
- baseline 模型集合
- 为什么当前阶段不做 physics-informed / KG
- 默认 baseline 方案
- 已知局限

## 18.2 `graph_ready_schema.md` 应包含

- `GraphSample` 字段
- `GraphFeatureBundle` 字段
- `GraphLabelBundle` 字段
- 稀疏 mask 字段
- manifest 说明

## 18.3 决策记录应包含

至少记录：

- 为什么 bus 作为主节点
- 为什么必须先做 non-graph baseline
- 为什么选择当前 graph baseline 集合
- 为什么 graph-ready 数据必须独立导出

---

## 19. 推荐文件级实现清单

以下是 Phase 4 推荐实现的文件级清单。Codex 应以此为主要目标。

```text
configs/
  phase4/
    phase4_dev.yaml
    datasets/
      graph_dataset_default.yaml
    models/
      mlp_baseline.yaml
      gcn_baseline.yaml
      graphsage_baseline.yaml
      gat_baseline.yaml
    eval/
      baseline_eval.yaml

docs/
  models/
    graph_baseline_overview.md
  data/
    graph_ready_schema.md
  decisions/
    0004_phase4_graph_design.md

src/
  gic/
    graph/
      __init__.py
      schema.py
      builder.py
      features.py
      labels.py
      masks.py
      export.py
      datasets.py
      validation.py
    models/
      __init__.py
      base.py
      mlp_baseline.py
      gcn_baseline.py
      graphsage_baseline.py
      gat_baseline.py
    eval/
      metrics.py
      reconstruction.py
      reporting.py
    training/
      __init__.py
      loops.py
      checkpoint.py

tests/
  test_graph_schema.py
  test_graph_builder.py
  test_graph_export.py
  test_mlp_baseline.py
  test_gcn_baseline.py
  test_training_loop.py
```

说明：

- 不要求一开始把所有模型做得非常复杂
- 但 graph schema、builder、dataset、baseline 训练链路必须优先写对
- `builder.py`、`datasets.py`、`mlp_baseline.py`、`gcn_baseline.py` 和 `loops.py` 是本阶段关键文件

---

## 20. Codex 在本阶段的实现顺序要求

Codex 必须按以下顺序推进，不允许先写多个模型再补图构造层。

### Step 1：建立 graph schema 与 graph-ready builder

先实现：

- `GraphSample`
- `NodeRecord`
- `EdgeRecord`
- `GraphFeatureBundle`
- `GraphLabelBundle`

### Step 2：实现 graph-ready 构造、导出与 dataset 类

确保：

- 可从 Phase 1/2/3 输入生成标准图样本
- 可导出
- 可被训练脚本稳定读取

### Step 3：实现 non-graph baseline

先做一个简单的 MLP 或等价 baseline，作为最低对照组。

### Step 4：实现基础 graph baseline

至少先打通：

- GCN

然后再补：

- GraphSAGE
- GAT

### Step 5：实现训练/评估脚手架

支持：

- train/val/test
- checkpoint
- 指标记录
- 预测导出

### Step 6：实现最小 ablation 与报告

至少输出：

- non-graph vs graph
- 不同稀疏率
- 有无 signal / physics features

### Step 7：补齐文档与测试

完成：

- graph 文档
- 决策记录
- 核心测试

---

## 21. Phase 4 的验收标准

只有满足以下条件，Phase 4 才算完成。

### 21.1 graph-ready 数据层完成

- 可从前置阶段数据构建图样本
- 图样本可导出与重载
- 稀疏 mask 明确

### 21.2 baseline 体系完成

- 至少一个 non-graph baseline
- 至少一个 graph baseline
- 建议完成 GCN + GraphSAGE + GAT

### 21.3 训练/评估链路完成

- train/val/test 可运行
- 指标可导出
- 预测可导出

### 21.4 最小对比完成

- non-graph vs graph
- 不同稀疏率
- 有无 signal-ready / physics baseline 特征

### 21.5 文档完成

- graph baseline 概述文档存在
- graph-ready schema 文档存在
- 决策记录存在

---

## 22. 最低可接受标准（Minimum Acceptable Outcome）

如果时间有限，Phase 4 至少必须达到以下底线：

1. 有 graph-ready schema
2. 能构建并导出图样本
3. 有一个 non-graph baseline
4. 有一个 graph baseline（至少 GCN）
5. 能完成一次训练与评估
6. 能输出最基本的对比结果

如果连这个底线都达不到，则 Phase 4 不能结束。

---

## 23. 风险与回退策略

## 23.1 风险：图对象设计不合理

### 对策

- 优先保持简单、清晰、可解释
- 先固定单主节点方案
- 复杂异构图留到 Phase 5 / 6

## 23.2 风险：graph baseline 没有优于 non-graph baseline

### 对策

- 先检查 graph builder 与标签映射是否正确
- 检查特征输入与 mask 是否合理
- 若结果仍不显著，也要如实记录，作为后续 Phase 5 的动力，而不是强行复杂化 Phase 4

## 23.3 风险：graph-ready 数据与训练脚手架耦合过紧

### 对策

- graph-ready 数据单独导出
- dataset 类只读取标准格式
- 不让训练脚本承担图构造职责

## 23.4 风险：模型数量多但比较不公平

### 对策

- 保持统一 split、统一损失、统一指标
- 所有 baseline 从同一 graph-ready 数据读取
- 记录配置快照

## 23.5 风险：过早进入复杂图模型

### 对策

- 严格限制在 baseline 范围
- 不在 Phase 4 引入 physics-informed / hetero / temporal 复杂度
- 为 Phase 5 预留扩展点而不是提前实现

---

## 24. 明确禁止事项

Codex 在本阶段**禁止**做以下事情：

1. 不得实现 physics-informed 主模型
2. 不得实现 KG 融合
3. 不得把前端与 GNN 联合训练
4. 不得跳过 non-graph baseline
5. 不得训练脚本内动态临时构图而不导出 graph-ready 数据
6. 不得不同 baseline 使用不同数据定义
7. 不得省略稀疏率与 mask 的显式记录
8. 不得把复杂 temporal/hetero 结构提前塞入本阶段
9. 不得只给最终指标，不保留预测与误差输出
10. 不得省略文档、测试与最小对比报告

---

## 25. 建议提交粒度

建议本阶段按以下粒度逐步提交，方便回溯。

### Commit 1
建立 `graph/` schema、builder 与 export 骨架

### Commit 2
实现 graph-ready dataset 与 mask 机制

### Commit 3
实现 non-graph baseline（MLP 或等价）

### Commit 4
实现 GCN baseline

### Commit 5
实现 GraphSAGE / GAT baseline

### Commit 6
实现训练评估脚手架与对比输出

### Commit 7
补齐文档、测试与阶段报告

---

## 26. 本阶段完成后的交接要求

Phase 4 完成后，应额外输出一份交接摘要，说明：

- 当前图对象是如何定义的
- 当前默认节点与边设计是什么
- 当前 baseline 集合有哪些
- 当前 graph 是否相对 non-graph 有增益
- 当前 signal / physics features 的增益情况
- Phase 5 应如何在此基础上加入 physics-informed 机制
- 当前 graph baseline 的已知局限是什么

建议存放于：

- `reports/phase4_summary.md`
  或
- `docs/phases/phase4_completion_note.md`

---

## 27. Phase 5 的前置接口要求

为了让后续阶段顺利开始，Phase 4 完成后至少应保证以下接口稳定：

- graph-ready schema
- graph dataset 读取接口
- baseline 训练脚手架
- 统一评估接口
- signal / physics feature bundle 接口
- sample_id / scenario_id / graph_id 映射关系

如果这些接口不稳定，则不应进入 Phase 5。

---

## 28. 最终执行指令（给 Codex 的摘要版）

下面这段可直接作为对 Codex 的高层执行约束摘要：

> 你正在执行 GIC 项目的 Phase 4。你的目标是把标准化数据、物理标签和前端特征转成 graph-ready 数据，并建立一套可复现的基础 GNN 重建基线。你必须先定义图对象、构造器和数据集，再实现 non-graph baseline 与基础 graph baseline，最后建立训练、评估与最小 ablation。你不得提前实现 physics-informed 主模型，不得引入 KG 融合，不得绕开 graph-ready 层在训练脚本中临时构图，不得跳过 non-graph baseline。

---

## 29. 结论

Phase 4 的本质不是“开始上 GNN”，而是：

- 验证图结构这条路线本身是否值得继续深化；
- 建立后续 physics-informed 主模型可继承的图数据与训练骨架；
- 把“图是否有用”与“复杂物理约束是否有用”分成两个独立问题。

如果 Phase 4 做得好，后续 Phase 5 就可以围绕一个稳定的 graph-ready 数据层和 baseline 训练框架来增加物理约束。  
如果 Phase 4 做得差，后续 Phase 5 很容易把所有增益都混杂在一起，无法清楚判断哪些改进真正来自 physics-informed 设计。

Phase 4 完成并验收后，下一步应开始：

- `phase_5_detailed_plan.md`
