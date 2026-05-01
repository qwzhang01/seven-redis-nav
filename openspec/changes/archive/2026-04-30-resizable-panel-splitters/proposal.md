## Why

当前三栏布局（Sidebar 240px / KeyPanel 320px / Workspace 自适应）使用固定宽度，用户无法根据实际使用场景调整面板比例。例如键名较长时 KeyPanel 显示不全，或者查看详情时希望 Workspace 更宽。需要在面板之间添加可拖拽的分隔条（splitter），让用户自由调整各面板宽度。

## What Changes

- 在 Sidebar 与 KeyPanel 之间添加可拖拽的垂直分隔条
- 在 KeyPanel 与 Workspace 之间添加可拖拽的垂直分隔条
- 拖拽时实时更新面板宽度，松开后保持新宽度
- 设置合理的最小/最大宽度约束，防止面板被拖到不可用状态
- 双击分隔条可重置对应面板到默认宽度
- 拖拽状态下鼠标光标变为 `col-resize`
- 面板宽度持久化到 localStorage，下次启动恢复

## Capabilities

### New Capabilities
- `panel-resize`: 面板拖拽调整大小的交互能力，包括分隔条组件、拖拽逻辑、宽度约束和持久化

### Modified Capabilities
- `app-shell`: 主窗口布局结构需要从固定宽度改为支持动态宽度，Sidebar 和 KeyPanel 的宽度由拖拽状态驱动

## Impact

- `src/views/MainLayout.vue` — 需要引入分隔条组件，面板宽度改为响应式变量
- `src/components/sidebar/Sidebar.vue` — 宽度从 CSS 变量改为动态 style 绑定
- `src/components/keypanel/KeyPanel.vue` — 宽度从 CSS 变量改为动态 style 绑定
- `src/styles/tokens.css` — `--srn-sidebar-w` 和 `--srn-keypanel-w` 变为默认值/初始值
- 新增 composable `useResizable` 或独立的 `ResizeSplitter.vue` 组件
- localStorage 新增面板宽度持久化 key
