## Purpose
Server config workspace adds CONFIG REWRITE/RESETSTAT support, diff panel for pending changes, dangerous parameter confirmation, and regrouped configuration display.

## MODIFIED Requirements

### Requirement: CONFIG REWRITE support
The system SHALL allow users to persist the current in-memory configuration to disk using CONFIG REWRITE with a confirmation dialog.

#### Scenario: CONFIG REWRITE with confirmation
- **WHEN** user clicks the "💾 落盘 (REWRITE)" button in the Config workspace toolbar
- **THEN** system shows a confirmation dialog warning "CONFIG REWRITE 将把当前运行配置写入 redis.conf，确定继续？"；user confirms, system calls `config_rewrite` IPC

#### Scenario: CONFIG REWRITE success
- **WHEN** CONFIG REWRITE succeeds
- **THEN** system shows a success Toast "配置已落盘" and clears the pending changes indicator

#### Scenario: CONFIG REWRITE failure
- **WHEN** CONFIG REWRITE fails (e.g., permission denied, config file not found)
- **THEN** system shows an error Toast with the error message from Redis

### Requirement: CONFIG RESETSTAT support
The system SHALL allow users to reset statistics counters using CONFIG RESETSTAT with a confirmation dialog.

#### Scenario: CONFIG RESETSTAT with confirmation
- **WHEN** user clicks the "🔄 清零统计 (RESETSTAT)" button
- **THEN** system shows a confirmation dialog "CONFIG RESETSTAT 将清零所有统计计数器（如 keyspace_hits 等），确定继续？"；user confirms, system calls `config_resetstat` IPC

#### Scenario: CONFIG RESETSTAT success
- **WHEN** CONFIG RESETSTAT succeeds
- **THEN** system shows a success Toast and refreshes the INFO panel data

### Requirement: Configuration diff panel
The system SHALL display a diff panel showing all pending changes (modified but not yet REWRITE'd) with original vs. new values.

#### Scenario: Diff panel display
- **WHEN** user has made one or more CONFIG SET changes
- **THEN** a "变更 (N)" badge appears on the "差异" tab; clicking it shows a table of changed parameters with columns: 参数名 | 原值 | 新值

#### Scenario: No pending changes
- **WHEN** no CONFIG SET changes have been made since last REWRITE
- **THEN** the "差异" tab shows "无待落盘变更" and the badge is hidden

#### Scenario: Revert a single change
- **WHEN** user clicks the "撤销" button next to a diff entry
- **THEN** system reverts that parameter to its original value via CONFIG SET and removes it from the diff list

### Requirement: Dangerous parameter confirmation
The system SHALL require an extra confirmation step for dangerous configuration parameters.

#### Scenario: Edit dangerous parameter
- **WHEN** user attempts to edit a parameter in the dangerous list (bind, protected-mode, requirepass, masterauth, cluster-announce-ip, rename-command)
- **THEN** system shows a red-bordered confirmation dialog with the warning "⚠️ 修改此参数可能导致 Redis 不可访问，请确认你知道自己在做什么" and requires the user to check a "我了解风险" checkbox before proceeding

#### Scenario: Edit non-dangerous parameter
- **WHEN** user edits a parameter not in the dangerous list
- **THEN** the standard confirmation dialog is shown without the extra warning

### Requirement: Regrouped configuration display
The system SHALL reorganize configuration parameters into the following built-in groups: Memory, Persistence, Replication, Security, Network, Clients, Slowlog, Advanced, Other.

#### Scenario: Regrouped display
- **WHEN** configuration is loaded in the Config workspace
- **THEN** parameters are grouped into the 9 built-in categories instead of the original grouping; each group shows parameter count and is collapsible

#### Scenario: Unmatched parameters
- **WHEN** a parameter does not match any built-in group
- **THEN** it is placed in the "Other" group
