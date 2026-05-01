## Context

当前 Seven Redis Nav 的窗口头部由 3 层组成：

1. **原生 macOS 标题栏**（38px）：系统交通灯 + "Seven Redis Nav" 文字，由 `decorations: true` 提供
2. **Vue Titlebar 组件**（38px）：`src/components/window/Titlebar.vue`，显示应用图标 + 名称 + 连接名 + 刷新/分享按钮
3. **Vue Toolbar 组件**（48px）：`src/components/window/Toolbar.vue`，显示 Tab 切换 + 搜索框 + 连接状态

Titlebar 与原生标题栏功能重叠，且登录页（WelcomePage）不需要 Toolbar（没有 Tab 功能可用）。

## Goals / Non-Goals

**Goals:**
- 删除 Vue Titlebar 组件，减少 38px 垂直空间浪费
- 通过 Tauri `window.setTitle()` 动态更新原生标题栏文字，保留连接信息展示
- 登录页隐藏 Toolbar，仅在已连接状态下显示
- 将 Titlebar 上的刷新/分享按钮迁移到 Toolbar 右侧

**Non-Goals:**
- 不改变原生标题栏样式（不使用 `titleBarStyle: overlay`）
- 不修改 Toolbar 的 Tab 切换逻辑
- 不涉及后端 Rust 代码变更
- 不改变 Statusbar 的行为

## Decisions

### D1: 使用纯原生标题栏 + `setTitle()` 动态更新

**选择**: 保留 `decorations: true`，通过 `@tauri-apps/api/window` 的 `getCurrentWindow().setTitle()` 动态设置标题文字。

**替代方案**: 使用 `titleBarStyle: overlay` 让交通灯叠加在 WebView 上，自定义标题栏内容。

**理由**: 方案 B（纯原生）更简单，不需要处理交通灯偏移、拖拽区域等复杂问题。虽然标题只能是纯文本，但对于显示 "Seven Redis Nav — connection-name" 已经足够。

### D2: 刷新/分享按钮迁移到 Toolbar

**选择**: 将 Titlebar 上的刷新和分享按钮移到 Toolbar 右侧（连接状态指示器旁边）。

**理由**: Toolbar 是已连接状态下唯一的操作栏，按钮放在这里符合用户操作习惯。

### D3: 登录页条件隐藏 Toolbar

**选择**: 在 `MainLayout.vue` 中通过 `v-if="store.connected"` 条件渲染 Toolbar。

**理由**: 登录页没有浏览器/命令行/监控等 Tab 功能，显示 Toolbar 没有意义，隐藏后可以让登录页更简洁。

### D4: 动态标题的触发时机

**选择**: 在 `useWorkspaceStore` 或连接状态变化时调用 `setTitle()`：
- 未连接时：`"Seven Redis Nav"`
- 已连接时：`"Seven Redis Nav — <connection-name>"`

**理由**: 标题跟随连接状态变化，用户一眼就能看到当前连接的是哪个 Redis 实例。

## Risks / Trade-offs

- **[纯文本限制]** → 原生标题栏只能显示纯文本，无法放图标或彩色元素。对于当前需求已足够，未来如需更丰富的标题栏可切换到 overlay 方案。
- **[按钮位置变化]** → 刷新/分享按钮从标题栏移到工具栏，用户需要适应新位置。由于是早期开发阶段，影响可忽略。
- **[Tauri API 依赖]** → `setTitle()` 是 Tauri 标准 API，稳定可靠，无风险。
