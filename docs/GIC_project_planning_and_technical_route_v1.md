# GIC 稀疏观测条件下的网络级态势重建项目规划与技术路线文档（Markdown 版）

## 1. 文档目的

本文档用于作为项目后续开发、建模、实验设计、数据接入、代码实现与阶段性验收的统一参考基线。目标不是写一份简短 proposal，而是形成一份后续可以反复回看、持续校验、不断细化的“工程—研究混合型主文档”。

本文档覆盖以下内容：

1. 项目目标、边界与成功标准。
2. 当前技术判断与总体方案选择依据。
3. 完整可实践的技术路线，包括前端信号处理、物理模型、GNN 主干、知识图谱增强、评估体系与工程化落地。
4. 当前已经查到的所有高价值公开数据、数据集、测试系统与论文支撑，并标明具体用途、价值判断与是否准备纳入项目。
5. 开发阶段划分、仓库模块拆分建议、实验路线与风险控制策略。

---

## 2. 项目总目标

### 2.1 核心目标

在**稀疏、含噪、局部可观测**的条件下，结合电网拓扑、地磁/地电场驱动、少量 GIC 观测与物理先验，重建**网络级 GIC situational map**，并输出：

- 全网或区域级 GIC 分布图；
- 高风险变压器/设备排序；
- 时序热点演化；
- 峰值时段预警；
- 结果不确定性估计；
- 可选的语义层解释（设备、区域、驱动因素、规则关系）。

### 2.2 项目更准确的学术定位

本项目不应被表述为：

> 用 AI 直接预测 GIC。

更准确的表述应为：

> 构建一个**物理约束下的数据驱动时空重建系统**，在少量传感器与不完备观测条件下，对网络级 GIC 态势进行估计、补全、校正与风险感知。

这个定位非常关键，因为它决定了：

- 我们不会把模型做成纯黑箱；
- 我们会保留可解释的物理中间层；
- 我们的评价不只看点对点误差，也看风险识别能力；
- 真实场景中，即便没有“全网真值”，项目依旧有工程价值。

---

## 3. 当前技术判断与核心结论

### 3.1 结论总览

基于现有两篇参考文献与公开资料，项目具备明显可行性，并且有研究与工程双重价值。

当前最优路线不是“FastICA + GNN”简单两段式，而应升级为五层结构：

1. **数据层**：多源时空输入；
2. **信号层**：鲁棒低频成分提取；
3. **物理层**：GIC forward / baseline solver；
4. **图学习层**：physics-informed spatio-temporal GNN；
5. **知识层**：知识图谱与规则增强。

### 3.2 为什么这条路线成立

#### 3.2.1 GIC 具有明确的物理局域性

Overbye 的 sensitivity analysis 结果说明，某一变压器的 GIC 主要由附近部分线路的地电场贡献主导，而不是对整个电网范围内的所有线路均匀敏感。这意味着：

- 电网是天然图结构；
- GIC 的传播不是完全长程无差别耦合；
- 基于拓扑和局域邻域的图建模是合理的；
- 消息传递半径可以依照物理局域性来设计；
- 这为 GNN 的 inductive bias 提供了理论支撑。fileciteturn2file5 fileciteturn2file7

#### 3.2.2 GIC 属于 quasi-DC，有清晰的频带先验

GIC 是受地电场沿输电线路积分驱动的低频/近直流电流，因此从高频、含噪时序中提取 quasi-DC 有明确物理合理性。你提供的 MT 长持续噪声抑制文献说明，自适应稀疏表示方法在低信噪比、全时段污染、长持续噪声场景下具备优势，这支持把 FastICA 视为前端候选之一，而不是唯一手段。fileciteturn2file1 fileciteturn2file2

#### 3.2.3 真实系统存在明显“观测不足”问题

现实世界里的 GIC 观测通常只有少量变压器中性点电流或局部站点数据，并没有标准化的全网 GIC 实时真值图。因此，本项目的根本价值在于：

- 用少量可用观测恢复更多空间信息；
- 将“点值监测”提升为“面状态势感知”；
- 在参数不完备和观测不足下，提高系统可观测性。

#### 3.2.4 纯物理方法与纯数据驱动方法都有不足

- 纯物理法依赖地电场建模、电导率模型、接地参数、线路参数与网络细节，误差会逐层积累；
- 纯数据驱动法在真实 GIC 标签稀缺、跨区域泛化差的情况下风险很大；
- 因此最优路线是**物理模型提供 baseline 与约束，GNN 学习残差与复杂性**。

---

## 4. 项目目标细化与交付标准

### 4.1 最终交付目标

最终系统理想上应支持以下能力：

#### A. 输入

- 电网测试系统或真实电网抽象图；
- 地磁观测、地电场估计或由磁扰反演的驱动量；
- 少量 GIC 传感器时序；
- 设备属性、接地属性、线路几何与区域属性；
- 可选历史 storm 事件与运维规则。

#### B. 输出

- transformer-level / bus-level / regional-level GIC 估计；
- 全网 GIC map；
- 高风险设备排名；
- hotspot 区域与热点时间窗；
- uncertainty / confidence；
- 基于 KG 的语义解释。

#### C. 工程形态

- 可重复的数据生成与训练流程；
- 模块化物理求解器；
- 可扩展的图数据建模方式；
- 具备 ablation 能力的研究框架；
- 后续可迁移到真实局部观测数据。

