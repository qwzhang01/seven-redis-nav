## MODIFIED Requirements

### Requirement: CLI 标签页独立会话
系统 SHALL 为每个 CLI 标签页维护独立的 Redis 连接（`CliSession`），互不干扰。每个标签页的命令历史 SHALL 持久化到 SQLite，使用 `conn_id` + `tab_id` 组合键区分不同标签页的历史记录。前端 SHALL 提供 `cliHistoryGetTab` IPC 封装函数，用于获取指定标签页的历史记录。

#### Scenario: 独立命令历史
- **WHEN** 用户在标签页 1 执行若干命令后切换到标签页 2
- **THEN** 标签页 2 的 ↑↓ 历史导航只显示标签页 2 自己的命令历史，不包含标签页 1 的历史

#### Scenario: 独立 DB 选择
- **WHEN** 用户在标签页 1 执行 `SELECT 3` 切换到 DB 3
- **THEN** 标签页 2 仍在 DB 0（或其自己选择的 DB），两个标签页的 DB 状态互相独立

#### Scenario: 空闲标签页超时
- **WHEN** 某个 CLI 标签页超过 30 分钟无命令执行
- **THEN** 后端自动释放该标签页的 Redis 连接，标签页标签显示"(已断开)"，用户下次输入命令时自动重连

#### Scenario: 标签页历史持久化
- **WHEN** 用户在多 Tab CLI 中执行命令
- **THEN** 命令历史写入 SQLite `cli_history` 表，使用 `tab_id` 字段区分不同标签页，App 重启后历史记录仍可通过 `cliHistoryGetTab` IPC 恢复

#### Scenario: 标签页历史加载
- **WHEN** 用户创建新 CLI 标签页或 App 重启后恢复标签页
- **THEN** 前端调用 `cliHistoryGetTab` IPC（传入 `conn_id` 和 `tab_id`），从 SQLite 加载该标签页的历史记录，历史导航（↑↓）可访问持久化的历史命令

#### Scenario: cliHistoryGetTab IPC 可用
- **WHEN** 前端需要获取指定标签页的历史记录
- **THEN** `phase4.ts` 中的 `cliHistoryGetTab(connId, tabId)` 函数可正常调用，返回该标签页的历史命令列表
