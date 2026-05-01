## 1. ResizeSplitter 组件

- [x] 1.1 创建 `src/components/common/ResizeSplitter.vue`：渲染 4px 宽的垂直分隔条，支持 hover/active 视觉状态切换（透明 → `rgba(0,0,0,0.08)` → `var(--srn-color-info)`）
- [x] 1.2 实现 pointer events 拖拽逻辑：`pointerdown` 启动拖拽 + `setPointerCapture`，`pointermove` 计算偏移量并 emit `resize` 事件，`pointerup` 结束拖拽并 emit `resize-end` 事件
- [x] 1.3 实现双击重置：监听 `dblclick` 事件，emit `reset` 事件
- [x] 1.4 拖拽期间在 document.body 添加 `cursor: col-resize` 和 `user-select: none`，拖拽结束后移除

## 2. MainLayout 集成

- [x] 2.1 在 `MainLayout.vue` 中添加 `sidebarWidth` 和 `keyPanelWidth` 响应式变量，初始值从 localStorage 读取（fallback 到 CSS 变量默认值 240/320）
- [x] 2.2 在 Sidebar 与 KeyPanel 之间插入 `<ResizeSplitter>`，绑定 `@resize` 更新 `sidebarWidth`，绑定 `@reset` 重置为 240px
- [x] 2.3 在 KeyPanel 与 Workspace 之间插入 `<ResizeSplitter>`，绑定 `@resize` 更新 `keyPanelWidth`，绑定 `@reset` 重置为 320px
- [x] 2.4 通过 CSS 变量覆盖 `:style` 将宽度绑定到 Sidebar 和 KeyPanel（覆盖组件内部的 CSS 变量宽度）
- [x] 2.5 实现宽度约束 clamp 逻辑：Sidebar [160, 400]，KeyPanel [200, 500]
- [x] 2.6 分隔条与面板显隐联动：`v-if="sidebarVisible"` 控制第一个分隔条，`v-if="keyPanelVisible"` 控制第二个分隔条

## 3. 持久化

- [x] 3.1 实现 `resize-end` 时将 `{ sidebar: number, keyPanel: number }` 写入 localStorage key `srn-panel-widths`
- [x] 3.2 实现双击重置后同步更新 localStorage
- [x] 3.3 应用启动时从 localStorage 读取并 clamp 到有效范围

## 4. 样式与动画兼容

- [x] 4.1 拖拽期间禁用面板的 width transition（添加 `.resizing` class 到 `.window-body`）
- [x] 4.2 双击重置时启用 transition 实现平滑过渡动画
- [x] 4.3 确保面板 slide 显隐动画与动态宽度兼容（隐藏时 width → 0，显示时恢复到存储的宽度）

## 5. 验证

- [x] 5.1 验证拖拽 Sidebar 分隔条可流畅调整 Sidebar 宽度，松开后保持
- [x] 5.2 验证拖拽 KeyPanel 分隔条可流畅调整 KeyPanel 宽度，松开后保持
- [x] 5.3 验证宽度约束生效：无法拖拽超出 min/max 范围
- [x] 5.4 验证双击分隔条恢复默认宽度（带平滑动画）
- [x] 5.5 验证刷新页面后面板宽度从 localStorage 恢复
- [x] 5.6 验证 ⌘1/⌘2 隐藏面板时对应分隔条同步隐藏，恢复时分隔条重新出现
- [x] 5.7 验证窗口宽度 < 900px 时分隔条不显示