### 4.2 成功标准

#### 最低成功标准

- 在公开测试系统上构建完整数据生成—训练—评估 pipeline；
- 能在不同观测稀疏率下完成 GIC map 重建；
- 在合成标签条件下相对于 baseline 明显更优；
- 能输出热点设备识别结果；
- 有清晰的误差分析与失败案例分析。

#### 中等成功标准

- 物理先验 GNN 明显优于纯 GNN；
- 在 50%–70% 观测缺失条件下仍保持较好重建能力；
- 对峰值时段和 Top-k 高风险设备有较高召回；
- 能完成跨 storm / 跨噪声强度泛化实验。

#### 高成功标准

- 用真实地磁驱动 + 局部真实 GIC 观测进行外部校验；
- 加入 KG 后，在缺失属性、结构约束、语义解释上有定量增益；
- 系统形成可演示的 research prototype。

---

## 5. 问题形式化

### 5.1 输入形式

设电网图为：

- 图结构：\( G = (V, E) \)
- 节点集合 \(V\)：母线、变电站、变压器、传感器、磁台站等
- 边集合 \(E\)：电气连接、接地关系、地理邻近、观测关系等

时序输入包括：

- \( X_t^{sensor} \)：GIC 传感器观测
- \( X_t^{mag} \)：磁场或 \(dB/dt\)
- \( X_t^{geo} \)：地电场估计或区域驱动
- \( X^{static} \)：静态设备参数、线路几何、电压等级、接地属性、区域属性、变压器类型等

### 5.2 输出形式

- \( \hat{Y}_t^{GIC} \)：每个关键节点/设备的 GIC 估计
- \( \hat{H}_t \)：hotspot mask 或 hotspot score
- \( \hat{R}_t \)：风险排序分数
- \( \hat{U}_t \)：不确定性估计

### 5.3 任务类型

本项目不是单一回归，而是一个**多任务学习问题**：

1. 节点/设备级回归；
2. 热点分类或分割；
3. 风险排序；
4. 时序峰值预测；
5. 可选因果或规则解释。

---

## 6. 总体技术路线

## 6.1 总体架构概述

建议采用以下分层架构：

1. **数据接入层**
2. **信号处理层**
3. **物理求解层**
4. **图重建层**
5. **知识图谱增强层**
6. **评估与可视化层**

下面逐层展开。

---

## 7. 数据接入层设计

### 7.1 输入数据类别

#### 7.1.1 电网拓扑与设备数据

需要包括：

- bus / substation / transformer / line / generator / load
- line resistance / length / orientation
- transformer winding type / effective GIC path
- grounding resistance
- 是否串补
- geographic coordinates
- 区域归属

#### 7.1.2 地磁驱动数据

包括：

- 磁场分量 \(B_x, B_y, B_z\)
- 导数 \(dB/dt\)
- 地磁活动指数（如 Kp、Dst）

#### 7.1.3 地电场或电导率相关数据

包括：

- geoelectric field gridded product
- regional conductivity / EMTF / MT-derived transfer functions
- simplified field proxies

#### 7.1.4 GIC 观测数据

包括：

- transformer neutral current time series
- station-level measured GIC
- 局部观测点标签

### 7.2 数据接入原则

#### 原则 1：合成训练为主，真实校验为辅

由于公开真实全网 GIC 标签极少，项目训练主力必须依赖合成标签。真实数据更适合作为：

- 模型输入驱动；
- 局部外部验证；
- 峰值时段对齐校验；
- few-shot calibration。

#### 原则 2：统一时空分辨率

需要定义统一的：

- 时间步长：例如 1 min、10 s 或 1 s；
- 空间层级：line / transformer / bus / substation / region；
- 坐标系与区域映射方式。

#### 原则 3：明确数据质量标签

每类数据都应附带 quality flag，例如：

- 原始 / 清洗后 / 插值后
- definitive / quasi-definitive / provisional
- 合成 / 真实 / 半真实
- 可信 / 低可信 / 缺失补全

---

## 8. 信号处理层设计

### 8.1 为什么前端信号处理必须存在

直接把原始高频时序或混杂噪声观测输入 GNN 并不稳妥。原因包括：

- GIC 是 quasi-DC，信号频谱特征特殊；
- 仪器噪声、趋势漂移、局部干扰可能远大于目标分量；
- 真实观测量少，前端噪声会放大后端重建误差。

因此需要一个“**低频/近直流有效成分提取**”模块。

### 8.2 前端候选方法

#### 8.2.1 FastICA

优点：

- 对盲源分离友好；
- 实现成熟；
- 适合做快速基线。

风险：

- 假设源独立性与线性混合；
- 对某些低频漂移和共模噪声并不一定最优；
- 在真实设备信号中未必稳定。

#### 8.2.2 SOBI / BSS 系列

相比 FastICA，可考虑加入基于二阶统计量的盲源分离方法，增强对时间相关信号的适配性。

#### 8.2.3 鲁棒趋势分解 / 滤波

例如：

- moving average / low-pass
- wavelet decomposition
- robust trend extraction
- total variation denoising

优点是简单稳定，适合作为可解释基线。

#### 8.2.4 自适应稀疏表示

根据你给出的 MT 文献，自适应字典学习与稀疏表示对长持续噪声场景有实际价值，因此建议纳入候选前端而不是只作为理论参考。fileciteturn2file1 fileciteturn2file2

