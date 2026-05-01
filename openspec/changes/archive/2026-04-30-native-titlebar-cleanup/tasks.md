## 1. 删除 Titlebar 组件

- [x] 1.1 从 `MainLayout.vue` 中移除 Titlebar 组件的 import 和模板引用
- [x] 1.2 删除 `src/components/window/Titlebar.vue` 文件
- [x] 1.3 从 `src/styles/tokens.css` 中删除 `--srn-titlebar-h` CSS 变量

## 2. 调整 Toolbar 显示逻辑

- [x] 2.1 在 `MainLayout.vue` 中将 Toolbar 用 `v-if="store.connected"` 包裹，登录页不显示
- [x] 2.2 将刷新和分享按钮添加到 `Toolbar.vue` 的右侧区域（`toolbar-right` 内）

## 3. 动态窗口标题

- [x] 3.1 创建 `src/composables/useWindowTitle.ts` composable，封装 `getCurrentWindow().setTitle()` 调用逻辑
- [x] 3.2 在 `MainLayout.vue` 中使用 `useWindowTitle`，监听连接状态变化并更新标题
- [x] 3.3 未连接时标题为 "Seven Redis Nav"，已连接时标题为 "Seven Redis Nav — <连接名>"

## 4. 验证

- [x] 4.1 启动应用确认登录页只显示原生标题栏，无 Titlebar 和 Toolbar
- [x] 4.2 连接后确认 Toolbar 出现，原生标题栏显示连接名
- [x] 4.3 断开连接后确认标题恢复为默认值，Toolbar 隐藏
