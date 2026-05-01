## ADDED Requirements

### Requirement: 主窗口布局结构

应用主窗口 SHALL 按自上而下顺序呈现六个固定区域：Titlebar、Toolbar、主体（Sidebar + KeyPanel + Workspace 三栏）、Statusbar，且各区域尺寸 MUST 与 `docs/index.html` 原型保持一致。

| 区域 | 尺寸 |
|---|---|
| Titlebar | 高 38px |
| Toolbar | 高 48px |
| Sidebar | 宽 240px |
| KeyPanel | 宽 320px |
| Workspace | 自适应填满剩余空间 |
| Statusbar | 高 28px |
| 窗口最大宽 | 1400px |
| 窗口最小高 | 720px |

#### Scenario: 默认窗口布局

- **WHEN** 用户在 macOS 上启动应用
- **THEN** 窗口呈现六个区域，且 Titlebar/Toolbar/Statusbar 高度精确等于 38/48/28 px，Sidebar/KeyPanel 宽度精确等于 240/320 px

#### Scenario: 响应式断点

- **WHEN** 窗口宽度位于 [900px, 1100px) 区间
- **THEN** Sidebar 收窄到 220px，KeyPanel 收窄到 280px

- **WHEN** 窗口宽度小于 900px
- **THEN** 三栏改为单栏纵向排列，Sidebar 高度上限 180px，KeyPanel 高度上限 300px

### Requirement: 标题栏视觉与红绿灯

Titlebar 背景 MUST 为线性渐变 `#e8e8ed → #d8d8dc`，底部 1px 边框 `rgba(0,0,0,0.1)`。左侧 SHALL 包含三个红绿灯按钮（关闭 `#ff5f57` / 最小化 `#febc2e` / 最大化 `#28c840`），尺寸 12×12 px，圆角 50%，0.5px 深色边框；居中 SHALL 显示 Redis 红色图标 + 文字 "Seven Redis Nav" + 灰色副标题。

#### Scenario: 红绿灯悬停显隐图标

- **WHEN** 鼠标悬停在红绿灯组上
- **THEN** 三个按钮分别在内部显示 `×`、`−`、`+` 字符

#### Scenario: 关闭按钮抖动动画

- **WHEN** 用户点击关闭红绿灯
- **THEN** 主窗口触发 `window-shake` 动画并在 400ms 内回到原位（Phase 0 不真正关闭应用）

#### Scenario: 最大化切换全屏

- **WHEN** 用户点击最大化红绿灯
- **THEN** 窗口在最大化与还原状态之间切换

### Requirement: 工具栏 6 Tab 切换

Toolbar 左侧 SHALL 渲染 6 个 Tab 按钮：浏览器 / 命令行 / 监控 / 慢查询 / 发布订阅 / 配置；每个 Tab MUST 有对应的 Remix Icon（`ri-file-list-3-line` / `ri-terminal-box-line` / `ri-pulse-line` / `ri-timer-flash-line` / `ri-broadcast-line` / `ri-settings-3-line`）和 `data-tab` 标识。同一时刻有且仅有一个 Tab 处于激活态，激活态视觉为白底红字带阴影。

#### Scenario: 单击 Tab 切换激活态

- **WHEN** 用户单击任意一个未激活的 Tab 按钮
- **THEN** 该按钮变为激活态、其他按钮恢复未激活态，且 Workspace 区域切换为对应 Tab 的容器组件（容器内可为静态占位）

#### Scenario: Tab 状态全局可读

- **WHEN** 任意组件读取当前激活的 Tab
- **THEN** 必须从 Pinia `useWorkspaceStore().activeTab` 获取，禁止组件间互传

### Requirement: 工具栏全局搜索

Toolbar 中部 SHALL 提供全局搜索输入框，最大宽度 360px，placeholder 为 `搜索键、命令或设置...`，右侧 SHALL 显示 `⌘K` 快捷键 chip。

#### Scenario: ⌘K 聚焦搜索

- **WHEN** 用户按下 `⌘+K`（macOS）或 `Ctrl+K`（其他平台）
- **THEN** 全局搜索输入框获得焦点

