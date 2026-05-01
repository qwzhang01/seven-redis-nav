## MODIFIED Requirements

### Requirement: Connection session management
系统 SHALL 管理连接会话使用 `MultiplexedConnection`。每个已打开的连接 SHALL 通过 `ConnId` 在 `ConnectionManager` 中追踪。系统 SHALL 支持打开、关闭和重连会话。系统 SHALL 支持持久化会话（通过 SQLite 中的 connId 打开）和临时会话（通过内联配置打开）。连接成功建立后，系统 SHALL 通过执行 `INFO server` 命令获取 Redis 服务器版本，并将版本信息存储在前端 connection store 的 `serverVersion` 字段中。

#### Scenario: Open a connection session (persistent)
- **WHEN** user clicks a connection in Sidebar or Welcome page saved list
- **THEN** system calls `connection_open` IPC with connId, backend loads config from SQLite + Keychain, creates `MultiplexedConnection`, returns success, frontend transitions to workspace

#### Scenario: Open a connection session (temporary)
- **WHEN** user uses quick connect from Welcome page
- **THEN** system calls `connection_open_temp` IPC with inline config, backend creates `MultiplexedConnection` with `temp-{uuid}` ConnId, returns ConnId, frontend transitions to workspace

#### Scenario: Close a connection session
- **WHEN** user right-clicks an active connection and selects "断开"
- **THEN** system calls `connection_close` IPC, backend drops `MultiplexedConnection`, Sidebar shows offline status, KeyPanel clears

#### Scenario: Connection lost recovery
- **WHEN** active connection drops (network error, Redis restart)
- **THEN** backend detects via failed command, emits `connection:state` event with `{id, state: "disconnected"}`, frontend shows reconnecting indicator, backend attempts exponential backoff reconnection

#### Scenario: Server version populated after connect
- **WHEN** connection is successfully established
- **THEN** frontend connection store 的 `serverVersion` 字段被更新为从 `INFO server` 获取的 Redis 版本号（如 `"7.2.4"`），不再保持 `null`

#### Scenario: Open a connection session (SSH隧道)
- **WHEN** 用户配置SSH隧道参数并点击连接
- **THEN** 系统调用`connection_open` IPC，后端通过SSH隧道建立Redis连接，创建`MultiplexedConnection`，返回成功，前端转换到工作区

#### Scenario: Open a connection session (TLS加密)
- **WHEN** 用户配置TLS加密参数并点击连接
- **THEN** 系统调用`connection_open` IPC，后端通过TLS加密建立Redis连接，创建`MultiplexedConnection`，返回成功，前端转换到工作区

#### Scenario: Connection type detection and handling
- **WHEN** 连接管理器处理不同类型的连接配置
- **THEN** 系统根据连接类型（TCP/SSH/TLS）选择合适的连接建立策略

#### Scenario: Connection configuration validation
- **WHEN** 用户提交包含SSH或TLS参数的连接配置
- **THEN** 系统验证配置完整性并根据连接类型进行特定参数验证
