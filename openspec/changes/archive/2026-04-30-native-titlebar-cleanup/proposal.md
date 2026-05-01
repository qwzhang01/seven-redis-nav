## Why

当前窗口有 3 行头部区域：原生 macOS 标题栏（38px）、Vue Titlebar 组件（38px）、Vue Toolbar 组件（48px），总计 124px。Vue Titlebar 与原生标题栏功能重叠（都显示应用名），浪费了垂直空间。

采用方案 B：保留纯原生标题栏，删除 Vue Titlebar 组件，通过 Tauri API `window.setTitle()` 动态更新标题文字（如 "Seven Redis Nav — production-cluster-01"）。同时，登录页（WelcomePage）不需要显示 Toolbar 行，因为登录页没有浏览器/命令行/监控等 Tab 功能。

## What Changes

- **删除** `Titlebar.vue` 组件及其在 `MainLayout.vue` 中的引用
- **删除** CSS 变量 `--srn-titlebar-h`（不再需要）
- **修改** `MainLayout.vue` 布局：登录页状态下隐藏 Toolbar 行，仅在已连接状态下显示
- **新增** 动态标题功能：连接成功后通过 Tauri `window.setTitle()` 更新原生标题栏文字，断开连接时恢复默认标题
- **迁移** Titlebar 上的刷新/分享按钮到 Toolbar 的右侧区域

## Capabilities

### New Capabilities
- `dynamic-title`: 通过 Tauri API 动态更新原生窗口标题，根据连接状态显示不同文字

### Modified Capabilities
- `app-shell`: 删除 Titlebar 组件，调整 MainLayout 布局逻辑（登录页隐藏 Toolbar），迁移操作按钮到 Toolbar

## Impact

- **前端组件**: 删除 `src/components/window/Titlebar.vue`，修改 `src/views/MainLayout.vue`、`src/components/window/Toolbar.vue`
- **样式**: 修改 `src/styles/tokens.css` 删除 `--srn-titlebar-h` 变量
- **Tauri API**: 新增 `@tauri-apps/api/window` 的 `setTitle` 调用
- **无后端改动**: 不涉及 Rust 代码变更
- **无 Breaking Change**: 纯 UI 层调整，不影响数据和连接逻辑
