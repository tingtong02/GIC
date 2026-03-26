# Phase 5 Detailed Plan  
## Physics-informed 时空 GNN 主模型（Detailed Execution Plan v1）

## 1. 文档元信息

- 文档名称：`phase_5_detailed_plan.md`
- 阶段名称：Phase 5 — Physics-informed 时空 GNN 主模型
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

本文件用于约束 Phase 5 的开发行为。  
在 Phase 5 中，核心任务是把 Phase 2 的物理基线、Phase 3 的时序前端、Phase 4 的图学习基线整合起来，构建项目的**主方法**：一个可训练、可解释、可复现的 physics-informed temporal GNN，用于网络级 GIC 态势重建与风险感知。

---

## 2. 本阶段的核心目标

Phase 5 的唯一核心目标是：

> 在保持 Phase 4 基线可比性的前提下，引入物理基线、物理一致性约束、时序建模与多任务输出，构建项目的主模型，并证明该主模型在关键场景下相对于 Phase 4 基线具有稳定且可解释的增益。

这意味着本阶段必须解决的问题包括：

- 物理基线以什么形式进入模型
- 时序结构如何进入图模型
- 模型学习的是“全量映射”还是“物理残差修正”
- 需要哪些损失项，哪些物理约束适合做成 penalty
- 输出只做数值回归，还是同时做热点识别和风险排序
- 如何保证与 Phase 4 的公平比较
- 如何让后续 KG 阶段是“增强”，而不是修补本阶段设计缺陷

---

## 3. 非目标（本阶段明确不做的事情）

为了防止 Phase 5 范围失控，本阶段明确**不做**以下内容：

### 3.1 不实现 KG 融合主逻辑

本阶段不实现：

- KG schema 进入模型
- relation-aware attention with KG
- 语义规则图与电网图融合
- 知识补全驱动的消息传递

这些属于 Phase 6。

### 3.2 不做大规模真实系统部署

本阶段不实现：

- 在线推断服务
- 实时监控系统
- 长期任务调度系统
- 交互式运维平台

这些属于后续系统整合阶段。

### 3.3 不做无边界的模型结构探索

本阶段不追求：

- 穷举所有 GNN 变体
- 穷举所有时序建模方法
- 穷举所有损失组合
- 大规模 hyperparameter search

本阶段必须围绕“主方法”收敛，而不是发散。

### 3.4 不抛弃 Phase 4 的可比性

本阶段不能：

- 重新定义任务，使 Phase 4 基线失去可比性
- 更换数据切分从而使比较失真
- 只报告对主方法有利的指标
- 用不同数据版本比较不同模型

### 3.5 不以复杂度替代解释性

本阶段不应把模型堆得过于庞大，以至于无法回答：

- 物理信息到底有没有帮助
- 时序模块到底有没有帮助
- 哪个输出头真正有价值
- 模型失败时是哪里出了问题

---

## 4. 本阶段完成后应具备的能力

Phase 5 完成后，项目至少应具备以下能力：

1. 能在统一 graph-ready / signal-ready / physics-ready 数据基础上训练主模型；
2. 能把物理 baseline 与图学习主干稳定结合；
3. 能在时间维度上处理连续输入；
4. 能输出至少一个主回归结果和一个辅助风险输出；
5. 能以统一评估体系比较 Phase 4 baseline 与 Phase 5 主模型；
6. 能给出物理信息、时序信息和多任务设计各自的增益分析；
7. 能为 Phase 6 的 KG 增强提供干净主干。

---

## 5. 本阶段总体策略

Phase 5 必须采用“**在 Phase 4 图基线之上逐层增加约束与时序能力**”的策略。

建议推进顺序如下：

1. 先固定主任务与主模型输入输出边界
2. 再固定物理信息进入方式
3. 再固定时序建模方式
4. 再加入多任务输出头
5. 再加入物理一致性损失
6. 再做模块化 ablation
7. 最后形成默认主模型配置与阶段报告

不要一开始就把所有增强点同时堆进去，否则无法区分增益来源。

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

## 6.2 Phase 2 提供的物理输入

必须可消费：

- transformer-level / node-level / line-level 物理标签
- 物理 baseline 输出
- scenario metadata
- assumptions / quality flags
- 时序物理结果（如有）

