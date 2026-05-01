## Purpose
Pub/Sub workspace adds per-channel subscription pause/resume, publish panel, keyspace notification presets, and message export.

## MODIFIED Requirements

### Requirement: Per-channel subscription pause
The system SHALL allow users to pause individual channel subscriptions while keeping others active.

#### Scenario: Pause a single channel
- **WHEN** user clicks the pause icon next to a channel in the active subscriptions list
- **THEN** system unsubscribes from that channel but keeps it in the list with a "已暂停" badge; messages from other channels continue to be received

#### Scenario: Resume a paused channel
- **WHEN** user clicks the resume icon next to a paused channel
- **THEN** system re-subscribes to the channel and removes the "已暂停" badge; messages from that channel start appearing again

### Requirement: Publish messages from Pub/Sub workspace
The system SHALL provide a publish panel within the Pub/Sub workspace for sending messages to channels.

#### Scenario: Open publish panel
- **WHEN** user clicks the "📤 发布" button in the Pub/Sub workspace toolbar
- **THEN** a PublishPanel drawer opens on the right side with channel input, message body textarea, and "🚀 发布" button

#### Scenario: Close publish panel
- **WHEN** user clicks the close button or clicks outside the PublishPanel
- **THEN** the drawer closes without affecting subscriptions

### Requirement: Quick subscription presets for keyspace notifications
The system SHALL provide quick-access preset buttons for subscribing to keyspace and keyevent notification patterns.

#### Scenario: Preset buttons display
- **WHEN** user opens the Pub/Sub workspace
- **THEN** two preset buttons are visible: "🔔 Keyspace 通知" and "🔔 Keyevent 通知"

#### Scenario: Subscribe via preset
- **WHEN** user clicks a preset button
- **THEN** system subscribes to the corresponding pattern (`__keyspace@*__:*` or `__keyevent@*__:*`) and the subscription appears in the active list

### Requirement: Export messages to local file
The system SHALL allow users to export received messages to a local file in JSON or NDJSON format.

#### Scenario: Open export dialog
- **WHEN** user clicks the "💾 导出" button in the message stream controls
- **THEN** an export dialog appears with format selection (JSON array / NDJSON) and scope selection (all messages / filtered messages / selected channel)

#### Scenario: Export as JSON array
- **WHEN** user selects "JSON 数组" format and clicks "导出"
- **THEN** system writes a JSON file containing an array of message objects with fields { timestamp, channel, pattern, message }

#### Scenario: Export as NDJSON
- **WHEN** user selects "NDJSON" format and clicks "导出"
- **THEN** system writes a file with one JSON object per line, each containing { timestamp, channel, pattern, message }
