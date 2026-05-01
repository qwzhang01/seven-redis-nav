## ADDED Requirements

### Requirement: Fetch slowlog entries
The system SHALL retrieve slow query log entries from Redis using SLOWLOG GET command and display them in a sortable table.

#### Scenario: Load slowlog
- **WHEN** user navigates to the Slowlog tab
- **THEN** system executes SLOWLOG GET and displays entries in a table with columns: ID, Timestamp, Duration (μs), Command, Client Address

#### Scenario: Custom entry count
- **WHEN** user specifies a count (e.g., 50) in the "Entries" input
- **THEN** system executes SLOWLOG GET 50 and displays up to 50 entries

### Requirement: Sort slowlog entries
The system SHALL allow sorting entries by any column, with duration descending as the default sort.

#### Scenario: Sort by duration
- **WHEN** user clicks the "Duration" column header
- **THEN** entries are sorted by duration in descending order (slowest first)

#### Scenario: Sort by timestamp
- **WHEN** user clicks the "Timestamp" column header
- **THEN** entries are sorted by timestamp in descending order (newest first)

### Requirement: Refresh slowlog
The system SHALL support manual refresh and optional auto-refresh with configurable interval.

#### Scenario: Manual refresh
- **WHEN** user clicks the "Refresh" button
- **THEN** system re-fetches SLOWLOG GET and updates the table

#### Scenario: Auto-refresh enabled
- **WHEN** user enables auto-refresh and sets interval to 5 seconds
- **THEN** system automatically re-fetches slowlog every 5 seconds until disabled

### Requirement: Reset slowlog
The system SHALL allow users to clear the slowlog with confirmation.

#### Scenario: Reset with confirmation
- **WHEN** user clicks "Reset Slowlog"
- **THEN** system shows a confirmation dialog; upon confirm, executes SLOWLOG RESET and refreshes the table showing empty results

### Requirement: Slowlog length display
The system SHALL display the current slowlog length (SLOWLOG LEN) in the toolbar area.

#### Scenario: Display length
- **WHEN** slowlog data is loaded
- **THEN** the total number of entries in Redis slowlog is displayed (may differ from displayed count if limited by GET parameter)

### Requirement: Duration formatting
The system SHALL format duration values with human-readable units and color coding.

#### Scenario: Color-coded duration
- **WHEN** entries are displayed
- **THEN** durations > 100ms are shown in red, > 10ms in orange, and < 10ms in default color
