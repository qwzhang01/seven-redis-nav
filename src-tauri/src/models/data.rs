use serde::{Deserialize, Serialize};

/// Result of a bulk operation (delete / ttl), shared by bulk commands
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BulkResult {
    /// Number of keys processed successfully
    pub success: u64,
    /// List of keys that failed
    pub failed: Vec<String>,
}

/// Redis key type
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum KeyType {
    String,
    Hash,
    List,
    Set,
    ZSet,
    Stream,
    Unknown,
}

impl From<&str> for KeyType {
    fn from(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "string" => KeyType::String,
            "hash" => KeyType::Hash,
            "list" => KeyType::List,
            "set" => KeyType::Set,
            "zset" => KeyType::ZSet,
            "stream" => KeyType::Stream,
            _ => KeyType::Unknown,
        }
    }
}

/// Key metadata (from SCAN result)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyMeta {
    pub key: String,
    pub key_type: KeyType,
    pub ttl: i64,       // -1 = no expiry, -2 = not exists
    pub size: u64,      // MEMORY USAGE in bytes
    pub encoding: String,
}

/// SCAN page result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScanPage {
    pub keys: Vec<KeyMeta>,
    pub cursor: u64,    // 0 = scan complete
    pub total_scanned: u64,
}

/// Redis value variants
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum RedisValue {
    String { value: String },
    Hash { fields: Vec<(String, String)> },
    List { items: Vec<String> },
    Set { members: Vec<String> },
    ZSet { members: Vec<(f64, String)> },
    Stream { entries: Vec<serde_json::Value> },
}

/// Full key detail (metadata + value)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyDetail {
    pub key: String,
    pub key_type: KeyType,
    pub ttl: i64,
    pub size: u64,
    pub encoding: String,
    pub length: u64,    // element count
    pub db: u8,
    pub value: RedisValue,
}

#[cfg(test)]
mod tests {
    use super::*;

    // ===== KeyType::from tests =====

    #[test]
    fn test_key_type_from_string() {
        assert_eq!(KeyType::from("string"), KeyType::String);
        assert_eq!(KeyType::from("STRING"), KeyType::String);
        assert_eq!(KeyType::from("String"), KeyType::String);
    }

    #[test]
    fn test_key_type_from_hash() {
        assert_eq!(KeyType::from("hash"), KeyType::Hash);
        assert_eq!(KeyType::from("HASH"), KeyType::Hash);
    }

    #[test]
    fn test_key_type_from_list() {
        assert_eq!(KeyType::from("list"), KeyType::List);
        assert_eq!(KeyType::from("LIST"), KeyType::List);
    }

    #[test]
    fn test_key_type_from_set() {
        assert_eq!(KeyType::from("set"), KeyType::Set);
        assert_eq!(KeyType::from("SET"), KeyType::Set);
    }

    #[test]
    fn test_key_type_from_zset() {
        assert_eq!(KeyType::from("zset"), KeyType::ZSet);
        assert_eq!(KeyType::from("ZSET"), KeyType::ZSet);
    }

    #[test]
    fn test_key_type_from_stream() {
        assert_eq!(KeyType::from("stream"), KeyType::Stream);
        assert_eq!(KeyType::from("STREAM"), KeyType::Stream);
    }

    #[test]
    fn test_key_type_from_unknown() {
        assert_eq!(KeyType::from("none"), KeyType::Unknown);
        assert_eq!(KeyType::from(""), KeyType::Unknown);
        assert_eq!(KeyType::from("foobar"), KeyType::Unknown);
    }

    // ===== RedisValue serialization =====

    #[test]
    fn test_redis_value_string_serialize() {
        let val = RedisValue::String { value: "hello".to_string() };
        let json = serde_json::to_string(&val).unwrap();
        assert!(json.contains("\"type\":\"string\""));
        assert!(json.contains("\"value\":\"hello\""));
    }

    #[test]
    fn test_redis_value_hash_serialize() {
        let val = RedisValue::Hash {
            fields: vec![("name".to_string(), "test".to_string())],
        };
        let json = serde_json::to_string(&val).unwrap();
        assert!(json.contains("\"type\":\"hash\""));
        assert!(json.contains("\"fields\""));
    }

    #[test]
    fn test_redis_value_list_serialize() {
        let val = RedisValue::List {
            items: vec!["a".to_string(), "b".to_string()],
        };
        let json = serde_json::to_string(&val).unwrap();
        assert!(json.contains("\"type\":\"list\""));
        assert!(json.contains("\"items\""));
    }

    #[test]
    fn test_redis_value_set_serialize() {
        let val = RedisValue::Set {
            members: vec!["x".to_string(), "y".to_string()],
        };
        let json = serde_json::to_string(&val).unwrap();
        assert!(json.contains("\"type\":\"set\""));
        assert!(json.contains("\"members\""));
    }

    #[test]
    fn test_redis_value_zset_serialize() {
        let val = RedisValue::ZSet {
            members: vec![(1.5, "member1".to_string())],
        };
        let json = serde_json::to_string(&val).unwrap();
        assert!(json.contains("\"type\":\"zset\""));
        assert!(json.contains("1.5"));
        assert!(json.contains("member1"));
    }

    // ===== KeyDetail =====

    #[test]
    fn test_key_detail_serialize() {
        let detail = KeyDetail {
            key: "test:key".to_string(),
            key_type: KeyType::String,
            ttl: -1,
            size: 128,
            encoding: "embstr".to_string(),
            length: 1,
            db: 0,
            value: RedisValue::String { value: "hello".to_string() },
        };
        let json = serde_json::to_string(&detail).unwrap();
        assert!(json.contains("\"key\":\"test:key\""));
        assert!(json.contains("\"key_type\":\"string\""));
        assert!(json.contains("\"ttl\":-1"));
        assert!(json.contains("\"encoding\":\"embstr\""));
    }

    // ===== ScanPage =====

    #[test]
    fn test_scan_page_serialize() {
        let page = ScanPage {
            keys: vec![KeyMeta {
                key: "user:1".to_string(),
                key_type: KeyType::Hash,
                ttl: 3600,
                size: 256,
                encoding: "ziplist".to_string(),
            }],
            cursor: 42,
            total_scanned: 1,
        };
        let json = serde_json::to_string(&page).unwrap();
        assert!(json.contains("\"cursor\":42"));
        assert!(json.contains("\"user:1\""));
    }
}
