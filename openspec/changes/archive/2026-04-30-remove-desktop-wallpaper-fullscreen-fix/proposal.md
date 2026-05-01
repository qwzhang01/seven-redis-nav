## Why

应用全屏后，左右两侧出现粉紫色渐变条（DesktopWallpaper 背景），主内容区域被 `max-width: 1400px` 限制无法铺满屏幕。作为 Tauri 原生桌面应用，不需要模拟"macOS 桌面上的窗口"效果——应用本身就是窗口，内容应当铺满整个窗口区域。

## What Changes

- **移除** `DesktopWallpaper` 组件及其在 `MainLayout.vue` 中的引用，不再渲染模拟桌面壁纸
- **移除** `.mac-window` 的 `max-width: 1400px` 限制，使内容区域铺满整个窗口宽度
- **移除** CSS 变量 `--srn-window-max-w`（如存在），因为不再需要窗口最大宽度约束
- **保留** 窗口最小宽度/高度约束（由 Tauri 配置 `minWidth: 960, minHeight: 600` 控制）

## Capabilities

### New Capabilities

（无新增 capability）

### Modified Capabilities

- `app-shell`: 移除"桌面壁纸背景"requirement，修改"主窗口布局结构"中的窗口最大宽限制为无限制（铺满窗口）

## Impact

- **前端组件**: `src/components/window/DesktopWallpaper.vue` 将被删除
- **布局视图**: `src/views/MainLayout.vue` 移除 DesktopWallpaper 引用和 max-width 约束
- **样式令牌**: `src/styles/tokens.css` 中 `--srn-window-max-w` 变量将被移除或修改
- **无破坏性变更**: 不影响任何功能逻辑，仅为视觉布局调整
