## ADDED Requirements

### Requirement: Biometric-protected Keychain write

The system SHALL save Redis connection passwords to macOS Keychain using `SecAccessControl` with `biometryAny | devicePasscode` flags, so that subsequent reads can be authorized via Touch ID instead of the login keychain password dialog.

#### Scenario: Save password with biometric access control

- **WHEN** user saves a new or edited connection with a non-empty password
- **THEN** backend calls `SecItemAdd` with `kSecAccessControlBiometryAny | kSecAccessControlOr | kSecAccessControlDevicePasscode` access control, storing the password under the same `conn-{id}` account key

#### Scenario: Touch ID prompt on password read

- **WHEN** backend calls `get_password()` for a Keychain item saved with biometric access control
- **THEN** macOS presents a Touch ID prompt (or device passcode fallback) instead of the login keychain password dialog; on success the password bytes are returned to the caller

#### Scenario: Touch ID not available fallback

- **WHEN** the device has no Touch ID hardware or biometrics are disabled by policy
- **THEN** macOS falls back to device passcode prompt; the `get_password()` call still succeeds after user enters the passcode

### Requirement: Legacy Keychain entry compatibility

The system SHALL remain able to read Keychain entries created without `SecAccessControl` (legacy entries saved by earlier versions of the app).

#### Scenario: Read legacy entry

- **WHEN** `get_password()` is called for an account key that has a legacy entry (no access control)
- **THEN** the system reads the password successfully; macOS may show the old-style login keychain password dialog for this entry

#### Scenario: Automatic upgrade on re-save

- **WHEN** user opens the connection edit form and saves without changing the password (or with a new password)
- **THEN** backend deletes the old legacy entry and writes a new entry with biometric access control, upgrading the entry in-place

### Requirement: Biometric auth availability check

The system SHALL expose a utility function to check whether biometric authentication is available on the current device.

#### Scenario: Check biometric availability

- **WHEN** `is_biometric_available()` is called
- **THEN** it returns `true` if Touch ID or Face ID is enrolled and available, `false` otherwise; this result MAY be used by the frontend to display an informational badge on the connection form
