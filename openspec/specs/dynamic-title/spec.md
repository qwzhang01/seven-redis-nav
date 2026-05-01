## ADDED Requirements

### Requirement: Dynamic window title on connection
The system SHALL update the native macOS window title via Tauri `getCurrentWindow().setTitle()` when the connection state changes.

#### Scenario: Default title when not connected
- **WHEN** the application starts or no connection is active
- **THEN** the native window title SHALL display "Seven Redis Nav"

#### Scenario: Title updates on successful connection
- **WHEN** a connection to a Redis instance is successfully established
- **THEN** the native window title SHALL display "Seven Redis Nav — <connection-name>"

#### Scenario: Title resets on disconnect
- **WHEN** the active connection is closed or lost
- **THEN** the native window title SHALL revert to "Seven Redis Nav"

### Requirement: Title reflects connection name
The system SHALL use the connection's display name (from saved config or host:port for quick connect) as the connection identifier in the title.

#### Scenario: Saved connection title
- **WHEN** user connects via a saved connection named "production-cluster-01"
- **THEN** the title SHALL display "Seven Redis Nav — production-cluster-01"

#### Scenario: Quick connect title
- **WHEN** user connects via quick connect to "192.168.1.100:6379"
- **THEN** the title SHALL display "Seven Redis Nav — 192.168.1.100:6379"
