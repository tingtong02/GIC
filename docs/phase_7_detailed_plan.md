# Phase 7 Detailed Plan  
## 真实事件驱动验证与泛化评估（Detailed Execution Plan v1）

## 1. 文档元信息

- 文档名称：`phase_7_detailed_plan.md`
- 阶段名称：Phase 7 — 真实事件驱动验证与泛化评估
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
  - `phase_6_detailed_plan.md`

本文件用于约束 Phase 7 的开发行为。  
在 Phase 7 中，核心任务是把前面阶段建立的物理、信号、图学习和 KG 增强能力，放到**真实事件驱动、跨场景、跨稀疏率与跨扰动条件**下进行验证，形成关于模型可信度、泛化能力和适用边界的系统性结论。

---

## 2. 本阶段的核心目标

Phase 7 的唯一核心目标是：

> 在不虚构真实标签、不夸大泛化能力的前提下，基于真实 geomagnetic storm 驱动、可获得的局部真实观测和一组严格定义的泛化/鲁棒性实验，建立本项目方法在真实条件下的可信度陈述。

这意味着本阶段必须解决的问题包括：

- 如何把真实 storm 事件组织成可评估数据
- 在真实真值有限的情况下，哪些验证是有效的
- 如何做 cross-event、cross-sparsity、cross-noise、cross-topology 等泛化实验
- 如何界定模型何时可信、何时不可信
- 如何展示真实世界中的失败模式，而不是只展示成功案例
- 如何把 Phase 5 主模型和 Phase 6 KG 增强都放到同一真实评估框架下比较

---

## 3. 非目标（本阶段明确不做的事情）

为了防止 Phase 7 范围失控，本阶段明确**不做**以下内容：

### 3.1 不把有限真实观测包装成“全网真值”

本阶段严禁：

- 把局部设备观测外推成全网真实标签并当作监督真值
- 用模型输出反过来当真实验证标签
- 对真实数据做没有记录的后验修正来伪装高准确率

### 3.2 不重新设计主模型

本阶段不推翻前面阶段模型设计。  
如果真实验证暴露问题，可以记录、分析、提出改进方向，但不应在本阶段大幅度改主模型结构。

### 3.3 不把所有真实数据问题都用“补丁工程”掩盖

本阶段不应通过大量 ad hoc patch 来“勉强跑通”真实事件评估。  
需要优先记录真实数据缺口、映射误差和适用边界。

### 3.4 不做实时业务部署

本阶段不实现：

- 实时在线 storm 响应系统
- 调度建议引擎
- 生产监控平台

本阶段仍然是研究验证阶段。

### 3.5 不夸大真实世界泛化结论

本阶段不得得出超出证据范围的结论，例如：

- “模型已经适用于所有真实电网”
- “模型已可替代物理模型”
- “模型已在真实环境中达到工业可用级”

---

## 4. 本阶段完成后应具备的能力

Phase 7 完成后，项目至少应具备以下能力：

1. 能基于若干真实 storm 事件构建标准评估集；
2. 能在真实驱动下运行主模型与相关 baseline；
3. 能使用局部真实观测、趋势、峰值和排序指标进行验证；
4. 能进行跨事件、跨稀疏率、跨噪声与跨配置的泛化分析；
5. 能分析模型在真实条件下的失败模式；
6. 能形成谨慎、可信、可审阅的真实性能结论；
7. 能为最终系统整合与论文/报告写作提供真实验证依据。

---

## 5. 本阶段总体策略

Phase 7 必须采用“**真实驱动优先、验证边界清晰、结论保守可信**”的策略。

建议推进顺序如下：

1. 先固定真实事件评估对象与可用验证信号
2. 再建立事件级数据组织与评估集
3. 再运行 baseline / 主模型 / KG 增强模型
4. 再做分层次验证：趋势、峰值、排序、热点
5. 再做泛化和鲁棒性实验
6. 最后做失败案例分析与可信度总结