### 8.3 建议方案

不固定单一前端，而是建设**前端候选池**：

- `FastICAFrontEnd`
- `SOBIFrontEnd`
- `RobustFilterFrontEnd`
- `SparseRepFrontEnd`

训练时支持：

- 单前端对比；
- 融合前端；
- 自动选择最优前端；
- 将多前端输出拼接成 feature channels。

### 8.4 前端输出形式

统一输出：

- quasi-DC signal estimate
- low-frequency envelope
- denoised residual
- frequency band statistics
- quality score

后端 GNN 与物理模块不直接依赖某一种前端实现。

---

## 9. 物理求解层设计

### 9.1 为什么物理层是必须的

这是整个项目最重要的设计点。没有物理中间层，GNN 很容易变成：

- 仅在 synthetic data 上表现好；
- 对参数变化、拓扑变化和真实噪声不稳；
- 缺乏解释性；
- 难以说服评审其结果不是“过拟合仿真器”。

### 9.2 物理层的角色

物理层不需要完美，但必须提供：

1. baseline GIC estimate
2. physics-consistency constraints
3. line-level / transformer-level intermediate quantities
4. residual learning interface

### 9.3 拟采用的物理思想

根据 Overbye 文献，GIC 计算可抽象为：

1. 由地电场沿线路积分得到等效线电压；
2. 将线路电压转换为 Norton 等效注入；
3. 在 DC conductance network 中求解节点电位与电流；
4. 进而得到变压器或网络中各支路的 GIC。fileciteturn2file4 fileciteturn2file6

### 9.4 物理层具体实现建议

#### 9.4.1 最简 baseline solver

输入：

- line geometry
- line resistance
- grounding resistance
- transformer model abstraction
- regional geoelectric field

输出：

- line induced voltage
- Norton equivalent current
- transformer GIC baseline

#### 9.4.2 增强版本

逐步加入：

- 区域化 conductivity model
- EMTF-based field mapping
- 线路方向性差异
- 不确定性传播
- 参数误差扰动分析

### 9.5 物理层在训练中的作用

建议至少有三种使用方式：

#### 模式 A：作为输入特征

将 baseline GIC 和 line-induced quantities 输入 GNN。

#### 模式 B：作为残差学习基底

让模型预测：

\[
\hat{Y} = Y_{physics} + \Delta Y_{GNN}
\]

#### 模式 C：作为损失约束

加入 physics consistency loss，例如：

- 节点电流守恒约束；
- 空间连续性约束；
- 线路投影一致性约束；
- 与物理 baseline 偏差不应无界。

### 9.6 建议优先级

必须优先实现最简 baseline solver。没有它，整条技术路线会明显降级。

---

## 10. 图学习层设计

### 10.1 为什么 GNN 是核心而不是附属

本项目的核心并不是“做一个比物理模型更复杂的神经网络”，而是：

- 解决稀疏观测下的空间补全；
- 利用网络拓扑和局域性进行传播推断；
- 把多源异构数据融合到统一图中；
- 在物理中间层之上建模误差与复杂耦合。

### 10.2 图的定义方式

不建议只建成传统单一 bus graph。建议直接采用**异构图**。

#### 节点类型

- `bus`
- `substation`
- `transformer`
- `line`（可作为 edge-as-node 处理）
- `sensor`
- `mag_station`
- `region`
- `storm_event`（可选）

#### 边类型

- `electrically_connected`
- `grounded_at`
- `contains`
- `measured_by`
- `located_in`
- `affected_by`
- `geographically_adjacent`
- `mapped_to_region`

### 10.3 特征设计

#### 静态特征

- voltage level
- line length
- line azimuth
- resistance
- grounding resistance
- transformer type
- serial compensation flag
- geographic coordinates
- region conductivity tag

#### 动态特征

- denoised GIC observations
- magnetic field features
- dB/dt
- geoelectric field
- historical window statistics
- physics baseline outputs
- missingness mask
- data quality indicators

### 10.4 模型候选

#### Baseline

- MLP + interpolation
- GCN
- GraphSAGE

#### 主力模型

- GATv2
- edge-aware message passing network
- hetero-GNN
- temporal GNN
- graph transformer（后期可选）

### 10.5 时序建模方案

建议采用以下之一：

#### 方案 A：TCN + GNN

先用 TCN 编码每个节点的局部时间窗，再做图传播。

#### 方案 B：GNN + GRU/LSTM

先做图编码，再用序列模型处理随时间变化的表示。

#### 方案 C：Spatio-temporal GNN

端到端学习时空依赖，适合后期提升性能。

### 10.6 输出头设计

建议至少使用三个 heads：

1. `gic_regression_head`
2. `hotspot_classification_head`
3. `risk_ranking_head`

可选第四个：

4. `uncertainty_head`

### 10.7 损失函数设计

建议总损失为：

\[
\mathcal{L} = \lambda_1 \mathcal{L}_{reg} + \lambda_2 \mathcal{L}_{hotspot} + \lambda_3 \mathcal{L}_{rank} + \lambda_4 \mathcal{L}_{physics} + \lambda_5 \mathcal{L}_{smooth}
\]

其中：