## 6.3 Phase 3 提供的前端输入

必须可消费：

- quasi-DC series
- signal-ready features
- 前端质量指标
- 时间索引对齐信息

## 6.4 Phase 4 提供的图学习基础

必须复用：

- graph-ready schema
- baseline 训练/评估脚手架
- 稀疏观测机制
- 统一指标体系
- sample_id / scenario_id / graph_id 映射关系

---

## 7. 本阶段输出

Phase 5 的输出应是**项目的主模型资产**。

至少包括：

- physics-informed 主模型定义
- temporal 图学习模块
- 多任务输出头
- 物理一致性损失模块
- 完整训练与评估脚本
- 模块化 ablation 结果
- 默认主模型配置
- 主实验报告

---

## 8. 主模型任务定义要求

Phase 5 不能只说“做一个更强模型”。  
必须明确主任务与辅助任务。

## 8.1 主任务（必须存在）

建议固定为：

> 在给定电网拓扑、稀疏观测、signal-ready 特征与物理 baseline 的条件下，重建 transformer-level 或映射后的 node-level GIC 数值。

这应是本阶段的核心回归任务。

## 8.2 辅助任务（建议至少一个）

建议从以下任务中至少选择一个：

### 8.2.1 热点识别任务
输出：

- hotspot probability 或高风险标签

作用：

- 提高对关键设备的感知能力
- 避免模型只优化平均误差

### 8.2.2 风险排序任务
输出：

- risk score / ranking score

作用：

- 贴近工程价值
- 支持 Top-k 风险设备评估

### 8.2.3 不确定性输出任务
输出：

- uncertainty estimate / confidence score

作用：

- 提升工程可解释性
- 帮助识别模型不可靠场景

## 8.3 本阶段建议任务组合

建议最小组合为：

- 主任务：GIC 数值回归
- 辅助任务：热点识别

风险排序与不确定性输出可以作为扩展，但至少预留接口。

---

## 9. 主模型输入设计要求

本阶段必须把模型输入设计清楚，避免输入过载或含义混乱。

## 9.1 输入组成建议

至少分成四类输入：

1. 图结构输入
2. 静态设备与拓扑特征
3. 时变观测与前端特征
4. 物理 baseline 与相关质量标记

## 9.2 静态特征建议

至少可包含：

- 电压等级
- 线路/设备拓扑属性
- grounding 相关属性（若可用）
- 节点度数或图结构统计量
- 缺失字段标记

## 9.3 时变特征建议

至少可包含：

- 稀疏观测值
- observation mask
- quasi-DC feature
- 窗口统计特征
- 时间位置编码（若需要）

## 9.4 物理特征建议

至少可包含：

- Phase 2 物理 baseline 输出
- line/bus/transformer 辅助基线量
- 物理求解状态标记
- assumptions / quality flags

## 9.5 输入约束

必须满足：

- 所有输入字段可追踪来源
- 训练与测试使用同一输入定义
- 不允许临时拼接未经文档定义的字段
- 必须可做“有/无某类输入”的 ablation

---

## 10. 物理信息进入模型的方式要求

这是本阶段最关键的设计点之一。  
必须明确“physics-informed”到底体现在哪里。

## 10.1 至少支持以下一种主路径

### 路径 A：物理 baseline 作为输入特征
优点：

- 最稳定
- 最容易与 Phase 4 可比
- 工程实现简单

### 路径 B：残差学习（Residual Correction）
模型学习：

- `prediction = physics_baseline + learned_residual`

优点：

- 更贴合“物理+数据驱动”的逻辑
- 容易解释模型在学什么

### 路径 C：物理一致性 penalty
在损失中引入：

- 与物理输出偏离惩罚
- 局部平滑/一致性惩罚
- 可行性约束

优点：

- 提升物理合理性
- 可控制模型偏离物理先验的程度

## 10.2 本阶段建议主路径

建议最小主路径为：

- **路径 A + 路径 B**
- 路径 C 作为可控附加项

也就是：

1. 先把物理 baseline 作为特征输入
2. 再用 residual formulation 做主回归
3. 再逐步加入 penalty ablation

## 10.3 物理约束设计原则

