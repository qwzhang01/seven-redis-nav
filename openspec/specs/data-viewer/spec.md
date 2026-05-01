## ADDED Requirements

### Requirement: Extended type dispatch for Stream, Bitmap, HyperLogLog
The system SHALL render a type-specific viewer based on the key's `TYPE` result. Supported types: String, Hash, List, Set, ZSet, Stream. Unknown types SHALL display a fallback raw view. String keys MAY be auto-detected as Bitmap or HyperLogLog based on key naming conventions and encoding.

#### Scenario: View a String key
- **WHEN** user selects a key with type String
- **THEN** Browser workspace renders StringViewer showing the full string value in a text area

#### Scenario: View a Hash key
- **WHEN** user selects a key with type Hash
- **THEN** Browser workspace renders HashViewer showing a table of field-value pairs (columns: 字段 | 值 | 操作)

#### Scenario: View a List key
- **WHEN** user selects a key with type List
- **THEN** Browser workspace renders ListViewer showing an indexed list (columns: 索引 | 值 | 操作)

#### Scenario: View a Set key
- **WHEN** user selects a key with type Set
- **THEN** Browser workspace renders SetViewer showing member cards with delete buttons

#### Scenario: View a ZSet key
- **WHEN** user selects a key with type ZSet
- **THEN** Browser workspace renders ZSetViewer showing a table of member-score pairs sorted by score (columns: 分数 | 成员 | 操作)

#### Scenario: View a Stream key (Phase 3)
- **WHEN** user selects a key with type Stream
- **THEN** Browser workspace renders StreamViewer with entries tab and consumer groups tab, supporting XRANGE-based pagination

#### Scenario: Auto-detect Bitmap (Phase 3)
- **WHEN** user selects a String key with name prefix "bitmap:" or manually selects Bitmap type
- **THEN** Browser workspace renders BitmapViewer with virtualized bit grid and chunk-based loading

#### Scenario: Auto-detect HyperLogLog (Phase 3)
- **WHEN** user selects a String key with raw encoding and manually selects HyperLogLog type
- **THEN** Browser workspace renders HyperLogLogViewer with cardinality display and PFADD/PFMERGE operations

#### Scenario: Unknown type fallback
- **WHEN** user selects a key with unsupported type (e.g., Module type)
- **THEN** Browser workspace shows "暂不支持此类型查看" message with raw DUMP preview option

### Requirement: Key detail header
The system SHALL display a detail header above the viewer with: key name (monospace bold), type badge, and action buttons (复制键名/⏱TTL/✏️重命名/🗑️删除).

#### Scenario: Detail header renders
- **WHEN** any key is selected
- **THEN** header shows: type icon + key name in monospace bold + type badge (colored) + action buttons row

### Requirement: Metadata bar
The system SHALL display a metadata bar below the detail header with 6 fields: 类型, TTL, 大小, 编码, 元素数, DB. Each field SHALL have a light gray background.

#### Scenario: Metadata bar renders
- **WHEN** any key is selected
- **THEN** metadata bar shows 6 fields with values from key_get result (e.g., 类型: Hash, TTL: 2h 30m, 大小: 2.4KB, 编码: ziplist, 元素数: 15, DB: 0)

### Requirement: Sub-tab navigation
The system SHALL provide sub-tabs within the Browser workspace: 数据 (default), 原始, 相关命令.

#### Scenario: Switch sub-tabs
- **WHEN** user clicks "原始" sub-tab
- **THEN** viewer area switches to raw JSON representation of the key's value

#### Scenario: Related commands tab
- **WHEN** user clicks "相关命令" sub-tab
- **THEN** viewer area shows command cards relevant to the current key type (e.g., Hash → HGET/HSET/HGETALL/HDEL/HKEYS/HLEN)

### Requirement: TTL formatted display
The system SHALL format TTL values according to rules: < 0 → "永久（无过期）", > 86400 → "X 天 X 小时", > 3600 → "X 小时 X 分钟", > 60 → "X 分钟 X 秒", else → "X 秒".

#### Scenario: TTL formatting
- **WHEN** key TTL is 90000
- **THEN** display shows "1 天 1 小时"

#### Scenario: Permanent key
- **WHEN** key TTL is -1
- **THEN** display shows "永久（无过期）"
