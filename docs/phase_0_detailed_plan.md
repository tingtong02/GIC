# Phase 0 Detailed Plan  
## 项目基线固化与工程骨架初始化（Detailed Execution Plan v1）

## 1. 文档元信息

- 文档名称：`phase_0_detailed_plan.md`
- 阶段名称：Phase 0 — 项目基线固化与工程骨架初始化
- 版本：v1
- 文档角色：**直接执行计划**
- 执行对象：Codex / 开发者
- 上位参考文档：
  - `GIC_project_planning_and_technical_route_v1.md`
  - `GIC_project_phase_roadmap_v1.md`

本文件用于约束 Phase 0 的开发行为。  
在 Phase 0 中，**禁止提前实现核心算法**；本阶段只负责建立后续所有阶段都要遵守的工程基础。

---

## 2. 本阶段的核心目标

Phase 0 的唯一目标是：

> 建立一个稳定、可维护、可扩展、可复现实验的项目工程骨架，使后续 Phase 1–Phase 8 能在统一规范下推进。

这意味着本阶段的输出不是“模型效果”，而是以下几类基础设施：

- 统一仓库目录结构
- 统一配置体系
- 统一命令行入口
- 统一日志与 artifacts 保存约定
- 统一测试与代码质量工具
- 统一文档索引与阶段文档组织方式
- 统一数据/模型/评估模块的预留接口骨架

---

## 3. 非目标（本阶段明确不做的事情）

为防止 Phase 0 失控扩张，本阶段明确**不做**以下内容：

### 3.1 不实现任何完整算法功能

本阶段不实现：

- GIC forward solver
- FastICA / 稀疏表示去噪
- GNN / Temporal GNN / Hetero-GNN
- KG 构建与推理
- 完整训练循环
- 完整评估逻辑

### 3.2 不接入复杂真实数据源

本阶段可以为数据目录、元数据注册和接口留出位置，但**不要求**：

- 实现 NOAA / SuperMAG / INTERMAGNET 完整下载器
- 完成真实数据解析
- 对接任何在线 API
- 完成测试系统转换

### 3.3 不做实验结果追求

本阶段不以任何模型指标为目标。  
只要求项目基础设施可以支撑未来实验。

### 3.4 不做重型 UI 或演示系统

不做：

- Web UI
- Dashboard
- 交互式前端
- 在线可视化系统

### 3.5 不做大规模自动化

本阶段不做复杂 workflow orchestration，不做集群调度，不做多机训练管理。

---

## 4. 本阶段完成后应具备的能力

Phase 0 完成后，项目至少应具备以下能力：

1. 可以在新机器上完成环境安装；
2. 可以通过统一命令行入口启动一个最小运行任务；
3. 可以读取 YAML 配置并输出规范化日志；
4. 可以生成唯一 run_id；
5. 可以将配置快照、日志和产出文件写入标准目录；
6. 可以运行基础测试；
7. 可以保证后续各模块在统一骨架下追加开发；
8. 可以让 Codex 明确知道应该把什么代码写到哪里。

---

## 5. 本阶段总体策略

Phase 0 应采用“**骨架优先、接口优先、约束优先**”的方式推进。

执行顺序建议如下：

1. 固定仓库目录与文件命名规范
2. 固定 Python 包结构与导入边界
3. 固定配置系统
4. 固定 CLI 入口
5. 固定日志与运行目录机制
6. 固定测试与代码质量工具
7. 固定文档目录与模板
8. 增加最小演示流程（dry run）

其中每一步都必须保持：

- 代码量尽量小
- 可读性优先
- 未来扩展明确
- 不引入与当前阶段无关的复杂依赖

---

## 6. 本阶段输入

本阶段输入主要是“规划约束”，而不是实际训练数据。

### 6.1 必须参考的输入

- `GIC_project_planning_and_technical_route_v1.md`
- `GIC_project_phase_roadmap_v1.md`
- 当前阶段文档 `phase_0_detailed_plan.md`

### 6.2 可以存在但不强依赖的输入

- 初始空仓库
- 本地开发环境
- Docker 开发环境（可选）
- 少量占位配置文件
- 少量占位测试数据

---

## 7. 本阶段输出

Phase 0 的输出应是一个**可运行的工程仓库基础版本**。

至少应包含：

- 目录结构
- 基础 README
- 配置模板
- 最小 CLI
- 统一运行目录管理
- 基础 logging 模块
- 占位模块包结构
- 基础测试
- 文档骨架
- 项目开发规则说明