- \(\mathcal{L}_{reg}\)：MAE / MSE / Huber
- \(\mathcal{L}_{hotspot}\)：BCE / focal loss
- \(\mathcal{L}_{rank}\)：pairwise ranking loss / listwise loss
- \(\mathcal{L}_{physics}\)：物理一致性惩罚
- \(\mathcal{L}_{smooth}\)：图上平滑但不抹平热点

### 10.8 训练策略

- 先在合成数据上预训练；
- 再用真实驱动做 domain adaptation / calibration；
- 支持 sparse-mask curriculum；
- 先学回归，再加入多任务；
- 支持多 storm 事件联合训练。

---

## 11. 知识图谱（KG）目标与设计

用户已明确要求把 KG 作为项目目标之一，因此本文档将 KG 定义为**项目第二阶段的重要组成部分**，而不是可有可无的附录。

### 11.1 KG 的角色定位

KG 不应替代 GNN 主干，也不应被当作主要预测器。其正确定位是：

1. **语义整合层**：统一异构数据源；
2. **先验组织层**：显式表达设备关系、规则、区域属性；
3. **特征增强层**：为 GNN 提供 relation-aware features；
4. **解释层**：支持对输出结果进行语义追溯。

### 11.2 为什么 KG 有价值

因为本项目数据天然异构：

- 设备台账与拓扑结构；
- 线路与变压器参数；
- 地理位置与区域归属；
- 磁台站与区域影响关系；
- storm 事件与时间片；
- 观测数据质量与来源；
- 规则知识，例如“串补线路阻断直流”。

这些关系如果只散落在 CSV 或 JSON 中，工程上会逐渐混乱；而 KG 能把这些关系显式化。

### 11.3 KG 设计目标

#### 目标 1：建立统一实体模式

实体建议包括：

- `Substation`
- `Bus`
- `Transformer`
- `TransmissionLine`
- `Sensor`
- `MagStation`
- `Region`
- `ConductivityModel`
- `StormEvent`
- `TimeSlice`
- `Observation`
- `RiskAlert`

#### 目标 2：建立核心关系模式

例如：

- `CONNECTED_TO`
- `CONTAINS`
- `MEASURES`
- `LOCATED_IN`
- `AFFECTED_BY`
- `USES_MODEL`
- `HAS_GROUNDING`
- `HAS_TRANSFORMER_TYPE`
- `BELONGS_TO_EVENT`
- `INFLUENCES`
- `NEARBY_TO`

#### 目标 3：存储规则与约束

例如：

- 串补线路阻断 GIC；
- 某类变压器在特定接线下更敏感；
- 某区域优先采用某 conductivity model；
- 某观测点只适用于局部区域；
- 某类型数据为 provisional，不宜用于高置信监督。

### 11.4 KG 如何与 GNN 结合

#### 方案 A：KG 生成结构化特征

例如：

- 节点所属区域；
- 设备类型 embedding；
- 规则标签；
- 关系计数；
- 近邻磁台站映射；
- 数据质量标签。

#### 方案 B：KG 生成 relation types

将 KG 的关系类型映射到 hetero-GNN 的边类型。

#### 方案 C：KG 做训练后解释

例如给出：

- 该变压器被判为高风险，因为其所在区域 conductivity 较高、接地敏感、邻近线路长度较大且当前 storm 驱动增强；
- 该告警主要受哪类输入与规则影响。

### 11.5 KG 的工程优先级

建议分阶段实施：

#### 第一阶段

不单独上图数据库，只在数据 schema 中保留 KG-ready 设计。

#### 第二阶段

建立轻量 KG 存储：例如 Neo4j 或 RDF/Property Graph 风格结构。

#### 第三阶段

把 KG 作为可查询知识层，与训练后可视化和解释模块联动。

### 11.6 对 KG 的最终判断

KG 是值得纳入项目目标的，但不应抢占主线资源。主线始终是：

> 物理先验 + 时空 GNN 重建。

KG 的最佳价值体现在：

- 数据治理；
- 异构关系表达；
- 规则增强；
- 解释性。

---

## 12. 数据、数据集、测试系统总表

下面整理目前已查到的所有高价值公开数据、数据集或测试系统，并对其用途与是否准备使用做明确判断。

## 12.1 地磁观测数据

### 12.1.1 SuperMAG

**来源**：SuperMAG 官方平台。官方信息显示其整合了全球地面磁力计数据，并持续更新数据持有；历史介绍说明其覆盖数百个台站。citeturn827197search0turn827197search4

**类型**：地磁观测数据平台

**可提供内容**：

- 地磁台站观测
- 多区域 storm 事件驱动
- 统一处理后的时间序列

**用途**：

- 作为真实 storm 驱动输入；
- 计算磁场分量与 \(dB/dt\)；
- 构建事件级输入数据集；
- 做跨 storm 泛化实验。

**优点**：

- 全球覆盖广；
- 对时空 storm 输入很有价值；
- 适合后续做跨区域试验。

**局限**：

- 不是 GIC 直接标签；
- 需要与电网区域做映射；
- 仍需配合 conductivity / geoelectric 推断。

**是否准备使用**：**是，优先使用**。

**建议角色**：真实驱动主来源之一。

### 12.1.2 INTERMAGNET

**来源**：INTERMAGNET 官方数据下载门户。官方说明可下载 provisional、quasi-definitive 和 definitive 数据，并支持 1-second 与 1-minute 数据。citeturn827197search1turn827197search5turn827197search16turn827197search19

**类型**：国际磁观测网络

