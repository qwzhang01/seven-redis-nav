## ADDED Requirements

### Requirement: Connection configuration CRUD
The system SHALL allow users to create, read, update, and delete connection configurations. Each configuration SHALL include: name, host, port, auth DB index, timeout, group name, and optional password.

#### Scenario: Create a new connection
- **WHEN** user clicks "新建连接" button (⌘N or Toolbar + button)
- **THEN** system opens ConnectionForm dialog with empty fields, user fills in host/port/name/password, clicks "测试连接" to verify, then clicks "保存" to persist

#### Scenario: Edit an existing connection
- **WHEN** user right-clicks a connection in Sidebar and selects "编辑"
- **THEN** system opens ConnectionForm dialog pre-filled with current values, user modifies and saves

#### Scenario: Delete a connection
- **WHEN** user right-clicks a connection and selects "删除"
- **THEN** system shows confirmation dialog, on confirm deletes from SQLite and removes Keychain entry

#### Scenario: Duplicate a connection
- **WHEN** user right-clicks a connection and selects "复制"
- **THEN** system creates a copy with name appended " (副本)", same host/port, no password copied

### Requirement: Connection configuration persistence
The system SHALL persist connection configurations to a local SQLite database. Passwords SHALL be stored in macOS Keychain, referenced by `keychain_key` in SQLite. The database SHALL be initialized on first launch via sqlx migrations.

#### Scenario: Connections survive app restart
- **WHEN** user creates a connection with password, quits and relaunches the app
- **THEN** the connection appears in Sidebar with saved name/host/port, password retrievable from Keychain

#### Scenario: First launch database initialization
- **WHEN** app starts and SQLite file does not exist
- **THEN** system creates `~/.seven-redis-nav/config.db` with `connections` and `cli_history` tables via migration

#### Scenario: Keychain access denied
- **WHEN** user saves a connection but macOS denies Keychain access
- **THEN** system shows informative message explaining Keychain permission; offers "仅本次会话" option (password held in memory only, not persisted)

### Requirement: Connection session management
The system SHALL manage connection sessions using `MultiplexedConnection`. Each opened connection SHALL be tracked by `ConnId` in a `ConnectionManager`. The system SHALL support opening, closing, and reconnecting sessions.

#### Scenario: Open a connection session
- **WHEN** user clicks a connection in Sidebar
- **THEN** system calls `connection_open` IPC, backend creates `MultiplexedConnection`, returns `SessionId`, Sidebar shows online status, KeyPanel begins SCAN

#### Scenario: Close a connection session
- **WHEN** user right-clicks an active connection and selects "断开"
- **THEN** system calls `connection_close` IPC, backend drops `MultiplexedConnection`, Sidebar shows offline status, KeyPanel clears

#### Scenario: Connection lost recovery
- **WHEN** active connection drops (network error, Redis restart)
- **THEN** backend detects via failed command, emits `connection:state` event with `{id, state: "disconnected"}`, frontend shows reconnecting indicator, backend attempts exponential backoff reconnection

### Requirement: Database selection
The system SHALL allow users to switch the active Redis database (DB 0-15). DB list and key counts SHALL be fetched from `INFO keyspace`.

#### Scenario: Select a different DB
- **WHEN** user clicks a DB item in Sidebar DB list
- **THEN** system calls `db_select` IPC with session ID and DB index, KeyPanel refreshes SCAN for new DB

#### Scenario: DB list populated from INFO
- **WHEN** user opens a connection
- **THEN** system calls `INFO keyspace`, parses DB indices and key counts, populates Sidebar DB list

### Requirement: Connection import/export
The system SHALL allow users to export all connection configurations to a JSON file and import from a JSON file. Passwords SHALL NOT be included in exports (marked as needs re-entry).

#### Scenario: Export connections
- **WHEN** user clicks "导出连接" in settings or context menu
- **THEN** system serializes all connections (excluding passwords) to JSON, triggers file save dialog

#### Scenario: Import connections
- **WHEN** user clicks "导入连接" and selects a JSON file
- **THEN** system parses JSON, creates new connections (skipping duplicates by name+host+port), shows import result summary

### Requirement: Connection status display
The system SHALL display real-time connection status (online/offline/connecting/reconnecting) in Sidebar with colored dot indicators.

#### Scenario: Status dot updates
- **WHEN** connection state changes to online
- **THEN** dot turns green with pulse animation; to connecting: dot turns yellow; to offline: dot turns gray; to reconnecting: dot blinks yellow
