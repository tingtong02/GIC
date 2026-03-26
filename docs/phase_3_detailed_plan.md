# Phase 3 Detailed Plan  
## 前端信号处理与 quasi-DC 成分提取模块（Detailed Execution Plan v1）

## 1. 文档元信息

- 文档名称：`phase_3_detailed_plan.md`
- 阶段名称：Phase 3 — 前端信号处理与 quasi-DC 成分提取模块
- 版本：v1
- 文档角色：**直接执行计划**
- 执行对象：Codex / 开发者
- 上位参考文档：
  - `GIC_project_planning_and_technical_route_v1.md`
  - `GIC_project_phase_roadmap_v1.md`
  - `phase_0_detailed_plan.md`
  - `phase_1_detailed_plan.md`
  - `phase_2_detailed_plan.md`

本文件用于约束 Phase 3 的开发行为。  
在 Phase 3 中，核心任务是建立**统一、可比较、可替换的时序前端信号处理模块**，用于从高频、含噪、稀疏或混合信号中提取与 GIC 相关的 quasi-DC 成分和稳定特征，供后续图模型与 physics-informed 主模型使用。

---

## 2. 本阶段的核心目标

Phase 3 的唯一核心目标是：

> 建立一个模块化的前端信号处理与特征提取框架，使项目能够在多种噪声条件和观测形式下，把原始时序转换为稳定、可对比、可落盘的 quasi-DC 特征表示，并明确这些前端处理对后续重建的价值。

这意味着本阶段必须解决的问题包括：

- 前端输入到底是什么
- 不同信号处理方法如何统一接口
- 从原始波形到 quasi-DC 特征的输出格式是什么
- 如何比较 FastICA、滤波、稀疏表示等方法
- 如何判断一个前端处理是否真的有价值
- 如何把前端输出对接到 Phase 4 / Phase 5，而不污染模型层

---

## 3. 非目标（本阶段明确不做的事情）

为了防止 Phase 3 范围失控，本阶段明确**不做**以下内容：

### 3.1 不实现主 GNN / 时空模型

本阶段不实现：

- GCN / GraphSAGE / GAT
- Temporal GNN
- Hetero-GNN
- Physics-informed training loop
- 多任务输出头

这些属于 Phase 4 / Phase 5。

### 3.2 不实现复杂物理仿真主体

本阶段可以消费 Phase 2 的时序场景输出，但不负责：

- GIC forward solver 核心实现
- 物理标签生成主逻辑
- 物理线性系统求解

这些属于 Phase 2。

### 3.3 不实现 KG 或语义增强

本阶段不实现：

- KG schema
- relation-aware feature fusion
- 规则推理
- 知识补全

这些属于 Phase 6。

### 3.4 不把前端做成与模型强耦合的 end-to-end 结构

本阶段不做：

- 把前端直接嵌进 GNN 内部联合训练
- 为某个模型结构专门设计私有前端输出
- 让前端输出只能被某一个训练脚本读取

### 3.5 不追求完整工业级信号处理平台

本阶段目标是建立研究型、可比较、可复现的前端模块，而不是：

- 兼容所有仪器原始格式
- 覆盖全部电磁噪声场景
- 一开始就实现所有高级 DSP 工具链

---

## 4. 本阶段完成后应具备的能力

Phase 3 完成后，项目至少应具备以下能力：

1. 能读取标准化时序输入；
2. 能对同一输入运行多种前端方法；
3. 能输出统一格式的 quasi-DC 成分和特征；
4. 能为每个前端结果记录方法、参数、质量指标和输出位置；
5. 能比较不同前端方法的效果；
6. 能导出供 Phase 4 / Phase 5 使用的 signal-ready 数据；
7. 能明确推荐一个默认前端 baseline，而不是只给一堆方法列表。

---

## 5. 本阶段总体策略

Phase 3 必须采用“**先定义统一接口，再实现方法，再做对比，再给默认推荐**”的策略。

建议推进顺序如下：