- 约束必须可配置开关
- 约束权重必须明确进入配置
- 不允许把约束写死在模型里
- 必须能做“无约束 / 有约束”公平比较

---

## 11. 时序建模要求

Phase 5 必须显式处理时间维度，但不能一开始就做最复杂时空模型。

## 11.1 最低时序能力要求

至少支持：

- 滑动窗口输入
- 连续多个时间步特征编码
- 输出对应当前时刻或窗口末端目标

## 11.2 可选时序路径

可以从以下几类中选择一条主线：

### 方案 A：TCN + GNN
优点：

- 结构相对清晰
- 易于与图模块分开实现

### 方案 B：RNN/GRU + GNN
优点：

- 适合较短窗口序列
- 实现成熟

### 方案 C：时序图消息传递
优点：

- 更自然
- 但复杂度更高

### 建议

本阶段建议优先采用：

- **TCN/GRU + Graph Backbone 的分层结构**

理由：

- 容易与 Phase 4 基线衔接
- 便于做时序模块增益分析
- 避免过早进入复杂 temporal graph transformer

## 11.3 时间索引要求

必须明确记录：

- 窗口长度
- stride
- 预测目标时刻
- 是否使用历史窗口统计特征
- 是否使用未来信息（通常禁止）

---

## 12. 主模型结构分层要求

本阶段必须采用模块化主模型设计，避免形成无法拆解分析的巨型网络。

## 12.1 推荐主结构

建议至少分为以下模块：

1. `InputEncoder`
2. `TemporalEncoder`
3. `GraphBackbone`
4. `PhysicsFusion`
5. `TaskHeads`
6. `LossComposer`

## 12.2 各模块职责

### 12.2.1 `InputEncoder`
职责：

- 静态/动态/物理特征对齐与编码

### 12.2.2 `TemporalEncoder`
职责：

- 处理时间窗口内的时序依赖

### 12.2.3 `GraphBackbone`
职责：

- 利用图拓扑进行空间消息传递

### 12.2.4 `PhysicsFusion`
职责：

- 将物理 baseline 作为特征、残差基线或约束信号注入

### 12.2.5 `TaskHeads`
职责：

- 回归头
- 分类头
- 可选风险或不确定性头

### 12.2.6 `LossComposer`
职责：

- 组合回归损失、分类损失、physics penalty 等

---

## 13. 多任务输出头要求

Phase 5 不应只做单一数值输出。  
但多任务必须有边界，不能无限膨胀。

## 13.1 必须实现的输出头

至少实现：

- `RegressionHead`：输出 GIC 数值预测

## 13.2 建议实现的辅助输出头

至少实现以下之一：

- `HotspotHead`
- `RiskScoreHead`
- `UncertaintyHead`

### 建议

最小建议为：

- `RegressionHead`
- `HotspotHead`

## 13.3 输出头约束

- 每个输出头的标签来源必须清晰
- 每个输出头都必须可关闭
- 多任务损失权重必须进入配置
- 不允许在没有足够标签定义时强行加头

---

## 14. 损失函数设计要求

本阶段必须有明确、可拆解的损失系统。

## 14.1 最低损失组成

至少支持：

1. 回归损失
2. 辅助任务损失（若启用）
3. 物理一致性 penalty（可选）

## 14.2 回归损失建议

至少支持：

- MAE
- MSE / RMSE 对应损失

### 建议

回归主损失优先：

- MAE 或 Huber 风格

原因：

- 对异常值更稳健
- 更贴近设备级误差控制

## 14.3 热点任务损失建议

至少支持：

- BCE
- focal-style loss（可选）

## 14.4 物理 penalty 建议

至少支持一种简单形式，例如：

- 对预测与 physics baseline 偏离的惩罚
- 对空间不连续的过大偏差惩罚
- 对不可信设备结果的约束

## 14.5 损失系统要求

- 所有损失项权重必须可配置
- 所有损失项必须可单独开关
- 必须能输出各损失项分量
- 必须能做损失 ablation

---

## 15. 训练与实验设计要求

Phase 5 必须在 Phase 4 脚手架上升级，而不是另起炉灶。

## 15.1 训练脚手架要求

至少支持：

- 主模型初始化
- 多输入模态
- 多输出头
- checkpoint
- mixed logging
- 配置快照
- best model 选择

