# Phase 8 Detailed Plan  
## 系统整合、可视化、复现与最终固化（Detailed Execution Plan v1）

## 1. 文档元信息

- 文档名称：`phase_8_detailed_plan.md`
- 阶段名称：Phase 8 — 系统整合、可视化、复现与最终固化
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
  - `phase_7_detailed_plan.md`

本文件用于约束 Phase 8 的开发行为。  
在 Phase 8 中，核心任务是把前面阶段形成的数据层、物理层、前端层、图学习层、主模型层、KG 层和真实验证层整合成一个**可运行、可复现、可回溯、可展示、可持续维护**的最终系统版本。

---

## 2. 本阶段的核心目标

Phase 8 的唯一核心目标是：

> 将项目从“多个阶段性的研究原型与中间资产”整合为一个统一的端到端系统版本，并完成复现实验、可视化输出、最终文档固化与交付级整理。

这意味着本阶段必须解决的问题包括：

- 如何把各阶段模块通过稳定接口真正串联起来
- 如何提供一条从输入到输出的端到端运行路径
- 如何让别人能够复现实验结果而不依赖隐性知识
- 如何将最终结果以图、表、案例和文档形式统一组织
- 如何把系统的能力与限制清晰交付出来
- 如何确保项目在未来仍可维护，而不是只停留在当前会话记忆中

---

## 3. 非目标（本阶段明确不做的事情）

为了防止 Phase 8 失控，本阶段明确**不做**以下内容：

### 3.1 不再引入新的核心研究方向

本阶段不新增：

- 全新主模型结构
- 全新 KG 路径
- 全新物理求解路线
- 全新真实验证框架

本阶段的重点是整合、固化、清理和交付，而不是继续扩展研究范围。

### 3.2 不做生产级在线服务平台

本阶段不实现：

- 在线推理服务
- Web 应用或多用户系统
- 实时流式监控平台
- 生产级 API 服务

如果需要交互演示，也应保持在轻量可控范围。

### 3.3 不做无边界重构

本阶段可以做必要的清理和小幅重构，但不能因为“想更优雅”而推翻各阶段稳定接口。

### 3.4 不重写前面阶段的实验结论

本阶段可以整理、统一、校验前面结果，但不应借系统整合之机悄悄改变前面已经文档化的结论、指标或边界。

### 3.5 不忽略失败与限制

本阶段不能只做“包装层”。  
必须同时固化：

- 系统能力
- 当前限制
- 已知失败模式
- 不适用场景

---

## 4. 本阶段完成后应具备的能力

Phase 8 完成后，项目至少应具备以下能力：

1. 能通过统一入口完成端到端运行；
2. 能从数据准备一直跑到预测输出和评估报告；
3. 能生成可视化结果与关键案例展示；
4. 能复现一条标准实验路径；
5. 能让新的开发者或评审者通过文档理解系统结构；
6. 能稳定引用默认模型、默认配置、默认数据版本；
7. 能作为后续论文、报告、演示或继续开发的正式基线。

---

## 5. 本阶段总体策略

Phase 8 必须采用“**先整合接口，再固化流程，再整理输出，最后清理收口**”的策略。

建议推进顺序如下：

1. 先冻结各阶段默认版本与接口
2. 再定义端到端 pipeline
3. 再实现统一运行入口
4. 再整理可视化与案例输出
5. 再完成复现实验脚本与运行说明
6. 再清理代码与文档
7. 最后形成最终交付版结构

不要一开始就做展示，而底层接口仍然漂移。

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
- `phase_7_detailed_plan.md`

## 6.2 前置阶段的默认输出

必须优先整合以下“默认版本”而不是任意版本：

- Phase 1 默认数据 schema / registry
- Phase 2 默认物理 solver 与标签格式
- Phase 3 默认前端方案
- Phase 4 最佳 baseline 图模型
- Phase 5 默认主模型
- Phase 6 默认 KG 增强方案（若确认纳入）
- Phase 7 默认真实验证事件集合与评估配置

## 6.3 可被整合的资产类型

至少包括：

1. 数据 schema 与目录结构
2. 物理标签与场景生成
3. signal-ready 与 graph-ready 数据
4. baseline 模型与主模型
5. KG 数据与查询层
6. 真实评估结果
7. 各阶段文档与 decision records

---

