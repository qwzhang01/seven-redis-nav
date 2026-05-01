## ADDED Requirements

### Requirement: Command execution
The system SHALL execute Redis commands entered by the user via `cli_exec` IPC. Commands SHALL be sent as raw strings to the Rust backend, which parses and executes them via `redis::cmd`.

#### Scenario: Execute a command
- **WHEN** user types "PING" in CLI input and presses Enter
- **THEN** system calls `cli_exec` IPC with the command string, displays result in output area with RESP-type coloring

#### Scenario: Command with arguments
- **WHEN** user types "GET user:10086:name" and presses Enter
- **THEN** system calls `cli_exec` IPC, displays the value or "(nil)" in output

#### Scenario: Empty command
- **WHEN** user presses Enter with empty input
- **THEN** system does nothing, no command is sent

### Requirement: RESP output coloring
The system SHALL colorize CLI output based on RESP type: errors in red, simple strings in green, integers in orange, bulk strings in white, arrays with indentation.

#### Scenario: Error response
- **WHEN** `cli_exec` returns an error reply
- **THEN** output line shows red text with "(error)" prefix

#### Scenario: Integer response
- **WHEN** `cli_exec` returns an integer (e.g., INCR result)
- **THEN** output line shows orange text with "(integer)" prefix

#### Scenario: Array response
- **WHEN** `cli_exec` returns a bulk array (e.g., KEYSCAN result)
- **THEN** output shows numbered items with indentation, each item on its own line

### Requirement: Command history navigation
The system SHALL support navigating command history with ↑/↓ arrow keys. History SHALL be persisted to SQLite `cli_history` table.

#### Scenario: Navigate history backward
- **WHEN** user presses ↑ arrow in CLI input
- **THEN** input field shows the previous command from history, replacing current input

#### Scenario: Navigate history forward
- **WHEN** user presses ↓ arrow
- **THEN** input field shows the next command, or empty if at the end of history

#### Scenario: History persists across restarts
- **WHEN** user executes commands, quits and relaunches the app
- **THEN** pressing ↑ shows previously executed commands from SQLite

### Requirement: Clear screen
The system SHALL support clearing the CLI output area with ⌘L shortcut or typing "CLEAR" command.

#### Scenario: Clear via shortcut
- **WHEN** user presses ⌘L while CLI Tab is active
- **THEN** output area is cleared, input remains focused

#### Scenario: Clear via command
- **WHEN** user types "CLEAR" and presses Enter
- **THEN** output area is cleared, "CLEAR" is NOT added to command history

### Requirement: Dangerous command interception
The system SHALL intercept dangerous commands (FLUSHDB, FLUSHALL, SHUTDOWN, DEBUG, CONFIG SET requirepass) and require user confirmation before execution.

#### Scenario: Dangerous command intercepted
- **WHEN** user types "FLUSHDB" and presses Enter
- **THEN** system shows confirmation dialog "此操作将删除当前数据库所有键，是否继续？", user must type "FLUSHDB" to confirm

#### Scenario: Confirm dangerous command
- **WHEN** user confirms a dangerous command
- **THEN** system re-sends `cli_exec` with `confirm_token`, backend executes the command

#### Scenario: Cancel dangerous command
- **WHEN** user cancels the confirmation dialog
- **THEN** command is NOT executed, output shows "(cancelled)" message

### Requirement: CLI auto-focus
The system SHALL auto-focus the CLI input field when the CLI Tab is activated.

#### Scenario: Switch to CLI Tab
- **WHEN** user clicks the CLI Tab in Toolbar
- **THEN** CLI input field receives focus immediately