---

## 8. 仓库目录设计要求

以下目录和文件是**必须实现**的最小集合。

## 8.1 顶层目录

```text
project_root/
├── README.md
├── pyproject.toml
├── .gitignore
├── .editorconfig
├── configs/
├── data/
├── docs/
├── scripts/
├── src/
├── tests/
├── artifacts/
├── logs/
├── reports/
└── notebooks/
```

### 8.1.1 目录职责约束

- `configs/`：所有 YAML 配置文件
- `data/`：本地数据入口，分 raw / interim / processed
- `docs/`：所有项目文档与阶段计划
- `scripts/`：轻量命令脚本与辅助运行入口
- `src/`：主 Python 源码
- `tests/`：测试代码
- `artifacts/`：模型文件、配置快照、图表等运行产物
- `logs/`：日志
- `reports/`：阶段性分析报告与实验汇总
- `notebooks/`：探索性分析，非主流程代码

## 8.2 `data/` 目录结构

```text
data/
├── raw/
├── interim/
├── processed/
└── registry/
```

说明：

- `raw/`：未经修改的原始文件
- `interim/`：清洗后但尚未成为标准训练格式的中间文件
- `processed/`：标准训练/评估格式数据
- `registry/`：数据注册表、元数据说明

## 8.3 `docs/` 目录结构

```text
docs/
├── roadmap/
├── phases/
├── data/
├── models/
├── evaluation/
├── decisions/
└── templates/
```

说明：

- `roadmap/`：总体路线图
- `phases/`：每个阶段的详细计划
- `data/`：数据说明
- `models/`：模型设计说明
- `evaluation/`：评估方法
- `decisions/`：关键工程决策记录
- `templates/`：文档模板

## 8.4 `src/` 目录结构

```text
src/
└── gic/
    ├── __init__.py
    ├── cli/
    ├── config/
    ├── data/
    ├── signal/
    ├── physics/
    ├── graph/
    ├── models/
    ├── kg/
    ├── eval/
    ├── visualization/
    └── utils/
```

说明：

- 包名建议固定为 `gic`
- 后续阶段所有代码都必须收敛到该包内
- 不允许未来出现多个平行主包

---

## 9. 文件命名与模块组织规则

## 9.1 命名规则

- 文件名统一使用 `snake_case`
- 类名使用 `PascalCase`
- 函数名使用 `snake_case`
- 配置文件名应体现用途，例如：
  - `base.yaml`
  - `paths.yaml`
  - `phase0_dev.yaml`

## 9.2 模块边界规则

- `src/gic/data/` 只处理数据相关逻辑
- `src/gic/signal/` 只处理信号相关逻辑
- `src/gic/physics/` 只处理物理求解逻辑
- `src/gic/graph/` 只处理图数据与图结构
- `src/gic/models/` 只处理模型定义
- `src/gic/eval/` 只处理评估
- `src/gic/kg/` 只处理知识图谱
- `src/gic/utils/` 只放跨模块通用工具

禁止把“什么都相关”的代码堆进 `utils/`。

---

## 10. 配置系统设计要求

## 10.1 总体要求

项目必须使用统一配置系统。  
建议：

- 主配置格式：YAML
- Python 侧读取后转为 dataclass 或结构化对象
- 命令行支持选择配置文件
- 支持少量 CLI 覆盖参数

## 10.2 最小配置结构

至少应支持以下配置域：

```yaml
project:
  name: gic_reconstruction
  seed: 42
  mode: dry_run

paths:
  data_root: data
  artifacts_root: artifacts
  logs_root: logs
  reports_root: reports

runtime:
  device: cpu
  num_workers: 0
  deterministic: true

logging:
  level: INFO
  save_to_file: true

stage:
  current: phase0
```

## 10.3 配置文件组织要求

至少创建以下文件：

- `configs/base.yaml`
- `configs/paths.yaml`
- `configs/phase0/phase0_dev.yaml`

如果要进一步细分，也必须保持层级清晰，不允许配置散落无序。

## 10.4 配置读取要求

必须提供一个统一入口，例如：

- `load_config(config_path: str) -> AppConfig`

要求：

- 有默认值
- 有基本字段校验
- 缺失关键字段时报错清晰
- 能序列化保存快照

---

## 11. CLI 设计要求

## 11.1 目标

建立统一命令行入口，为后续所有阶段提供一致调用方式。

## 11.2 最小命令集