## 7. 本阶段输出

Phase 8 的输出应是**统一系统版本与最终交付资产**。

至少包括：

- 端到端 pipeline
- 最终运行入口
- 最终默认配置集
- 标准复现实验脚本
- 可视化产物
- 案例展示
- 最终 README / 运行手册 / 结构文档
- 最终限制说明
- 交付版结果目录

---

## 8. 端到端 pipeline 设计要求

本阶段最核心的对象不是单个模块，而是端到端流程。

## 8.1 最低需要定义的 pipeline

至少应定义一条标准 pipeline：

1. 读取数据与配置
2. 准备/加载 physics-ready 数据
3. 准备/加载 signal-ready 数据
4. 准备/加载 graph-ready 数据
5. 加载默认主模型与可选 KG 增强
6. 运行预测
7. 运行评估
8. 导出可视化与报告

## 8.2 pipeline 类型建议

至少组织成三类：

### 8.2.1 Reproduction Pipeline
用于复现默认实验结果。

### 8.2.2 Evaluation Pipeline
用于对单个模型版本做评估与案例输出。

### 8.2.3 Demonstration Pipeline
用于展示系统从输入到输出的完整路径。

## 8.3 本阶段默认主 pipeline

建议优先固化：

- **Reproduction Pipeline**
- **Evaluation Pipeline**

Demonstration Pipeline 可复用前两者的子集。

---

## 9. 默认版本冻结要求

本阶段必须冻结一组默认版本，否则系统无法真正固化。

## 9.1 必须冻结的对象

至少包括：

- 数据版本
- 物理标签版本
- signal-ready 版本
- graph-ready 版本
- Phase 5 默认主模型版本
- Phase 6 默认 KG 配置（若保留）
- Phase 7 默认真实验证配置

## 9.2 冻结方式要求

至少通过以下形式之一记录：

- manifest
- version yaml
- release note
- final config bundle

## 9.3 默认版本命名建议

建议采用统一命名，例如：

- `v1_default_data`
- `v1_default_physics`
- `v1_default_signal`
- `v1_default_graph`
- `v1_default_main_model`
- `v1_default_kg`
- `v1_default_real_eval`

---

## 10. 统一运行入口要求

本阶段必须有统一 CLI 或脚本入口，而不是要求用户手动按阶段调用大量命令。

## 10.1 最低需要支持的统一命令

至少支持：

- `run-pipeline`
- `run-reproduction`
- `run-final-eval`
- `build-final-report`
- `build-final-visuals`

## 10.2 命令要求

- 统一使用默认配置或配置 bundle
- 支持明确切换是否启用 KG
- 支持指定输出目录
- 支持 dry-run / check mode
- 出错时能指出是哪个阶段接口失败

## 10.3 错误分类要求

至少区分：

- data missing
- schema mismatch
- physics artifact missing
- signal artifact missing
- graph artifact missing
- checkpoint missing
- eval config invalid
- visualization export failed

---

## 11. 系统接口冻结要求

Phase 8 必须对核心接口做最终收口。  
否则最终系统仍然只是“很多可运行碎片”。

## 11.1 必须冻结的接口

至少包括：

1. 数据加载接口
2. 物理标签读取接口
3. signal-ready 读取接口
4. graph-ready 读取接口
5. 主模型加载接口
6. KG 特征加载接口
7. 评估结果输出接口
8. 可视化输出接口

## 11.2 接口冻结方式

建议：

- 明确 Python API
- 明确 CLI 命令
- 明确输入/输出 schema
- 在文档中单独列出

## 11.3 禁止事项

禁止：

- 最终系统仍依赖 notebook 内手工步骤
- 不同模块私自更改接口
- 需要“知道作者的默认习惯”才能运行系统

---

## 12. 可视化输出要求

本阶段必须把结果可视化输出正式化。  
这不是附属任务，而是最终交付的重要组成部分。

## 12.1 至少需要支持的可视化类型

至少包括：

### 12.1.1 网络级 GIC 态势图
展示：

- 设备级或节点级预测强度
- 热点区域
- 可选地对比 baseline / main model

### 12.1.2 时间序列对比图
展示：

- 真实/参考趋势 vs 预测
- 峰值时段
- 前端处理效果（如适用）

### 12.1.3 模型比较图
展示：