1. 先固定信号输入 schema 和前端输出 schema
2. 再实现最小 baseline 方法
3. 再实现 FastICA 路线
4. 再实现鲁棒低频提取路线
5. 再实现自适应稀疏表示路线
6. 再建立统一评估与对比流程
7. 最后导出默认推荐配置与 signal-ready 数据格式

不要一开始就写很多复杂方法，却没有统一比较框架。

---

## 6. 本阶段必须依赖的输入

## 6.1 上位文档与阶段文档

必须参考：

- `GIC_project_planning_and_technical_route_v1.md`
- `GIC_project_phase_roadmap_v1.md`
- `phase_0_detailed_plan.md`
- `phase_1_detailed_plan.md`
- `phase_2_detailed_plan.md`

## 6.2 Phase 1 与 Phase 2 提供的接口

必须复用：

- 标准化时序 schema
- 时序加载器
- 时序 manifest / registry
- 场景级时间索引
- 可选的 Phase 2 时序标签和 baseline 结果

## 6.3 本阶段允许的输入类型

至少支持以下输入形式：

1. 原始多通道观测时序
2. 合成高频 + 低频混合信号
3. Phase 2 生成的物理时序结果
4. 手工构造的带噪样例
5. 未来真实观测的占位输入格式

---

## 7. 本阶段输出

Phase 3 的输出应是**统一、可复用、可追踪的 signal-ready 特征资产**。

至少包括：

- 去噪后时序
- quasi-DC 提取结果
- 窗口级或时刻级特征
- 前端处理质量指标
- 方法比较报告
- signal-ready 数据导出
- 默认前端推荐方案

---

## 8. 信号层对象设计要求

本阶段要在现有数据层之上，再建立面向前端处理的对象表示。

## 8.1 最低需要定义的对象

至少应定义：

1. `SignalSample`
2. `SignalBatch`
3. `SignalWindow`
4. `FrontendConfig`
5. `FrontendResult`
6. `QuasiDCSeries`
7. `SignalFeatureSet`
8. `SignalQualityReport`
9. `FrontendComparisonReport`

## 8.2 `SignalSample` 最低字段建议

- `sample_id`
- `source_name`
- `sensor_id`
- `time_index`
- `channels`
- `values`
- `units`
- `sampling_interval`
- `scenario_id`（可选）
- `metadata`

## 8.3 `FrontendResult` 最低字段建议

- `result_id`
- `sample_id`
- `method_name`
- `method_version`
- `config_hash`
- `denoised_series`
- `quasi_dc_series`
- `feature_set`
- `quality_metrics`
- `status`
- `notes`

## 8.4 `SignalFeatureSet` 最低字段建议

至少保留：

- `feature_id`
- `window_definition`
- `summary_statistics`
- `peak_features`
- `trend_features`
- `spectral_features`（可选）
- `quality_flags`

说明：

- 本阶段不强制把特征做得很复杂
- 但必须明确输出层级，不只输出一条波形

---

## 9. 前端模块分层设计要求

Phase 3 必须按统一分层实现，避免每种方法自成体系。

## 9.1 输入准备层（Input Preparation Layer）

职责：

- 加载标准化时序
- 对齐时间轴
- 处理缺失值标记
- 切分窗口
- 做基础归一化或预处理（如需要）

这层不做“核心前端方法”。

## 9.2 方法执行层（Method Layer）

职责：

- 运行具体前端算法
- 输出去噪结果与 quasi-DC 结果
- 记录方法参数和运行状态

每种方法都必须实现统一接口，不允许方法间输入输出完全不同。

## 9.3 后处理层（Postprocess Layer）

职责：

- 输出统一 `FrontendResult`
- 提取标准特征
- 计算质量指标
- 写 manifest / metadata

## 9.4 比较与报告层（Comparison Layer）

职责：

- 对比多个方法
- 汇总指标
- 给出默认推荐
- 生成比较报告与图表

---

## 10. 前端方法集合要求

