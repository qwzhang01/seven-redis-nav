## ADDED Requirements

### Requirement: Inline editing
The system SHALL support inline editing of field values in Hash, List, Set, ZSet viewers. Editing SHALL be triggered by double-clicking a value cell or clicking the edit icon.

#### Scenario: Edit a Hash field value
- **WHEN** user double-clicks a value cell in HashViewer
- **THEN** cell becomes editable input, user modifies value, presses ⌘+Enter or clicks ✓ to save, system calls `key_set` IPC

#### Scenario: Edit a String value
- **WHEN** user clicks edit button in StringViewer
- **THEN** text area becomes editable, user modifies, presses ⌘+Enter, system calls `key_set` IPC

### Requirement: Delete key with confirmation
The system SHALL require confirmation before deleting a key. For single key deletion, a dialog SHALL show the key name. User MUST type the key name to confirm.

#### Scenario: Delete a single key
- **WHEN** user clicks 🗑️ delete button on a key
- **THEN** system shows confirmation dialog with key name, user types exact key name, clicks "确认删除", system calls `key_delete` IPC

#### Scenario: Cancel deletion
- **WHEN** user clicks "取消" in delete confirmation dialog
- **THEN** dialog closes, no action taken

### Requirement: Key rename
The system SHALL allow renaming a key via `RENAME` command. A dialog SHALL accept the new key name.

#### Scenario: Rename a key
- **WHEN** user clicks ✏️ rename button
- **THEN** system shows dialog with current key name pre-filled, user enters new name, clicks "确认", system calls `key_rename` IPC

#### Scenario: Rename to existing key
- **WHEN** user enters a key name that already exists
- **THEN** system shows warning "目标键已存在，重命名将覆盖", user confirms or cancels

### Requirement: TTL management
The system SHALL allow setting, removing, and modifying TTL on keys via `EXPIRE` and `PERSIST` commands.

#### Scenario: Set TTL
- **WHEN** user clicks ⏱ TTL button and selects "设置过期时间"
- **THEN** system shows TTL editor dialog with unit selector (秒/分/时/天), user enters value, clicks "确认", system calls `key_ttl_set` IPC

#### Scenario: Remove TTL (make permanent)
- **WHEN** user clicks ⏱ TTL button and selects "移除过期时间"
- **THEN** system calls `key_ttl_set` IPC with ttl_secs = -1 (PERSIST), key becomes permanent

### Requirement: Create new key
The system SHALL allow creating a new key with a selected type and initial value.

#### Scenario: Create a new String key
- **WHEN** user clicks + button in KeyPanel and selects "String"
- **THEN** system shows key creation form with key name input and value textarea, user fills in and clicks "创建", system calls `key_set` IPC

#### Scenario: Create a new Hash key
- **WHEN** user clicks + button in KeyPanel and selects "Hash"
- **THEN** system shows key creation form with key name input and initial field-value pair, user fills in and clicks "创建"

### Requirement: Operation feedback
The system SHALL display Toast notifications for all data operations indicating success or failure.

#### Scenario: Successful operation
- **WHEN** a key_set/key_delete/key_rename/key_ttl_set operation succeeds
- **THEN** system shows success Toast (green) with operation description, refreshes affected data

#### Scenario: Failed operation
- **WHEN** a data operation fails (Redis error, timeout)
- **THEN** system shows error Toast (red) with error message from IpcError

### Requirement: JSON smart detection and editor (Phase 3)
The system SHALL automatically detect JSON content in String keys and provide a CodeMirror 6-based JSON editor with format/compress capabilities.

#### Scenario: Auto-detect JSON
- **WHEN** user selects a String key whose value is valid JSON
- **THEN** StringViewer automatically switches to JSON mode with syntax highlighting

#### Scenario: Format JSON
- **WHEN** user clicks the format button in JSON mode
- **THEN** system pretty-prints the JSON with 2-space indentation

#### Scenario: Compress JSON
- **WHEN** user clicks the compress button
- **THEN** system minifies the JSON to a single line

### Requirement: Binary data views (Phase 3)
The system SHALL provide three view modes for binary/non-printable String data: Hex dump, Base64, and UTF-8 text.

#### Scenario: View as Hex
- **WHEN** user selects Hex view mode
- **THEN** system displays the value as a hex dump with offset addresses and ASCII preview

#### Scenario: View as Base64
- **WHEN** user selects Base64 view mode
- **THEN** system displays the Base64-encoded representation

### Requirement: Stream entry add and delete
The system SHALL allow adding and deleting entries in a Stream key, and managing consumer groups.

#### Scenario: Add Stream entry
- **WHEN** user fills in field-value pairs and clicks "添加" in StreamViewer
- **THEN** system executes XADD with the specified fields and refreshes the entry list

#### Scenario: Delete Stream entry
- **WHEN** user clicks delete on a Stream entry
- **THEN** system shows confirmation and executes XDEL on confirmation

### Requirement: Bitmap bit editing (Phase 3)
The system SHALL allow toggling individual bits in a Bitmap key.

#### Scenario: Toggle a bit
- **WHEN** user clicks a bit cell in the Bitmap grid
- **THEN** system executes SETBIT to toggle the bit and refreshes the grid
