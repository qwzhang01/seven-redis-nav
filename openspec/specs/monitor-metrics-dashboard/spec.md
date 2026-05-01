## ADDED Requirements

### Requirement: Metrics dashboard sub-tab
The system SHALL provide a "Metrics Dashboard" sub-tab within the Monitor workspace that displays real-time performance indicators sampled from Redis INFO.

#### Scenario: Navigate to metrics dashboard
- **WHEN** user clicks the "指标仪表盘" sub-tab in the Monitor workspace
- **THEN** system starts the INFO sampling task (default interval 2s) and renders the dashboard layout

#### Scenario: Pause sampling when tab is inactive
- **WHEN** user switches away from the Monitor workspace or to the "命令追踪" sub-tab
- **THEN** system stops the INFO sampling task to conserve resources

#### Scenario: Resume sampling when tab becomes active
- **WHEN** user returns to the "指标仪表盘" sub-tab
- **THEN** system restarts the INFO sampling task and resumes updating the dashboard

### Requirement: Four metric cards
The system SHALL display four real-time metric cards: OPS/s, Memory, Connections, and Hit Rate.

#### Scenario: OPS/s card
- **WHEN** a metrics tick arrives
- **THEN** the OPS/s card shows the current value from `INFO stats.instantaneous_ops_per_sec` with a blue accent color

#### Scenario: Memory card
- **WHEN** a metrics tick arrives
- **THEN** the Memory card shows `INFO memory.used_memory` formatted in MB/GB with a purple accent color

#### Scenario: Connections card
- **WHEN** a metrics tick arrives
- **THEN** the Connections card shows `INFO clients.connected_clients` with a green accent color

#### Scenario: Hit rate card
- **WHEN** a metrics tick arrives
- **THEN** the Hit Rate card shows the percentage calculated as `keyspace_hits / (keyspace_hits + keyspace_misses) * 100`, formatted to one decimal place, with an amber accent color; if both hits and misses are zero, display "N/A"

### Requirement: ECharts trend charts
The system SHALL display a trend chart for each of the four metrics using ECharts, maintaining a sliding window of the last 40 data points.

#### Scenario: Chart updates on tick
- **WHEN** a new metrics tick arrives
- **THEN** each chart appends the new data point and removes the oldest if the window exceeds 40 points, updating smoothly without full re-render

#### Scenario: Chart visual style
- **WHEN** charts are rendered
- **THEN** each chart uses a gradient area fill, a rounded end-point dot, and matches the accent color of its corresponding metric card

### Requirement: Server info card
The system SHALL display a server information card showing static and semi-static Redis server properties.

#### Scenario: Server info display
- **WHEN** the metrics dashboard is active
- **THEN** the server info card shows: Redis version, OS, PID, port, uptime (formatted as days/hours), role (master/slave with color badge), connected slaves count, AOF status, and last RDB save time

### Requirement: Keyspace statistics card
The system SHALL display a keyspace statistics card showing per-database key counts and expiry information.

#### Scenario: Keyspace stats display
- **WHEN** the metrics dashboard is active
- **THEN** the keyspace card shows for each database (up to DB7): total keys, keys with TTL, permanent keys, and expired keys today (from `INFO keyspace`)

### Requirement: Client list
The system SHALL display a live client list showing the most recent active connections.

#### Scenario: Client list display
- **WHEN** the metrics dashboard is active
- **THEN** the client list shows up to 6 entries from `CLIENT LIST`, each with: address, last command, and connection duration

## MODIFIED Requirements

### Requirement: Start monitor session
The system SHALL establish a dedicated Redis connection and execute MONITOR command to receive real-time command stream. This feature is now accessible via the "命令追踪" sub-tab within the Monitor workspace.

#### Scenario: Start monitoring
- **WHEN** user navigates to the "命令追踪" sub-tab and clicks "Start"
- **THEN** system acquires a dedicated connection, executes MONITOR, and begins streaming commands to the UI

#### Scenario: Already monitoring
- **WHEN** user is already in an active monitor session and clicks "Start"
- **THEN** system shows a message indicating monitoring is already active