Phase 3 不能只实现一种方法。  
至少应建立三类前端 baseline。

## 10.1 方法 A：FastICA / 盲源分离类

目标：

- 从多通道混合信号中提取独立成分
- 识别低频 GIC 相关成分候选

最低要求：

- 支持多通道输入
- 支持成分数配置
- 支持输出成分解释信息或索引
- 支持与统一结果 schema 对接

## 10.2 方法 B：鲁棒低频提取类

目标：

- 通过平滑、趋势分解、鲁棒滤波等方式提取 quasi-DC 成分
- 作为最简单、最稳定的 baseline

最低要求：

- 支持单通道和多通道
- 支持可配置窗口或平滑参数
- 支持生成低频趋势输出

## 10.3 方法 C：自适应稀疏表示 / 字典学习类

目标：

- 处理长持续噪声、低信噪比和复杂污染
- 作为更强但复杂度更高的前端候选

最低要求：

- 支持基于字典/稀疏表示的降噪框架
- 支持可配置稀疏参数
- 支持输出降噪结果与低频成分

## 10.4 方法扩展要求

可以为未来预留：

- 小波类
- EMD/CEEMDAN 类
- 频域滤波类
- 其他 blind source separation 类

但本阶段不要求全部实现。

---

## 11. 统一接口要求

这是本阶段最重要的工程约束之一。  
Codex 必须确保不同方法都满足统一调用接口。

## 11.1 推荐统一接口

建议每种前端方法都提供类似接口：

```python
run_frontend(
    signal_sample,
    frontend_config,
) -> FrontendResult
```

或者以类形式实现：

```python
class BaseFrontend:
    def run(self, signal_sample, config) -> FrontendResult:
        ...
```

## 11.2 必须统一的输出内容

不管使用哪种方法，最终都必须输出：

- 标准化后的方法名
- 方法参数
- 去噪后时序
- quasi-DC 时序
- 特征集
- 指标
- 状态信息

## 11.3 禁止事项

禁止出现：

- 某方法只输出数组
- 某方法只输出图像不输出数据
- 某方法需要特殊下游脚本才能读
- 不同方法输出字段完全不一致

---

## 12. 输入准备要求

## 12.1 时间对齐

必须处理：

- 时间索引标准化
- 多通道同步对齐
- 缺失点保留或标记
- 窗口切分

## 12.2 缺失值策略

本阶段必须明确记录缺失值处理方式，例如：

- 保留 NaN
- 插值
- 丢弃窗口
- 前向填充
- 用 mask 传递

但不允许静默填充不记录。

## 12.3 归一化与标准化

允许做最小必要预处理，例如：

- 去均值
- 方差归一化
- 通道标准化

但必须满足：

- 参数可配置
- 写入 metadata
- 不破坏可比性

---

## 13. 特征导出要求

本阶段不能只输出“处理后的波形”，还必须形成供后续模型使用的特征。

## 13.1 最低特征层级

至少导出以下三类：

### 13.1.1 时序级输出
例如：

- quasi-DC series
- denoised series
- component series

### 13.1.2 窗口级统计特征
例如：

- mean
- std
- max / min
- peak-to-peak
- slope
- rolling trend

### 13.1.3 质量相关特征
例如：

- 残余高频能量
- 平滑强度指标
- 缺失率
- 有效窗口比例

## 13.2 输出要求

必须支持：

- 原始时间索引保留
- 窗口定义保留
- 特征名固定
- manifest 可追踪

---

## 14. 前端效果评估要求

Phase 3 的核心不只是“做信号处理”，而是“比较信号处理”。

## 14.1 必须建立统一评估框架

评估维度至少包括：

1. 去噪效果
2. 低频保真度
3. 峰值保持能力
4. 时间趋势保持能力
5. 与 Phase 2 物理标签的一致性（如可用）
6. 对后续重建任务的潜在帮助

## 14.2 最低评估指标建议

至少应支持部分或全部：

