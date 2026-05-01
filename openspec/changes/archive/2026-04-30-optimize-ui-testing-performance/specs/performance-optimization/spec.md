## ADDED Requirements

### Requirement: 懒加载机制
The system SHALL implement lazy loading for large data content to improve rendering performance.

**当前状态**：`StringViewer.vue` 和 `HashViewer.vue` 已实现基于 Intersection Observer 的懒加载：
- `StringViewer`：数据超过 10KB 时启用懒加载，进入视口后才渲染完整内容
- `HashViewer`：字段数超过 100 个时启用懒加载，进入视口后才渲染完整表格

**已知 Bug**：`StringViewer.vue` 的 `truncatedValue` 计算属性对 `{ value: string }` 包装对象处理错误，导致显示 JSON 字符串而非原始值。

#### Scenario: 字符串值正确显示
- **WHEN** 用户查看 string 类型的 Redis 键
- **THEN** `StringViewer` 应显示原始字符串值（如 `Hello, Redis!`），不显示 JSON 包装（如 `{"value":"Hello, Redis!"}`）

#### Scenario: 大数据懒加载
- **WHEN** 用户查看超过 10KB 的字符串值
- **THEN** 组件应显示占位符，滚动到可视区域后自动加载完整内容

#### Scenario: 哈希字段懒加载
- **WHEN** 用户查看超过 100 个字段的哈希
- **THEN** 组件应显示前 10 个字段的预览，滚动到可视区域后加载完整字段列表

### Requirement: 数据分页加载
The system SHALL implement pagination for key browsing to handle large Redis databases.

**当前状态**：`keyBrowser.ts` store 已实现完整的分页逻辑：
- `scan(cursor)`：扫描指定游标位置的键
- `loadMore()`：追加下一批键（用于无限滚动）
- `nextPage()` / `prevPage()`：翻页导航
- `allKeysLoaded`：标记是否已加载所有键

#### Scenario: 键列表分页浏览
- **WHEN** 用户浏览包含大量键的 Redis 数据库
- **THEN** 键列表应分批次加载，每批约 100 个键（由后端 SCAN 命令控制）

#### Scenario: 无限滚动加载
- **WHEN** 用户滚动到键列表底部
- **THEN** 系统应自动调用 `loadMore()` 追加下一批键，不重置已有列表

### Requirement: 内存管理优化
The system SHALL properly clean up resources when components are unmounted.

**当前状态**：`StringViewer.vue` 和 `HashViewer.vue` 的 `onUnmounted` 钩子已调用 `observer.value?.disconnect()`，但需要验证所有定时器和事件监听器也被正确清理。

#### Scenario: 组件卸载清理
- **WHEN** 用户切换工作区或关闭对话框
- **THEN** 系统应正确清理 Intersection Observer、定时器等资源，防止内存泄漏

#### Scenario: 连接状态监听清理
- **WHEN** 用户断开 Redis 连接
- **THEN** `connection.ts` 的 `stopListening()` 应被调用，清理 `unlistenFn`

### Requirement: 性能监控
The system SHALL provide basic performance visibility for debugging.

**当前状态**：暂无性能监控实现，此需求为未来规划。

#### Scenario: 渲染性能可观测
- **WHEN** 开发者需要排查性能问题
- **THEN** 应能通过 Vue DevTools 或浏览器 Performance 面板观察组件渲染时间
