use serde::{Deserialize, Serialize};

// ... existing code ...

/// A single Stream entry (from XRANGE / XREVRANGE)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StreamEntry {
    /// Entry ID (e.g., "1619123456789-0")
    pub id: String,
    /// Field-value pairs
    pub fields: Vec<FieldValuePair>,
    /// Unix timestamp in milliseconds (parsed from entry ID)
    pub timestamp_ms: u64,
}

/// A field-value pair in a Stream entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FieldValuePair {
    pub field: String,
    pub value: String,
}

/// A Stream consumer group (from XINFO GROUPS)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StreamGroup {
    /// Group name
    pub name: String,
    /// Number of consumers in the group
    pub consumers: u64,
    /// Number of pending messages
    pub pending: u64,
    /// Last delivered entry ID
    pub last_delivered_id: String,
}

/// A pending entry summary (from XPENDING)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PendingEntry {
    /// Consumer name
    pub consumer_name: String,
    /// Number of pending messages for this consumer
    pub pending_count: u64,
    /// Idle time in milliseconds
    pub idle_ms: u64,
    /// Last delivered entry ID
    pub last_delivered_id: String,
}

/// A chunk of bitmap data (Base64-encoded raw bytes)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BitmapChunk {
    /// Base64-encoded raw byte data
    pub data_base64: String,
    /// Starting byte offset
    pub start_byte: u64,
    /// Length of the raw byte data
    pub byte_length: u64,
}

/// HyperLogLog statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HllStats {
    /// Estimated cardinality
    pub estimated_cardinality: u64,
    /// Encoding method (e.g., "dense", "sparse")
    pub encoding: String,
}

/// Stream metadata (from XINFO STREAM)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StreamInfo {
    /// Stream length (number of entries)
    pub length: u64,
    /// Number of radix tree nodes
    pub radix_nodes: u64,
    /// Number of radix tree levels
    pub radix_levels: u64,
    /// Last generated entry ID
    pub last_id: String,
    /// Max entries (from MAXLEN), 0 if not set
    pub max_length: u64,
    /// Number of consumer groups
    pub groups: u64,
    /// First entry ID in the stream
    pub first_entry_id: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    // ... existing code ...

    // ===== StreamEntry tests =====

    #[test]
    fn test_stream_entry_serialize() {
        let entry = StreamEntry {
            id: "1619123456789-0".to_string(),
            fields: vec![
                FieldValuePair { field: "temp".to_string(), value: "22.5".to_string() },
            ],
            timestamp_ms: 1619123456789,
        };
        let json = serde_json::to_string(&entry).unwrap();
        assert!(json.contains("\"id\":\"1619123456789-0\""));
        assert!(json.contains("\"field\":\"temp\""));
    }

    #[test]
    fn test_stream_entry_deserialize() {
        let json = r#"{"id":"1-0","fields":[{"field":"k","value":"v"}],"timestamp_ms":1}"#;
        let entry: StreamEntry = serde_json::from_str(json).unwrap();
        assert_eq!(entry.id, "1-0");
        assert_eq!(entry.fields.len(), 1);
        assert_eq!(entry.fields[0].field, "k");
    }

    // ===== StreamGroup tests =====

    #[test]
    fn test_stream_group_roundtrip() {
        let group = StreamGroup {
            name: "mygroup".to_string(),
            consumers: 3,
            pending: 10,
            last_delivered_id: "1619123456789-0".to_string(),
        };
        let json = serde_json::to_string(&group).unwrap();
        let de: StreamGroup = serde_json::from_str(&json).unwrap();
        assert_eq!(de.name, "mygroup");
        assert_eq!(de.consumers, 3);
        assert_eq!(de.pending, 10);
    }

    // ===== PendingEntry tests =====

    #[test]
    fn test_pending_entry_roundtrip() {
        let entry = PendingEntry {
            consumer_name: "worker-1".to_string(),
            pending_count: 5,
            idle_ms: 120000,
            last_delivered_id: "1619123456789-0".to_string(),
        };
        let json = serde_json::to_string(&entry).unwrap();
        let de: PendingEntry = serde_json::from_str(&json).unwrap();
        assert_eq!(de.consumer_name, "worker-1");
        assert_eq!(de.pending_count, 5);
    }

    // ===== BitmapChunk tests =====

    #[test]
    fn test_bitmap_chunk_roundtrip() {
        let chunk = BitmapChunk {
            data_base64: "AQID".to_string(),
            start_byte: 0,
            byte_length: 3,
        };
        let json = serde_json::to_string(&chunk).unwrap();
        let de: BitmapChunk = serde_json::from_str(&json).unwrap();
        assert_eq!(de.data_base64, "AQID");
        assert_eq!(de.start_byte, 0);
        assert_eq!(de.byte_length, 3);
    }

    // ===== HllStats tests =====

    #[test]
    fn test_hll_stats_roundtrip() {
        let stats = HllStats {
            estimated_cardinality: 12345,
            encoding: "dense".to_string(),
        };
        let json = serde_json::to_string(&stats).unwrap();
        let de: HllStats = serde_json::from_str(&json).unwrap();
        assert_eq!(de.estimated_cardinality, 12345);
        assert_eq!(de.encoding, "dense");
    }
}