- SNR improvement
- MAE / RMSE（相对参考信号）
- correlation
- peak error
- trend consistency
- runtime cost
- memory cost

## 14.3 对比方法要求

至少比较：

- FastICA
- 一个低频 baseline
- 一个稀疏表示 baseline
- 原始未处理输入（作为 no-frontend baseline）

---

## 15. 比较与推荐机制要求

## 15.1 不能只输出分散结果

本阶段必须形成：

- 统一比较表
- 场景级对比报告
- 默认推荐方法与原因

## 15.2 默认推荐规则

至少应考虑：

- 效果稳定性
- 对噪声鲁棒性
- 计算成本
- 实现复杂度
- 与后续模型接口兼容性

### 15.2.1 推荐结果形式

建议最终给出：

- 默认方法
- 默认配置
- 备选方法
- 适用场景说明

而不是简单说“某方法最好”。

---

## 16. signal-ready 导出要求

这是连接 Phase 3 和后续阶段的关键。

## 16.1 导出目标

必须能够把前端结果导出到标准位置，例如：

```text
data/processed/signal_ready/
```

## 16.2 导出内容

至少包括：

- signal-ready 时序数据
- 窗口级特征
- 方法 metadata
- quality report
- manifest

## 16.3 导出约束

- 必须可被 Phase 4 / Phase 5 读取
- 不得依赖 notebook 临时文件
- 不得只保存图像而不保存数据
- 每个导出结果都必须可回溯到原始 sample 与前端配置

---

## 17. Phase 3 的 CLI 要求

在复用既有 CLI 结构的基础上，建议增加最小前端相关命令。

至少应支持：

- `signal-run-frontend`
- `signal-compare-frontends`
- `signal-export-features`
- `signal-validate-input`
- `signal-build-report`

### 17.1 命令要求

- 所有命令必须使用统一配置系统
- 必须支持指定输入数据集或 manifest
- 输出路径必须可配置
- 错误信息必须说明是：
  - 输入数据问题
  - 方法参数问题
  - 运行失败
  - 输出失败
  - 参考标签不可用

---

## 18. 配置文件要求

Phase 3 必须新增专用配置文件，例如：

```text
configs/phase3/
  phase3_dev.yaml
  methods/
    fastica.yaml
    lowfreq_baseline.yaml
    sparse_denoise.yaml
  comparisons/
    default_comparison.yaml
```

## 18.1 配置域建议

至少包括：

```yaml
stage:
  current: phase3

signal:
  input_dataset: sample_timeseries
  output_root: data/processed/signal_ready
  window:
    enabled: true
    size: 128
    stride: 32

frontend:
  active_methods:
    - raw_baseline
    - fastica
    - lowfreq_baseline
    - sparse_denoise

  comparison:
    run_enabled: true
    export_report: true

quality:
  compute_signal_metrics: true
  use_reference_if_available: true
```

---

## 19. 文档要求

Phase 3 必须新增一组前端信号处理文档，明确记录方法边界与比较标准。

至少新增：

- `docs/models/signal_frontend_overview.md`
- `docs/data/signal_feature_schema.md`
- `docs/decisions/0003_phase3_frontend_design.md`

## 19.1 `signal_frontend_overview.md` 应包含

- 前端目标
- 输入输出
- 方法集合
- 为什么需要多方法比较
- 当前默认方案与理由
- 已知局限

## 19.2 `signal_feature_schema.md` 应包含

- `FrontendResult` 字段
- `SignalFeatureSet` 字段
- signal-ready 导出结构
- manifest 字段说明

## 19.3 决策记录应包含

至少记录：

- 为什么前端要与主模型解耦
- 为什么选择当前三类 baseline
- 为什么需要 no-frontend baseline
- 默认推荐方法如何确定

---

## 20. 推荐文件级实现清单

以下是 Phase 3 推荐实现的文件级清单。Codex 应以此为主要目标。

