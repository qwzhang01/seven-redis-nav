## MODIFIED Requirements

### Requirement: 主窗口布局结构

应用主窗口 SHALL 按自上而下顺序呈现五个固定区域：原生标题栏、Toolbar（仅已连接时显示）、主体（Sidebar + KeyPanel + Workspace 三栏）、Statusbar，且各区域尺寸 MUST 与设计保持一致。

| 区域 | 尺寸 |
|---|---|
| 原生标题栏 | 系统默认（约 28px） |
| Toolbar | 高 48px（仅已连接时显示） |
| Sidebar | 宽 240px |
| KeyPanel | 宽 320px |
| Workspace | 自适应填满剩余空间 |
| Statusbar | 高 28px |
| 窗口最小宽 | 960px（由 Tauri 配置控制） |
| 窗口最小高 | 600px（由 Tauri 配置控制） |

主窗口容器 SHALL NOT 设置 max-width 限制，内容 MUST 铺满整个窗口宽度。

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
- **THEN** 三栏改为单栏纵向排列，Sidebar 高度上限 180px，KeyPanel 高度上限 300px

## REMOVED Requirements

### Requirement: 桌面壁纸背景

**Reason**: 作为 Tauri 原生桌面应用，应用本身就是系统窗口，不需要模拟 macOS 桌面壁纸效果。全屏时壁纸渐变色暴露在窗口两侧，导致视觉异常。

**Migration**: 移除 `DesktopWallpaper` 组件及其在 `MainLayout.vue` 中的引用。移除 CSS 变量 `--srn-window-max-w`。窗口背景由系统原生窗口装饰和应用内部 surface 颜色提供。
