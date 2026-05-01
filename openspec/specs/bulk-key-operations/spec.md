## ADDED Requirements

### Requirement: Multi-select keys in key panel
The system SHALL support multi-select of keys in the key panel via keyboard modifiers and select-all shortcut.

#### Scenario: Command-click to toggle selection
- **WHEN** user holds ⌘ and clicks a key item
- **THEN** that key is added to the selection set without deselecting others; clicking again removes it from the selection

#### Scenario: Shift-click range selection
- **WHEN** user holds Shift and clicks a key item
- **THEN** all keys between the last selected key and the clicked key are added to the selection

#### Scenario: Select all with ⌘A
- **WHEN** user presses ⌘A while the key panel is focused
- **THEN** all currently loaded keys are added to the selection

#### Scenario: Clear selection on normal click
- **WHEN** user clicks a key item without any modifier key
- **THEN** all previous selections are cleared and only the clicked key is selected (and its detail is shown in the workspace)

#### Scenario: Selection count badge
- **WHEN** one or more keys are selected
- **THEN** a bulk action bar appears at the bottom of the key panel showing the count of selected keys and available actions

### Requirement: Bulk delete keys
The system SHALL allow users to delete all selected keys in batches with progress feedback.

#### Scenario: Initiate bulk delete
- **WHEN** user clicks "Delete" in the bulk action bar with N keys selected
- **THEN** system shows a confirmation dialog displaying the count; if N ≥ 100, user must type "DELETE" to confirm

#### Scenario: Batch execution with progress
- **WHEN** user confirms bulk delete
- **THEN** system splits keys into batches of 100, executes each batch sequentially, and shows a progress bar (X / N deleted)

#### Scenario: Partial failure handling
- **WHEN** one or more batches fail during bulk delete
- **THEN** system continues remaining batches, then shows a summary with the count of successfully deleted keys and a list of failed keys

#### Scenario: Completion feedback
- **WHEN** all batches complete successfully
- **THEN** system shows a success toast, clears the selection, and refreshes the key list

### Requirement: Bulk TTL modification
The system SHALL allow users to set or remove TTL for all selected keys at once.

#### Scenario: Set TTL for selected keys
- **WHEN** user clicks "Set TTL" in the bulk action bar
- **THEN** system shows a TTL input dialog; on confirm, applies EXPIRE to all selected keys and shows success/failure summary

#### Scenario: Remove TTL for selected keys
- **WHEN** user clicks "Remove TTL" in the bulk action bar
- **THEN** system applies PERSIST to all selected keys and shows success/failure summary

### Requirement: Bulk copy key names
The system SHALL allow users to copy all selected key names to the clipboard.

#### Scenario: Copy key names
- **WHEN** user clicks "Copy Names" in the bulk action bar
- **THEN** system copies all selected key names to the clipboard as a newline-separated list and shows a toast confirming the count