## 15.2 评估脚手架要求

至少支持：

- 回归指标
- 热点识别指标
- Top-k 风险设备指标（若启用风险头）
- 稀疏率分组评估
- 场景类型分组评估
- 跨事件或跨 case 分组评估（若数据可用）

## 15.3 结果保存要求

必须保存：

- 训练曲线
- 分任务损失曲线
- baseline 对比表
- 样本级预测导出
- 关键场景重建图
- 错误案例分析

---

## 16. 必做 ablation 要求

Phase 5 的价值必须通过清楚的 ablation 体现。  
至少应完成以下比较。

## 16.1 baseline vs 主模型

必须比较：

- Phase 4 最佳 graph baseline
- Phase 5 主模型

## 16.2 物理信息增益

至少比较：

- 无物理特征
- 物理特征输入
- residual learning
- + physics penalty（如实现）

## 16.3 时序模块增益

至少比较：

- 无时序编码
- 有时序编码

## 16.4 辅助任务增益

至少比较：

- 仅回归
- 回归 + hotspot

## 16.5 输入模态增益

至少比较：

- 仅拓扑 + 稀疏观测
- + signal-ready
- + physics baseline
- + 两者同时

---

## 17. 默认主模型推荐要求

本阶段结束时，不能只留下一堆实验。  
必须明确给出“默认主模型”。

## 17.1 默认主模型至少应明确以下内容

- 主干图网络类型
- 时序编码方式
- 物理信息进入方式
- 是否使用 residual formulation
- 启用哪些输出头
- 默认损失组合
- 默认适用数据版本

## 17.2 推荐形式

建议最终给出：

- `main_model_default.yaml`
- 一份对应的模型说明文档
- 一份相对于 Phase 4 最佳 baseline 的增益摘要

---

## 18. Phase 5 的 CLI 要求

在复用既有 CLI 结构的基础上，建议增加主模型相关命令。

至少应支持：

- `train-main-model`
- `eval-main-model`
- `run-ablation`
- `export-main-predictions`
- `build-main-report`

### 18.1 命令要求

- 使用统一配置系统
- 必须可指定 physics/signal/task head 开关
- 必须能加载 Phase 4 graph-ready 数据
- 错误信息必须区分：
  - graph-ready 缺失
  - physics baseline 缺失
  - signal-ready 缺失
  - 时间窗口配置错误
  - checkpoint 加载失败

---

## 19. 配置文件要求

Phase 5 必须新增专用配置文件，例如：

```text
configs/phase5/
  phase5_dev.yaml
  models/
    main_model_default.yaml
    no_physics.yaml
    no_temporal.yaml
    regression_only.yaml
  losses/
    default_loss.yaml
  ablations/
    main_ablation.yaml
```

## 19.1 配置域建议

至少包括：

```yaml
stage:
  current: phase5

model:
  graph_backbone: graphsage
  temporal_encoder: gru
  physics_fusion: residual
  use_signal_features: true
  use_physics_features: true

tasks:
  regression: true
  hotspot: true
  risk_score: false
  uncertainty: false

loss:
  regression_weight: 1.0
  hotspot_weight: 0.5
  physics_penalty_weight: 0.1

training:
  batch_size: 16
  epochs: 80
  lr: 1e-3
  seed: 42

evaluation:
  export_predictions: true
  export_case_studies: true
  compare_with_phase4_best: true
```

---

## 20. 文档要求

Phase 5 必须新增一组主模型文档，明确记录主方法设计。

至少新增：

- `docs/models/main_model_overview.md`
- `docs/models/physics_fusion_design.md`
- `docs/decisions/0005_phase5_main_model_design.md`

## 20.1 `main_model_overview.md` 应包含

- 主任务与辅助任务
- 主模型整体结构
- 输入输出定义
- 与 Phase 4 的关系
- 默认模型配置
- 已知局限

## 20.2 `physics_fusion_design.md` 应包含

- 物理信息进入方式
- residual formulation 说明
- physics penalty 说明
- 为什么这样设计
- 不同路径的适用边界

## 20.3 决策记录应包含

至少记录：

- 为什么主模型采用当前 temporal + graph 组合
- 为什么选择当前 physics fusion 方案
- 为什么当前辅助任务是 hotspot 而不是其他头
- 为什么默认损失组合这样设置

