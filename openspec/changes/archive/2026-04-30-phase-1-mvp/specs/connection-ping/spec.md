## MODIFIED Requirements

### Requirement: Welcome 页测试连接 UI

前端 SHALL 提供 Welcome 页，包含快速连接简表单（host/port/password/测试连接按钮）和已有连接列表。Phase 1 新增"保存为新连接"选项和已有连接列表区域。

#### Scenario: 默认值

- **WHEN** 用户首次打开 Welcome 页
- **THEN** host 默认 `127.0.0.1`、port 默认 `6379`、password 为空

#### Scenario: 字段校验

- **WHEN** host 为空或 port 不在 [1, 65535] 范围内
- **THEN** "测试连接" 按钮禁用

#### Scenario: 快速连接成功后保存

- **WHEN** 用户快速连接成功后
- **THEN** 显示"保存为新连接"按钮，点击后弹出 ConnectionForm 预填 host/port/password，用户补充名称后保存

#### Scenario: 已有连接列表

- **WHEN** SQLite 中存在保存的连接
- **THEN** Welcome 页在快速连接表单下方显示"已保存的连接"列表

### Requirement: connection_test IPC 命令

后端 SHALL 提供 `connection_test` IPC 命令，接受 `{ host: string, port: u16, password?: string, timeout_ms?: u32 }`，使用 redis-rs 异步建立短连接、执行 `PING`、解析 `INFO server` 提取版本号、关闭连接，返回 `PingResult { latency_ms: u32, server_version: Option<String> }`。Phase 1 中 `connection_test` 保持独立可用，同时成为 ConnectionForm 弹窗中"测试连接"步骤的后端。

#### Scenario: 成功连接本地 Redis

- **WHEN** 调用 `connection_test({ host: "127.0.0.1", port: 6379 })` 且本地 Redis 可达
- **THEN** 返回 `Ok(PingResult)`，`latency_ms` 大于 0、`server_version` 为类似 `"7.2.4"` 的字符串

#### Scenario: 带密码连接

- **WHEN** 调用 `connection_test({ host, port, password: "correct-pass" })`
- **THEN** 后端在 PING 前先执行 `AUTH`，全流程成功后返回 `Ok(PingResult)`

#### Scenario: 密码错误

- **WHEN** 调用时密码错误
- **THEN** 返回 `Err(IpcError::AuthFailed { message: "WRONGPASS ..." })`

#### Scenario: 主机不可达

- **WHEN** host 解析失败或端口拒绝连接
- **THEN** 返回 `Err(IpcError::ConnectionRefused { target: "host:port" })`

#### Scenario: 超时

- **WHEN** 网络耗时超过 `timeout_ms`（默认 5000ms）
- **THEN** 返回 `Err(IpcError::Timeout { ms: 5000 })`
