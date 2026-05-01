## Purpose
IPC foundation adds Stream, Bitmap, HyperLogLog, Pub/Sub publish, CONFIG REWRITE/RESETSTAT, and keyspace notification configuration IPC commands.

## MODIFIED Requirements

### Requirement: Stream IPC commands
The system SHALL provide IPC commands for Stream operations: stream_range, stream_rev_range, stream_add, stream_del, stream_groups, stream_pending.

#### Scenario: Stream range query
- **WHEN** frontend invokes `stream_range` with connection_id, key, start, end, and count
- **THEN** backend executes XRANGE and returns array of { id, fields: HashMap<String, String>, timestamp }

#### Scenario: Stream reverse range query
- **WHEN** frontend invokes `stream_rev_range` with connection_id, key, end, start, and count
- **THEN** backend executes XREVRANGE and returns array of { id, fields, timestamp }

#### Scenario: Stream add entry
- **WHEN** frontend invokes `stream_add` with connection_id, key, id (or "*" for auto), and field-value pairs
- **THEN** backend executes XADD and returns the generated entry ID

#### Scenario: Stream delete entry
- **WHEN** frontend invokes `stream_del` with connection_id, key, and entry_id
- **THEN** backend executes XDEL and returns the number of deleted entries

#### Scenario: Stream consumer groups
- **WHEN** frontend invokes `stream_groups` with connection_id and key
- **THEN** backend executes XINFO GROUPS and returns array of { name, consumers, pending, last_delivered_id }

#### Scenario: Stream pending entries
- **WHEN** frontend invokes `stream_pending` with connection_id, key, and group
- **THEN** backend executes XPENDING and returns array of { consumer_name, pending_count, idle_ms, last_delivered_id }

### Requirement: Bitmap IPC commands
The system SHALL provide IPC commands for Bitmap operations: bitmap_get_range, bitcount, bitpos, setbit.

#### Scenario: Bitmap get range
- **WHEN** frontend invokes `bitmap_get_range` with connection_id, key, start_byte, and end_byte
- **THEN** backend executes GETRANGE and returns the raw bytes as a Base64-encoded string

#### Scenario: Bitmap bit count
- **WHEN** frontend invokes `bitcount` with connection_id, key, and optional start/end
- **THEN** backend executes BITCOUNT and returns the count of set bits

#### Scenario: Bitmap bit position
- **WHEN** frontend invokes `bitpos` with connection_id, key, bit (0 or 1), and optional start/end
- **THEN** backend executes BITPOS and returns the position of the first matching bit

#### Scenario: Bitmap set bit
- **WHEN** frontend invokes `setbit` with connection_id, key, offset, and value (0 or 1)
- **THEN** backend executes SETBIT and returns the original bit value at that position

### Requirement: HyperLogLog IPC commands
The system SHALL provide IPC commands for HyperLogLog operations: hll_pfcount, hll_pfadd, hll_pfmerge.

#### Scenario: HyperLogLog count
- **WHEN** frontend invokes `hll_pfcount` with connection_id and key
- **THEN** backend executes PFCOUNT and returns the estimated cardinality

#### Scenario: HyperLogLog add
- **WHEN** frontend invokes `hll_pfadd` with connection_id, key, and elements array
- **THEN** backend executes PFADD and returns whether the cardinality was updated (1 or 0)

#### Scenario: HyperLogLog merge
- **WHEN** frontend invokes `hll_pfmerge` with connection_id, dest_key, and source_keys array
- **THEN** backend executes PFMERGE and returns success

### Requirement: Pub/Sub publish IPC command
The system SHALL provide an IPC command `pubsub_publish` for publishing messages to channels.

#### Scenario: Publish message
- **WHEN** frontend invokes `pubsub_publish` with connection_id, channel, and message
- **THEN** backend executes PUBLISH and returns the number of receivers

### Requirement: Config rewrite IPC command
The system SHALL provide an IPC command `config_rewrite` for persisting configuration to disk.

#### Scenario: Config rewrite
- **WHEN** frontend invokes `config_rewrite` with connection_id
- **THEN** backend executes CONFIG REWRITE and returns success or error

### Requirement: Config resetstat IPC command
The system SHALL provide an IPC command `config_resetstat` for resetting statistics counters.

#### Scenario: Config resetstat
- **WHEN** frontend invokes `config_resetstat` with connection_id
- **THEN** backend executes CONFIG RESETSTAT and returns success

### Requirement: Notify-keyspace-events config IPC command
The system SHALL provide an IPC command `config_get_notify_keyspace_events` for retrieving the current keyspace events configuration.

#### Scenario: Get notify-keyspace-events
- **WHEN** frontend invokes `config_get_notify_keyspace_events` with connection_id
- **THEN** backend executes CONFIG GET notify-keyspace-events and returns the current config string