不要一开始就追求一个“综合分数”，而忽略真实验证的证据边界。

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
- `phase_6_detailed_plan.md`

## 6.2 前置阶段提供的关键对象

必须复用：

- Phase 1 的数据 registry、事件清单和数据 schema
- Phase 2 的物理 baseline 与场景生成逻辑
- Phase 3 的 signal-ready 特征导出能力
- Phase 4 的 baseline 模型和 graph-ready 数据
- Phase 5 的主模型和统一评估脚手架
- Phase 6 的 KG 增强开关与结果接口

## 6.3 真实验证输入来源

至少可包括以下类型：

1. 真实 geomagnetic storm 驱动
2. 真实 geomagnetic station 时序
3. 可获得的局部 GIC 观测
4. 真实或半真实 geoelectric 参考输入
5. 事件级索引、时间范围和元数据

---

## 7. 本阶段输出

Phase 7 的输出应是**真实验证与泛化评估资产**。

至少包括：

- 真实事件评估集
- 事件级 manifest
- 真实驱动评估脚本
- 泛化实验结果
- 鲁棒性测试结果
- 失败案例分析
- 可信度与适用边界总结
- 真实验证阶段报告

---

## 8. 真实事件评估集设计要求

本阶段必须先固定“评估集是什么”。  
不能边跑边换事件。

## 8.1 最低需要定义的对象

至少应定义：

1. `RealEventRecord`
2. `RealEventDataset`
3. `RealEventManifest`
4. `ValidationEvidenceBundle`
5. `GeneralizationSplitConfig`
6. `RobustnessScenarioConfig`

## 8.2 `RealEventRecord` 最低字段建议

- `event_id`
- `event_name`
- `time_range`
- `data_sources`
- `available_geomagnetic_inputs`
- `available_geoelectric_inputs`
- `available_gic_observations`
- `quality_notes`
- `region`
- `status`

## 8.3 `ValidationEvidenceBundle` 最低字段建议

- `event_id`
- `available_truth_types`
- `direct_measurements`
- `indirect_references`
- `trend_reference`
- `peak_reference`
- `ranking_reference`
- `limitations`

说明：

- 真实验证的证据层次必须被显式编码
- 不能把“有真实点观测”和“只有趋势参考”混在一起当成同一层证据

---

## 9. 真实验证证据层级要求

这是本阶段最重要的科学约束之一。  
必须区分真实验证的证据强度。

## 9.1 证据等级建议

建议至少分为四级：

### Level 1：直接设备级测量
例如：

- 某变压器中性点 GIC 实测

这是最强证据。

### Level 2：局部区域或少量设备对照
例如：

- 若干设备观测的趋势或峰值

这是中等强证据。

### Level 3：事件级趋势或峰值对照
例如：

- 模型峰值时段与真实事件扰动高峰是否对齐

这是弱到中等证据。

### Level 4：仅物理合理性与事件一致性
例如：

- 风险区域与已知事件背景是否大致一致

这是最弱证据，只能做支持性说明。

## 9.2 必须记录证据等级

所有真实验证结果都必须带上证据等级。  
禁止把 Level 3/4 的支持性一致性表述成“准确率”。

---

## 10. 真实事件选择要求

本阶段不应任意挑选事件。  
必须定义一套清楚的选择规则。

## 10.1 事件选择标准建议

至少满足以下部分条件：

- 事件具有明确时间范围
- 有足够完整的 geomagnetic 驱动
- 至少有一类可用验证证据
- 与项目目标区域或测试系统映射有意义
- 数据质量可接受

## 10.2 事件集合结构建议

至少组织成三类：

1. **主验证事件**
   - 数据最完整
   - 用于详细分析和展示

2. **泛化事件**
   - 用于 cross-event 评估
   - 不一定有最完整观测

3. **边界/困难事件**
   - 数据质量较差或观测更稀疏
   - 用于测试鲁棒性与失败模式

