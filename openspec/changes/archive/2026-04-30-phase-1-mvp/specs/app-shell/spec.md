## MODIFIED Requirements

### Requirement: 侧边栏三个分区

Sidebar 背景 MUST 为 `#f2f2f4`，自上而下 SHALL 包含三个分区：连接列表（顶部，数据来自 SQLite）、数据库列表（中部，数据来自 `INFO keyspace`）、用户信息（底部固定，上方有分隔线）。Phase 1 三个分区均使用真实数据驱动，取代 Phase 0 的静态 mock 数据。

#### Scenario: 连接项视觉结构

- **WHEN** 渲染单个连接项
- **THEN** 必须包含状态圆点（online 绿 / connecting 黄 / offline 灰 / reconnecting 黄闪）、连接名称、`host:port`（等宽字体）、版本徽章（红底白字）

#### Scenario: 连接列表从 SQLite 加载

- **WHEN** 应用启动或用户创建/删除连接
- **THEN** Sidebar 连接列表从 SQLite `connections` 表读取，按 `sort_order` 排序

#### Scenario: 右键上下文菜单

- **WHEN** 用户右键点击连接项
- **THEN** 弹出上下文菜单：编辑 / 复制 / 删除 / 断开（仅已连接时）

#### Scenario: 数据库项视觉结构

- **WHEN** 渲染单个 DB 项
- **THEN** 必须包含 `ri-database-line` 图标、`DB n` 标签、键数量（千分位等宽数字），数据从 `INFO keyspace` 解析

#### Scenario: 数据库列表按连接刷新

- **WHEN** 用户选中一个已连接的连接
- **THEN** 数据库列表刷新为该连接的 DB 信息（DB 0-15 + 各 DB 键数）

## ADDED Requirements

### Requirement: Sidebar 可收起

Sidebar SHALL 支持通过 ⌘1 快捷键或 UI 按钮折叠/展开。折叠时宽度变为 0，Workspace 区域自动扩展。

#### Scenario: ⌘1 收起 Sidebar

- **WHEN** 用户按下 ⌘1
- **THEN** Sidebar 以 200ms 动画滑出，Workspace 区域扩展占满

#### Scenario: ⌘1 展开 Sidebar

- **WHEN** Sidebar 已收起，用户按下 ⌘1
- **THEN** Sidebar 以 200ms 动画滑入恢复 240px 宽度

### Requirement: ConnectionForm 弹窗

系统 SHALL 提供 ConnectionForm 弹窗（TDesign Dialog），支持新建和编辑连接。表单包含：名称、分组、主机、端口、密码、DB 索引、超时时间。底部有"测试连接"和"保存"按钮。

#### Scenario: 新建连接弹窗

- **WHEN** 用户点击 Toolbar + 按钮或 ⌘N
- **THEN** 弹出 ConnectionForm 弹窗，所有字段为空，底部按钮为"测试连接"和"保存"

#### Scenario: 编辑连接弹窗

- **WHEN** 用户右键点击连接选择"编辑"
- **THEN** 弹出 ConnectionForm 弹窗，字段预填当前值，密码显示为占位符

#### Scenario: 弹窗内测试连接

- **WHEN** 用户在 ConnectionForm 中点击"测试连接"
- **THEN** 调用 `connection_test` IPC，按钮显示 loading，结果显示在弹窗内

### Requirement: KeyPanel 真实数据驱动

KeyPanel SHALL 从 `useKeyBrowserStore` 获取真实 SCAN 数据，替代 Phase 0 的 mock 数据。搜索、类型筛选、分页均连接真实 IPC。

#### Scenario: KeyPanel SCAN 加载

- **WHEN** 用户选中一个连接和 DB
- **THEN** KeyPanel 调用 `keys_scan` IPC，显示真实键列表

#### Scenario: KeyPanel 可收起

- **WHEN** 用户按下 ⌘2
- **THEN** KeyPanel 以动画折叠/展开

### Requirement: Welcome 页已有连接列表

Welcome 页 SHALL 在"快速连接"表单下方显示已有连接列表（从 SQLite 读取），用户可直接点击连接。

#### Scenario: 显示已有连接

- **WHEN** 应用启动且 SQLite 中存在已保存的连接
- **THEN** Welcome 页下方显示"已保存的连接"列表，每项显示名称和 host:port

#### Scenario: 点击已有连接

- **WHEN** 用户点击已有连接列表中的一项
- **THEN** 系统尝试打开该连接，成功后进入主界面

### Requirement: Statusbar 动态数据

Statusbar 左侧 SHALL 显示当前活跃连接的 host:port 和 Redis 版本（从 PingResult 获取），右侧性能指标在 Phase 1 继续使用占位文本（Phase 2 Monitor Tab 实现时接入真实数据）。

#### Scenario: 连接后更新状态栏

- **WHEN** 用户成功连接到一个 Redis 实例
- **THEN** 状态栏左侧更新为该连接的 host:port · Redis 版本号 · DB 索引
