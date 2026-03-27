# Decision Record 0002

- 日期：2026-03-27
- 状态：accepted
- 上下文：Phase 2 需要先建立可运行的 baseline solver，但 Phase 1 样例缺少完整 GIC 所需空间字段。
- 决策：先实现简化 baseline solver；线路 `length_km` 与 `azimuth_deg` 允许通过显式 config override 补全；bus grounding 采用统一阻值假设；transformer 采用 effective resistance 简化。
- 影响：当前 solver 可运行、可记录 assumptions、可为后续阶段提供 baseline 与标签，但物理精度仍受限于样例字段和简化方式。
- 后续动作：Phase 2 后续可逐步引入更真实的线路空间信息、接地参数和更细的 transformer 结构。
