## Context

Redis 导航工具基于 **Tauri + Vue 3 + TypeScript** 构建，使用 Pinia 状态管理，已具备以下工作区：
- `BrowserWorkspace`：键浏览器，支持 string/hash/list/set/zset 类型查看和编辑
- `CliWorkspace`：Redis CLI 终端
- `MonitorWorkspace`：实时监控（OPS、内存、客户端数）
- `SlowlogWorkspace`：慢日志查看
- `PubsubWorkspace`：发布/订阅
- `ServerConfigWorkspace`：服务器配置

已有基础设施：
- `src/styles/tokens.css`：完整的 CSS 设计令牌系统（颜色、间距、字体、圆角、阴影、动效）
- `src/components/ui/`：基础 UI 组件库（Button、Input、DataDisplay）
- Vitest 测试框架已配置，`src/test/setup.ts` 和 `src/test/utils.ts` 已就绪
- 部分测试文件已存在：`connection.test.ts`、`data.test.ts`、`StringViewer.test.ts`、`HashViewer.test.ts`、`BrowserWorkspace.test.ts`

**当前测试运行结果（`pnpm test:run`）**：
- 93 个测试用例，11 个失败
- `data.test.ts`：21 个全部通过 ✅
- `connection.test.ts`：24 个，4 个失败 ❌
- `StringViewer.test.ts`：10 个，4 个失败 ❌
- `HashViewer.test.ts`：15 个，1 个失败 ❌
- `BrowserWorkspace.test.ts`：23 个，2 个失败 ❌

## Goals / Non-Goals

**Goals:**
- 修复所有现有测试 bug，使 93 个测试用例全部通过
- 修复对应的组件 bug（测试失败往往反映了真实的组件问题）
- 完善各工作区视觉一致性（统一空状态、加载状态、错误状态的样式）
- 完善性能优化的边界情况处理（内存清理、数据格式处理）

**Non-Goals:**
- 不重写现有核心业务逻辑
- 不改变现有的数据结构和 IPC 通信机制
- 不引入新的第三方依赖
- 不破坏现有的用户工作流程
- 不实现 E2E 测试（Playwright 配置留待后续）

## Decisions

### 1. Pinia Store 属性访问方式
- **问题**：`connection.test.ts` 中大量使用 `connectionStore.activeConnId = 'conn1'` 直接赋值，但也有部分错误地使用了 `connectionStore.activeConnId.value = 'conn1'`
- **决策**：Pinia `defineStore` 中的 `ref` 在 store 外部访问时已自动解包，应直接赋值 `store.activeConnId = 'conn1'`，而不是 `store.activeConnId.value = 'conn1'`
- **影响文件**：`src/stores/connection.test.ts`

### 2. StringViewer 数据格式处理
- **问题**：测试中 `value` 是 `{ value: 'Hello, Redis!' }` 对象，但 `truncatedValue` 计算属性对非字符串直接 `JSON.stringify`，导致显示 `{"value":"Hello, Redis!"}` 而非 `Hello, Redis!`
- **决策**：`StringViewer.vue` 的 `truncatedValue` 应先尝试提取 `value.value`（字符串类型的 Redis 值通常包装在 `{ value: string }` 中），再 fallback 到 `JSON.stringify`
- **影响文件**：`src/components/workspaces/browser/StringViewer.vue`

### 3. HashViewer 可访问性
- **问题**：`HashViewer.vue` 中所有 `<button>` 元素缺少 `type="button"` 属性，测试断言 `button.attributes('type')` 为 `'button'` 失败
- **决策**：为所有 `<button>` 添加 `type="button"`，这也是 HTML 最佳实践（防止在 form 中意外触发 submit）
- **影响文件**：`src/components/workspaces/browser/HashViewer.vue`

### 4. BrowserWorkspace TTL 格式化
- **问题**：`formatTTL(3600)` 当前返回 `60m 0s`（因为 `ttl > 60` 分支先匹配），但测试期望 `1h 0m`
- **决策**：修正 `formatTTL` 的条件判断顺序，`ttl >= 3600` 应在 `ttl > 60` 之前判断
- **影响文件**：`src/components/workspaces/browser/BrowserWorkspace.vue`

### 5. BrowserWorkspace 重命名对话框
- **问题**：测试期望重命名对话框中 `.btn-save` 在输入为空时有 `disabled` 属性，但当前实现 `:disabled="!newKeyName"` 在初始值等于当前键名时不为空，导致按钮不被禁用
- **决策**：重命名对话框的保存按钮应在新键名与原键名相同或为空时禁用
- **影响文件**：`src/components/workspaces/browser/BrowserWorkspace.vue`

### 6. saveTempConnection 测试签名
- **问题**：`saveTempConnection` 实际签名是 `saveTempConnection(name: string, groupName: string = '')` 需要 `name` 参数，但测试中调用 `connectionStore.saveTempConnection()` 不传参数
- **决策**：测试应传入必要参数，或修改 store 方法使 `name` 可选（从 `tempConnectionConfig` 中读取）
- **影响文件**：`src/stores/connection.test.ts` 和 `src/stores/connection.ts`

## Risks / Trade-offs

**Risks:**
- [测试修复可能暴露更多 bug] → 逐一分析每个失败测试，确保修复方向正确
- [组件 bug 修复可能影响现有功能] → 修复前后对比组件行为，确保向后兼容

**Trade-offs:**
- 修复测试 vs 修改测试期望：优先修复组件 bug，使组件行为符合测试期望（测试代表正确的行为规范）
- 完整性 vs 速度：先修复阻塞测试的 bug，再完善 UI 一致性细节
