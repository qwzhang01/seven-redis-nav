## ADDED Requirements

### Requirement: Pub/Sub subscribe command
The system SHALL provide an IPC command `pubsub_subscribe` that establishes a dedicated connection and subscribes to specified channels or patterns.

#### Scenario: Subscribe via IPC
- **WHEN** frontend invokes `pubsub_subscribe` with connection_id, channels list, and optional pattern flag
- **THEN** backend acquires a dedicated connection, executes SUBSCRIBE or PSUBSCRIBE, and begins emitting `pubsub:message` events

### Requirement: Pub/Sub unsubscribe command
The system SHALL provide an IPC command `pubsub_unsubscribe` that unsubscribes from channels and releases the dedicated connection when no subscriptions remain.

#### Scenario: Unsubscribe via IPC
- **WHEN** frontend invokes `pubsub_unsubscribe` with connection_id and channels list
- **THEN** backend executes UNSUBSCRIBE/PUNSUBSCRIBE; if no subscriptions remain, the dedicated connection is released

### Requirement: Pub/Sub message event
The system SHALL emit `pubsub:message` Tauri events for each received message, containing channel, pattern (if PSUBSCRIBE), message body, and timestamp.

#### Scenario: Message event emission
- **WHEN** a message is received on a subscribed channel
- **THEN** backend emits a `pubsub:message` event with payload { channel, pattern, message, timestamp }

### Requirement: Monitor start command
The system SHALL provide an IPC command `monitor_start` that establishes a dedicated connection and begins MONITOR mode.

#### Scenario: Start monitor via IPC
- **WHEN** frontend invokes `monitor_start` with connection_id
- **THEN** backend acquires a dedicated connection, executes MONITOR, and begins emitting `monitor:command` events

### Requirement: Monitor stop command
The system SHALL provide an IPC command `monitor_stop` that stops the MONITOR session and releases the dedicated connection.

#### Scenario: Stop monitor via IPC
- **WHEN** frontend invokes `monitor_stop` with connection_id
- **THEN** backend closes the dedicated connection and stops emitting `monitor:command` events

### Requirement: Monitor command event
The system SHALL emit `monitor:command` Tauri events for each monitored command, containing timestamp, client, database, and command string.

#### Scenario: Command event emission
- **WHEN** a command is executed on the monitored Redis server
- **THEN** backend emits a `monitor:command` event with payload { timestamp, client, db, command, args }

### Requirement: Slowlog get command
The system SHALL provide an IPC command `slowlog_get` that retrieves slowlog entries.

#### Scenario: Get slowlog via IPC
- **WHEN** frontend invokes `slowlog_get` with connection_id and optional count
- **THEN** backend executes SLOWLOG GET [count] and returns array of { id, timestamp, duration_us, command, client_addr }

### Requirement: Slowlog reset command
The system SHALL provide an IPC command `slowlog_reset` that clears the slowlog.

#### Scenario: Reset slowlog via IPC
- **WHEN** frontend invokes `slowlog_reset` with connection_id
- **THEN** backend executes SLOWLOG RESET and returns success

### Requirement: Config get all command
The system SHALL provide an IPC command `config_get_all` that retrieves all Redis configuration parameters.

#### Scenario: Get config via IPC
- **WHEN** frontend invokes `config_get_all` with connection_id
- **THEN** backend executes CONFIG GET * and returns array of { key, value } pairs

### Requirement: Config set command
The system SHALL provide an IPC command `config_set` that modifies a Redis configuration parameter.

#### Scenario: Set config via IPC
- **WHEN** frontend invokes `config_set` with connection_id, parameter name, and new value
- **THEN** backend executes CONFIG SET <param> <value> and returns success or error message

### Requirement: Server info command
The system SHALL provide an IPC command `server_info` that retrieves Redis INFO data.

#### Scenario: Get server info via IPC
- **WHEN** frontend invokes `server_info` with connection_id and optional section
- **THEN** backend executes INFO [section] and returns parsed key-value data grouped by section
