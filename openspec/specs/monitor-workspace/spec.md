## ADDED Requirements

### Requirement: Start monitor session
The system SHALL establish a dedicated Redis connection and execute MONITOR command to receive real-time command stream.

#### Scenario: Start monitoring
- **WHEN** user navigates to the Monitor tab and clicks "Start"
- **THEN** system acquires a dedicated connection, executes MONITOR, and begins streaming commands to the UI

#### Scenario: Already monitoring
- **WHEN** user is already in an active monitor session and clicks "Start"
- **THEN** system shows a message indicating monitoring is already active

### Requirement: Stop monitor session
The system SHALL allow users to stop the monitor session and release the dedicated connection.

#### Scenario: Stop monitoring
- **WHEN** user clicks "Stop"
- **THEN** system closes the dedicated connection, stops receiving commands, and the stream freezes at current state

### Requirement: Real-time command display
The system SHALL display each monitored command with timestamp, client info, database number, and the full command string.

#### Scenario: Command received
- **WHEN** a Redis command is executed by any client
- **THEN** the command appears in the stream showing: timestamp, client IP:port, DB number, and full command with arguments

#### Scenario: Command syntax coloring
- **WHEN** commands are displayed
- **THEN** read commands (GET, MGET, HGET, etc.) are colored green, write commands (SET, DEL, HSET, etc.) are colored orange, and admin commands (CONFIG, FLUSHDB, etc.) are colored red

### Requirement: Monitor stream controls
The system SHALL provide pause/resume, keyword filter, and clear controls.

#### Scenario: Pause stream
- **WHEN** user clicks "Pause"
- **THEN** incoming commands are buffered but not rendered; a badge shows buffered count

#### Scenario: Resume stream
- **WHEN** user clicks "Resume"
- **THEN** buffered commands are rendered and stream returns to real-time

#### Scenario: Keyword filter
- **WHEN** user enters a filter keyword (e.g., "SET")
- **THEN** only commands containing the keyword are displayed; others are hidden but still counted

#### Scenario: Clear stream
- **WHEN** user clicks "Clear"
- **THEN** all displayed commands are removed from the UI

### Requirement: Auto-scroll behavior
The system SHALL auto-scroll to the bottom when new commands arrive, unless the user has manually scrolled up.

#### Scenario: Auto-scroll active
- **WHEN** user is at the bottom of the stream and new commands arrive
- **THEN** the view automatically scrolls to show the newest command

#### Scenario: Auto-scroll paused by user scroll
- **WHEN** user scrolls up to review older commands
- **THEN** auto-scroll is disabled and a "Scroll to bottom" button appears

### Requirement: Ring buffer memory protection
The system SHALL limit the command buffer to 10000 entries, discarding the oldest when the limit is reached.

#### Scenario: Buffer overflow
- **WHEN** the 10001st command arrives
- **THEN** the oldest command is discarded and the buffer maintains exactly 10000 entries

### Requirement: Performance safeguard
The system SHALL batch-render commands using requestAnimationFrame to prevent UI thread blocking under high command rates.

#### Scenario: High throughput
- **WHEN** commands arrive at more than 5000/second
- **THEN** system batches rendering at 60fps intervals, maintaining smooth scrolling and responsive UI controls
