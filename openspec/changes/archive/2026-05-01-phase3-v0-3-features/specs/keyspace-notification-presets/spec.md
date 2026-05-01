## Purpose
Keyspace notification presets provide quick-access preset buttons for subscribing to keyspace and keyevent notification patterns.

## ADDED Requirements

### Requirement: Keyspace notification subscription presets
The system SHALL provide quick-access preset buttons for subscribing to keyspace and keyevent notification patterns.

#### Scenario: Keyspace notification preset
- **WHEN** user clicks "🔔 Keyspace 通知" preset button in the Pub/Sub workspace
- **THEN** system checks the current `notify-keyspace-events` config via `config_get_notify_keyspace_events` IPC; if keyspace events (K flag) are not enabled, shows a warning dialog with a "启用" button; after enabling (or if already enabled), subscribes to `__keyspace@*__:*` pattern

#### Scenario: Keyevent notification preset
- **WHEN** user clicks "🔔 Keyevent 通知" preset button
- **THEN** system checks the current `notify-keyspace-events` config; if keyevent events (E flag) are not enabled, shows a warning dialog with a "启用" button; after enabling (or if already enabled), subscribes to `__keyevent@*__:*` pattern

#### Scenario: Notification config already enabled
- **WHEN** the required notification type is already enabled in Redis config
- **THEN** system directly subscribes to the corresponding pattern without showing a warning

#### Scenario: Enable notification config
- **WHEN** user clicks "启用" in the warning dialog
- **THEN** system calls `config_set` IPC with `notify-keyspace-events` set to include the required flags (preserving existing flags) and then subscribes to the pattern

### Requirement: Keyspace notification config check IPC
The system SHALL provide an IPC command `config_get_notify_keyspace_events` to retrieve the current keyspace events configuration.

#### Scenario: Get notification config
- **WHEN** frontend invokes `config_get_notify_keyspace_events` with connection_id
- **THEN** backend executes `CONFIG GET notify-keyspace-events` and returns the current config string (e.g., "AKE", "Ex", "")
