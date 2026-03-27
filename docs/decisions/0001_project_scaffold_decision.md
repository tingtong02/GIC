# Decision Record 0001

- 日期：2026-03-27
- 状态：accepted
- 上下文：项目当前处于 Phase 0，需要先固化统一目录、配置、CLI、runtime、日志和文档骨架。
- 决策：主包固定为 `gic`，配置文件统一放在 `configs/`，运行产物按 `artifacts/`、`logs/`、`reports/` 分离保存，后续阶段必须复用该骨架。
- 影响：后续所有实现都应收敛到 `src/gic/` 下，并通过统一配置与运行入口接入。
- 后续动作：在 Phase 1 继续扩展数据接口，在 Phase 2 以后逐步填充 physics / signal / graph / models / kg / eval 模块。