- Phase 4 baseline vs Phase 5 主模型 vs Phase 6 KG 增强
- 不同稀疏率或不同事件分组

### 12.1.4 失败案例图
展示：

- 失败事件
- 偏差位置
- 可能原因说明

### 12.1.5 KG 解释图（如保留 KG）
展示：

- 关键设备的关系邻域
- assumptions / quality / observed relations

## 12.2 可视化输出要求

- 图要能稳定导出到文件
- 图与数据一一对应
- 图的生成不依赖 notebook 手动处理
- 图标题、图例、时间范围、模型版本等 metadata 要清楚

---

## 13. 最终报告与案例集要求

本阶段不能只交付代码。  
必须交付统一结果文档与案例资产。

## 13.1 至少需要形成的报告类型

至少包括：

1. 最终系统概述报告
2. 默认实验复现报告
3. 真实验证摘要报告
4. 失败案例与限制说明
5. KG 作用摘要（如保留 KG）

## 13.2 案例集要求

至少整理以下案例：

- 一个标准成功案例
- 一个高稀疏率案例
- 一个真实事件案例
- 一个失败或边界案例
- 一个 KG 解释案例（如适用）

## 13.3 案例集目标

案例集必须服务于：

- 研究展示
- 方法解释
- 后续汇报
- 项目交接

---

## 14. 复现要求

Phase 8 的核心之一是复现。  
必须保证项目中至少有一条标准路径可以被他人复现。

## 14.1 最低复现目标

至少保证：

- 新环境安装依赖
- 使用默认配置
- 运行一条标准 pipeline
- 得到可核对的关键输出

## 14.2 至少应复现的内容

至少包括：

1. 一个 graph baseline 结果
2. 一个默认主模型结果
3. 一组真实事件评估摘要
4. 一组可视化输出

## 14.3 复现脚本要求

建议提供：

- 单命令复现脚本
- 分阶段复现脚本
- 结果校验说明

---

## 15. 代码清理与结构整理要求

Phase 8 必须做代码清理，否则最终系统难以维护。

## 15.1 必须做的清理动作

至少包括：

- 删除废弃脚本
- 合并重复工具函数
- 清理无用配置
- 清理临时调试输出
- 整理 import 路径
- 检查文档与代码是否一致

## 15.2 可选重构动作

可选做小幅重构，但必须满足：

- 不改变稳定接口
- 不影响默认复现路径
- 有测试覆盖
- 有清晰 commit 记录

---

## 16. 最终文档集要求

Phase 8 必须把文档从“阶段性记录”提升为“最终可交付文档集”。

## 16.1 最低必须存在的最终文档

至少包括：

- `README.md`（最终版）
- `docs/architecture/final_system_overview.md`
- `docs/evaluation/final_results_summary.md`
- `docs/evaluation/final_limitations.md`
- `docs/reproduction/reproduction_guide.md`
- `docs/roadmap/future_extensions.md`

## 16.2 README 最终版必须覆盖的内容

至少包括：

- 项目目标
- 系统组成
- 默认运行路径
- 默认模型与默认数据版本
- 如何复现
- 关键结果
- 当前局限
- 文档索引

## 16.3 限制文档必须包含

至少包括：

- 数据限制
- 物理建模限制
- 真实验证限制
- KG 限制
- 不建议使用的场景

---

## 17. 最终配置集要求

本阶段必须把最终默认配置收束成一组清晰的 final bundle。

## 17.1 至少需要冻结的最终配置文件

建议包括：

```text
configs/final/
  final_default.yaml
  final_reproduction.yaml
  final_real_eval.yaml
  final_with_kg.yaml
  final_without_kg.yaml
```

## 17.2 配置要求

- 名称清楚
- 适用目的清楚
- 与最终文档一致
- 不再依赖阶段性临时配置

---

## 18. Phase 8 的 CLI 要求

在复用既有 CLI 结构的基础上，建议增加最终整合相关命令。

至少应支持：

- `run-final-default`
- `run-final-reproduction`
- `run-final-real-eval`
- `export-final-visuals`
- `export-final-casebook`
- `export-final-doc-summary`

### 18.1 命令要求

- 使用最终默认配置集
- 输出目录明确
- 支持 `--with-kg` / `--without-kg`
- 支持 `--check-only`
- 必须能给出最终报告摘要

---

## 19. 文档要求

