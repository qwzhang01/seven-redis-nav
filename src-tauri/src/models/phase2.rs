use serde::{Deserialize, Serialize};

/// A single Pub/Sub message received from Redis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PubSubMessage {
    /// Channel name the message was received on
    pub channel: String,
    /// Pattern that matched (if subscribed via PSUBSCRIBE)
    pub pattern: Option<String>,
    /// Message body
    pub message: String,
    /// Timestamp (ISO 8601) when the message was received
    pub timestamp: String,
}

/// A single MONITOR command entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MonitorCommand {
    /// Raw timestamp from Redis MONITOR output
    pub timestamp: f64,
    /// Client address (IP:port)
    pub client: String,
    /// Database number
    pub db: u8,
    /// Full command string (e.g., "SET foo bar")
    pub command: String,
    /// Command arguments split
    pub args: Vec<String>,
}

/// A single SLOWLOG entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SlowlogEntry {
    /// Unique slowlog entry ID
    pub id: u64,
    /// Unix timestamp when the command was logged
    pub timestamp: i64,
    /// Execution duration in microseconds
    pub duration_us: u64,
    /// The command and its arguments
    pub command: Vec<String>,
    /// Client address (IP:port), may be empty on older Redis versions
    pub client_addr: String,
    /// Client name (if set via CLIENT SETNAME)
    pub client_name: String,
}

/// A single metrics snapshot from periodic INFO sampling
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricsSnapshot {
    /// Instantaneous operations per second
    pub ops_per_sec: f64,
    /// Used memory in bytes
    pub used_memory_bytes: u64,
    /// Number of connected clients
    pub connected_clients: u64,
    /// Keyspace hits
    pub keyspace_hits: u64,
    /// Keyspace misses
    pub keyspace_misses: u64,
    /// Server info summary
    pub server_info: MetricsServerInfo,
    /// Keyspace info per database
    pub keyspace: Vec<DbKeyspace>,
    /// Client list entries (up to 10)
    pub clients: Vec<ClientEntry>,
    /// Timestamp (ISO 8601) when this snapshot was taken
    pub timestamp: String,
}

/// Server info relevant to the metrics dashboard
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricsServerInfo {
    /// Redis version string
    pub redis_version: String,
    /// Server OS
    pub os: String,
    /// Process ID
    pub process_id: u64,
    /// TCP port
    pub tcp_port: u64,
    /// Uptime in seconds
    pub uptime_secs: u64,
    /// Role: "master" or "slave"
    pub role: String,
    /// Number of connected slaves (master only)
    pub connected_slaves: u64,
    /// AOF enabled
    pub aof_enabled: bool,
    /// Last RDB save time (Unix timestamp)
    pub last_rdb_save_ts: i64,
}

/// Keyspace info for a single database
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DbKeyspace {
    /// Database index (e.g., 0 for db0)
    pub db: u64,
    /// Total number of keys
    pub keys: u64,
    /// Number of keys with TTL set
    pub expires: u64,
    /// Average TTL in seconds (0 if no expiring keys)
    pub avg_ttl_secs: f64,
}

/// A single entry from CLIENT LIST
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientEntry {
    /// Client ID
    pub id: u64,
    /// Client address (IP:port)
    pub addr: String,
    /// Client name (if set)
    pub name: String,
    /// Last command executed
    pub cmd: String,
    /// Connection age in seconds
    pub age_secs: u64,
    /// Database index
    pub db: u64,
}

/// A single Redis CONFIG parameter
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfigItem {
    /// Parameter name
    pub key: String,
    /// Parameter value
    pub value: String,
}

/// Redis server INFO summary
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerInfo {
    /// Redis version string
    pub redis_version: String,
    /// Uptime in seconds
    pub uptime_secs: u64,
    /// Number of connected clients
    pub connected_clients: u64,
    /// Used memory in bytes
    pub used_memory: u64,
    /// Max memory setting in bytes (0 = unlimited)
    pub max_memory: u64,
    /// Keyspace hit rate (hits / (hits + misses)), 0.0 if no data
    pub hit_rate: f64,
    /// Total number of keys across all databases
    pub total_keys: u64,
    /// Instantaneous operations per second
    pub ops_per_sec: u64,
}

#[cfg(test)]
mod tests {
    use super::*;

    // ===== PubSubMessage tests =====

    #[test]
    fn test_pubsub_message_serialize() {
        let msg = PubSubMessage {
            channel: "news".to_string(),
            pattern: Some("news.*".to_string()),
            message: "hello world".to_string(),
            timestamp: "2024-01-01T00:00:00Z".to_string(),
        };
        let json = serde_json::to_string(&msg).unwrap();
        assert!(json.contains("\"channel\":\"news\""));
        assert!(json.contains("\"pattern\":\"news.*\""));
        assert!(json.contains("\"message\":\"hello world\""));
    }