Phase 0 只要求支持最小命令，不要求复杂子命令体系，但建议预留扩展结构。  
最低要求至少支持：

- `run`：执行一次 dry run
- `show-config`：打印解析后的配置
- `init-run`：生成 run_id 与运行目录
- `validate-env`：检查基本环境是否可用

## 11.3 推荐调用形式

```bash
python -m gic.cli.main run --config configs/phase0/phase0_dev.yaml
```

或者预留为：

```bash
python -m gic.cli.main show-config --config ...
python -m gic.cli.main init-run --config ...
```

## 11.4 CLI 约束

- 不要过早引入非常复杂的命令树
- 错误提示必须清晰
- 输出要适合日志记录
- 所有 CLI 都应复用统一配置加载逻辑

---

## 12. 运行目录与 artifacts 规范

## 12.1 目标

建立统一运行目录结构，以保证每次运行都可追踪、可回溯、可复现。

## 12.2 运行目录组织

每次运行应生成唯一 run_id，例如：

```text
artifacts/runs/phase0/20260325_153000_ab12cd/
```

目录下至少包含：

```text
artifacts/runs/phase0/<run_id>/
├── config_snapshot.yaml
├── metadata.json
├── stdout.log
├── summary.json
└── placeholders/
```

## 12.3 `metadata.json` 最小字段

至少包括：

- run_id
- stage
- timestamp
- config_path
- git_commit（若可获取）
- hostname（可选）
- python_version
- status

## 12.4 状态更新机制

run 状态建议有：

- `initialized`
- `running`
- `completed`
- `failed`

## 12.5 Phase 0 中必须实现的最低能力

- 能创建运行目录
- 能写入配置快照
- 能写入元数据
- 能保存一份简单 summary

---

## 13. 日志系统要求

## 13.1 基本要求

项目必须有统一 logger，而不是依赖零散 `print`。

## 13.2 日志输出要求

至少支持：

- 控制台输出
- 文件输出

## 13.3 日志内容要求

日志至少应包含：

- 时间
- 日志级别
- 模块名
- 消息内容

## 13.4 日志级别

至少支持：

- DEBUG
- INFO
- WARNING
- ERROR

## 13.5 日志使用规范

- 关键阶段进入/退出必须记录
- 配置路径、run_id、输出路径必须记录
- 出错必须带上下文
- 不要在 library 代码里滥用打印

---

## 14. Python 包管理与开发环境要求

## 14.1 依赖管理

建议使用 `pyproject.toml` 管理项目。  
允许后续使用 `pip` / `uv` / `poetry` 风格，但 Phase 0 不应引入过多工具耦合。

## 14.2 Python 版本

建议固定为较新的稳定版本，例如：

- Python 3.11 或 3.12

要求在文档中明确写清楚。

## 14.3 初始依赖原则

Phase 0 只保留最小必要依赖，避免提前装入大量深度学习包。  
最低可包含：

- `pyyaml`
- `pydantic` 或 dataclass 辅助工具（可选）
- `pytest`
- `rich` 或标准 logging（可选）
- `ruff`
- `black`（若选择）
- `mypy`（可选）

如无必要，Phase 0 不要强制安装 PyTorch Geometric 等重依赖。

---

## 15. 代码质量工具要求

## 15.1 格式化工具

至少应选定一种：

- `black`
- 或其他单一格式化工具

## 15.2 lint 工具

建议：

- `ruff`

## 15.3 类型检查

可选但推荐：

- `mypy`

## 15.4 测试工具

必须：

- `pytest`

## 15.5 pre-commit

可选但推荐。  
如果实现，不要过度复杂，至少包含：

- 格式化
- lint
- 基础检查

---

## 16. 测试要求

## 16.1 本阶段测试目标

不是覆盖业务算法，而是确认工程骨架稳定。

## 16.2 必须有的测试项

至少包括：

1. 配置可成功加载
2. run 目录可成功创建
3. metadata 可成功写入
4. CLI 最小命令可运行
5. 项目主包可正确导入

## 16.3 测试目录建议

```text
tests/
├── test_config.py
├── test_runtime.py
├── test_cli.py
└── conftest.py
```

## 16.4 测试原则

- 测试要小而快
- 不依赖真实大数据
- 不依赖网络访问
- 不依赖 GPU

---

## 17. README 要求

README 是项目第一层入口，因此 Phase 0 必须给出可用初稿。

README 至少应包含：