---

## 21. 推荐文件级实现清单

以下是 Phase 5 推荐实现的文件级清单。Codex 应以此为主要目标。

```text
configs/
  phase5/
    phase5_dev.yaml
    models/
      main_model_default.yaml
      no_physics.yaml
      no_temporal.yaml
      regression_only.yaml
    losses/
      default_loss.yaml
    ablations/
      main_ablation.yaml

docs/
  models/
    main_model_overview.md
    physics_fusion_design.md
  decisions/
    0005_phase5_main_model_design.md

src/
  gic/
    models/
      encoders/
        __init__.py
        input_encoder.py
        temporal_encoder.py
      fusion/
        __init__.py
        physics_fusion.py
      heads/
        __init__.py
        regression_head.py
        hotspot_head.py
        risk_head.py
        uncertainty_head.py
      main_model.py
    losses/
      __init__.py
      regression.py
      hotspot.py
      physics_penalty.py
      composer.py
    training/
      main_loops.py
      ablation.py
    eval/
      hotspot_metrics.py
      case_studies.py
      comparison_reports.py

tests/
  test_main_model.py
  test_temporal_encoder.py
  test_physics_fusion.py
  test_loss_composer.py
  test_hotspot_head.py
  test_main_training_loop.py
```

说明：

- 不要求一开始把所有头都实现完整
- 但 `main_model.py`、`physics_fusion.py`、`temporal_encoder.py`、`composer.py` 和 `main_loops.py` 是本阶段关键文件

---

## 22. Codex 在本阶段的实现顺序要求

Codex 必须按以下顺序推进，不允许先写很多头和损失再补主结构。

### Step 1：固定主模型输入输出边界与主任务定义

先实现：

- 主模型 schema
- 输入 bundle 定义
- 输出 bundle 定义

### Step 2：实现 temporal encoder 与 graph backbone 组合

先打通：

- 无物理、仅时序 + 图的路径

### Step 3：实现 physics fusion 与 residual path

确保：

- 物理 baseline 可进入模型
- residual formulation 可开关

### Step 4：实现主回归头与基础损失

先确保主任务完整可训练。

### Step 5：实现 hotspot head 与多任务损失

在主回归稳定后再加辅助任务。

### Step 6：实现 ablation、比较与报告

至少覆盖：

- baseline vs main model
- no physics
- no temporal
- regression only

### Step 7：补齐文档、测试与默认配置

完成：

- 主模型文档
- 决策记录
- 核心测试
- 默认模型配置

---

## 23. Phase 5 的验收标准

只有满足以下条件，Phase 5 才算完成。

### 23.1 主模型完成

- 有统一主模型定义
- 支持时序与图输入
- 支持物理信息进入
- 支持至少一个辅助任务

### 23.2 训练评估链路完成

- 主模型可训练
- 可评估
- 可导出样本级预测
- 可与 Phase 4 baseline 比较

### 23.3 关键 ablation 完成

至少完成：

- baseline vs main model
- no physics
- no temporal
- regression only

### 23.4 默认主模型完成

- 有明确默认配置
- 有明确默认说明
- 有相对基线的增益摘要

### 23.5 文档完成

- 主模型概述文档存在
- physics fusion 设计文档存在
- 决策记录存在

---

## 24. 最低可接受标准（Minimum Acceptable Outcome）

如果时间有限，Phase 5 至少必须达到以下底线：

1. 有一个 temporal + graph 的主模型
2. 支持 physics baseline 作为输入或 residual
3. 有主回归头
4. 能和 Phase 4 最佳 baseline 做比较
5. 能完成至少一个 no-physics 或 no-temporal ablation
6. 有一份默认主模型配置

如果连这个底线都达不到，则 Phase 5 不能结束。

---

## 25. 风险与回退策略

## 25.1 风险：物理约束加太重导致模型退化

### 对策

- 物理 penalty 权重必须可调
- 先以物理特征输入和 residual 为主
- penalty 作为逐步增强项，而不是硬约束起点

## 25.2 风险：时序模块复杂度过高导致训练不稳定

### 对策

