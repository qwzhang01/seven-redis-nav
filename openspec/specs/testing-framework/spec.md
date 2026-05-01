## ADDED Requirements

### Requirement: 单元测试覆盖
The system SHALL provide comprehensive unit test coverage for all core components and business logic.

**当前状态**：Vitest 已配置，`src/test/setup.ts` 和 `src/test/utils.ts` 已就绪。已有测试文件：`connection.test.ts`（24 个用例，4 个失败）、`data.test.ts`（21 个用例，全部通过）、`StringViewer.test.ts`（10 个用例，4 个失败）、`HashViewer.test.ts`（15 个用例，1 个失败）、`BrowserWorkspace.test.ts`（23 个用例，2 个失败）。

#### Scenario: Pinia Store 测试
- **WHEN** 运行 `connection.test.ts`
- **THEN** 所有 24 个测试用例应通过
- **AND** Pinia store 属性应通过直接赋值访问（`store.prop = value`），不使用 `.value`
- **AND** `unlistenFn` 应在 store 的 `return` 中暴露，初始值为 `null`

#### Scenario: 组件单元测试
- **WHEN** 运行 `StringViewer.test.ts`
- **THEN** 所有 10 个测试用例应通过
- **AND** `textarea.element.value` 应显示提取后的字符串值（不是 JSON 包装对象）

#### Scenario: 组件可访问性测试
- **WHEN** 运行 `HashViewer.test.ts`
- **THEN** 所有 15 个测试用例应通过
- **AND** 所有 `<button>` 元素应有 `type="button"` 属性

### Requirement: 集成测试支持
The system SHALL support integration testing for component interactions and data flow.

**当前状态**：`BrowserWorkspace.test.ts` 已实现 23 个集成测试用例，覆盖空状态、键显示、标签页导航、数据查看器、对话框交互、Toast 通知等场景。

#### Scenario: BrowserWorkspace 集成测试
- **WHEN** 运行 `BrowserWorkspace.test.ts`
- **THEN** 所有 23 个测试用例应通过
- **AND** `formatTTL(3600)` 应返回 `1h 0m`（不是 `60m 0s`）
- **AND** 重命名对话框在初始状态（新键名等于原键名）时 `.btn-save` 应被禁用

### Requirement: 测试报告和覆盖率
The system SHALL generate detailed test reports and coverage metrics。

**当前状态**：`pnpm test:run` 可运行所有测试，`pnpm test` 可进入 watch 模式。

#### Scenario: 全量测试通过
- **WHEN** 运行 `pnpm test:run`
- **THEN** 所有 93 个测试用例应全部通过，0 个失败

#### Scenario: 测试结果展示
- **WHEN** 测试执行完成
- **THEN** 系统应提供清晰的测试结果摘要，显示通过/失败数量和失败详情