1. 项目简介
2. 项目当前状态（Phase 0）
3. 仓库结构说明
4. 环境安装方法
5. 最小运行命令
6. 文档索引
7. 后续阶段说明
8. 注意事项

README 不要求现在写成论文式长文，但必须足够让未来开发者快速进入状态。

---

## 18. 文档模板要求

为了后续阶段统一，Phase 0 应在 `docs/templates/` 中至少放置以下模板：

- 阶段详细计划模板
- 决策记录模板
- 实验报告模板

### 18.1 阶段详细计划模板字段建议

- 背景
- 目标
- 非目标
- 输入
- 输出
- 要实现的模块
- 配置要求
- 测试要求
- 验收标准
- 风险与回退策略

### 18.2 决策记录模板字段建议

- 决策编号
- 日期
- 上下文
- 备选方案
- 决策内容
- 影响范围
- 后续动作

---

## 19. 决策记录机制要求

Phase 0 必须建立 `docs/decisions/` 目录，并加入第一条基础决策文档，例如：

- 为什么主包名叫 `gic`
- 为什么采用 YAML 配置
- 为什么 artifacts 与 logs 分目录
- 为什么本项目采用阶段化开发

这非常重要。  
因为后续与 Codex 多轮协作时，如果不保留决策记录，工程理由会很快丢失。

---

## 20. 最小 dry run 流程要求

Phase 0 最终必须支持一个完整但最小的 dry run。  
这个 dry run 不做真实算法，只做：

1. 加载配置
2. 创建 run_id
3. 创建输出目录
4. 初始化 logger
5. 记录配置快照
6. 生成 metadata
7. 写入 summary
8. 正常退出

### 20.1 dry run 的意义

这是对整个工程骨架的第一轮集成测试。  
只有 dry run 稳定，后续阶段才适合往里面塞真实逻辑。

---

## 21. 推荐文件级实现清单

以下是 Phase 0 推荐实现的文件级清单。Codex 应以此为主要目标。

```text
README.md
pyproject.toml
.gitignore
.editorconfig

configs/
  base.yaml
  paths.yaml
  phase0/
    phase0_dev.yaml

docs/
  phases/
  roadmap/
  templates/
    phase_plan_template.md
    decision_record_template.md
    experiment_report_template.md
  decisions/
    0001_project_scaffold_decision.md

src/
  gic/
    __init__.py
    cli/
      __init__.py
      main.py
    config/
      __init__.py
      loader.py
      schema.py
    utils/
      __init__.py
      logging_utils.py
      runtime.py
      paths.py
      metadata.py
    data/__init__.py
    signal/__init__.py
    physics/__init__.py
    graph/__init__.py
    models/__init__.py
    kg/__init__.py
    eval/__init__.py
    visualization/__init__.py

tests/
  conftest.py
  test_config.py
  test_runtime.py
  test_cli.py
```

---

## 22. Codex 在本阶段的实现顺序要求

Codex 必须按以下顺序实现，不允许跳步乱写。

### Step 1：创建顶层目录与基础文件
包括：

- README
- pyproject
- 基础 `.gitignore`
- 目录骨架

### Step 2：创建 `src/gic` 主包与占位子包
只建立结构，不实现复杂逻辑。

### Step 3：实现配置加载模块
包括 schema、loader、默认配置。

### Step 4：实现 runtime 与 run directory 管理
包括 run_id 生成、输出目录创建、metadata 写入。

### Step 5：实现日志模块
统一控制台和文件日志输出。

### Step 6：实现 CLI 最小入口
支持 `show-config`、`init-run`、`run`、`validate-env`。

### Step 7：补齐测试
优先覆盖 config / runtime / cli。

### Step 8：补齐 README 与模板文档
确保后续阶段可以继续写。

---

## 23. Phase 0 的验收标准

只有满足以下全部条件，Phase 0 才算完成。

### 23.1 工程骨架完成

- 顶层目录齐全
- `src/gic/` 主包存在
- 各阶段子模块占位目录存在

### 23.2 配置系统完成

- YAML 配置可加载
- 缺失关键字段时报错清晰
- 可输出配置快照

### 23.3 运行系统完成

- 可生成 run_id
- 可创建标准 artifacts 目录
- 可写 metadata
- 可写 summary

### 23.4 CLI 完成

- `show-config` 可运行
- `init-run` 可运行
- `run` 可完成 dry run
- `validate-env` 可执行

### 23.5 测试完成

- `pytest` 能通过基础测试
- 至少覆盖 config / runtime / cli 三类

### 23.6 文档完成

