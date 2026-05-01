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

### Requirement: Timed repeat publishing (Phase 3)
The system SHALL allow users to configure timed repeat message publishing with configurable interval and maximum count.

#### Scenario: Enable repeat publishing
- **WHEN** user toggles the repeat timer and sets an interval (e.g., 2s)
- **THEN** system automatically re-publishes the message at the specified interval

#### Scenario: Rate limiting
- **WHEN** user sets interval below 0.1s (100ms)
- **THEN** system enforces a minimum interval of 100ms (10 messages/second max)

#### Scenario: Stop repeat
- **WHEN** user clicks stop or reaches the configured maximum count
- **THEN** system stops the repeat timer

### Requirement: Per-channel pause/resume (Phase 3)
The system SHALL allow users to pause and resume individual subscribed channels without unsubscribing.

#### Scenario: Pause a channel
- **WHEN** user clicks the pause button on a subscribed channel
- **THEN** messages from that channel are buffered but not displayed; channel tag shows "paused" state

#### Scenario: Resume a channel
- **WHEN** user clicks resume on a paused channel
- **THEN** buffered messages for that channel are flushed to the display

### Requirement: Message export (Phase 3)
The system SHALL allow users to export received messages in JSON or NDJSON format.

#### Scenario: Export all messages
- **WHEN** user clicks export and selects "全部消息" with JSON format
- **THEN** system generates a JSON array of all messages and triggers a file download

#### Scenario: Export filtered messages
- **WHEN** user selects "筛选结果" scope
- **THEN** only messages matching the current filter keyword are exported

#### Scenario: Export by channel
- **WHEN** user selects "指定频道" and enters a channel name
- **THEN** only messages from that channel are exported

### Requirement: Keyspace notification presets (Phase 3)
The system SHALL provide quick-access buttons for common Keyspace/Keyevent notification configurations.

#### Scenario: Apply Keyspace preset
- **WHEN** user clicks "键空间 + 通用命令" preset
- **THEN** system executes CONFIG SET notify-keyspace-events "KE$" and subscribes to __keyspace@0__:* pattern

#### Scenario: Disable notifications
- **WHEN** user clicks "关闭通知" preset
- **THEN** system executes CONFIG SET notify-keyspace-events "" and unsubscribes from notification patterns
