## Purpose
Pub/Sub publisher provides a panel for publishing messages to Redis channels, including timed repeat publishing.

## ADDED Requirements

### Requirement: Pub/Sub message publishing
The system SHALL allow users to publish messages to Redis channels directly from the Pub/Sub workspace.

#### Scenario: Publish a single message
- **WHEN** user enters a channel name and message body in the Publish panel and clicks "🚀 发布"
- **THEN** system calls `pubsub_publish` IPC with the channel and message, and displays the number of receivers

#### Scenario: Empty message disabled
- **WHEN** message body input is empty
- **THEN** the "🚀 发布" button is disabled (greyed out)

#### Scenario: Empty channel disabled
- **WHEN** channel name input is empty
- **THEN** the "🚀 发布" button is disabled (greyed out)

### Requirement: Timed repeat publishing
The system SHALL allow users to set up a timed repeat publish at a specified interval.

#### Scenario: Set up timed publish
- **WHEN** user clicks "定时重复" toggle, enters an interval (e.g., 1s), and clicks "开始"
- **THEN** system publishes the message at the specified interval, shows a countdown and remaining count

#### Scenario: Stop timed publish
- **WHEN** user clicks "停止" button
- **THEN** system cancels the timed publish task and displays "已停止"

#### Scenario: Maximum repetition rate
- **WHEN** user sets an interval below 100ms
- **THEN** system caps the interval at 100ms (10 times/second max) and shows a warning

### Requirement: Per-channel subscription pause
The system SHALL allow users to pause individual channel subscriptions while keeping others active.

#### Scenario: Pause a single channel
- **WHEN** user clicks the pause icon next to a channel in the active subscriptions list
- **THEN** system unsubscribes from that channel but keeps it in the list with a "已暂停" badge; messages from other channels continue to be received

#### Scenario: Resume a paused channel
- **WHEN** user clicks the resume icon next to a paused channel
- **THEN** system re-subscribes to the channel and removes the "已暂停" badge; messages from that channel start appearing again

### Requirement: Keyspace notification quick subscription presets
The system SHALL provide quick-access presets for subscribing to keyspace and keyevent notifications.

#### Scenario: Subscribe to keyspace notifications
- **WHEN** user clicks "Keyspace 通知" preset button
- **THEN** system checks current `notify-keyspace-events` config; if keyspace events (K/A) are not enabled, shows a warning with a "启用" button that calls `config_get_notify_keyspace_events` IPC to enable; then subscribes to `__keyspace@*__:*` pattern

#### Scenario: Subscribe to keyevent notifications
- **WHEN** user clicks "Keyevent 通知" preset button
- **THEN** system checks current `notify-keyspace-events` config; if keyevent events (E/A) are not enabled, shows a warning with a "启用" button; then subscribes to `__keyevent@*__:*` pattern

#### Scenario: Notification config already enabled
- **WHEN** the required notification type is already enabled in Redis config
- **THEN** system directly subscribes without showing a warning
