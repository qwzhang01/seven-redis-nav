## Context

当前 Seven Redis Nav 采用三栏布局：Sidebar（240px 固定）、KeyPanel（320px 固定）、Workspace（flex: 1 自适应）。面板宽度通过 CSS 变量 `--srn-sidebar-w` 和 `--srn-keypanel-w` 定义在 `tokens.css` 中，各组件通过 `width: var(--srn-sidebar-w)` 引用。

布局容器 `MainLayout.vue` 的 `.window-body` 使用 flexbox 横向排列三个面板。Sidebar 和 KeyPanel 已支持通过快捷键 ⌘1/⌘2 切换显隐（带 slide 动画）。

用户需要在面板之间拖拽调整宽度，这是桌面应用的标准交互模式。

## Goals / Non-Goals

**Goals:**
- 用户可以通过拖拽 Sidebar 与 KeyPanel 之间的分隔条调整 Sidebar 宽度
- 用户可以通过拖拽 KeyPanel 与 Workspace 之间的分隔条调整 KeyPanel 宽度
- 拖拽过程流畅无卡顿（使用 pointer events，避免 iframe 捕获问题）
- 面板宽度有合理的最小/最大约束
- 双击分隔条恢复默认宽度
- 面板宽度持久化到 localStorage
- 与现有的面板显隐动画兼容

**Non-Goals:**
- 不支持垂直方向的面板拖拽
- 不支持移动端触摸拖拽（桌面应用）
- 不修改响应式断点逻辑（< 900px 单栏模式下不显示分隔条）
- 不引入第三方拖拽库

## Decisions

### Decision 1: 使用独立的 `ResizeSplitter.vue` 组件

**选择**: 创建一个通用的垂直分隔条组件 `src/components/common/ResizeSplitter.vue`，通过 props 接收方向和约束，emit 拖拽偏移量。

**理由**: 两个分隔条的行为完全一致，抽象为组件可复用且易于测试。组件职责单一：渲染分隔条 UI + 处理 pointer 事件 + emit 宽度变化。

**备选方案**: 使用 composable `useResizable` → 需要在 MainLayout 中手动管理 DOM ref 和事件绑定，代码更分散。组件方案更符合 Vue 的声明式风格。

### Decision 2: 宽度状态由 MainLayout 统一管理

**选择**: 在 `MainLayout.vue` 中使用 `ref<number>` 管理 sidebarWidth 和 keyPanelWidth，通过 inline style 绑定到面板组件。

**理由**: MainLayout 是三栏布局的容器，由它统一管理宽度状态最自然。面板组件不需要知道自己的宽度是如何确定的。

**备选方案**: 使用 Pinia store 管理宽度 → 过度设计，宽度状态不需要跨组件共享（只有 MainLayout 需要）。

### Decision 3: 使用 Pointer Events API 处理拖拽

**选择**: 使用 `pointerdown` → `pointermove` → `pointerup` 事件链，配合 `setPointerCapture` 确保拖拽不丢失。

**理由**: Pointer Events 统一了鼠标和触控笔输入，`setPointerCapture` 保证即使鼠标移出分隔条区域也能继续接收事件，避免拖拽中断。

**备选方案**: 使用 mousedown + document mousemove → 需要手动管理全局事件监听器的添加/移除，且不支持 pointer capture。

### Decision 4: 面板宽度约束

**选择**:
| 面板 | 默认宽度 | 最小宽度 | 最大宽度 |
|------|---------|---------|---------|
| Sidebar | 240px | 160px | 400px |
| KeyPanel | 320px | 200px | 500px |

**理由**: 最小宽度确保面板内容可读（Sidebar 至少能显示连接名，KeyPanel 至少能显示键名和类型标签）。最大宽度防止 Workspace 被压缩到不可用。

### Decision 5: localStorage 持久化

**选择**: 使用 key `srn-panel-widths` 存储 JSON `{ sidebar: number, keyPanel: number }`。启动时读取，拖拽结束时写入（非实时写入，避免频繁 IO）。

**理由**: 简单直接，无需额外依赖。仅在 pointerup 时写入，性能开销可忽略。

## Risks / Trade-offs

- [拖拽时 iframe/webview 内容可能捕获事件] → 使用 `setPointerCapture` + 拖拽时在 body 上添加 `user-select: none` 和覆盖层
- [与面板显隐动画冲突] → 面板隐藏时不渲染对应的分隔条（v-if 联动 sidebarVisible/keyPanelVisible）
- [响应式断点下宽度冲突] → < 900px 单栏模式下不显示分隔条，面板宽度约束不生效
- [性能：频繁 style 更新] → 使用 CSS `will-change: width` 提示浏览器优化，拖拽时禁用面板 transition
