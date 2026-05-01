## Context

本次变更是对全局代码走查（2026-05-01）发现的 12 个问题的集中修复。项目为 Tauri + Vue 3 + Rust 架构的 Redis GUI 客户端，前后端通过 IPC 命令通信。

当前问题分布：
- **Rust 后端**：死锁风险、占位实现、性能瓶颈、序列化不一致、事务缺失
- **前端 TypeScript**：自定义快捷键不生效、serverVersion 未更新、IPC 封装缺失、参数不匹配

所有修复均为内部实现修正，不引入新的用户可见功能，不变更 IPC 接口签名（除补全缺失的 `cliHistoryGetTab` 封装）。

## Goals / Non-Goals

**Goals:**
- 消除 `export_keys_json` 中的死锁风险
- 实现 `key_scan_memory_export_csv` 的真实 CSV 导出
- 将 `key_analyzer` 的串行 Redis 命令改为 pipeline 批量执行
- 修复自定义快捷键绑定在 `handleKeydown` 中不生效
- 修复 `serverVersion` 连接后未更新
- 优化 `export_db_json` 的逐 key 加锁性能
- 修复 `heartbeat` 状态序列化大小写不一致（`Connected` → `connected`）
- 统一多 Tab CLI 历史记录持久化策略
- 补全 `cliHistoryGetTab` IPC 前端封装
- 修复 `healthCheckExportMarkdown` 前后端参数不匹配
- 为 `masking_rule_reorder` 添加事务保护

**Non-Goals:**
- 不引入新功能或新 UI
- 不变更数据库 schema（多 Tab CLI 历史复用现有 `cli_history` 表）
- 不修改 `BrowserWorkspace` 的 key 类型前缀检测逻辑（已有手动切换兜底）

## Decisions

### 决策 1：`export_keys_json` 死锁修复策略

**问题**：在持有 `session.lock()` 的 guard 期间，再次调用 `manager.lock()` 获取 config，而 `get_config_cloned` 内部也会锁 session，形成循环等待。

**决策**：重构为"先获取 config，再获取 session"的顺序，确保两个锁不会嵌套持有。具体：在获取 session guard 之前，先通过 `manager.lock()` 获取 `config`，然后释放 manager 锁，再获取 session 锁。

**备选方案**：将 config 和 session 合并为同一个锁对象 → 拒绝，会破坏现有架构。

### 决策 2：`export_db_json` 性能优化策略

**问题**：每导出一个 key 都获取/释放 session 锁，N 个 key 产生 N 次锁竞争。

**决策**：持锁完成整个导出循环（SCAN + 所有 key 的 GET），而非逐 key 加锁。由于导出是用户主动触发的一次性操作，持锁时间较长是可接受的，不会影响其他并发操作（heartbeat 使用独立连接）。

**备选方案**：批量分组（每 100 个 key 一组）→ 复杂度更高，收益有限，暂不采用。

### 决策 3：`key_analyzer` pipeline 改造

**问题**：每个 key 串行发出 4 个 Redis 命令（MEMORY USAGE、TYPE、OBJECT ENCODING、LLEN/HLEN/SCARD/ZCARD）。

**决策**：参照 `key_browser.rs` 中 `get_key_metas` 的 pipeline 实现，将每批 key（与 SCAN count 对齐，默认 100）的 4 个命令合并为一个 pipeline 批量发送。

### 决策 4：`heartbeat` 序列化修复

**问题**：`ConnectionState` 枚举序列化为 `"Connected"` / `"Disconnected"`，前端期望 `"connected"` / `"disconnected"`。

**决策**：在 `ConnectionState` 枚举上添加 `#[serde(rename_all = "snake_case")]` 标注。这是最小侵入性的修复，不影响枚举的其他用途。

### 决策 5：多 Tab CLI 历史持久化策略

**问题**：多 Tab 模式历史仅存内存，关闭 tab 后丢失；单 Tab 模式有 SQLite 持久化。

**决策**：复用现有 `cli_history` 表，为多 Tab 历史记录添加 `tab_id` 字段区分（通过现有的 `conn_id` + `tab_id` 组合键）。前端 `terminal.ts` 在 tab 关闭时不清除历史，在 tab 创建时从 SQLite 加载历史。

**备选方案**：为多 Tab 新建独立表 → 不必要，现有表结构已足够。

### 决策 6：`healthCheckExportMarkdown` 参数修复

**问题**：后端命令签名需要 `conn_id` 参数，前端调用时未传。

**决策**：在前端 `phase4.ts` 的 `healthCheckExportMarkdown` 函数中补充 `connId` 参数，与后端签名对齐。

### 决策 7：`masking_rule_reorder` 事务保护

**问题**：N 次独立 SQL UPDATE，部分失败会导致排序数据不一致。

**决策**：使用 `sqlx` 的 `begin()` 事务包裹所有 UPDATE 操作，失败时自动回滚。

## Risks / Trade-offs

- **[风险] `export_db_json` 持锁时间较长** → 缓解：导出是用户主动触发的操作，期间 UI 显示进度条，用户预期会等待；heartbeat 使用独立连接不受影响。
- **[风险] `key_analyzer` pipeline 改造可能改变错误处理行为** → 缓解：pipeline 中单个命令失败不会中断整批，需确保错误被正确收集并上报。
- **[风险] `cli_history` 表添加 `tab_id` 字段** → 缓解：通过 migration 添加可空字段，历史数据（tab_id = NULL）视为单 Tab 历史，向后兼容。
- **[风险] `heartbeat` 序列化修复影响现有前端状态判断** → 缓解：修复后前端状态匹配将正确工作，但需确认前端所有判断 `state === 'connected'` 的地方均使用小写，避免遗漏。
