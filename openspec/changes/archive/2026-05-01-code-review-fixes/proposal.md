## Why

全局代码走查发现 12 个问题，涵盖死锁风险、功能缺失、前后端协议不一致、性能瓶颈等，部分问题会导致运行时崩溃或功能完全失效，需要集中修复以保证应用稳定性和正确性。

## What Changes

- **[修复] `export_keys_json` 死锁风险**：在持有 session 锁期间再次锁 manager，形成潜在死锁；需重构为先获取 config 再获取 session。
- **[修复] `key_scan_memory_export_csv` 占位实现**：当前返回空 CSV（仅表头），需实现真实的内存分析结果导出逻辑。
- **[修复] `key_analyzer` 串行 Redis 命令**：每个 key 发出 4 个串行命令，需改为 pipeline 批量执行，与 `key_browser` 保持一致。
- **[修复] `useShortcut` 自定义快捷键不生效**：`customBindings` 加载后从未被 `handleKeydown` 读取，需在快捷键匹配逻辑中优先查找自定义绑定。
- **[修复] `serverVersion` 永远为 null**：连接成功后未执行 INFO 命令更新版本号，需在连接建立后获取并填充。
- **[修复] `export_db_json` 逐 key 加锁性能问题**：每次导出一个 key 都获取/释放 session 锁，需批量处理或持锁完成整个导出循环。
- **[修复] `heartbeat` 状态序列化大小写不一致**：后端 `ConnectionState` 枚举序列化为首字母大写（`Connected`），前端期望全小写（`connected`），需添加 `#[serde(rename_all = "snake_case")]`。
- **[修复] 多 Tab CLI 历史记录不持久化**：多 Tab 模式历史仅存内存，与单 Tab 的 SQLite 持久化行为不一致，需统一持久化策略。
- **[修复] `cliHistoryGetTab` IPC 封装缺失**：后端已注册 `cli_history_get_tab` 命令，但前端 `phase4.ts` 中无对应封装函数。
- **[修复] `healthCheckExportMarkdown` 前后端参数不匹配**：前端调用缺少 `conn_id` 参数，导致命令调用直接报错。
- **[修复] `masking_rule_reorder` 缺少事务保护**：N 次独立 SQL 更新无事务包裹，部分失败会导致数据不一致。
- **[优化] `BrowserWorkspace` key 类型检测**：当前仅靠前缀启发式判断，已有手动切换兜底，维持现状可接受，本次不修改。

## Capabilities

### New Capabilities

- `bug-fixes-code-review`: 本次走查发现的所有 bug 修复，不引入新的用户可见功能，仅修复现有功能的正确性与稳定性。

### Modified Capabilities

- `data-import-export`: `export_keys_json` 死锁修复 + `export_db_json` 性能修复 + `key_scan_memory_export_csv` 实现补全。
- `key-analyzer`: 将串行 Redis 命令改为 pipeline 批量执行。
- `shortcut-customization`: 修复自定义快捷键绑定不生效的问题。
- `connection-manager`: 修复 `serverVersion` 未更新 + `heartbeat` 状态序列化大小写不一致。
- `multi-tab-cli`: 修复历史记录不持久化 + 补全 `cliHistoryGetTab` IPC 封装。
- `health-check-report`: 修复 `healthCheckExportMarkdown` 前后端参数不匹配。
- `data-masking`: 为 `masking_rule_reorder` 添加事务保护。

## Impact

- **Rust 后端**：`src-tauri/src/commands/import_export.rs`、`src-tauri/src/services/key_analyzer.rs`、`src-tauri/src/services/heartbeat.rs`、`src-tauri/src/utils/config_store.rs`、`src-tauri/src/commands/tools.rs`
- **前端 TypeScript**：`src/composables/useShortcut.ts`、`src/ipc/phase4.ts`、`src/stores/connection.ts`、`src/stores/terminal.ts`
- **无 API 变更**：所有修复均为内部实现修正，不涉及 IPC 接口签名变更（除补全缺失的 `cliHistoryGetTab` 封装）
- **无数据库 schema 变更**：多 Tab CLI 历史持久化复用现有 `cli_history` 表结构
