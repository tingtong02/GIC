# Physics Solver Overview

## Solver 分层结构

- 输入层：`PhysicsGridCase` 与 `ElectricFieldSnapshot` / `ElectricFieldSeries`
- 组网层：由 `PhysicsGridCase` 形成节点与线路求解结构
- 求解层：uniform field baseline 下的线性 DC 求解
- 输出层：line-level / bus-level / transformer-level 标签与 manifest

## 当前物理简化

- 使用 uniform grounding resistance 假设
- 对缺失的 `length_km` 与 `azimuth_deg` 通过显式 config override 补全
- transformer GIC 目前采用基于节点电位差的简化 effective resistance 近似
- geomagnetic -> electric field 的时序模式采用线性缩放占位

## 输入输出说明

- 输入：Phase 1 `GridCase`、uniform field snapshot 或 geomagnetic 派生 series
- 输出：`GICSolution`、标签数据集摘要、manifest、validation/sanity 报告

## 适用范围

- Phase 2 最小可信 baseline
- 小到中等规模测试系统的单时刻与简单时序场景
- 后续 Phase 4 / Phase 5 的物理 baseline 与标签来源

## 已知局限

- 当前不覆盖工业级复杂变压器结构
- 当前线路空间字段依赖显式 assumptions 补全
- 当前时序场景只支持线性缩放的简化电场构造
