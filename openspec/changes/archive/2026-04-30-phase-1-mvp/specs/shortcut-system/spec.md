## ADDED Requirements

### Requirement: Global shortcut registration
The system SHALL register the following global keyboard shortcuts when the app is focused. Shortcuts SHALL be handled via frontend `keydown` event listeners in a `useShortcut()` composable.

#### Scenario: ⌘K — Global search
- **WHEN** user presses ⌘K
- **THEN** global search input in Toolbar receives focus

#### Scenario: ⌘N — New connection
- **WHEN** user presses ⌘N
- **THEN** ConnectionForm dialog opens in "create" mode

#### Scenario: ⌘F — Key search focus
- **WHEN** user presses ⌘F
- **THEN** KeyPanel search input receives focus

#### Scenario: ⌘1 — Toggle Sidebar
- **WHEN** user presses ⌘1
- **THEN** Sidebar visibility toggles (visible ↔ collapsed)

#### Scenario: ⌘2 — Toggle KeyPanel
- **WHEN** user presses ⌘2
- **THEN** KeyPanel visibility toggles (visible ↔ collapsed)

#### Scenario: ⌘L — CLI clear screen
- **WHEN** user presses ⌘L while CLI Tab is active
- **THEN** CLI output area is cleared

#### Scenario: ⌘+Enter — Save edit
- **WHEN** user presses ⌘+Enter while in edit mode
- **THEN** current edit is submitted (calls key_set IPC)

#### Scenario: ⌘+Shift+R — Refresh data
- **WHEN** user presses ⌘+Shift+R
- **THEN** current view's data is refreshed (re-SCAN, re-fetch key detail, etc.)

### Requirement: Shortcut context awareness
Shortcuts SHALL be context-aware — they SHALL only fire when the appropriate context is active (e.g., ⌘L only in CLI Tab, ⌘+Enter only in edit mode).

#### Scenario: ⌘L ignored in non-CLI Tab
- **WHEN** user presses ⌘L while Browser Tab is active
- **THEN** no action is taken (shortcut is not active)

#### Scenario: ⌘+Enter ignored outside edit mode
- **WHEN** user presses ⌘+Enter while not editing any value
- **THEN** no action is taken

### Requirement: Shortcut conflict prevention
The system SHALL prevent browser/WebView default shortcuts from conflicting with app shortcuts.

#### Scenario: Prevent default browser search
- **WHEN** user presses ⌘F
- **THEN** app handles the shortcut (focus KeyPanel search) and prevents browser's default Find behavior