**用途**：

- 高质量地磁观测输入；
- 为特定区域事件构建更可靠驱动；
- 与 SuperMAG 互补验证；
- 做数据质量标签实验。

**优点**：

- 官方标准化程度高；
- 数据类型和质量等级清晰；
- 适合严谨实验与复现实验记录。

**局限**：

- 仍然不是 GIC 标签；
- 接口使用和格式处理略复杂；
- 台站与项目目标区域需要映射。

**是否准备使用**：**是，建议使用**。

**建议角色**：高质量地磁驱动与验证数据源。

---

## 12.2 地电场与地球电导率相关产品

### 12.2.1 NOAA SWPC Geoelectric Field Models

**来源**：NOAA SWPC 官方产品。官方说明该产品可提供 geoelectric field，对电力线路等人工导体的感应风险具有直接意义；其 1D/3D EMTF 版本支持按地球电导率模型估计地电场。citeturn827197search2turn827197search6turn827197search10turn827197search17

**类型**：操作型/准操作型地电场产品

**用途**：

- 作为物理层输入的区域 geoelectric field；
- 省去从头做磁场到地电场反演；
- 用于生成线路沿线积分驱动；
- 适合做 baseline 物理求解。

**优点**：

- 与电力感应风险直接相关；
- 官方产品，较易对接；
- 可减少前期建模复杂度。

**局限**：

- 区域覆盖有限；
- 空间分辨率与所选测试系统未必天然匹配；
- 仍需线路几何与区域映射。

**是否准备使用**：**是，强烈建议使用**。

**建议角色**：物理 baseline 求解的重要输入。

### 12.2.2 USGS / EMTF / MT 相关产品

**来源**：此前调研中已确认 USGS 提供与 geoelectric、magnetotelluric 相关的数据产品，且 NOAA 的 3D EMTF 模型明确依赖 MT survey transfer functions。citeturn827197search10turn827197search17

**类型**：地球电导率 / EMTF / MT 派生数据

**用途**：

- 支撑更真实的地电场建模；
- 作为 conductivity 先验；
- 对后续区域化实验有价值。

**优点**：

- 有助于增强物理真实性；
- 适合做更高保真版本。

**局限**：

- 前处理复杂；
- 初期原型可能不需要直接接入完整 EMTF 体系；
- 与项目最小可行产品相比属于增强项。

**是否准备使用**：**阶段性使用，第二优先级**。

**建议角色**：中后期增强型物理先验。

---

## 12.3 GIC 直接观测与案例数据

### 12.3.1 日本 Hokkaido / Tokyo 相关 GIC 观测研究

**来源**：已在前序调研中确认有日本实测论文，涉及单变压器和东京地区多站点统计研究。

**类型**：论文级公开案例数据或图表信息

**用途**：

- 作为真实局部 GIC 外部验证参考；
- 用于确定真实量级、时序形态与峰值行为；
- 用于讨论中纬度区域实际 GIC 风险。

**优点**：

- 与真实系统相关；
- 可帮助限制 synthetic assumptions；
- 对论文写作价值高。

**局限**：

- 不一定能直接获得原始全量时序；
- 更适合作为校验与参考，而非大规模训练集。

**是否准备使用**：**准备作为外部验证参考，非主训练集**。

### 12.3.2 New Zealand / 2024 Gannon storm 相关 GIC 实测案例

**来源**：前序调研中已查到相关论文，描述 storm 期间实测变压器 GIC 及 mitigation 效果。

**类型**：真实案例研究

**用途**：

- 作为工程价值论证；
- 用于说明网络级 GIC situational awareness 的现实必要性；
- 可做少量外部案例对照。

**优点**：

- 时间近；
- 具有明确 operational relevance；
- 适合在项目文档中支撑“工程需求真实存在”。

**局限**：

- 数据获取未必直接；
- 覆盖设备有限；
- 不足以形成训练集。

**是否准备使用**：**作为背景论证与可能的外部验证参考使用**。

### 12.3.3 其他公开 GIC 数据库（如俄罗斯数据库）

**来源**：前序调研中已发现论文声称其数据库可访问。

**类型**：潜在公开数据库

**用途**：

- 若可用，可作为额外真实 GIC 测点来源；
- 支持跨区域校验。

**优点**：

- 如果可直接获取，价值很高。

**局限**：

- 当前可用性、接口、格式与许可尚未核实；
- 风险较高，不宜作为项目主依赖。

**是否准备使用**：**暂不作为主计划依赖，后续单独核查**。

---

## 12.4 电网测试系统与公开测试案例

### 12.4.1 Texas A&M Electric Grid Test Case Repository

**来源**：Texas A&M 官方测试系统仓库。官方说明其提供多种电网测试数据集与 synthetic cases。citeturn827197search3turn827197search7turn827197search18

**类型**：电网测试系统集合

**用途**：

- 提供可复现实验平台；
- 选择含地理 footprint 的测试系统；
- 寻找适合 GIC 实验的扩展案例；
- 支撑规模扩展实验。

**优点**：

- 官方、公开、系统化；
- 数据集类别丰富；
- 对后续扩容、迁移实验很有帮助。

**局限**：

- 并非所有案例都适合直接做 GIC；
- 参数完备度不一；
- 需要筛选最匹配的 case。

**是否准备使用**：**是，强烈建议使用**。

**建议角色**：主测试系统来源之一。