- 优先使用简单稳健的 TCN/GRU 路线
- 控制窗口长度
- 先稳定训练，再扩展时序复杂度

## 25.3 风险：多任务互相干扰

### 对策

- 所有头都必须可开关
- 先 regression，再逐步加入 hotspot
- 记录各损失项贡献

## 25.4 风险：与 Phase 4 比较不公平

### 对策

- 使用同一 graph-ready 数据
- 使用同一 split 与基础指标
- 明确哪些变化来自模型而非数据

## 25.5 风险：模型过于复杂，难以解释

### 对策

- 保持模块化
- 必做 ablation
- 记录每一层增强的增益

---

## 26. 明确禁止事项

Codex 在本阶段**禁止**做以下事情：

1. 不得引入 KG 融合
2. 不得重新定义导致 Phase 4 不可比较的任务
3. 不得省略 baseline vs main model 对比
4. 不得把 physics penalty 写死为不可配置
5. 不得在没有标签定义时强行加很多任务头
6. 不得把所有增强点一次性全部堆上而不做 ablation
7. 不得让 temporal、physics、task heads 与 graph backbone 强耦合到不可拆解
8. 不得只输出总体平均指标，不做关键案例分析
9. 不得跳过默认主模型配置的明确给出
10. 不得省略文档、测试和设计记录

---

## 27. 建议提交粒度

建议本阶段按以下粒度逐步提交，方便回溯。

### Commit 1
建立主模型骨架、输入输出 bundle 与配置骨架

### Commit 2
实现 temporal encoder + graph backbone 主路径

### Commit 3
实现 physics fusion 与 residual learning

### Commit 4
实现 regression head 与基础 loss

### Commit 5
实现 hotspot head 与多任务 loss

### Commit 6
实现 ablation、对比报告与案例导出

### Commit 7
补齐文档、测试与默认配置

---

## 28. 本阶段完成后的交接要求

Phase 5 完成后，应额外输出一份交接摘要，说明：

- 当前主模型结构是什么
- 当前默认 temporal / graph / physics fusion 选择是什么
- 哪些 ablation 显示物理信息确实有效
- 哪些场景下时序模块帮助明显
- 当前辅助任务带来了什么收益
- 哪些问题应留给 Phase 6 的 KG 增强
- 当前主模型的已知局限是什么

建议存放于：

- `reports/phase5_summary.md`
  或
- `docs/phases/phase5_completion_note.md`

---

## 29. Phase 6 的前置接口要求

为了让后续阶段顺利开始，Phase 5 完成后至少应保证以下接口稳定：

- 主模型输入 bundle
- 物理 baseline / quality flag 接口
- temporal 输入接口
- 多任务输出接口
- 统一损失与评估接口
- 与 Phase 4 可比的 baseline 结果引用接口

如果这些接口不稳定，则不应进入 Phase 6。

---

## 30. 最终执行指令（给 Codex 的摘要版）

下面这段可直接作为对 Codex 的高层执行约束摘要：

> 你正在执行 GIC 项目的 Phase 5。你的目标是在 Phase 4 的图学习基线之上，构建一个可解释、可配置、可做 ablation 的 physics-informed temporal GNN 主模型。你必须先固定主任务、输入输出与时序路径，再加入 physics baseline 输入与 residual formulation，随后再加入辅助任务和可配置的 physics penalty。你必须保证和 Phase 4 的公平可比性，必须完成 baseline vs main model、no-physics、no-temporal 和 regression-only 等关键 ablation。你不得引入 KG，不得把所有增强点一次性混在一起，不得省略默认主模型配置和阶段总结。

---

## 31. 结论

Phase 5 是整个项目从“图学习基线”走向“主方法”的关键阶段。  
它的核心价值不在于把模型做得最复杂，而在于：

- 把物理先验真正整合进学习框架；
- 把时间维度纳入重建过程；
- 把平均误差优化扩展到热点和风险层面；
- 给项目形成一个真正可以被称为主方法的模型版本。

如果 Phase 5 做得好，后续 Phase 6 的 KG 增强将是“锦上添花”；  
如果 Phase 5 做得差，Phase 6 很容易变成“用语义层修补主模型结构不清”的被动操作。

Phase 5 完成并验收后，下一步应开始：

- `phase_6_detailed_plan.md`