Phase 8 必须新增最终整合文档。

至少新增：

- `docs/architecture/final_system_overview.md`
- `docs/evaluation/final_results_summary.md`
- `docs/evaluation/final_limitations.md`
- `docs/reproduction/reproduction_guide.md`
- `docs/decisions/0008_phase8_final_integration.md`

## 19.1 `final_system_overview.md` 应包含

- 系统模块总览
- 端到端 pipeline
- 默认版本引用
- 数据流与接口流
- 可视化与输出说明

## 19.2 `final_results_summary.md` 应包含

- baseline vs main model
- KG 是否纳入默认路径
- 真实验证主要结论
- 成功案例与失败案例摘要

## 19.3 `final_limitations.md` 应包含

- 当前系统不解决什么
- 当前系统在哪些条件下不可靠
- 后续最重要改进方向

## 19.4 决策记录应包含

至少记录：

- 为什么最终默认路径这样确定
- 是否将 KG 纳入最终默认流程
- 为什么保留或移除某些阶段性产物
- 为什么当前复现实验选这条路径

---

## 20. 推荐文件级实现清单

以下是 Phase 8 推荐实现的文件级清单。Codex 应以此为主要目标。

```text
configs/
  final/
    final_default.yaml
    final_reproduction.yaml
    final_real_eval.yaml
    final_with_kg.yaml
    final_without_kg.yaml

docs/
  architecture/
    final_system_overview.md
  evaluation/
    final_results_summary.md
    final_limitations.md
  reproduction/
    reproduction_guide.md
  roadmap/
    future_extensions.md
  decisions/
    0008_phase8_final_integration.md

src/
  gic/
    pipelines/
      __init__.py
      final_pipeline.py
      reproduction.py
      evaluation.py
      visualization.py
      casebook.py
    visualization/
      final_figures.py
      network_maps.py
      timelines.py
      model_comparison.py
      failure_cases.py
      kg_views.py
    reports/
      final_summary.py
      final_exports.py

tests/
  test_final_pipeline.py
  test_reproduction_pipeline.py
  test_final_configs.py
  test_final_visualization_exports.py
```

说明：

- 不要求新建复杂系统框架
- 但 `final_pipeline.py`、`reproduction.py`、`evaluation.py`、`final_figures.py` 和 `final_summary.py` 是本阶段关键文件

---

## 21. Codex 在本阶段的实现顺序要求

Codex 必须按以下顺序推进，不允许先做展示再补复现链路。

### Step 1：冻结默认版本与最终配置集

先确定：

- 默认数据版本
- 默认主模型版本
- 默认 KG 版本（如保留）
- 默认真实评估版本

### Step 2：实现统一 final pipeline

先打通：

- 输入加载
- 模型加载
- 预测
- 评估
- 导出

### Step 3：实现 reproduction pipeline

确保：

- 能单命令复现一条标准实验路径
- 能导出关键结果

### Step 4：实现最终可视化与案例导出

至少导出：

- 网络级态势图
- 时间序列比较图
- 模型对比图
- 失败案例图
- KG 解释图（如启用）

### Step 5：整理最终文档与限制说明

完成：

- 最终 README
- 最终系统概述
- 复现指南
- 限制说明

### Step 6：代码清理、测试与最终阶段总结

完成：

- 清理废弃代码
- 补齐关键测试
- 输出最终阶段总结

---

## 22. Phase 8 的验收标准

只有满足以下条件，Phase 8 才算完成。

### 22.1 统一 pipeline 完成

- 有端到端运行路径
- 有统一入口
- 能完成标准输出

### 22.2 默认版本冻结完成

- 数据/模型/评估版本明确
- 默认配置集存在
- 文档与默认配置一致

### 22.3 复现路径完成

- 至少一条标准复现路径可运行
- 可导出关键结果
- 有复现文档

### 22.4 最终可视化与案例集完成

- 至少四类图表可导出
- 有成功案例与失败案例
- KG 视图（如纳入默认流程）可导出

### 22.5 最终文档完成

- 最终 README
- 最终系统概述
- 最终结果摘要
- 限制说明
- 复现指南

### 22.6 代码整理完成

- 关键废弃代码已清理
- 接口基本稳定
- 最终测试可运行

---

## 23. 最低可接受标准（Minimum Acceptable Outcome）