### 12.4.2 IEEE 118-bus System

**来源**：TAMU 官方页面与 MATPOWER case118。官方说明 IEEE 118-bus 是经典公开测试系统，包含 19 generators、177 lines、9 transformers、91 loads 等。citeturn827197search11

**类型**：经典标准测试系统

**用途**：

- 作为最小可行原型系统；
- 用于验证 pipeline 跑通；
- 做 baseline 对比；
- 作为 codex 初始开发的目标 case。

**优点**：

- 标准、经典、被广泛采用；
- 社区工具支持成熟；
- 实现成本低。

**局限**：

- 传统版本主要面向潮流研究；
- 对 GIC 而言，可能缺少完整地理、接地与方向信息；
- 需要人工扩展或借助其他来源补足。

**是否准备使用**：**是，建议作为第一阶段原型使用**。

**建议角色**：MVP 测试系统。

### 12.4.3 UIUC 150-bus System

**来源**：此前调研中已确认 TAMU/UIUC 页面说明其 benchmark results 中包括 GIC。

**类型**：扩展型公开测试系统

**用途**：

- 作为比 IEEE 118 更适合 GIC 的候选系统；
- 用于更真实的中期实验；
- 可能减少自行扩展参数的工作量。

**优点**：

- 对 GIC 友好度更高；
- 有 benchmark 价值；
- 适合中期主实验。

**局限**：

- 获取、格式与适配成本高于 case118；
- 仍需核查参数完整性。

**是否准备使用**：**是，建议作为第二阶段主实验系统**。

### 12.4.4 更大规模 synthetic systems（Texas 6717-bus 等）

**来源**：TAMU 仓库。官方说明存在大规模 synthetic grid。citeturn827197search3turn827197search7

**类型**：大规模 synthetic power grid

**用途**：

- 用于后期可扩展性实验；
- 测试模型在更大图上的性能与推理效率；
- 研究局部性假设在大系统上的表现。

**优点**：

- 可用于验证 scalability；
- 工程展示效果强。

**局限**：

- 并不适合作为第一阶段起点；
- GIC 所需额外属性可能仍需补充；
- 训练与数据生成成本高。

**是否准备使用**：**后期可选，不作为早期主线**。

---

## 12.5 总体数据使用计划汇总

### 第一阶段（必须使用）

1. **IEEE 118-bus / MATPOWER case118**
   - 用途：快速跑通最小可行系统。
   - 是否使用：是。

2. **TAMU / UIUC 150-bus 或其他更适合 GIC 的 case**
   - 用途：中期主实验。
   - 是否使用：是。

3. **SuperMAG 或 INTERMAGNET 地磁驱动**
   - 用途：真实 storm 输入。
   - 是否使用：是。

4. **NOAA SWPC geoelectric field model**
   - 用途：物理 baseline 输入。
   - 是否使用：是。

### 第二阶段（增强使用）

5. **USGS / EMTF / MT conductivity-related products**
   - 用途：提升物理真实性。
   - 是否使用：是，但第二优先级。

6. **真实 GIC 论文案例数据**
   - 用途：外部验证和量级校验。
   - 是否使用：是，但不作为主训练。

### 第三阶段（探索使用）

7. **更多真实 GIC 数据库**
   - 用途：扩展真实校验。
   - 是否使用：待核查。

8. **大规模 synthetic grid cases**
   - 用途：可扩展性展示。
   - 是否使用：后期可选。

---

## 13. 数据集构建策略

### 13.1 为什么必须自己构建数据集

当前没有确认存在一个标准化、可直接下载、专门用于：

> 从稀疏传感器重建全网 GIC situational map

的公开 benchmark 数据集。

因此我们必须采用“**多源拼装 + 物理生成标签 + 真实驱动校验**”策略。

### 13.2 数据集三层结构

#### 层 1：原始源数据层

- 电网测试系统
- 磁观测数据
- 地电场产品
- 真实局部 GIC 观测
- 设备与规则元数据

#### 层 2：中间标准化层

统一为：

- 时序 parquet / HDF5 / zarr
- 图结构 JSON / networkx / torch-geometric format
- metadata YAML
- KG triples / property graph schema

#### 层 3：训练样本层

每个样本包括：

- 时间窗输入
- 静态图
- 观测 mask
- 噪声配置
- 物理 baseline
- 目标标签
- quality flags

### 13.3 合成标签生成流程

1. 选定测试系统；
2. 补全 GIC 所需参数；
3. 输入真实或半真实 geoelectric 驱动；
4. 用物理 solver 生成全网 GIC 真值；
5. 采样少量测点作为可观测传感器；
6. 注入噪声、偏置、缺失；
7. 保存为训练样本。

### 13.4 稀疏观测设定

建议至少做以下稀疏率：

- 10% 观测缺失
- 30% 观测缺失
- 50% 观测缺失
- 70% 观测缺失
- 90% 观测缺失

并做两类缺失模式：

- 随机缺失；
- 结构性缺失（例如某区域全部无观测）。

### 13.5 噪声设定

建议覆盖：

- 高斯白噪声
- 长持续低频漂移
- 突发脉冲噪声
- 传感器偏置
- 量化误差
- 时间不同步

### 13.6 真实驱动 + 合成标签的价值

这类“半真实”数据比纯随机仿真更有说服力，因为：