#### Scenario: 聚焦时蓝色光晕

- **WHEN** 全局搜索输入框获得焦点
- **THEN** 边框颜色变为蓝色且伴随蓝色 box-shadow 光晕

### Requirement: 侧边栏三个分区

Sidebar 背景 MUST 为 `#f2f2f4`，自上而下 SHALL 包含三个分区：连接列表（顶部）、数据库列表（中部）、用户信息（底部固定，上方有分隔线）。Phase 0 三个分区均使用静态 mock 数据展示。

#### Scenario: 连接项视觉结构

- **WHEN** 渲染单个连接项
- **THEN** 必须包含状态圆点（online 绿 / warning 黄 / offline 灰）、连接名称、`host:port`（等宽字体）、版本徽章（红底白字）

#### Scenario: 数据库项视觉结构

- **WHEN** 渲染单个 DB 项
- **THEN** 必须包含 `ri-database-line` 图标、`DB n` 标签、键数量（千分位等宽数字）

### Requirement: 键面板视觉与类型徽章配色

KeyPanel 背景 MUST 为白色，自上而下 SHALL 包含搜索筛选栏、统计行、键列表、分页栏。键列表中每个键项的类型徽章配色 MUST 与下表精确一致：

| 类型 | 背景 | 文字 |
|---|---|---|
| String | `#dbeafe` | `#1e40af` |
| Hash | `#fef3c7` | `#92400e` |
| List | `#dcfce7` | `#166534` |
| Set | `#f3e8ff` | `#6b21a8` |
| ZSet | `#fce7f3` | `#9f1239` |
| Stream | `#cffafe` | `#155e75` |

#### Scenario: 键项选中态

- **WHEN** 用户单击一个键项
- **THEN** 该项呈现浅红背景 + 红色左边框，其他项恢复默认态

#### Scenario: 空状态

- **WHEN** 键列表为空（mock 或过滤后无结果）
- **THEN** 显示 `ri-inbox-line` 大图标 + "没有匹配的键" 文案

### Requirement: 状态栏视觉与内容

Statusbar 背景 MUST 为 `#e8e8ed`，顶部 1px 边框。左侧 SHALL 显示服务器连接信息（绿色 host:port 圆点 + Redis 版本 + DB 编号），右侧 SHALL 显示性能指标（CPU / RAM / OPS / Uptime）。Phase 0 全部使用静态占位文本。

#### Scenario: 默认状态栏文本

- **WHEN** 应用首次启动
- **THEN** 状态栏左侧显示 `🟢 redis-master.prod.local:6379 · Redis 7.2.4 · DB 0 / 16`，右侧显示 4 个占位指标

### Requirement: 设计令牌单一来源

所有颜色、圆角、阴影、动效时长 MUST 定义于 `src/styles/tokens.css` 作为 CSS 变量（前缀 `--srn-`），并在 `tailwind.config.ts` 中通过 `var(--srn-*)` 映射。组件 SHALL NOT 出现硬编码色值（`#xxxxxx`、`rgb()`）或硬编码动效时长（`200ms` 等）。

#### Scenario: 令牌完整覆盖原型

- **WHEN** 检查原型 `docs/style.css` + `docs/style-ext.css` 中出现的所有色值
- **THEN** 每一个唯一色值在 `tokens.css` 中都有对应变量

#### Scenario: 令牌命名规范

- **WHEN** 新增一个设计令牌
- **THEN** 命名必须遵循 `--srn-{category}-{name}-{variant?}` 模式（如 `--srn-color-bg-1` / `--srn-radius-md` / `--srn-motion-fast`）

### Requirement: 桌面壁纸背景

应用窗口外层 SHALL 渲染一个 fixed 定位的桌面壁纸 div，使用与原型一致的多层径向渐变（左上 `#ff6b9d` + 右上 `#7c5cff` + 底部 `#00d4ff` + 基底 `linear-gradient(135deg, #1a1a2e → #16213e → #0f3460)`），位于主窗口下方营造 macOS 桌面感。

#### Scenario: 壁纸位置

- **WHEN** 应用启动
- **THEN** 桌面壁纸出现在主窗口外侧，z-index 低于窗口