如果时间有限，Phase 8 至少必须达到以下底线：

1. 有统一 final pipeline
2. 有最终默认配置
3. 有一条可运行的复现路径
4. 有最基本的最终文档集
5. 有至少一组最终可视化输出
6. 有一份清楚的限制说明

如果连这个底线都达不到，则项目不能算进入“最终固化状态”。

---

## 24. 风险与回退策略

## 24.1 风险：阶段接口不稳定，整合困难

### 对策

- 先冻结默认版本
- 优先适配默认路径，而非支持所有历史变体
- 必要时增加兼容层，但不重写核心结构

## 24.2 风险：复现链路过于脆弱

### 对策

- 先保证一条最小复现路径
- 使用 final 配置 bundle
- 避免依赖隐式环境变量与手工步骤

## 24.3 风险：代码清理导致旧结果失效

### 对策

- 清理前先冻结默认产物
- 清理后保留必要的兼容测试
- 重要路径必须回归测试

## 24.4 风险：文档和代码脱节

### 对策

- 文档以 final 配置为准
- 最终运行命令必须实际测试过
- 文档中的每个关键路径都要有对应脚本或命令

## 24.5 风险：为了“展示好看”而掩盖限制

### 对策

- 最终限制文档必须单独存在
- 成功案例与失败案例同时展示
- KG 是否纳入默认流程要基于证据，而不是展示偏好

---

## 25. 明确禁止事项

Codex 在本阶段**禁止**做以下事情：

1. 不得新增全新研究方向
2. 不得重写核心模型替代前面阶段结果
3. 不得只做包装，不做复现与限制说明
4. 不得让最终系统仍依赖 notebook 手工操作
5. 不得在没有冻结默认版本的情况下宣称“最终版”
6. 不得删除失败案例与边界说明
7. 不得让 final 配置与文档描述不一致
8. 不得保留大量未说明用途的废弃脚本作为最终交付一部分
9. 不得省略最终测试与复现校验
10. 不得夸大系统已达到生产可用级

---

## 26. 建议提交粒度

建议本阶段按以下粒度逐步提交，方便回溯。

### Commit 1
冻结默认版本与 final 配置集

### Commit 2
实现 final pipeline 与 reproduction pipeline

### Commit 3
实现 final evaluation / report / visualization 导出

### Commit 4
整理最终文档集

### Commit 5
清理代码、补齐测试与输出阶段总结

---

## 27. 本阶段完成后的交接要求

Phase 8 完成后，应额外输出一份最终交接摘要，说明：

- 当前系统默认运行路径是什么
- 默认数据/模型/KG/评估版本是什么
- 如何完成标准复现
- 当前最重要结果是什么
- 当前最关键限制是什么
- 后续继续开发最建议从哪里开始
- 哪些模块最值得优先扩展

建议存放于：

- `reports/final_handoff_summary.md`
  或
- `docs/roadmap/final_handoff_summary.md`

---

## 28. 最终执行指令（给 Codex 的摘要版）

下面这段可直接作为对 Codex 的高层执行约束摘要：

> 你正在执行 GIC 项目的 Phase 8。你的目标不是新增研究内容，而是把前面所有阶段的稳定成果整合成一个统一、可复现、可展示、可维护的最终系统版本。你必须先冻结默认数据、模型、KG 和评估版本，再实现 final pipeline 与 reproduction pipeline，然后导出最终可视化、案例集和最终文档，并完成代码清理、测试和限制说明。你不得让最终系统依赖 notebook 手工步骤，不得在没有冻结默认版本的情况下宣称最终版，不得只做包装而不做复现与边界说明。

---

## 29. 结论

Phase 8 的核心不是“把项目做漂亮”，而是：

- 让项目真正从阶段性研究资产变成统一系统；
- 让结果可以被复现、解释、展示和继续维护；
- 让所有前面阶段的努力在最终交付中有清楚归宿。

如果 Phase 8 做得好，这个项目就不仅仅是一组分散的模型和脚本，而是一个有明确默认路径、明确证据边界和明确扩展方向的完整研究系统。  
如果 Phase 8 做得差，前面所有阶段即使各自完成，也会停留在“碎片化资产”的状态。

Phase 8 完成并验收后，整个项目将进入：

- 最终固化状态
- 可复现状态
- 可交付状态
- 可继续演进状态
