## MODIFIED Requirements

### Requirement: 统一错误模型 IpcError

后端所有 IPC 命令的错误返回 MUST 使用统一的 `IpcError` 枚举，并以 `serde(tag = "kind")` 方式序列化为带 `kind` 字段的 JSON 对象，便于前端按 `kind` 分支处理与 i18n 映射。

`IpcError` SHALL 包含以下变体：`Redis` / `ConnectionRefused` / `Timeout` / `InvalidArgument` / `Internal` / `AuthFailed` / `NotFound` / `DangerousCommand`，每个变体携带结构化字段。

#### Scenario: 错误序列化结构

- **WHEN** 后端返回 `IpcError::Timeout { ms: 5000 }`
- **THEN** 前端收到的 JSON 形如 `{ "kind": "timeout", "ms": 5000 }`

#### Scenario: AuthFailed 错误

- **WHEN** 连接时 AUTH 失败（密码错误或无需密码却收到 AUTH 要求）
- **THEN** 返回 `IpcError::AuthFailed { message: "WRONGPASS invalid username-password pair" }`

#### Scenario: NotFound 错误

- **WHEN** 操作的目标不存在（如删除不存在的连接 ID）
- **THEN** 返回 `IpcError::NotFound { target: "connection", id: "xxx" }`

#### Scenario: DangerousCommand 错误

- **WHEN** `cli_exec` 命令匹配危险命令白名单且无确认 token
- **THEN** 返回 `IpcError::DangerousCommand { command: "FLUSHDB", confirm_token: "xxx" }`，前端需用 confirm_token 重新发送

#### Scenario: 前端错误分支处理

- **WHEN** 前端 `try/catch` 接到 IPC 错误
- **THEN** 必须按 `error.kind` 分支处理，禁止直接拼接 `error.message` 显示给用户

## ADDED Requirements

### Requirement: Phase 1 新增 IPC 命令

Phase 1 SHALL 新增以下 IPC 命令，均遵循 `{domain}_{verb}` 命名规范：

| Command | 参数 | 返回 | 说明 |
|---|---|---|---|
| `connection_list` | — | `Vec<ConnectionMeta>` | 列出所有保存的连接 |
| `connection_save` | `ConnectionConfig` | `ConnId` | 新建/更新连接 |
| `connection_delete` | `{ id: ConnId }` | `()` | 删除连接 |
| `connection_open` | `{ id: ConnId }` | `SessionId` | 建立连接会话 |
| `connection_close` | `{ id: ConnId }` | `()` | 关闭连接会话 |
| `db_select` | `{ session_id, db: u8 }` | `DbStat` | 切换 DB |
| `keys_scan` | `{ session_id, cursor, match, count, type? }` | `ScanPage` | SCAN 分页 |
| `key_get` | `{ session_id, key }` | `KeyDetail` | 获取键详情 |
| `key_set` | `{ session_id, key, value, type, options }` | `()` | 写入键值 |
| `key_delete` | `{ session_id, keys: Vec<String> }` | `u64` | 删除键 |
| `key_rename` | `{ session_id, src, dst }` | `()` | 重命名键 |
| `key_ttl_set` | `{ session_id, key, ttl_secs }` | `()` | 设置/移除 TTL |
| `cli_exec` | `{ session_id, command, confirm_token? }` | `CliReply` | 执行命令 |
| `cli_history_get` | `{ limit }` | `Vec<CliHistoryEntry>` | 获取历史 |

#### Scenario: IPC 类型化封装

- **WHEN** 前端调用 `keys_scan`
- **THEN** 必须通过 `import { keysScan } from '@/ipc/data'` 调用，入参/返回值有完整 TypeScript 类型

### Requirement: Tauri Event connection:state

后端 SHALL 在连接状态变化时向前端推送 `connection:state` 事件，payload 为 `{ id: ConnId, state: ConnectionState }`。

#### Scenario: 连接断开推送

- **WHEN** 后端检测到活跃连接断开
- **THEN** 推送 `connection:state` 事件，state 为 `"disconnected"`，前端更新 Sidebar 状态点

#### Scenario: 重连成功推送

- **WHEN** 后端自动重连成功
- **THEN** 推送 `connection:state` 事件，state 为 `"connected"`

### Requirement: Phase 1 前端 IPC 模块扩展

前端 `src/ipc/` SHALL 新增以下模块：`data.ts`（keys_scan/key_get/key_set/key_delete/key_rename/key_ttl_set/db_select）、`terminal.ts`（cli_exec/cli_history_get），`connection.ts` 扩展（connection_list/connection_save/connection_delete/connection_open/connection_close）。

#### Scenario: data.ts IPC 模块

- **WHEN** 组件需要扫描键列表
- **THEN** 调用 `import { keysScan } from '@/ipc/data'`，类型安全

#### Scenario: terminal.ts IPC 模块

- **WHEN** 组件需要执行 CLI 命令
- **THEN** 调用 `import { cliExec } from '@/ipc/terminal'`，类型安全