- 驱动来自真实 storm；
- 图结构来自标准测试系统；
- 标签来自物理求解；
- 稀疏观测与噪声更接近工程场景。

---

## 14. 评估体系

### 14.1 为什么不能只看 reconstruction accuracy

如果只看平均精度，模型可能在低值区域很好，但在最重要的高风险变压器上失败。因此本项目的评估必须是多维的。

### 14.2 回归指标

- MAE
- RMSE
- MAPE（谨慎使用，低值敏感）
- Pearson correlation
- Spearman correlation
- peak MAE

### 14.3 热点识别指标

- hotspot precision / recall / F1
- IoU
- top-k hotspot recall

### 14.4 排序指标

- top-k recall
- NDCG
- Kendall / Spearman rank correlation

### 14.5 时序指标

- peak timing error
- event onset detection delay
- temporal correlation

### 14.6 泛化指标

- 跨 storm 事件测试
- 跨噪声强度测试
- 跨拓扑 / 跨测试系统迁移
- 跨稀疏率稳定性曲线

### 14.7 物理一致性指标

- 电流守恒残差
- 与物理 baseline 偏差分布
- 局部性符合程度
- 极端事件下是否出现非物理爆炸输出

### 14.8 不确定性指标

- calibration error
- prediction interval coverage
- confidence-risk curve

---

## 15. Baseline 与对比实验设计

### 15.1 非图方法 baseline

- 邻域插值
- 线性回归
- kriging / spatial interpolation
- MLP

### 15.2 图方法 baseline

- GCN
- GraphSAGE
- GAT

### 15.3 物理相关 baseline

- 纯 physics solver
- physics solver + simple correction

### 15.4 消融实验

必须设计：

1. 去掉物理层
2. 去掉前端去噪
3. 去掉时间建模
4. 去掉异构图，仅保留同构图
5. 去掉 KG 特征
6. 去掉 physics loss
7. 不同稀疏率下性能对比

---

## 16. 工程实现路线

### 16.1 总体开发原则

- 先实现最小可行 pipeline；
- 所有模块都要可替换；
- 统一配置驱动；
- 实验结果必须可复现；
- 每个阶段都能独立验收。

### 16.2 建议仓库结构

```text
project_root/
  configs/
    data/
    model/
    train/
    eval/
  data/
    raw/
    interim/
    processed/
  docs/
  notebooks/
  src/
    ingestion/
    preprocessing/
    physics/
    graph/
    kg/
    models/
    training/
    evaluation/
    visualization/
    utils/
  tests/
  scripts/
```

### 16.3 模块说明

#### `ingestion/`

负责接入：

- test case
- SuperMAG / INTERMAGNET
- NOAA geoelectric
- real GIC case data

#### `preprocessing/`

负责：

- 对齐时间轴
- 质量标记
- 前端去噪
- 缺失模拟
- 样本切片

#### `physics/`

负责：

- line voltage integration
- Norton equivalent
- DC conductance solver
- transformer GIC baseline

#### `graph/`

负责：

- 构图
- 异构图 schema
- feature builder
- spatial neighborhood rules

#### `kg/`

负责：

- entity schema
- relation builder
- rule tags
- graph export / import
- feature extraction from KG

#### `models/`

负责：

- baseline models
- GNN backbones
- temporal models
- multi-task heads

#### `training/`

负责：

- train loop
- curriculum strategy
- checkpointing
- logging
- hyperparameter management

#### `evaluation/`

负责：

- all metrics
- ablation summaries
- uncertainty evaluation
- error breakdown

#### `visualization/`

负责：

- GIC map
- risk ranking dashboard
- temporal plots
- model comparison plots
- KG-based explanation views

---

## 17. 分阶段里程碑

### Phase 0：准备阶段

目标：

- 明确问题定义；
- 确定第一批数据源；
- 搭建仓库骨架；
- 写出配置模板。

验收：

- 文档完成；
- case118 能成功读入；
- 至少一类地磁/地电场数据能成功下载与解析。

### Phase 1：最小可行原型

目标：

- 基于 IEEE 118-bus 构建图；
- 实现最简物理 baseline；
- 构建 synthetic training samples；
- 实现一个简单 GNN 回归器。

验收：

- 跑通 end-to-end；
- 输出 transformer-level GIC estimate；
- 有第一版误差结果。

### Phase 2：前端去噪与时序建模

目标：

- 接入 FastICA 和至少一种替代前端；
- 增加 temporal encoder；
- 评估不同噪声场景。

验收：

- 前端模块可插拔；
- 噪声场景下性能曲线完整。

### Phase 3：Physics-informed 主模型

目标：

- 加入 residual learning；
- 加入 physics consistency loss；
- 比较纯 GNN 与 physics-informed GNN。

验收：

- 有明确的增益结果；
- 有误差分解。

### Phase 4：异构图与多任务输出

目标：

- 建立 hetero graph；
- 增加 hotspot 与 ranking heads；
- 输出不确定性。

验收：

- 多任务结果完整；
- 可视化可用。

### Phase 5：KG 集成

目标：

- 建立实体与关系 schema；
- 从 KG 派生特征；
- 引入规则标签和解释模块。

验收：

- KG 能为 GNN 提供额外特征或解释；
- 至少有一组对比表明 KG 有实用价值。

### Phase 6：真实案例校验与规模扩展

目标：

