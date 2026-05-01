## ADDED Requirements

### Requirement: Temporary connection session (open without persistence)

The system SHALL support opening a Redis connection session from a temporary configuration (not saved to SQLite). The temporary session SHALL use a generated `temp-{uuid}` as ConnId and be managed identically to persistent sessions in the ConnectionManager.

#### Scenario: Open temporary connection

- **WHEN** frontend calls `connection_open_temp` IPC with a full ConnectionConfig (host, port, password, timeout_ms)
- **THEN** backend creates a `MultiplexedConnection` using the provided config, registers it in ConnectionManager with `temp-{uuid}` ConnId, and returns the ConnId

#### Scenario: Temporary connection lifecycle

- **WHEN** a temporary connection is established
- **THEN** it participates in heartbeat PING, emits `connection:state` events, and supports all data operations (SCAN, GET, SET, etc.) identically to persistent connections

#### Scenario: Save temporary connection to persistent

- **WHEN** frontend calls `connection_save` with the temporary connection's config (id field empty)
- **THEN** backend persists to SQLite + Keychain, returns new ConnId; frontend MAY then close the temp session and open a persistent one, or simply update the ConnId mapping

#### Scenario: Close temporary connection

- **WHEN** user disconnects or app closes while a temporary session is active
- **THEN** backend drops the MultiplexedConnection; no SQLite/Keychain cleanup needed since nothing was persisted

## MODIFIED Requirements

### Requirement: Connection session management

The system SHALL manage connection sessions using `MultiplexedConnection`. Each opened connection SHALL be tracked by `ConnId` in a `ConnectionManager`. The system SHALL support opening, closing, and reconnecting sessions. The system SHALL support both persistent sessions (opened by connId from SQLite) and temporary sessions (opened by inline config).

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