## 10.3 事件冻结原则

一旦本阶段主验证事件集合确定，后续实验必须优先在该集合上复现。  
除非有明确文档记录，不应频繁更换事件集合。

---

## 11. 真实驱动输入组织要求

本阶段必须正式组织真实 storm 驱动，而不是临时读几段时序。

## 11.1 最低支持的真实驱动输入

至少支持：

- geomagnetic station series
- 事件级时间窗口
- 对齐后的时序驱动输入

## 11.2 可选支持的辅助输入

可选支持：

- geoelectric reference products
- storm index / event metadata
- 区域 conductivity 参考信息

## 11.3 输入组织要求

必须明确：

- 数据来源
- 时间粒度
- 采样间隔
- 缺失值情况
- 对齐策略
- 与模型输入时间窗口的映射方式

---

## 12. 模型运行要求

本阶段必须在真实驱动下运行至少以下模型集合。

## 12.1 baseline 集合

至少包括：

- Phase 4 的最佳 graph baseline
- Phase 5 的默认主模型

## 12.2 KG 比较集合

如果 Phase 6 已完成默认 KG 增强，则至少还应包括：

- Phase 5 默认主模型 + KG 增强

## 12.3 可选集合

可选加入：

- no-physics ablation
- no-temporal ablation
- regression-only ablation

但至少要保证主 baseline 和主模型可以在真实事件上对比。

---

## 13. 真实验证指标要求

本阶段不能只延用 synthetic 场景下的平均误差。  
必须建立更适合真实证据边界的指标体系。

## 13.1 数值对照指标（当有直接测量时）

至少支持：

- MAE
- RMSE
- correlation
- peak error
- lag / peak timing error

## 13.2 趋势一致性指标

当只有局部或弱真值时，至少支持：

- Pearson / Spearman correlation
- trend agreement
- up/down consistency
- peak coincidence rate

## 13.3 风险识别指标

若有热点或风险参考，至少支持：

- hotspot recall / precision（如可定义）
- Top-k overlap
- ranking correlation

## 13.4 可信度相关指标

至少支持：

- high-uncertainty case coverage（如有 uncertainty head）
- quality-flag grouped performance
- evidence-level grouped reporting

## 13.5 指标约束

- 所有指标必须注明适用证据等级
- 不得把不同证据等级混合成一个看似精确的总分

---

## 14. 泛化评估要求

Phase 7 的关键之一是泛化。  
必须有正式泛化实验，而不是只报告主验证事件结果。

## 14.1 必做泛化维度

至少完成以下一种或多种：

### 14.1.1 Cross-event Generalization
训练 / 调参不使用某事件，在该事件上测试。

### 14.1.2 Cross-sparsity Generalization
在某稀疏率训练，在更高或更低稀疏率测试。

### 14.1.3 Cross-noise Generalization
在一种噪声条件训练，在另一种噪声条件下测试。

### 14.1.4 Cross-case / Cross-topology Generalization
在一个测试系统或 case 上训练，在另一 case 上测试。

## 14.2 本阶段建议最低要求

建议至少完成：

- cross-event
- cross-sparsity
- cross-noise

cross-topology 如果条件允许则加入，但不强制作为最低要求。

---

## 15. 鲁棒性评估要求

除了泛化，本阶段还必须看输入异常与系统脆弱性。

## 15.1 至少需要测试的鲁棒性场景

至少包括以下一类或多类：

1. 传感器失效
2. 观测缺失增加
3. 时间对齐偏移
4. 输入噪声增强
5. 物理 baseline 误差扩大
6. KG 特征缺失（若启用 KG）

## 15.2 鲁棒性输出要求

必须说明：

- 哪些输入扰动对性能影响最大
- 模型对哪些类型缺失最敏感
- KG 或物理先验是否在某些扰动下提供了额外鲁棒性

---

## 16. 失败案例分析要求