```text
configs/
  phase3/
    phase3_dev.yaml
    methods/
      fastica.yaml
      lowfreq_baseline.yaml
      sparse_denoise.yaml
    comparisons/
      default_comparison.yaml

docs/
  models/
    signal_frontend_overview.md
  data/
    signal_feature_schema.md
  decisions/
    0003_phase3_frontend_design.md

src/
  gic/
    signal/
      __init__.py
      schema.py
      base.py
      preprocess.py
      postprocess.py
      features.py
      metrics.py
      comparison.py
      export.py
      validation.py
      methods/
        __init__.py
        fastica_frontend.py
        lowfreq_frontend.py
        sparse_frontend.py
        raw_baseline.py

tests/
  test_signal_schema.py
  test_signal_preprocess.py
  test_fastica_frontend.py
  test_lowfreq_frontend.py
  test_signal_export.py
  test_signal_comparison.py
```

说明：

- 不要求一开始把每种方法做得非常复杂
- 但必须先把统一框架和结果接口写对
- `base.py`、`schema.py`、`comparison.py` 和 `export.py` 是本阶段关键文件

---

## 21. Codex 在本阶段的实现顺序要求

Codex 必须按以下顺序推进，不允许先写很多方法再补接口。

### Step 1：建立 signal 层 schema 与统一接口

先实现：

- `SignalSample`
- `FrontendConfig`
- `FrontendResult`
- `SignalFeatureSet`
- `BaseFrontend`

### Step 2：实现输入准备与最小 raw baseline

先打通：

- 输入准备
- 一个不做复杂处理的 raw baseline
- 统一结果导出

### Step 3：实现 low-frequency baseline

先做一个简单、稳定、可解释的低频提取方法。

### Step 4：实现 FastICA 方法

确保：

- 多通道输入可用
- 输出能映射到统一 schema
- 失败状态可记录

### Step 5：实现 sparse/dictionary baseline

可以先做简化版本，但必须纳入统一比较框架。

### Step 6：实现质量指标、比较与报告

至少支持：

- no-frontend vs 多方法
- 指标汇总
- 默认推荐生成

### Step 7：实现 signal-ready 导出、文档和测试

完成：

- 导出机制
- 文档
- 测试

---

## 22. Phase 3 的验收标准

只有满足以下条件，Phase 3 才算完成。

### 22.1 统一前端框架完成

- 不同方法可共享统一接口
- 不同方法输出统一 `FrontendResult`

### 22.2 至少三类前端 baseline 可运行

必须至少包含：

- raw baseline
- low-frequency baseline
- FastICA
- sparse/dictionary baseline

其中后三者至少三选三实现；raw baseline 必须存在。

### 22.3 比较与评估完成

- 能在同一批样本上比较方法
- 能导出对比结果
- 能给出默认推荐

### 22.4 signal-ready 导出完成

- 可导出时序级与特征级结果
- 可被后续阶段消费
- manifest 完整

### 22.5 文档完成

- 前端概述文档存在
- 特征 schema 文档存在
- 决策记录存在

---

## 23. 最低可接受标准（Minimum Acceptable Outcome）

如果时间有限，Phase 3 至少必须达到以下底线：

1. 有统一前端接口
2. 有 raw baseline
3. 有一个低频 baseline
4. 有 FastICA 或稀疏表示中的至少一个较强方法
5. 能导出 quasi-DC 结果
6. 能做最基础比较与报告

如果连这个底线都达不到，则 Phase 3 不能结束。

---

## 24. 风险与回退策略

## 24.1 风险：FastICA 在某些数据上不稳定

### 对策

- 保留 low-frequency baseline 作为稳定方案
- 对 FastICA 记录失败状态，不做静默 fallback
- 不把默认方案绑定为 FastICA 唯一选项

## 24.2 风险：稀疏表示实现复杂度过高

### 对策

- 先实现简化版本
- 重点保证统一接口和比较框架
- 复杂优化延后，不阻塞本阶段

## 24.3 风险：前端评估缺乏“真值”

### 对策

