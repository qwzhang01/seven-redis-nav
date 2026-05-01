## Purpose
Data editor provides inline editing and advanced data manipulation capabilities for Redis keys, including Stream entry management, JSON editing with CodeMirror 6, binary content editing, and HyperLogLog operations.

## ADDED Requirements

### Requirement: Stream entry add and delete
The system SHALL allow users to add entries to a Stream via XADD and delete entries via XDEL from the StreamViewer.

#### Scenario: Add entry to Stream
- **WHEN** user clicks "添加条目" button in StreamViewer
- **THEN** system shows a form with fields (ID: auto/manual toggle, field-value pairs editor), user fills and clicks "提交", system calls `stream_add` IPC (XADD)

#### Scenario: Delete entry from Stream
- **WHEN** user clicks the delete icon next to a Stream entry
- **THEN** system shows confirmation dialog with entry ID, user confirms, system calls `stream_del` IPC (XDEL)

### Requirement: JSON editing with CodeMirror 6
The system SHALL use CodeMirror 6 as the editor for String key values that are detected as JSON, replacing the plain textarea.

#### Scenario: Edit JSON value
- **WHEN** user edits a JSON String value in the CodeMirror 6 editor and presses ⌘+Enter
- **THEN** system validates the JSON syntax; if valid, calls `key_set` IPC with the updated JSON string; if invalid, shows an inline error and prevents save

#### Scenario: Beautify before save
- **WHEN** user clicks the "美化" button in the JSON editor toolbar
- **THEN** the JSON content is reformatted with proper indentation; user can then edit and save the beautified version

### Requirement: Binary content editing
The system SHALL allow editing binary content in Hex or Base64 view modes.

#### Scenario: Edit in Hex view
- **WHEN** user modifies hex bytes in the Hex view and presses ⌘+Enter
- **THEN** system converts the hex string back to bytes and calls `key_set` IPC

#### Scenario: Edit in Base64 view
- **WHEN** user modifies the Base64 string and presses ⌘+Enter
- **THEN** system decodes the Base64 string back to bytes and calls `key_set` IPC; if the Base64 is invalid, shows an inline error

### Requirement: HyperLogLog operations
The system SHALL allow users to add elements via PFADD and merge HyperLogLog keys via PFMERGE.

#### Scenario: Add element via PFADD
- **WHEN** user enters element values (comma-separated) in the HyperLogLogViewer and clicks "PFADD"
- **THEN** system calls `hll_pfadd` IPC with the key and elements, and refreshes the cardinality display

#### Scenario: Merge via PFMERGE
- **WHEN** user clicks "PFMERGE" button and selects target keys from a dropdown
- **THEN** system calls `hll_pfmerge` IPC with the source key and target keys, and shows the merged cardinality result
