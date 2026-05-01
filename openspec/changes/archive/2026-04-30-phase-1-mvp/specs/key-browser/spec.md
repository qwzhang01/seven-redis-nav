## ADDED Requirements

### Requirement: SCAN-based key listing
The system SHALL list Redis keys using `SCAN` command with cursor-based pagination. Each page SHALL request `COUNT 200` keys. The frontend SHALL maintain a cursor stack for forward/backward navigation.

#### Scenario: Initial key list load
- **WHEN** user selects a connection and DB
- **THEN** system calls `keys_scan` IPC with cursor 0, MATCH "*", COUNT 200, displays returned keys in KeyPanel

#### Scenario: Load next page
- **WHEN** user clicks next page button in KeyPanel pagination
- **THEN** system calls `keys_scan` with current cursor, pushes previous cursor onto stack, displays new page

#### Scenario: Load previous page
- **WHEN** user clicks previous page button
- **THEN** system pops cursor from stack, re-issues `keys_scan` with that cursor, displays previous page

#### Scenario: SCAN returns cursor 0 (complete)
- **WHEN** `keys_scan` returns cursor 0
- **THEN** system marks pagination as "last page", disables next button

### Requirement: Pattern search
The system SHALL support key pattern matching via `SCAN MATCH`. The search input SHALL accept glob-style patterns (e.g., `user:*`, `session:*`).

#### Scenario: Search by pattern
- **WHEN** user types a pattern in KeyPanel search input and presses Enter
- **THEN** system resets cursor stack, calls `keys_scan` with MATCH pattern, displays filtered results

#### Scenario: Empty pattern shows all
- **WHEN** search input is cleared
- **THEN** system resets cursor stack, calls `keys_scan` with MATCH "*", displays all keys

### Requirement: Type filtering
The system SHALL support filtering keys by Redis data type. Filtering SHALL be performed client-side after SCAN results are returned (each key's TYPE is fetched lazily or from cache).

#### Scenario: Filter by type
- **WHEN** user selects "Hash" from type dropdown in KeyPanel
- **THEN** system filters displayed keys to show only Hash type keys

#### Scenario: All types selected
- **WHEN** user selects "全部类型" from type dropdown
- **THEN** system shows all keys regardless of type

### Requirement: Key metadata display
The system SHALL display key metadata in KeyPanel list items: type badge (colored), key name (monospace, ellipsis on overflow), TTL (formatted), size (human-readable).

#### Scenario: Key item renders metadata
- **WHEN** a key is listed in KeyPanel
- **THEN** item shows: type badge with correct color (String=blue, Hash=amber, List=green, Set=purple, ZSet=pink), key name in monospace, TTL formatted (永久/Xd Xh/Xm Xs/Xs), size in B/KB/MB

### Requirement: Key selection and detail loading
The system SHALL load full key detail when a key is selected in KeyPanel. Detail includes type, TTL, size, encoding, element count, and value data.

#### Scenario: Select a key
- **WHEN** user clicks a key item in KeyPanel
- **THEN** system calls `key_get` IPC, loads detail into Browser workspace, highlights selected key in list

#### Scenario: Selected key indicates active
- **WHEN** a key is selected
- **THEN** key item shows red left border + light red background, Browser workspace renders the key's detail view