- 在有 Phase 2 合成标签的场景下使用参考指标
- 在无真值时用趋势/平滑/峰值保真等替代指标
- 显式区分“有参考”和“无参考”的评价

## 24.4 风险：前端与后续模型接口不稳定

### 对策

- signal-ready 导出格式固定
- 用 manifest 与 schema 管理
- 不让模型层直接依赖某个方法内部结构

## 24.5 风险：过度调参导致无法复现

### 对策

- 所有方法参数进入配置文件
- 输出 config snapshot
- 默认配置保持少量关键参数

---

## 25. 明确禁止事项

Codex 在本阶段**禁止**做以下事情：

1. 不得实现 GNN 或训练主循环
2. 不得把前端方法直接嵌入模型联合训练
3. 不得只输出图，不输出标准化数据
4. 不得不同方法使用不同输出 schema
5. 不得静默处理失败或缺失值
6. 不得跳过 no-frontend baseline
7. 不得绕开统一配置硬编码方法参数
8. 不得只写 notebook 版方法而不进入正式模块
9. 不得省略比较报告与默认推荐
10. 不得让 signal-ready 输出不可追踪来源

---

## 26. 建议提交粒度

建议本阶段按以下粒度逐步提交，方便回溯。

### Commit 1
建立 `signal/` 模块骨架、schema 与 base interface

### Commit 2
实现 preprocess、raw baseline 与导出

### Commit 3
实现 low-frequency baseline

### Commit 4
实现 FastICA baseline

### Commit 5
实现 sparse/dictionary baseline

### Commit 6
实现 metrics、comparison 与 report

### Commit 7
补齐文档、测试和默认配置

---

## 27. 本阶段完成后的交接要求

Phase 3 完成后，应额外输出一份交接摘要，说明：

- 当前前端支持哪些方法
- 默认方法与默认参数是什么
- 哪些方法适合哪些场景
- 当前评估使用了哪些指标
- signal-ready 输出格式是什么
- Phase 4 / Phase 5 应如何消费这些结果
- 当前前端模块的已知局限是什么

建议存放于：

- `reports/phase3_summary.md`
  或
- `docs/phases/phase3_completion_note.md`

---

## 28. Phase 4 / Phase 5 的前置接口要求

为了让后续阶段顺利开始，Phase 3 完成后至少应保证以下接口稳定：

### 28.1 给 Phase 4 的接口
- 窗口级或时刻级 signal-ready 特征导出
- 原始 sample_id / scenario_id 映射
- 前端质量指标接口

### 28.2 给 Phase 5 的接口
- quasi-DC series 输出
- 前端配置与 quality flags
- 可与物理 baseline 对齐的时间索引

如果这些接口不稳定，则不应进入后续主模型阶段。

---

## 29. 最终执行指令（给 Codex 的摘要版）

下面这段可直接作为对 Codex 的高层执行约束摘要：

> 你正在执行 GIC 项目的 Phase 3。你的目标是建立统一、可比较、可导出的前端信号处理框架，用于从原始或含噪时序中提取 quasi-DC 成分和稳定特征。你必须先写统一 schema 和统一接口，再依次实现 raw baseline、低频 baseline、FastICA 和稀疏表示类方法，并建立统一比较与默认推荐机制。你不得实现主 GNN，不得把前端和模型强耦合，不得只输出图像而不输出标准化结果，不得让不同方法输出不同格式。

---

## 30. 结论

Phase 3 的本质不是“多做几个信号处理方法”，而是：

- 把前端做成一个真正可复用的模块层；
- 明确前端在整个项目中的位置；
- 让后续图模型与 physics-informed 模型能够消费稳定、可追踪的 signal-ready 输入。

如果 Phase 3 做得好，后续模型阶段就能把“输入质量”与“模型结构”区分开来，避免把所有问题都压给主模型。  
如果 Phase 3 做得差，后续阶段会不断在输入噪声、输出格式不统一和方法不可比较之间来回返工。

Phase 3 完成并验收后，下一步应开始：

- `phase_4_detailed_plan.md`
