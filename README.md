# GIC

Phase 0 工程骨架仓库，用于后续 Phase 1 到 Phase 8 在统一目录、配置、CLI、日志和 artifacts 规范下继续开发。

## Phase 0 当前范围

- 建立统一目录结构
- 建立最小配置系统
- 建立最小 CLI
- 建立 run_id / metadata / summary / logging 机制
- 建立基础测试与文档模板

当前阶段不实现任何 GIC solver、信号处理、GNN、KG 或真实数据下载逻辑。

## 快速开始

```bash
PYTHONPATH=src python -m gic.cli.main validate-env
PYTHONPATH=src python -m gic.cli.main show-config --config configs/phase0/phase0_dev.yaml
PYTHONPATH=src python -m gic.cli.main init-run --config configs/phase0/phase0_dev.yaml
PYTHONPATH=src python -m gic.cli.main run --config configs/phase0/phase0_dev.yaml
python -m pytest
```

也可以直接运行：

```bash
./scripts/phase0_dry_run.sh
```

## 目录概览

- `configs/`: JSON-compatible YAML 配置文件
- `data/`: `raw/`, `interim/`, `processed/`, `registry/`
- `docs/`: 规划文档、模板与决策记录
- `scripts/`: 轻量运行脚本
- `src/gic/`: 主 Python 包
- `tests/`: 基础测试
- `artifacts/`, `logs/`, `reports/`: 运行产物与记录

## 说明

当前环境未额外安装 `PyYAML`，因此 Phase 0 先采用“JSON-compatible YAML”文件格式，保持 `.yaml` 后缀并确保后续可平滑升级到完整 YAML 解析。