本阶段必须明确做失败案例分析。  
这是可信度陈述的核心部分。

## 16.1 最低需要分析的失败类型

至少分析以下一类或多类：

- 峰值错位
- 高风险设备漏检
- 物理 baseline 与模型残差同时失真
- 稀疏率过高导致不稳定
- KG 增强无效甚至退化
- 真实驱动与测试系统映射误差过大

## 16.2 每个失败案例至少应说明

- 事件与样本背景
- 使用了哪些输入
- 证据等级
- 哪个模块最可能导致失败
- 未来应在哪个阶段或方向修复

---

## 17. 可信度与适用边界陈述要求

这是本阶段最终最重要的输出之一。  
必须形成一份明确、保守、分层次的结论。

## 17.1 至少应回答的问题

- 本方法在哪些条件下表现最好
- 本方法在哪些条件下只能做趋势参考
- 本方法在哪些条件下不应被过度信任
- 物理先验和 KG 在真实条件下各自贡献了什么
- 当前系统更像“研究原型”还是“接近工程可用”

## 17.2 陈述要求

- 必须以证据等级为基础
- 必须区分“已验证”与“合理推断”
- 必须明确列出局限，不允许只写优势

---

## 18. Phase 7 的 CLI 要求

在复用既有 CLI 结构的基础上，建议增加真实验证相关命令。

至少应支持：

- `real-build-event-set`
- `real-run-eval`
- `real-run-generalization`
- `real-run-robustness`
- `real-build-case-studies`
- `real-build-report`

### 18.1 命令要求

- 必须使用统一配置系统
- 必须能指定事件集合、证据等级筛选和模型版本
- 错误信息必须区分：
  - 真实事件数据缺失
  - 时间对齐失败
  - 观测证据不足
  - 模型 checkpoint 缺失
  - 评估配置与证据等级不匹配

---

## 19. 配置文件要求

Phase 7 必须新增专用配置文件，例如：

```text
configs/phase7/
  phase7_dev.yaml
  events/
    main_event_set.yaml
    generalization_set.yaml
  eval/
    real_eval_default.yaml
    robustness_eval.yaml
```

## 19.1 配置域建议

至少包括：

```yaml
stage:
  current: phase7

real_eval:
  event_set: main_event_set
  include_phase4_best: true
  include_phase5_default: true
  include_phase6_kg_default: true

  evidence:
    min_level: 2
    report_all_levels: true

  metrics:
    numeric: true
    trend: true
    ranking: true
    uncertainty: true

generalization:
  run_cross_event: true
  run_cross_sparsity: true
  run_cross_noise: true
  run_cross_topology: false

robustness:
  sensor_dropout: true
  timing_shift: true
  noise_stress: true
```

---

## 20. 文档要求

Phase 7 必须新增一组真实验证文档，明确记录证据边界与泛化结论。

至少新增：

- `docs/evaluation/real_event_validation_overview.md`
- `docs/evaluation/evidence_levels.md`
- `docs/decisions/0007_phase7_real_validation_design.md`

## 20.1 `real_event_validation_overview.md` 应包含

- 真实验证目标
- 事件集合
- 使用的模型集合
- 指标体系
- 主要结果
- 失败案例
- 可信度结论

## 20.2 `evidence_levels.md` 应包含

- 证据等级定义
- 各等级适合使用的指标
- 不能做的结论类型
- 报告写作规范

## 20.3 决策记录应包含

至少记录：

- 为什么采用当前事件集合
- 为什么采用当前证据等级体系
- 为什么某些真实事件只做趋势验证而不做数值验证
- 为什么当前泛化维度这样选择

---

## 21. 推荐文件级实现清单

以下是 Phase 7 推荐实现的文件级清单。Codex 应以此为主要目标。

