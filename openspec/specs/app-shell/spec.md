### Requirement: 主窗口布局结构

应用主窗口 SHALL 按自上而下顺序呈现五个固定区域：原生标题栏、Toolbar（仅已连接时显示）、主体（Sidebar + KeyPanel + Workspace 三栏）、Statusbar，且各区域尺寸 MUST 与设计保持一致。

| 区域 | 尺寸 |
|---|---|
| 原生标题栏 | 系统默认（约 28px） |
| Toolbar | 高 48px（仅已连接时显示） |
| Sidebar | 默认宽 240px，可拖拽调整（160px ~ 400px） |
| KeyPanel | 默认宽 320px，可拖拽调整（200px ~ 500px） |
| Workspace | 自适应填满剩余空间 |
| Statusbar | 高 28px |
| 窗口最小宽 | 960px（由 Tauri 配置控制） |
| 窗口最小高 | 600px（由 Tauri 配置控制） |

主窗口容器 SHALL NOT 设置 max-width 限制，内容 MUST 铺满整个窗口宽度。Sidebar 和 KeyPanel 之间、KeyPanel 和 Workspace 之间 SHALL 各有一个 4px 宽的可拖拽分隔条。

#### Scenario: 默认窗口布局

- **WHEN** 用户在 macOS 上启动应用
- **THEN** 窗口呈现原生标题栏 + 主体区域 + Statusbar，内容铺满整个窗口宽度，无多余背景色

#### Scenario: 全屏布局

- **WHEN** 用户将窗口全屏
- **THEN** 应用内容铺满整个屏幕，左右两侧无多余背景色或壁纸渐变

#### Scenario: 响应式断点

- **WHEN** 窗口宽度位于 [900px, 1100px) 区间
- **THEN** Sidebar 收窄到 220px，KeyPanel 收窄到 280px

- **WHEN** 窗口宽度小于 900px
- **THEN** 三栏改为单栏纵向排列，Sidebar 高度上限 180px，KeyPanel 高度上限 300px，分隔条不显示

### Requirement: Workspace tab routing
The system SHALL route Toolbar tab clicks to their corresponding workspace components, replacing placeholder components with fully functional workspace implementations.

#### Scenario: Navigate to Monitor tab
- **WHEN** user clicks the "Monitor" tab in the Toolbar
- **THEN** the workspace area renders the MonitorWorkspace component (not a placeholder)

#### Scenario: Navigate to Slowlog tab
- **WHEN** user clicks the "Slowlog" tab in the Toolbar
- **THEN** the workspace area renders the SlowlogWorkspace component

#### Scenario: Navigate to Pub/Sub tab
- **WHEN** user clicks the "Pub/Sub" tab in the Toolbar
- **THEN** the workspace area renders the PubsubWorkspace component

#### Scenario: Navigate to Config tab
- **WHEN** user clicks the "Config" tab in the Toolbar
- **THEN** the workspace area renders the ServerConfigWorkspace component

#### Scenario: Tab switch cleanup
- **WHEN** user switches away from Monitor or Pub/Sub tab while a session is active
- **THEN** the active session (MONITOR/SUBSCRIBE) continues running in the background; switching back restores the stream view
