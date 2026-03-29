# GIC 项目展示网页设计与实现计划 (v1.0)

## 1. 项目定位与核心目标
本网页旨在作为学术/工程简历中的一个高质感 Showcase 页面。
- **视觉基调**：极简学术风（Minimalist Academic），排版干净克制，类似顶级学术实验室或顶级开源工具的介绍页。
- **交互基调**：细节精美（Smooth & Polished），带有高级且不夸张的丝滑滚动动画，数据和架构展示具备交互性。
- **内容基调**：真实、保守、有层次、不夸张。必须严守证据边界，明确展示 Trade-off。

## 2. 技术栈选型 (Result-Oriented Stack)
为实现“单页长滚动加载快”且“拥有丝滑动画与复杂交互”，确定以下技术栈：
- **核心框架**：Astro (提供极致的静态生成性能和极客感)。
- **UI/组件层**：React (用于编写交互组件)。
- **样式方案**：Tailwind CSS (确保排版精细控制和极简的代码风格)。
- **动画库**：Framer Motion (用于实现页面滚动时的元素渐显、架构对比切换的丝滑过渡)。
- **数据可视化**：Apache ECharts 或 Recharts (用于渲染可交互的对比柱状图、时序曲线图)。

## 3. 视觉与排版设计规范 (Design System)
- **色彩规范 (Color Palette)**：
  - **背景色**：大面积纯白 (`#FFFFFF`) 或极浅的灰 (`#FAFAFA`)。
  - **主文本色**：深邃的炭黑 (`#1A1A1A`)，副标题使用深灰 (`#52525B`)。
  - **强调色/交互色**：克制的学术蓝 (`#2563EB`) 或沉稳的深青色 (`#0F766E`)，仅用于按钮、可点击 Tab 和数据图表的高亮。
  - **警告/限制色**：赭石色或暗橙色 (`#B45309`)，专用于“边界限制”和“不可宣教的底线”提醒。
- **字体排版 (Typography)**：
  - **正文/标题**：Inter 或系统自带的无衬线字体 (San Francisco/Segoe UI)，突出清晰易读。
  - **代码/模型名/专有名词**：JetBrains Mono 或 Fira Code，体现硬核工程感。
  - **字号与留白**：采用大留白 (Generous Whitespace) 设计，区块之间保持充足的 Margin，降低阅读压迫感。

## 4. 单页架构与叙事流 (Single-Page Scroll Architecture)
页面采用单页长滚动设计，左侧（或顶部固定）提供平滑滚动的目录导航 (Spy Navigation)。

**区块划分与表现形式：**
1. **Hero Section (项目总览)**
   - 极简的标题、一句话定位。
   - 动画：加载时文字自下而上柔和 Fade-in。
2. **问题为什么难 (Problem & Motivation)**
   - 简短解释性段落。配以简单的交互式卡片（Hover时显示难度细节）。
3. **技术路线总览 (Timeline)**
   - 使用交互式时间轴组件（Interactive Timeline），用户滚动时逐个点亮 Phase 0 到 Phase 8 的里程碑。
4. **当前系统架构：默认 vs 可选 (Architecture & Trade-offs)**
   - **核心交互组件**：[Toggle Tab] 切换“Phase 5 默认路径”与“Phase 6 可选 KG 路径”。
   - 切换时使用 Framer Motion 实现平滑的形态过渡。
   - 配套**Trade-off 说明块**：明确解释为什么 KG 精度高却没有作为默认（真实证据的保守性）。
5. **结果与对比 (Results Dashbaord)**
   - 引入 ECharts 渲染动态柱状图（对比 Baseline 与 GraphSAGE/GRU 的 hidden-node MAE 从 7.73 到 5.94 的下降）。
   - 支持鼠标 Hover 查看具体指标意味着什么（不只贴数字，带解释）。
6. **真实事件验证与边界 (Real-Event Limits)**
   - **限制提醒文字块 (Admonition UI)**：使用红色/赭色边框包围，醒目地列出“当前的证据仅为基于特定测站局部扰乱，绝不可宣称拥有成熟的灾变预测准度”。
7. **工程实现 (Engineering)**
   - 极简展示仓库的代码树形态，体现“未发生大重构、高内聚”的工程素养。附带 GitHub 链接。
8. **限制与未来工作 (Future Work)**
   - 最终结论摘要，强调未来是“下一轮增强”而非补漏洞。

## 5. 核心交互动画要求 (Animation Guidelines)
- **Scroll Reveal**：随着页面向下滚动，新的 Section 采用 `opacity: 0` 到 `1`，伴随极其微小的 `y: 20px` 到 `0` 的位移（时长 0.6s，缓动曲线 `easeOut`），切忌弹簧般的花哨动画。
- **Tabs Transition**：在架构对比区域，切换标签时，内容区域通过交叉淡入淡出（Cross-fade）平滑过渡，高度变化必须有动画计算（AnimatePresence）。