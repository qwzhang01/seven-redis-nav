## ADDED Requirements

### Requirement: connection_test IPC 命令

后端 SHALL 提供 `connection_test` IPC 命令，接受 `{ host: string, port: u16, password?: string, timeout_ms?: u32 }`，使用 redis-rs 异步建立短连接、执行 `PING`、解析 `INFO server` 提取版本号、关闭连接，返回 `PingResult { latency_ms: u32, server_version: Option<String> }`。

#### Scenario: 成功连接本地 Redis

- **WHEN** 调用 `connection_test({ host: "127.0.0.1", port: 6379 })` 且本地 Redis 可达
- **THEN** 返回 `Ok(PingResult)`，`latency_ms` 大于 0、`server_version` 为类似 `"7.2.4"` 的字符串

#### Scenario: 带密码连接

- **WHEN** 调用 `connection_test({ host, port, password: "correct-pass" })`
- **THEN** 后端在 PING 前先执行 `AUTH`，全流程成功后返回 `Ok(PingResult)`

#### Scenario: 密码错误

- **WHEN** 调用时密码错误
- **THEN** 返回 `Err(IpcError::Redis { message: "WRONGPASS ..." })`

#### Scenario: 主机不可达

- **WHEN** host 解析失败或端口拒绝连接
- **THEN** 返回 `Err(IpcError::ConnectionRefused { target: "host:port" })`

#### Scenario: 超时

- **WHEN** 网络耗时超过 `timeout_ms`（默认 5000ms）
- **THEN** 返回 `Err(IpcError::Timeout { ms: 5000 })`

### Requirement: 短连接策略

Phase 0 的 `connection_test` MUST 每次调用新建独立连接、命令完成后立即关闭、不保留连接池。后端 SHALL NOT 在 Phase 0 引入任何连接管理状态。

#### Scenario: 连续两次调用互不影响

- **WHEN** 前端连续调用两次 `connection_test`，第二次故意传错误密码
- **THEN** 第一次返回 `Ok`，第二次返回 `Err`，且没有任何状态泄漏（如复用了第一次的认证态）

### Requirement: 密码不落盘

Phase 0 的 `connection_test` 在内存中持有密码 SHALL 使用 `secrecy::Secret<String>` 包装，连接结束后立即 drop。后端 MUST NOT 将密码写入任何文件、数据库、日志、配置项。

#### Scenario: 日志脱敏

- **WHEN** 后端记录 `connection_test` 调用日志
- **THEN** 日志中 `password` 字段输出为 `***`，原始密码不出现在任何日志行

#### Scenario: 无持久化

- **WHEN** 应用关闭后检查文件系统、Keychain、SQLite
- **THEN** 不存在任何来自 `connection_test` 调用的密码痕迹

### Requirement: Welcome 页测试连接 UI

前端 SHALL 提供 Welcome 页（路由 `/welcome`），包含一个简表单（host 输入框、port 输入框、password 输入框、测试连接按钮）。表单 MUST 使用 TDesign Vue Next 组件，遵循设计令牌。

#### Scenario: 默认值

- **WHEN** 用户首次打开 Welcome 页
- **THEN** host 默认 `127.0.0.1`、port 默认 `6379`、password 为空

#### Scenario: 字段校验

- **WHEN** host 为空或 port 不在 [1, 65535] 范围内
- **THEN** "测试连接" 按钮禁用

### Requirement: Toast 反馈

调用 `connection_test` 后，前端 SHALL 通过 TDesign 的 MessagePlugin 给出 Toast 反馈。

#### Scenario: 成功提示

- **WHEN** 调用返回 `Ok(PingResult)`
- **THEN** 弹出绿色成功 Toast：`已连接 · Redis 7.2.4 · 12 ms`，2 秒自动消失

#### Scenario: 失败提示

- **WHEN** 调用返回任意 `Err(IpcError)`
- **THEN** 弹出红色错误 Toast，文案根据 `error.kind` 映射：
  - `connection_refused` → `连接被拒绝：{target}`
  - `timeout` → `连接超时（{ms}ms）`
  - `redis` → `Redis 错误：{message}`
  - `internal` → `内部错误，请查看日志`
  - 错误 Toast 不自动消失，需手动关闭

### Requirement: 按钮加载态

"测试连接" 按钮在 IPC 调用进行中 SHALL 切换为 loading 态、禁用其他交互；调用完成（无论成功失败）后恢复正常态。

#### Scenario: 加载态切换

- **WHEN** 用户点击"测试连接"
- **THEN** 按钮立即显示 spinner 并禁用 click，调用结束后 spinner 消失、可再次点击
