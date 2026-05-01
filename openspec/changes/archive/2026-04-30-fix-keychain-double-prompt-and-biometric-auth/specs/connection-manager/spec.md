## MODIFIED Requirements

### Requirement: Connection list does not expose password plaintext

The system SHALL return connection configurations from `connection_list` WITHOUT reading passwords from Keychain. Instead, the response SHALL include a `has_password: bool` field indicating whether a password is stored, and the `password` field SHALL always be `None`/`null`.

#### Scenario: List connections with passwords stored

- **WHEN** frontend calls `connection_list` IPC and one or more connections have a `keychain_key` set
- **THEN** backend returns `ConnectionConfig` entries with `password: null` and `has_password: true` for those connections; NO Keychain access occurs during this call

#### Scenario: List connections without passwords

- **WHEN** frontend calls `connection_list` IPC and a connection has no `keychain_key`
- **THEN** backend returns `ConnectionConfig` with `password: null` and `has_password: false`

#### Scenario: Connection list triggers no authorization dialog

- **WHEN** frontend calls `connection_list` IPC at app startup
- **THEN** macOS does NOT show any Keychain authorization dialog; the call completes without user interaction

### Requirement: Password read is deferred to connection open

The system SHALL read the password from Keychain only when `connection_open` is called, not during `connection_list`.

#### Scenario: Open connection reads password once

- **WHEN** frontend calls `connection_open` IPC with a `conn_id`
- **THEN** backend reads the password from Keychain exactly once (via `get_password()`), uses it to authenticate with Redis, and does NOT store the plaintext password beyond the scope of the `connection_open` call

#### Scenario: Single authorization dialog per connection open

- **WHEN** user clicks to open a connection that has a password stored in Keychain
- **THEN** macOS shows the authorization dialog (Touch ID or passcode) exactly once per `connection_open` call; the dialog does NOT appear during `connection_list`

### Requirement: Connection save preserves existing password when not modified

The system SHALL support saving a connection without changing the stored password. When the frontend omits the `password` field (or passes `null`) during `connection_save`, the backend SHALL retain the existing Keychain entry unchanged.

#### Scenario: Save connection without changing password

- **WHEN** frontend calls `connection_save` with `password: null` and the connection already has a `keychain_key`
- **THEN** backend updates SQLite metadata (name, host, port, etc.) but does NOT modify the Keychain entry; the existing `keychain_key` is preserved in the updated record

#### Scenario: Save connection with new password

- **WHEN** frontend calls `connection_save` with a non-empty `password` string
- **THEN** backend writes the new password to Keychain (with biometric access control) and updates `keychain_key` in SQLite
