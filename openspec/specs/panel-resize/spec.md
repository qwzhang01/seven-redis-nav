### Requirement: 垂直分隔条视觉与交互

系统 SHALL 在 Sidebar 与 KeyPanel 之间、KeyPanel 与 Workspace 之间各渲染一个垂直分隔条。分隔条宽度 MUST 为 4px，默认透明，悬停时显示为半透明灰色条（`rgba(0,0,0,0.08)`），拖拽时显示为主题蓝色条（`var(--srn-color-info)`）。

#### Scenario: 分隔条默认状态

- **WHEN** 用户未与分隔条交互
- **THEN** 分隔条区域宽 4px，视觉上透明，不影响面板间的视觉连续性

#### Scenario: 分隔条悬停状态

- **WHEN** 用户鼠标悬停在分隔条上
- **THEN** 分隔条显示为 `rgba(0,0,0,0.08)` 背景色，鼠标光标变为 `col-resize`

#### Scenario: 分隔条拖拽状态

- **WHEN** 用户在分隔条上按下鼠标并拖动
- **THEN** 分隔条显示为 `var(--srn-color-info)` 背景色，全局光标变为 `col-resize`，页面文本不可选中

### Requirement: 拖拽调整面板宽度

用户 SHALL 能够通过拖拽分隔条来实时调整相邻面板的宽度。拖拽过程中面板宽度 MUST 实时跟随鼠标位置更新。

#### Scenario: 拖拽 Sidebar 分隔条

- **WHEN** 用户拖拽 Sidebar 与 KeyPanel 之间的分隔条向右移动 50px
- **THEN** Sidebar 宽度增加 50px，KeyPanel 和 Workspace 相应缩小

#### Scenario: 拖拽 KeyPanel 分隔条

- **WHEN** 用户拖拽 KeyPanel 与 Workspace 之间的分隔条向左移动 30px
- **THEN** KeyPanel 宽度减少 30px，Workspace 宽度增加 30px

#### Scenario: 拖拽释放后保持宽度

- **WHEN** 用户释放分隔条
- **THEN** 面板保持拖拽结束时的宽度，分隔条恢复默认视觉状态

### Requirement: 面板宽度约束

系统 MUST 对面板宽度施加最小和最大约束，防止面板被拖拽到不可用状态。

| 面板 | 默认宽度 | 最小宽度 | 最大宽度 |
|------|---------|---------|---------|
| Sidebar | 240px | 160px | 400px |
| KeyPanel | 320px | 200px | 500px |

#### Scenario: 达到最小宽度

- **WHEN** 用户向左拖拽 Sidebar 分隔条使 Sidebar 宽度达到 160px
- **THEN** 继续向左拖拽不再减小 Sidebar 宽度，分隔条停止响应该方向的移动

#### Scenario: 达到最大宽度

- **WHEN** 用户向右拖拽 Sidebar 分隔条使 Sidebar 宽度达到 400px
- **THEN** 继续向右拖拽不再增大 Sidebar 宽度，分隔条停止响应该方向的移动

### Requirement: 双击重置默认宽度

用户 SHALL 能够通过双击分隔条将对应面板宽度重置为默认值。

#### Scenario: 双击 Sidebar 分隔条

- **WHEN** 用户双击 Sidebar 与 KeyPanel 之间的分隔条
- **THEN** Sidebar 宽度平滑过渡回 240px（默认值）

#### Scenario: 双击 KeyPanel 分隔条

- **WHEN** 用户双击 KeyPanel 与 Workspace 之间的分隔条
- **THEN** KeyPanel 宽度平滑过渡回 320px（默认值）

### Requirement: 面板宽度持久化

系统 SHALL 将用户调整后的面板宽度持久化到 localStorage，下次启动时恢复。

#### Scenario: 宽度持久化写入

- **WHEN** 用户完成一次拖拽操作（释放鼠标）
- **THEN** 系统将当前 Sidebar 和 KeyPanel 的宽度写入 localStorage key `srn-panel-widths`

#### Scenario: 启动时恢复宽度

- **WHEN** 应用启动且 localStorage 中存在 `srn-panel-widths`
- **THEN** Sidebar 和 KeyPanel 使用存储的宽度值（在约束范围内）

#### Scenario: 无持久化数据时使用默认值

- **WHEN** 应用启动且 localStorage 中不存在 `srn-panel-widths`
- **THEN** Sidebar 使用 240px，KeyPanel 使用 320px

### Requirement: 面板隐藏时分隔条联动

当面板通过快捷键隐藏时，对应的分隔条 MUST 同步隐藏。

#### Scenario: Sidebar 隐藏时

- **WHEN** 用户按 ⌘1 隐藏 Sidebar
- **THEN** Sidebar 与 KeyPanel 之间的分隔条同步隐藏

#### Scenario: KeyPanel 隐藏时

- **WHEN** 用户按 ⌘2 隐藏 KeyPanel
- **THEN** KeyPanel 与 Workspace 之间的分隔条同步隐藏，Sidebar 分隔条保持可见（如果 Sidebar 可见）
