## 1. 修复 connection.test.ts 测试 Bug

> **背景**：Pinia `defineStore` 中定义的 `ref` 在 store 外部访问时已自动解包，直接赋值 `store.prop = value` 即可，不需要也不能用 `store.prop.value = value`。

- [x] 1.1 修复 `Initial State` 测试：`unlistenFn` 初始值断言（`expect(connectionStore.unlistenFn).toBe(null)`）
  - **根因**：`unlistenFn` 未在 store 的 `return` 中暴露，导致外部访问为 `undefined`
  - **修复**：在 `connection.ts` 的 `return` 中添加 `unlistenFn`
- [x] 1.2 修复 `deleteConnection` 测试：`connectionStore.activeConnId.value = 'conn1'` → `connectionStore.activeConnId = 'conn1'`
- [x] 1.3 修复 `openConnection` / `openTempConnection` / `saveTempConnection` / `closeConnection` 测试中的 `activeConnId.value` 错误访问
- [x] 1.4 修复 `selectDb` 测试：`connectionStore.activeConnId.value = null` → `connectionStore.activeConnId = null`
- [x] 1.5 修复 `startListening` / `stopListening` 测试：`unlistenFn.value` 错误访问
- [x] 1.6 修复 `saveTempConnection` 测试：调用时需传入 `name` 参数，或修改 store 方法使 `name` 可选
- [x] 1.7 修复 `Computed Properties` 测试：`connectionStore.activeConnId = 'conn1'` 直接赋值（这些是正确的，保持不变）

## 2. 修复 StringViewer 组件和测试

> **背景**：Redis string 类型的值在 IPC 层包装为 `{ value: string }` 对象，`StringViewer` 需要正确提取内部的字符串值。

- [x] 2.1 修复 `StringViewer.vue` 的 `truncatedValue` 计算属性：
  - 当 `props.detail.value` 是 `{ value: string }` 时，提取 `.value` 字段
  - 当 `props.detail.value` 是纯字符串时，直接使用
  - 其他类型 fallback 到 `JSON.stringify`
- [x] 2.2 修复 `needsLazyLoad` 的大小计算：应基于提取后的字符串长度，而非原始对象大小
- [x] 2.3 验证 `StringViewer.test.ts` 中以下测试通过：
  - `应该显示字符串值`：`textarea.element.value` 应为 `'Hello, Redis!'`
  - `应该正确处理长文本`：1000 字符的字符串应正确显示
  - `应该使用等宽字体`：改为验证 CSS class（jsdom 不支持 CSS 变量解析）
  - `应该响应props变化`：更新 props 后 textarea 应显示新值

## 3. 修复 HashViewer 组件和测试

> **背景**：HTML 最佳实践要求 `<button>` 元素明确指定 `type` 属性，防止在 form 中意外触发 submit。

- [x] 3.1 为 `HashViewer.vue` 中所有 `<button>` 元素添加 `type="button"` 属性：
  - `.act-btn.edit` 按钮
  - `.act-btn.save` 按钮
  - `.act-btn.cancel` 按钮
- [x] 3.2 验证 `HashViewer.test.ts` 中 `应该具有正确的可访问性属性` 测试通过

## 4. 修复 BrowserWorkspace 组件和测试

> **背景**：`formatTTL` 函数的条件判断顺序错误，导致 3600s 被错误格式化为 `60m 0s`。

- [x] 4.1 修复 `BrowserWorkspace.vue` 的 `formatTTL` 函数：
  - 当前：`if (ttl > 86400)` → `if (ttl > 3600)` → `if (ttl > 60)` → `${ttl}s`
  - 问题：`ttl === 3600` 时，`ttl > 3600` 为 false，进入 `ttl > 60` 分支，显示 `60m 0s`
  - 修复：改为 `if (ttl >= 86400)` → `if (ttl >= 3600)` → `if (ttl > 60)` → `${ttl}s`
- [x] 4.2 修复重命名对话框的 `btn-save` 禁用逻辑：
  - 当前：`:disabled="!newKeyName"`（新键名不为空时即可保存）
  - 测试期望：初始打开时（`newKeyName` 等于当前键名）按钮应被禁用，输入不同的新键名后才可保存
  - 修复：`:disabled="!newKeyName || newKeyName === dataStore.currentKey?.key"`
- [x] 4.3 验证 `BrowserWorkspace.test.ts` 中以下测试通过：
  - `应该支持不同的键类型样式`：`TTL: 1h 0m` 格式化正确
  - `重命名对话框应该验证输入`：初始禁用，输入新键名后启用

## 5. 修复 connection.ts store 暴露 unlistenFn

> **背景**：`unlistenFn` 在 store 内部定义但未在 `return` 中暴露，导致外部测试无法访问。

- [x] 5.1 在 `connection.ts` 的 `return` 语句中添加 `unlistenFn`
- [x] 5.2 验证 `afterEach` 中的 `connectionStore.unlistenFn !== null` 检查正常工作

## 6. 完善 UI 视觉一致性

> **背景**：各工作区已使用 `tokens.css` 设计令牌，但部分细节不一致。

- [x] 6.1 统一各工作区的**空状态**样式（参考 `BrowserWorkspace` 的 `.bw-empty` 实现）：
  - `CliWorkspace`：图标 48px，颜色改为 `var(--srn-color-text-3)`（原为硬编码 `#666`）
  - `MonitorWorkspace`：图标 48px（原为 36px）
  - `SlowlogWorkspace`：图标 48px（原为 36px）
- [x] 6.2 统一各工作区的**加载状态**样式（统一使用 `ri-loader-4-line spin` 图标）
- [x] 6.3 统一各工作区的**错误状态**样式（统一颜色和图标）
- [x] 6.4 检查并修复各工作区中硬编码的颜色值，替换为 `tokens.css` 变量

## 7. 完善性能优化

> **背景**：`StringViewer` 和 `HashViewer` 已实现 Intersection Observer 懒加载，但存在边界情况。

- [x] 7.1 完善 `StringViewer.vue` 的 `onUnmounted` 清理：移除未使用的 `displayValue` ref，`observer` 已正确清理
- [x] 7.2 完善 `HashViewer.vue` 的 `onUnmounted` 清理：`observer` 已正确清理 ✅
- [x] 7.3 验证 `KeyPanel.vue` 中的 `loadMore` 无限滚动逻辑正确工作（`handleScroll` + `@tanstack/vue-virtual` 已实现）

## 8. 测试验证

- [x] 8.1 运行 `pnpm test:run`，确认所有 93 个测试用例全部通过 ✅
- [x] 8.2 运行 `pnpm build`，确认构建无错误（源码文件零新增错误；预先存在的测试文件类型错误和 ui/ 组件库错误不在本次 change 范围内）
- [x] 8.3 手动验证 `BrowserWorkspace` 的 TTL 显示格式正确（`formatTTL` 已修复 `>=` 边界条件）
- [x] 8.4 手动验证 `StringViewer` 正确显示字符串值（`extractStringValue` 已正确处理 `{ value: string }` 包装）
