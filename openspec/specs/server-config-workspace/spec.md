## ADDED Requirements

### Requirement: Load all server configuration
The system SHALL retrieve all Redis configuration parameters using CONFIG GET * and display them in a grouped, searchable interface.

#### Scenario: Load configuration
- **WHEN** user navigates to the Config tab
- **THEN** system executes CONFIG GET * and displays all parameters grouped by category (Network, Memory, Persistence, Replication, Security, Clients, Lua, Cluster, Slowlog, Other)

#### Scenario: Group display
- **WHEN** configuration is loaded
- **THEN** each group is displayed as a collapsible section with the group name and parameter count

### Requirement: Search and filter configuration
The system SHALL allow users to search configuration parameters by name or value.

#### Scenario: Search by parameter name
- **WHEN** user types "max" in the search input
- **THEN** only parameters whose name contains "max" are displayed (e.g., maxmemory, maxclients)

#### Scenario: Filter by group
- **WHEN** user selects a specific group from the group filter dropdown
- **THEN** only parameters in that group are displayed

### Requirement: Edit configuration parameter
The system SHALL allow users to modify configuration parameters using CONFIG SET with confirmation.

#### Scenario: Edit a parameter
- **WHEN** user clicks the edit icon next to a parameter and enters a new value
- **THEN** system shows a confirmation dialog displaying parameter name, current value, and new value

#### Scenario: Confirm edit
- **WHEN** user confirms the edit in the confirmation dialog
- **THEN** system executes CONFIG SET <param> <value> and updates the displayed value on success

#### Scenario: Edit failure
- **WHEN** CONFIG SET returns an error (e.g., invalid value or read-only parameter)
- **THEN** system displays the error message and reverts the displayed value to the original

### Requirement: Server info overview panel
The system SHALL display a summary panel with key Redis server metrics from INFO command.

#### Scenario: Info panel display
- **WHEN** Config tab is active
- **THEN** a top panel shows: Redis version, uptime, connected clients, used memory / max memory, hit rate (keyspace_hits / total), total keys, and ops/sec

#### Scenario: Info refresh
- **WHEN** user clicks refresh on the info panel
- **THEN** system re-executes INFO and updates all metrics

### Requirement: Read-only parameter indication
The system SHALL visually distinguish read-only parameters that cannot be modified via CONFIG SET.

#### Scenario: Read-only display
- **WHEN** a parameter is known to be read-only (e.g., bind, port)
- **THEN** the edit icon is disabled/hidden and a lock icon is shown instead

### Requirement: Parameter value validation
The system SHALL validate parameter values before sending CONFIG SET where possible.

#### Scenario: Numeric validation
- **WHEN** user enters a non-numeric value for a numeric parameter (e.g., maxmemory)
- **THEN** system shows an inline validation error and prevents submission

### Requirement: Configuration difference panel (Phase 3)
The system SHALL display a diff panel showing configuration parameters that differ from their default values.

#### Scenario: View configuration diff
- **WHEN** user clicks the "差异" tab
- **THEN** system shows only parameters whose current value differs from the Redis default, with old/new comparison

#### Scenario: No differences
- **WHEN** all parameters match defaults
- **THEN** system displays "当前配置与默认值一致" message

### Requirement: Dangerous parameter confirmation (Phase 3)
The system SHALL require an extra confirmation step for parameters that may cause data loss or service disruption.

#### Scenario: Edit dangerous parameter
- **WHEN** user attempts to edit a dangerous parameter (e.g., save, appendonly, requirepass, maxmemory-policy)
- **THEN** system shows a prominent warning dialog with the parameter name and risk description; user must acknowledge risk before proceeding

### Requirement: Configuration regrouping (Phase 3)
The system SHALL organize configuration parameters into user-friendly groups beyond raw Redis categories.

#### Scenario: Smart grouping
- **WHEN** configuration is loaded
- **THEN** parameters are grouped into: 常规、网络、内存、持久化、复制、安全、客户端、慢日志、集群、高级, with cross-category parameters placed in the most relevant group