```text
configs/
  phase7/
    phase7_dev.yaml
    events/
      main_event_set.yaml
      generalization_set.yaml
    eval/
      real_eval_default.yaml
      robustness_eval.yaml

docs/
  evaluation/
    real_event_validation_overview.md
    evidence_levels.md
  decisions/
    0007_phase7_real_validation_design.md

src/
  gic/
    eval/
      real_events.py
      evidence.py
      generalization.py
      robustness.py
      case_studies.py
      trustworthiness.py
      reports.py

tests/
  test_real_event_schema.py
  test_evidence_levels.py
  test_generalization_splits.py
  test_robustness_configs.py
  test_real_eval_pipeline.py
```

说明：

- 不要求本阶段新增很多模型代码
- 重点在于真实评估管线、证据等级机制和报告输出
- `real_events.py`、`evidence.py`、`generalization.py`、`robustness.py` 和 `trustworthiness.py` 是本阶段关键文件

---

## 22. Codex 在本阶段的实现顺序要求

Codex 必须按以下顺序推进，不允许先跑大量实验再补证据框架。

### Step 1：固定真实事件 schema、事件集合与证据等级体系

先实现：

- `RealEventRecord`
- `ValidationEvidenceBundle`
- 事件 manifest
- 证据等级定义

### Step 2：实现真实驱动评估集构建

确保：

- 事件时序与输入可对齐
- 事件样本可导出
- 证据 metadata 完整

### Step 3：实现主模型/基线真实评估流程

至少打通：

- Phase 4 最佳 baseline
- Phase 5 默认主模型
- Phase 6 KG 默认增强（若可用）

### Step 4：实现泛化与鲁棒性实验脚手架

先覆盖：

- cross-event
- cross-sparsity
- cross-noise
- sensor dropout / timing shift 等鲁棒性场景

### Step 5：实现失败案例、可信度报告与边界总结

至少输出：

- 失败样本集
- 证据等级分组报告
- 可信度与适用边界摘要

### Step 6：补齐文档与测试

完成：

- 真实验证文档
- 决策记录
- 核心测试

---

## 23. Phase 7 的验收标准

只有满足以下条件，Phase 7 才算完成。

### 23.1 真实事件评估集完成

- 有冻结的事件集合
- 有事件 manifest
- 有证据等级标注

### 23.2 真实评估流程完成

- 至少能在真实驱动下运行 baseline 与主模型
- 能输出真实验证结果
- 能按证据等级分层报告

### 23.3 泛化与鲁棒性评估完成

- 至少完成 cross-event、cross-sparsity、cross-noise 中的主要实验
- 至少完成一组鲁棒性测试

### 23.4 失败案例分析完成

- 至少有一组正式失败案例
- 能说明失败原因和边界

### 23.5 可信度陈述完成

- 有独立结论文档或报告段落
- 明确列出适用边界与限制

### 23.6 文档完成

- 真实验证概述文档存在
- 证据等级文档存在
- 决策记录存在

---

## 24. 最低可接受标准（Minimum Acceptable Outcome）

如果时间有限，Phase 7 至少必须达到以下底线：

1. 有一个真实事件评估集
2. 有证据等级体系
3. 能在真实驱动下比较 baseline 与主模型
4. 能完成至少一组 cross-event 或 cross-sparsity 泛化实验
5. 能输出至少一个失败案例分析
6. 能给出一份保守可信的真实性能结论

如果连这个底线都达不到，则 Phase 7 不能结束。

---

## 25. 风险与回退策略

## 25.1 风险：真实标签严重不足

### 对策

- 用证据等级分层报告
- 不强行做伪精确数值结论
- 强调趋势、峰值、排序和事件一致性验证

## 25.2 风险：真实驱动与测试系统映射误差过大

### 对策

- 显式记录映射假设
- 在失败案例中单独分析映射误差
- 不把该类误差掩盖为模型问题或成功案例

## 25.3 风险：不同事件数据质量差异很大

### 对策

- 事件质量 metadata 必须完整
- 报告必须分事件、分等级展示
- 不把所有事件混成一个总分

