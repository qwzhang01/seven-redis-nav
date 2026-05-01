## Why

Redis 导航工具（Tauri + Vue 3 + TypeScript）已完成核心功能开发，但存在以下三类问题需要系统性解决：

1. **UI 视觉不一致**：各工作区（Browser、CLI、Monitor、Slowlog、PubSub、ServerConfig）在按钮样式、间距、字体、交互反馈等细节上存在差异，尽管已有 `tokens.css` 设计令牌系统，但部分组件仍使用硬编码值
2. **测试覆盖不足且存在 Bug**：已有 Vitest 测试框架和部分测试文件，但测试中存在多处错误（Pinia store ref 访问方式错误、组件 props 数据结构与实现不匹配、可访问性属性缺失），导致测试无法通过
3. **性能优化不完整**：`StringViewer` 和 `HashViewer` 已实现 Intersection Observer 懒加载，`keyBrowser` store 已实现分页和 `loadMore`，但存在数据格式处理 bug 和内存清理不完善的问题

## What Changes

- **修复测试 Bug**：修正 `connection.test.ts` 中 Pinia store 属性访问方式、`StringViewer.test.ts` 中数据结构不匹配、`HashViewer.test.ts` 中可访问性断言、`BrowserWorkspace.test.ts` 中 TTL 格式化和对话框逻辑
- **修复组件 Bug**：为 `HashViewer.vue` 所有按钮添加 `type="button"`；修正 `StringViewer.vue` 中 `truncatedValue` 对嵌套对象的处理逻辑；修正 `BrowserWorkspace.vue` 中 TTL 格式化边界条件（3600s 应显示 `1h 0m`）
- **UI 一致性完善**：统一各工作区的空状态样式、加载状态样式、错误状态样式，确保所有工作区遵循 `tokens.css` 设计令牌
- **性能优化完善**：完善组件卸载时的资源清理，优化 `KeyPanel.vue` 中的虚拟滚动实现

## Capabilities

### Modified Capabilities
- **testing-framework**：修复现有测试 bug，使测试套件全部通过
- **component-library**：修复 `HashViewer`、`StringViewer`、`BrowserWorkspace` 组件 bug
- **ui-design-system**：完善各工作区视觉一致性
- **performance-optimization**：完善懒加载和内存管理

## Impact

- **代码影响**：`src/stores/connection.test.ts`、`src/components/workspaces/browser/` 下的组件和测试文件
- **API 影响**：无破坏性变更，仅修复 bug
- **依赖影响**：无新增依赖
- **测试影响**：修复后所有测试应全部通过（93 个测试用例）
