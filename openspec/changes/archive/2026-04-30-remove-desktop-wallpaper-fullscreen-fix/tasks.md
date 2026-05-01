## 1. 移除 DesktopWallpaper 组件

- [x] 1.1 删除 `src/components/window/DesktopWallpaper.vue` 文件
- [x] 1.2 从 `src/views/MainLayout.vue` 中移除 `DesktopWallpaper` 的 import 和 `<DesktopWallpaper />` 标签

## 2. 移除窗口最大宽度限制

- [x] 2.1 从 `src/styles/tokens.css` 中删除 `--srn-window-max-w: 1400px` 变量
- [x] 2.2 从 `src/views/MainLayout.vue` 的 `.mac-window` 样式中移除 `max-width: var(--srn-window-max-w)` 和 `margin: 0 auto` 属性

## 3. 验证

- [x] 3.1 确认应用正常启动，内容铺满窗口，无左右空白或彩色渐变
- [x] 3.2 确认全屏模式下内容完全铺满屏幕
- [x] 3.3 确认响应式断点（窗口缩小到 1100px 以下、900px 以下）仍正常工作
