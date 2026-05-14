## Why

Key 面板批量选择当前存在两个可见问题：首次在普通点击后按 Shift 做范围选择时，范围锚点不稳定，导致选中的 key 不符合用户预期；进入批量选择后，当前详情 key 的 active 高亮仍然显示，容易被误认为也是批量选中项，视觉上也显得杂乱。

## What Changes

- 修复首次 Shift-click 范围选择：普通点击过的当前 key 应作为后续 Shift 范围选择锚点。
- 明确“当前详情 key”和“批量选中 key”的语义边界：普通点击只打开详情并清空批量选择，不应进入批量操作选中集。
- 批量选择模式下弱化/隐藏当前详情 key 的 active 选中样式，只突出显示真正进入批量操作的 key。
- 清理筛选、刷新、批量操作完成后的选择锚点，避免过期锚点影响下一次 Shift 选择。
- 不引入破坏性 API 变更。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `bulk-key-operations`: 修正 key 面板批量选择的 Shift 范围选择语义、普通点击与批量选中语义、批量模式下 active key 的展示规则。

## Impact

- 主要影响前端 Key 面板交互：`src/components/keypanel/KeyPanel.vue`、`src/stores/keyBrowser.ts`。
- 可能影响批量操作栏状态同步：`src/components/keypanel/BulkActionBar.vue`。
- 需要补充/调整批量选择相关单元测试或组件交互测试。