## 25.4 风险：KG 增强在真实场景下无收益

### 对策

- 如实报告
- 分析是数据不足、关系设计不合理，还是任务本身不需要 KG
- 不强行保留 KG 为默认路径

## 25.5 风险：结论写得过满

### 对策

- 强制写“适用边界”和“当前不支持的结论”
- 强制保留失败案例
- 只对证据支持的范围发言

---

## 26. 明确禁止事项

Codex 在本阶段**禁止**做以下事情：

1. 不得把局部真实观测包装成全网真值
2. 不得把弱证据等级结论表述成高精度验证
3. 不得为通过真实验证而大幅度临时重写模型
4. 不得删除失败案例或只保留成功事件
5. 不得混淆不同证据等级的指标
6. 不得省略事件质量与映射假设记录
7. 不得用模型输出反向充当真实标签
8. 不得只报告综合平均分，不做分事件分析
9. 不得夸大工程可用性结论
10. 不得省略文档、测试与边界总结

---

## 27. 建议提交粒度

建议本阶段按以下粒度逐步提交，方便回溯。

### Commit 1
建立真实事件 schema、事件集合配置和证据等级框架

### Commit 2
实现真实驱动评估集构建与 manifest

### Commit 3
实现 baseline / 主模型真实评估流程

### Commit 4
实现泛化与鲁棒性评估脚手架

### Commit 5
实现失败案例和可信度报告

### Commit 6
补齐文档、测试与阶段总结

---

## 28. 本阶段完成后的交接要求

Phase 7 完成后，应额外输出一份交接摘要，说明：

- 当前真实事件集合包含哪些事件
- 当前证据等级体系如何定义
- baseline 与主模型在真实场景下的主要结论是什么
- 哪些场景支持较强结论，哪些只支持弱结论
- 当前最主要的失败模式是什么
- KG 在真实场景下是否带来实际帮助
- 当前系统距离“工程可用”还有哪些缺口

建议存放于：

- `reports/phase7_summary.md`
  或
- `docs/phases/phase7_completion_note.md`

---

## 29. Phase 8 的前置接口要求

为了让后续阶段顺利开始，Phase 7 完成后至少应保证以下接口稳定：

- 真实事件 manifest
- 证据等级与结果分组接口
- 泛化/鲁棒性评估接口
- baseline / 主模型 / KG 增强结果统一导出接口
- 失败案例导出接口
- 可信度结论摘要接口

如果这些接口不稳定，则不应进入 Phase 8。

---

## 30. 最终执行指令（给 Codex 的摘要版）

下面这段可直接作为对 Codex 的高层执行约束摘要：

> 你正在执行 GIC 项目的 Phase 7。你的目标是在真实 geomagnetic storm 驱动和有限真实观测证据下，建立一个严格分层、证据边界清楚的真实验证与泛化评估体系。你必须先定义真实事件集合和证据等级，再运行 baseline、主模型和 KG 增强模型，随后进行 cross-event、cross-sparsity、cross-noise 以及鲁棒性实验，并输出失败案例和可信度结论。你不得把局部观测包装成全网真值，不得混淆不同证据等级，不得为了通过真实验证而临时重写模型，不得夸大工程可用性结论。

---

## 31. 结论

Phase 7 的核心不是“证明模型已经在真实世界上完美工作”，而是：

- 给出经得住审查的真实验证证据；
- 明确模型的泛化能力与鲁棒性边界；
- 形成可信的成功案例与失败案例；
- 让最终系统与最终文档都建立在诚实、分层、可追踪的真实性能陈述之上。

如果 Phase 7 做得好，项目就不再只是一个 synthetic benchmark 原型，而是一个具有真实世界可信度基础的研究系统；  
如果 Phase 7 做得差，前面所有方法学设计都很难支撑有说服力的最终交付。

Phase 7 完成并验收后，下一步应开始：

- `phase_8_detailed_plan.md`
