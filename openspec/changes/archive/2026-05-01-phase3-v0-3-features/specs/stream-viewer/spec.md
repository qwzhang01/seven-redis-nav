## Purpose
Stream viewer provides visualization and operations for Redis Stream keys, including paginated entry browsing, consumer group management, and entry add/delete.

## ADDED Requirements

### Requirement: Stream paginated browsing
The system SHALL allow users to browse Stream entries using XRANGE/XREVRANGE with pagination.

#### Scenario: Forward browse Stream entries
- **WHEN** user selects a Stream key in the Browser workspace
- **THEN** StreamViewer renders with the first page of entries (up to 500) fetched via `stream_range` IPC, displaying ID, field-value pairs, and timestamp

#### Scenario: Navigate to next page
- **WHEN** user clicks "下一页" or the last entry's ID is used as the start ID for the next XRANGE call
- **THEN** system fetches the next page of entries and appends to the list

#### Scenario: Reverse browse Stream entries
- **WHEN** user clicks "倒序" toggle
- **THEN** system switches to XREVRANGE via `stream_rev_range` IPC and displays entries in reverse chronological order

### Requirement: Stream Consumer Groups viewing
The system SHALL allow users to view Consumer Groups of a Stream.

#### Scenario: View Consumer Groups
- **WHEN** user clicks "Consumer Groups" tab within StreamViewer
- **THEN** system calls `stream_groups` IPC, displays a table with Group Name, Consumers count, Pending entries count, Last-delivered-ID

#### Scenario: View pending entries per group
- **WHEN** user clicks on a Consumer Group row
- **THEN** system calls `stream_pending` IPC, displays a table with Consumer Name, Pending count, Idle time (ms), Last-delivered-ID

### Requirement: Stream entry operations
The system SHALL allow users to add and delete Stream entries.

#### Scenario: Add entry to Stream
- **WHEN** user clicks "添加条目" button in StreamViewer
- **THEN** system shows a form with fields (ID pattern: auto/manual, field-value pairs), user fills and clicks "提交", system calls `stream_add` IPC (XADD)

#### Scenario: Delete entry from Stream
- **WHEN** user clicks the delete icon next to a Stream entry
- **THEN** system shows confirmation dialog with entry ID, user confirms, system calls `stream_del` IPC (XDEL)

### Requirement: Stream key detail metadata
The system SHALL display Stream-specific metadata in the key detail header.

#### Scenario: Stream metadata display
- **WHEN** a Stream key is selected
- **THEN** metadata bar shows: 类型: Stream, 长度 (XLEN), Radix tree nodes, Last-generated-ID, Max-length, Groups count