- README 初稿存在
- 模板文档存在
- 首条 decision record 存在

---

## 24. 最低可接受标准（Minimum Acceptable Outcome）

如果时间有限，Phase 0 至少也必须达到以下底线：

1. 项目目录结构存在
2. 可以加载配置
3. 可以执行一次 dry run
4. 可以写出 run directory、config snapshot、metadata
5. 可以运行最基础测试
6. 后续阶段可以在此基础上继续

如果连上述底线都达不到，则 Phase 0 不能结束。

---

## 25. 风险与回退策略

## 25.1 风险：设计过度

可能出现的问题：

- 配置系统过度复杂
- CLI 命令树过于庞大
- 工具链引入太多
- 为未来假想场景提前优化

### 对策

- 只做最小骨架
- 所有复杂功能必须延后到后续阶段
- 保留扩展点，不实现扩展本体

## 25.2 风险：目录结构混乱

### 对策

- 严格按本计划建目录
- 不允许把实验脚本乱放到顶层
- 不允许把 notebook 逻辑直接当正式代码

## 25.3 风险：Codex 写出“能跑但不可维护”的样板

### 对策

- 强制要求类型注解
- 强制要求模块职责清晰
- 强制要求测试与 README 同步

## 25.4 风险：提前开始写业务逻辑

### 对策

- 所有与 GIC 求解、图模型、KG 具体实现相关代码一律不写
- 只允许创建占位包与简单 stub

---

## 26. 明确禁止事项

Codex 在本阶段**禁止**做以下事情：

1. 不得实现 GIC forward solver 主体
2. 不得实现真实信号处理算法
3. 不得实现任何完整 GNN 模型
4. 不得实现 KG 推理系统
5. 不得下载大型数据集
6. 不得引入与当前阶段不必要的深度学习重依赖
7. 不得把复杂逻辑直接写进 notebook
8. 不得绕开配置系统硬编码路径
9. 不得把运行结果直接丢在随机目录
10. 不得省略测试和文档

---

## 27. 建议提交粒度

建议本阶段按以下粒度逐步提交，方便回溯。

### Commit 1
建立仓库骨架和顶层目录

### Commit 2
加入 `src/gic` 主包和占位模块

### Commit 3
实现配置系统

### Commit 4
实现 runtime / artifacts / metadata

### Commit 5
实现 logging 和 CLI

### Commit 6
实现测试

### Commit 7
补齐 README、模板和 decision record

---

## 28. 本阶段完成后的交接要求

Phase 0 完成后，应额外输出一份简短交接摘要，说明：

- 已实现哪些基础设施
- 当前目录结构是什么
- 如何执行 dry run
- 后续 Phase 1 可以直接复用哪些接口
- 当前已知限制是什么

这份交接摘要可以存放于：

- `reports/phase0_summary.md`
  或
- `docs/phases/phase0_completion_note.md`

---

## 29. Phase 1 的前置接口要求

为了让 Phase 1 能顺利开始，Phase 0 完成后至少应保证后续能直接使用以下能力：

- 配置加载接口
- 路径解析接口
- run 管理接口
- logging 接口
- 文档与模板骨架
- 数据目录骨架

如果这些接口不稳定，Phase 1 不应开始。

---

## 30. 最终执行指令（给 Codex 的摘要版）

下面这段可直接作为对 Codex 的高层执行约束摘要：

> 你正在执行 GIC 项目的 Phase 0。你的目标不是实现算法，而是建立整个项目未来所有阶段都要遵守的工程骨架。你必须严格创建统一的目录结构、主包结构、配置系统、CLI、日志与 artifacts 机制、基础测试和文档模板。你不得提前实现 GIC 物理求解、信号处理、GNN、KG 或真实数据下载逻辑。你必须优先保证可维护性、可复现性和接口清晰。最终结果必须支持一次完整 dry run，并能让后续阶段直接在统一骨架上开发。

---

## 31. 结论

Phase 0 是整个项目的基础设施阶段。  
它的重要性在于：

- 让后续所有阶段都在同一工程语言下进行；
- 避免随着功能增加而出现目录混乱、配置失控、日志缺失、结果不可复现的问题；
- 给 Codex 一套清晰、稳定、严格可执行的工程边界。

Phase 0 完成后，项目应从“想法与文档”正式进入“可持续开发状态”。

下一步在执行顺序上，应在 Phase 0 完成并验收后，再开始撰写并执行：

- `phase_1_detailed_plan.md`
