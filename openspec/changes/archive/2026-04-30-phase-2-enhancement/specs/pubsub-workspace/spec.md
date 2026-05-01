## ADDED Requirements

### Requirement: Subscribe to channels
The system SHALL allow users to subscribe to one or more Redis channels by name, and SHALL support pattern-based subscriptions (PSUBSCRIBE).

#### Scenario: Subscribe to a single channel
- **WHEN** user enters a channel name and clicks "Subscribe"
- **THEN** system establishes a dedicated Redis connection and executes SUBSCRIBE command, and the channel appears in the active subscriptions list

#### Scenario: Subscribe with pattern
- **WHEN** user enters a glob pattern (e.g., `news.*`) and clicks "Pattern Subscribe"
- **THEN** system executes PSUBSCRIBE and all matching channels' messages are received

#### Scenario: Subscribe to multiple channels
- **WHEN** user enters comma-separated channel names
- **THEN** system subscribes to all specified channels in a single SUBSCRIBE command

### Requirement: Unsubscribe from channels
The system SHALL allow users to unsubscribe from individual channels or all channels at once.

#### Scenario: Unsubscribe from a single channel
- **WHEN** user clicks the unsubscribe button next to a channel in the active subscriptions list
- **THEN** system executes UNSUBSCRIBE for that channel and removes it from the list

#### Scenario: Unsubscribe all
- **WHEN** user clicks "Unsubscribe All"
- **THEN** system unsubscribes from all channels and patterns, and the subscriptions list becomes empty

### Requirement: Real-time message display
The system SHALL display incoming Pub/Sub messages in a scrollable message stream with timestamp, channel name, and message body.

#### Scenario: Message received
- **WHEN** a message is published to a subscribed channel
- **THEN** the message appears in the stream within 100ms, showing formatted timestamp, channel name (color-coded), and message body

#### Scenario: High-frequency messages
- **WHEN** messages arrive at more than 1000/second
- **THEN** system buffers and batch-renders messages using requestAnimationFrame, maintaining UI responsiveness

### Requirement: Message stream controls
The system SHALL provide pause/resume, filter, and clear controls for the message stream.

#### Scenario: Pause message stream
- **WHEN** user clicks "Pause"
- **THEN** new messages are still received and buffered but not rendered; a counter shows buffered message count

#### Scenario: Resume message stream
- **WHEN** user clicks "Resume" after pausing
- **THEN** all buffered messages are rendered and stream returns to real-time display

#### Scenario: Filter messages
- **WHEN** user enters a keyword in the filter input
- **THEN** only messages containing the keyword (in channel name or body) are displayed

#### Scenario: Clear messages
- **WHEN** user clicks "Clear"
- **THEN** all messages in the stream are removed and the counter resets to zero

### Requirement: Message statistics
The system SHALL display real-time statistics including total messages received, messages per second, and per-channel message counts.

#### Scenario: Statistics display
- **WHEN** messages are being received
- **THEN** the statistics panel shows total count, current rate (msgs/sec), and a breakdown by channel

### Requirement: Ring buffer memory protection
The system SHALL limit the message buffer to a maximum of 5000 messages, discarding the oldest when the limit is reached.

#### Scenario: Buffer overflow
- **WHEN** the 5001st message arrives
- **THEN** the oldest message is discarded and the new message is appended, maintaining exactly 5000 messages in the buffer
