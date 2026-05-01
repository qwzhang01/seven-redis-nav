## ADDED Requirements

### Requirement: Quick connect with direct session establishment

The Welcome page SHALL provide a "快速连接" form (host, port, password) with a primary "连接" button that directly establishes a Redis session and transitions to the workspace upon success.

#### Scenario: Successful quick connect

- **WHEN** user fills in host/port (and optional password) and clicks "连接"
- **THEN** system establishes a Redis connection, transitions to workspace view, and displays the connected state in Statusbar

#### Scenario: Quick connect failure

- **WHEN** user clicks "连接" but connection fails (refused/timeout/auth error)
- **THEN** system displays an inline error message with specific failure reason, and remains on Welcome page

#### Scenario: Quick connect with test-only option

- **WHEN** user clicks the secondary "测试连接" link/button
- **THEN** system performs a PING test without establishing a persistent session, and displays latency + server version on success

### Requirement: Temporary connection save prompt

After a successful quick connect (temporary connection), the system SHALL display a persistent, non-intrusive "保存连接" prompt in the Toolbar or Statusbar area.

#### Scenario: User saves temporary connection

- **WHEN** user clicks "保存连接" prompt while in a temporary session
- **THEN** system opens ConnectionForm dialog pre-filled with current host/port/password, allowing user to add name/group before saving

#### Scenario: User ignores save prompt

- **WHEN** user does not click "保存连接" and continues working
- **THEN** the prompt remains visible but does not block any operations; connection is lost on app close

### Requirement: Saved connections list display

The Welcome page SHALL display all saved connections in a list on the left side (or full-width when no connections exist), grouped by `group_name`.

#### Scenario: Display saved connections with groups

- **WHEN** user has saved connections with different group_name values
- **THEN** connections are displayed grouped under collapsible group headers, sorted by sort_order within each group

#### Scenario: Display saved connections without groups

- **WHEN** user has saved connections with empty group_name
- **THEN** connections are displayed in a flat list sorted by sort_order

#### Scenario: Empty state (no saved connections)

- **WHEN** user has no saved connections
- **THEN** the left panel shows an empty state illustration with guidance text and a "新建连接" button; the quick connect form is centered

### Requirement: One-click connect from saved list

Each saved connection item SHALL be clickable to directly establish a connection.

#### Scenario: Click saved connection to connect

- **WHEN** user clicks a saved connection item
- **THEN** system calls connectionOpen with the connId, establishes session, and transitions to workspace

#### Scenario: Saved connection fails to connect

- **WHEN** user clicks a saved connection but connection fails
- **THEN** system displays error Toast and remains on Welcome page; the connection item shows error state indicator

### Requirement: Saved connection item actions

Each saved connection item SHALL provide edit and delete actions.

#### Scenario: Edit saved connection

- **WHEN** user hovers a connection item and clicks the edit icon (or right-clicks → "编辑")
- **THEN** system opens ConnectionForm dialog pre-filled with the connection's config for editing

#### Scenario: Delete saved connection

- **WHEN** user hovers a connection item and clicks the delete icon (or right-clicks → "删除")
- **THEN** system shows a confirmation dialog; upon confirm, deletes from SQLite + Keychain and removes from list

### Requirement: New connection entry point

The Welcome page SHALL provide a prominent "新建连接" button that opens the full ConnectionForm dialog.

#### Scenario: Create new connection from Welcome page

- **WHEN** user clicks "新建连接" button
- **THEN** system opens ConnectionForm dialog in create mode (empty fields); upon save, connection appears in saved list and auto-connects

### Requirement: Responsive layout adaptation

The Welcome page layout SHALL adapt based on whether saved connections exist and window width.

#### Scenario: With saved connections (normal width)

- **WHEN** window width ≥ 960px and saved connections exist
- **THEN** page displays left-right split layout: saved connections list (left) | quick connect + new connection (right)

#### Scenario: No saved connections

- **WHEN** no saved connections exist
- **THEN** page displays centered single-column layout with quick connect form and "新建连接" button prominently displayed

#### Scenario: Narrow window

- **WHEN** window width is at minimum (960px)
- **THEN** layout remains functional with reduced padding; saved list and form stack if needed
