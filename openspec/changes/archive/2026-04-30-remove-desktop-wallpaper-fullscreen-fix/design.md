## Context

当前应用使用了一个 `DesktopWallpaper` 组件（`src/components/window/DesktopWallpaper.vue`）在窗口底层渲染模拟 macOS 桌面壁纸的多层径向渐变背景。同时 `.mac-window` 容器设置了 `max-width: 1400px`（通过 CSS 变量 `--srn-window-max-w`）并居中显示。

这个设计源自 HTML 原型（`docs/index.html`），原型在浏览器中模拟一个"macOS 桌面上的窗口"效果。但作为 Tauri 原生桌面应用，应用本身就是一个系统窗口，不需要再模拟桌面壁纸。当用户全屏时，1400px 的最大宽度限制导致内容无法铺满，两侧露出壁纸渐变色，视觉效果不佳。

## Goals / Non-Goals

**Goals:**
- 全屏时应用内容铺满整个窗口，无多余背景色
- 移除不必要的桌面壁纸模拟组件
- 简化组件层级，减少无用 DOM 节点

**Non-Goals:**
- 不修改窗口最小尺寸约束（保留 Tauri 配置中的 `minWidth: 960, minHeight: 600`）
- 不修改应用内部的布局结构（Sidebar/KeyPanel/Workspace 三栏布局不变）
- 不修改响应式断点逻辑

## Decisions

### Decision 1: 完全移除 DesktopWallpaper 组件

**选择**: 删除 `src/components/window/DesktopWallpaper.vue` 文件，并从 `MainLayout.vue` 中移除其引用。

**理由**: 作为原生桌面应用，模拟桌面壁纸没有实际意义。保留它只会增加 DOM 复杂度和潜在的渲染开销。

**备选方案**: 仅在全屏时隐藏壁纸 → 增加了不必要的状态管理复杂度，且非全屏时壁纸也无实际价值（Tauri 窗口本身就有系统级边框和背景）。

### Decision 2: 移除 max-width 限制，改为 100% 铺满

**选择**: 删除 `--srn-window-max-w: 1400px` CSS 变量，移除 `.mac-window` 的 `max-width` 和 `margin: 0 auto` 属性。

**理由**: 窗口大小由系统窗口管理器控制，应用内容应始终铺满整个窗口区域。

**备选方案**: 将 max-width 改为 100% → 效果相同但保留了无用的属性声明，不如直接移除干净。

## Risks / Trade-offs

- [超宽屏幕上内容过于分散] → 三栏布局中 Workspace 区域使用 `flex: 1` 自适应，内容本身有合理的内边距和最大宽度约束，不会出现阅读困难
- [移除壁纸后窗口边缘视觉变化] → 原生窗口由系统管理背景色，非全屏时窗口边缘由系统装饰处理，无需应用层干预
