## ADDED Requirements

### Requirement: IPC 命令命名规范

所有 Tauri IPC 命令 MUST 遵循 `{domain}_{verb}` 格式，使用 snake_case，全小写。`domain` SHALL 取自固定列表：`connection` / `db` / `keys` / `key` / `cli` / `monitor` / `slowlog` / `pubsub` / `config` / `tools` / `app`。

#### Scenario: 合法命令名

- **WHEN** 后端使用 `#[tauri::command]` 注册命令
- **THEN** 函数名形如 `connection_test` / `keys_scan` / `cli_exec` 时通过校验

#### Scenario: 非法命令名拒绝

- **WHEN** 出现命令名 `testConnection`、`connection.test`、`connectionTest` 中任意一种
- **THEN** Code Review SHALL 拒绝该 PR

### Requirement: 统一错误模型 IpcError

后端所有 IPC 命令的错误返回 MUST 使用统一的 `IpcError` 枚举，并以 `serde(tag = "kind")` 方式序列化为带 `kind` 字段的 JSON 对象，便于前端按 `kind` 分支处理与 i18n 映射。

`IpcError` SHALL 至少包含以下变体：`Redis` / `ConnectionRefused` / `Timeout` / `InvalidArgument` / `Internal`，每个变体携带结构化字段（如 `message`、`target`、`ms`、`field`）。

#### Scenario: 错误序列化结构

- **WHEN** 后端返回 `IpcError::Timeout { ms: 5000 }`
- **THEN** 前端收到的 JSON 形如 `{ "kind": "timeout", "ms": 5000 }`

#### Scenario: 前端错误分支处理

- **WHEN** 前端 `try/catch` 接到 IPC 错误
- **THEN** 必须按 `error.kind` 分支处理，禁止直接拼接 `error.message` 显示给用户

### Requirement: 前端 IPC 类型化封装

前端调用 IPC 时 MUST 通过 `src/ipc/{domain}.ts` 模块的类型化函数，禁止在组件中直接 import `@tauri-apps/api` 的 `invoke` 或 `listen`。每个 IPC 函数 SHALL 同时声明请求类型、响应类型与函数签名。

#### Scenario: 合法的 IPC 调用

- **WHEN** 组件需要测试连接
- **THEN** 必须调用 `import { connectionTest } from '@/ipc/connection'`，且 `connectionTest` 的入参/返回值有完整 TypeScript 类型

#### Scenario: 禁止裸 invoke

- **WHEN** 任意组件文件中出现 `import { invoke } from '@tauri-apps/api/core'`
- **THEN** 该 PR 不予合并（Phase 0 由 Code Review 把关，Phase 1 起改为 ESLint 规则强制）

### Requirement: Tauri Event 命名规范

后端推送给前端的事件 MUST 遵循 `{domain}:{event}` 格式（冒号分隔），全小写。Phase 0 不实际使用任何事件，但规范 SHALL 在 `docs/overview-and-roadmap.md` §2.4 中文档化，供后续 Phase 引用。

#### Scenario: 事件名示例

- **WHEN** 设计监控采样推送事件
- **THEN** 事件名 MUST 为 `monitor:tick`，禁止 `monitorTick` / `monitor.tick` / `MonitorTick` 等其他写法

### Requirement: 类型一致性

后端 Rust 模型（`src-tauri/src/models/`）与前端 TypeScript 类型（`src/types/`）SHALL 保持字段名与结构完全一致。Phase 0 由人工同步维护，并在 PR 模板中显式提示"是否同步更新前端类型"。

#### Scenario: PingResult 双端定义

- **WHEN** 后端定义 `pub struct PingResult { latency_ms: u32, server_version: Option<String> }`
- **THEN** 前端 `src/types/connection.d.ts` MUST 定义 `interface PingResult { latency_ms: number; server_version: string | null }`，字段名严格一致

### Requirement: IPC 调用日志

后端所有 IPC 命令 MUST 在入口处通过 `tracing` 记录 INFO 级别日志，至少包含命令名与请求参数摘要（密码等敏感字段 MUST 脱敏为 `***`）。

#### Scenario: 命令调用被记录

- **WHEN** 前端调用 `connection_test({ host: "127.0.0.1", port: 6379, password: "secret" })`
- **THEN** 后端日志输出 `INFO ipc command=connection_test host=127.0.0.1 port=6379 password=***`
