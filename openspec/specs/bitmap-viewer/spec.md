# bitmap-viewer Specification

## Purpose
TBD - created by archiving change phase3-v0-3-features. Update Purpose after archive.
## Requirements
### Requirement: Bitmap visual grid display
The system SHALL render a Bitmap value as a 32-column × N-row visual grid where each cell represents a bit (1 = filled dark, 0 = empty light).

#### Scenario: View Bitmap key
- **WHEN** user selects a Bitmap key in the Browser workspace
- **THEN** BitmapViewer renders with the bitmap data fetched via `bitmap_get_range` IPC, displayed as a visual grid

#### Scenario: Large bitmap pagination
- **WHEN** the bitmap is larger than 4096 bytes (32 × 128 rows)
- **THEN** system loads only the visible rows, with vertical scroll triggering lazy loading of additional chunks

### Requirement: Bitmap quick commands
The system SHALL provide shortcut buttons for common bitmap operations.

#### Scenario: BITCOUNT operation
- **WHEN** user clicks "BITCOUNT" button
- **THEN** system calls `bitcount` IPC with the current key and displays the count of set bits

#### Scenario: BITPOS operation
- **WHEN** user clicks "BITPOS" button
- **THEN** system calls `bitpos` IPC with the current key, bit=1, and displays the position of the first set bit

#### Scenario: SETBIT operation
- **WHEN** user clicks "SETBIT" button
- **THEN** system shows a dialog with offset and value (0/1) inputs, user fills and confirms, system calls `setbit` IPC

### Requirement: Bitmap byte preview
The system SHALL display a byte-level view alongside the bit grid.

#### Scenario: Switch to byte view
- **WHEN** user clicks "按字节" tab
- **THEN** system displays the raw bytes as hex dump, aligned with the bit grid rows

### Requirement: Bitmap key detail metadata
The system SHALL display Bitmap-specific metadata in the key detail header.

#### Scenario: Bitmap metadata display
- **WHEN** a Bitmap key is selected
- **THEN** metadata bar shows: 类型: Bitmap, 位图长度 (BITCOUNT), 最大偏移 (BITPOS 1), 首个置位偏移 (BITPOS 1)