- 用真实 storm 驱动与局部真实观测做校验；
- 尝试更大测试系统；
- 形成最终 demo 或论文级实验结果。

验收：

- 有外部验证；
- 有跨系统结果；
- 有最终汇报材料。

---

## 18. 主要技术风险与应对

### 18.1 风险：FastICA 不稳定

**应对**：

- 不把 FastICA 设为唯一前端；
- 同时保留稀疏表示与鲁棒滤波基线；
- 对不同噪声类型单独评估。

### 18.2 风险：物理参数不完备

**应对**：

- 从最简参数化开始；
- 对缺失参数做范围扰动与敏感性分析；
- 明确记录 synthetic assumptions。

### 18.3 风险：synthetic-to-real gap 太大

**应对**：

- 使用真实 storm 驱动而不是全随机驱动；
- 用真实局部观测做后验校准；
- 引入 physics-informed 约束；
- 做 domain randomization。

### 18.4 风险：评价指标误导

**应对**：

- 不只看全局均值误差；
- 强制报告 high-risk / peak-related 指标；
- 使用多任务评估表。

### 18.5 风险：KG 工作量过大

**应对**：

- 先做 KG-ready schema；
- 第二阶段再上图数据库；
- 优先做 feature enhancement，而非复杂知识推理。

---

## 19. 当前推荐的第一版实施决策

截至目前，建议明确以下决策：

### 决策 1

**主线模型路线确定为：**

> 前端低频提取 + 物理 baseline solver + physics-informed temporal hetero-GNN + 可选 KG 增强

### 决策 2

**数据主线确定为：**

> 公开测试系统 + 真实 storm 驱动 + 物理生成标签 + 稀疏观测模拟 + 少量真实局部观测校验

### 决策 3

**KG 作为正式项目目标纳入，但排在主线模型之后**。

### 决策 4

**第一批必须接入的数据/系统**：

- IEEE 118-bus / MATPOWER case118
- TAMU / UIUC 150-bus 或同类适合 GIC 的测试系统
- SuperMAG 或 INTERMAGNET
- NOAA SWPC geoelectric field products

### 决策 5

**第一阶段不追求真实全网绝对真值，只追求：**

- pipeline 跑通；
- physics-informed 建模成立；
- 稀疏重建优于 baseline；
- 可输出热点与排序。

---

## 20. 项目最终描述模板（可供后续复用）

下面给出一段可在后续文档、汇报、代码仓库 README 或研究说明中复用的项目描述：

> 本项目旨在解决 GIC 监测中观测稀疏、噪声复杂和全网不可直接测量的问题。我们计划构建一个物理约束下的数据驱动时空重建系统，结合公开电网测试系统、真实地磁/地电场驱动、少量 GIC 观测与 GIC forward model，利用 temporal hetero-GNN 对网络级 GIC 态势图进行重建，并进一步识别高风险设备与热点区域。系统同时将引入知识图谱对电网设备、区域、观测与规则知识进行统一建模，以增强数据治理、特征表达与结果解释能力。

---

## 21. 后续紧接着要做的事情

为了让文档真正进入可执行阶段，接下来最合理的顺序是：

1. 固化代码仓库目录与配置模板；
2. 先实现 IEEE 118-bus 的读取与图构建；
3. 实现最简物理 baseline solver；
4. 接入一个真实地磁/地电场数据源；
5. 生成第一版 synthetic dataset；
6. 跑通一个最小 GNN baseline；
7. 再逐步加入前端去噪、时序建模、hetero graph 和 KG。

这会比一开始就同时做所有模块更可控。

---

## 22. 参考资料（当前文档中实际使用）

### 用户提供文献

1. *Power Grid Sensitivity Analysis of Geomagnetically Induced Currents*。用于支撑 GIC 局域性、Norton 等效与 DC 网络建模思想。fileciteturn2file4 fileciteturn2file5 fileciteturn2file6 fileciteturn2file7
2. *Research on Magnetotelluric Long-Duration Noise Reduction Based on Adaptive Sparse Representation*。用于支撑自适应稀疏表示前端与长持续噪声处理思路。fileciteturn2file1 fileciteturn2file2

### 在线公开数据与平台

3. SuperMAG 官方信息与数据平台。citeturn827197search0turn827197search4
4. INTERMAGNET 官方数据下载与数据说明。citeturn827197search1turn827197search5turn827197search16turn827197search19
5. NOAA SWPC geoelectric field products。citeturn827197search2turn827197search6turn827197search10turn827197search17
6. Texas A&M Electric Grid Test Case Repository。citeturn827197search3turn827197search7turn827197search18
7. IEEE 118-bus 官方测试系统说明。citeturn827197search11

---

## 23. 文档结论

这份文档的最终判断非常明确：

- 项目可行；
- 技术路线应以**physics-informed temporal hetero-GNN**为主；
- 前端应采用“多候选低频提取模块”，不要押注单一 FastICA；
- KG 应作为正式目标纳入，但排在主线模型之后；
- 当前不存在现成的标准 benchmark，需要自建数据集；
- 公开测试系统 + 真实 storm 驱动 + 物理生成标签，是最现实且最稳的实施路径；
- 第一阶段目标应聚焦于可运行原型，而不是追求不现实的真实全网精确反演。

这份 Markdown 文档应被视为后续开发中的“总控文档”。后续如果新增数据源、改动模块设计、改变实验结论，都应该回到本文档进行版本化更新。