    #[test]
    fn test_pubsub_message_deserialize() {
        let json = r#"{"channel":"test","pattern":null,"message":"data","timestamp":"2024-01-01T00:00:00Z"}"#;
        let msg: PubSubMessage = serde_json::from_str(json).unwrap();
        assert_eq!(msg.channel, "test");
        assert!(msg.pattern.is_none());
        assert_eq!(msg.message, "data");
    }

    #[test]
    fn test_pubsub_message_clone() {
        let msg = PubSubMessage {
            channel: "ch".to_string(),
            pattern: None,
            message: "msg".to_string(),
            timestamp: "ts".to_string(),
        };
        let cloned = msg.clone();
        assert_eq!(cloned.channel, msg.channel);
        assert_eq!(cloned.message, msg.message);
    }

    // ===== MonitorCommand tests =====

    #[test]
    fn test_monitor_command_serialize() {
        let cmd = MonitorCommand {
            timestamp: 1619123456.789,
            client: "127.0.0.1:6379".to_string(),
            db: 0,
            command: "SET".to_string(),
            args: vec!["key".to_string(), "value".to_string()],
        };
        let json = serde_json::to_string(&cmd).unwrap();
        assert!(json.contains("\"command\":\"SET\""));
        assert!(json.contains("\"db\":0"));
        assert!(json.contains("\"args\":[\"key\",\"value\"]"));
    }

    #[test]
    fn test_monitor_command_deserialize() {
        let json = r#"{"timestamp":1.0,"client":"c","db":3,"command":"GET","args":["foo"]}"#;
        let cmd: MonitorCommand = serde_json::from_str(json).unwrap();
        assert_eq!(cmd.db, 3);
        assert_eq!(cmd.command, "GET");
        assert_eq!(cmd.args, vec!["foo"]);
    }

    #[test]
    fn test_monitor_command_empty_args() {
        let cmd = MonitorCommand {
            timestamp: 0.0,
            client: String::new(),
            db: 0,
            command: "PING".to_string(),
            args: vec![],
        };
        let json = serde_json::to_string(&cmd).unwrap();
        assert!(json.contains("\"args\":[]"));
    }

    // ===== SlowlogEntry tests =====

    #[test]
    fn test_slowlog_entry_serialize() {
        let entry = SlowlogEntry {
            id: 1,
            timestamp: 1619123456,
            duration_us: 50000,
            command: vec!["KEYS".to_string(), "*".to_string()],
            client_addr: "10.0.0.1:1234".to_string(),
            client_name: "worker".to_string(),
        };
        let json = serde_json::to_string(&entry).unwrap();
        assert!(json.contains("\"duration_us\":50000"));
        assert!(json.contains("\"client_name\":\"worker\""));
    }

    #[test]
    fn test_slowlog_entry_deserialize() {
        let json = r#"{"id":42,"timestamp":1000,"duration_us":999,"command":["SET","k","v"],"client_addr":"","client_name":""}"#;
        let entry: SlowlogEntry = serde_json::from_str(json).unwrap();
        assert_eq!(entry.id, 42);
        assert_eq!(entry.duration_us, 999);
        assert_eq!(entry.command.len(), 3);
    }

    // ===== ServerConfigItem tests =====

    #[test]
    fn test_server_config_item_roundtrip() {
        let item = ServerConfigItem {
            key: "maxmemory-policy".to_string(),
            value: "allkeys-lru".to_string(),
        };
        let json = serde_json::to_string(&item).unwrap();
        let deserialized: ServerConfigItem = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized.key, "maxmemory-policy");
        assert_eq!(deserialized.value, "allkeys-lru");
    }

    // ===== ServerInfo tests =====

    #[test]
    fn test_server_info_roundtrip() {
        let info = ServerInfo {
            redis_version: "7.2.0".to_string(),
            uptime_secs: 86400,
            connected_clients: 10,
            used_memory: 1048576,
            max_memory: 0,
            hit_rate: 0.95,
            total_keys: 500,
            ops_per_sec: 1000,
        };
        let json = serde_json::to_string(&info).unwrap();
        let deserialized: ServerInfo = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized.redis_version, "7.2.0");
        assert_eq!(deserialized.uptime_secs, 86400);
        assert_eq!(deserialized.max_memory, 0);
        assert!((deserialized.hit_rate - 0.95).abs() < 0.001);
    }

    #[test]
    fn test_server_info_default_values() {
        let info = ServerInfo {
            redis_version: String::new(),
            uptime_secs: 0,
            connected_clients: 0,
            used_memory: 0,
            max_memory: 0,
            hit_rate: 0.0,
            total_keys: 0,
            ops_per_sec: 0,
        };
        let json = serde_json::to_string(&info).unwrap();
        assert!(json.contains("\"hit_rate\":0.0"));
    }
}
