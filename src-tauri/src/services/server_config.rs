use crate::models::phase2::{SlowlogEntry, ServerConfigItem, ServerInfo};
use crate::services::connection_manager::SharedConnectionManager;
use crate::error::{IpcError, IpcResult};

/// Get slowlog entries
pub async fn slowlog_get(mgr: &SharedConnectionManager, conn_id: &str, count: Option<u32>) -> IpcResult<Vec<SlowlogEntry>> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let count = count.unwrap_or(128);
    let result: Vec<redis::Value> = redis::cmd("SLOWLOG")
        .arg("GET")
        .arg(count)
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    let entries = parse_slowlog_entries(&result);
    Ok(entries)
}

/// Reset slowlog
pub async fn slowlog_reset(mgr: &SharedConnectionManager, conn_id: &str) -> IpcResult<()> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    redis::cmd("SLOWLOG")
        .arg("RESET")
        .query_async::<()>(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(())
}

/// Get all config parameters
pub async fn config_get_all(mgr: &SharedConnectionManager, conn_id: &str) -> IpcResult<Vec<ServerConfigItem>> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let result: Vec<String> = redis::cmd("CONFIG")
        .arg("GET")
        .arg("*")
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    // Result is a flat list of [key, value, key, value, ...]
    let items: Vec<ServerConfigItem> = result
        .chunks(2)
        .filter_map(|chunk| {
            if chunk.len() == 2 {
                Some(ServerConfigItem {
                    key: chunk[0].clone(),
                    value: chunk[1].clone(),
                })
            } else {
                None
            }
        })
        .collect();

    Ok(items)
}

/// Set a config parameter
pub async fn config_set(mgr: &SharedConnectionManager, conn_id: &str, key: &str, value: &str) -> IpcResult<()> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    redis::cmd("CONFIG")
        .arg("SET")
        .arg(key)
        .arg(value)
        .query_async::<()>(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(())
}

/// Get server INFO
pub async fn server_info(mgr: &SharedConnectionManager, conn_id: &str, section: Option<&str>) -> IpcResult<ServerInfo> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let mut cmd = redis::cmd("INFO");
    if let Some(sec) = section {
        cmd.arg(sec);
    }

    let info_str: String = cmd
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(parse_server_info(&info_str))
}

/// CONFIG REWRITE — persist current config to the configuration file
pub async fn config_rewrite(mgr: &SharedConnectionManager, conn_id: &str) -> IpcResult<()> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    redis::cmd("CONFIG")
        .arg("REWRITE")
        .query_async::<()>(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(())
}

/// CONFIG RESETSTAT — reset statistics counters
pub async fn config_resetstat(mgr: &SharedConnectionManager, conn_id: &str) -> IpcResult<()> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    redis::cmd("CONFIG")
        .arg("RESETSTAT")
        .query_async::<()>(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(())
}

/// Get notify-keyspace-events configuration value
pub async fn config_get_notify_keyspace_events(mgr: &SharedConnectionManager, conn_id: &str) -> IpcResult<String> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let result: Vec<String> = redis::cmd("CONFIG")
        .arg("GET")
        .arg("notify-keyspace-events")
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    // Result is [key, value]
    if result.len() >= 2 {
        Ok(result[1].clone())
    } else {
        Ok(String::new())
    }
}

/// Parse SLOWLOG GET result (pub for testing)
pub(crate) fn parse_slowlog_entries(values: &[redis::Value]) -> Vec<SlowlogEntry> {
    let mut entries = Vec::new();

    for value in values {
        if let redis::Value::Array(ref fields) = value {
            if fields.len() >= 4 {
                let id = extract_int(&fields[0]) as u64;
                let timestamp = extract_int(&fields[1]);
                let duration_us = extract_int(&fields[2]) as u64;

                let command = if let redis::Value::Array(ref cmd_parts) = fields[3] {
                    cmd_parts.iter().map(|v| extract_string(v)).collect()
                } else {
                    vec![extract_string(&fields[3])]
                };

                let client_addr = if fields.len() > 4 {
                    extract_string(&fields[4])
                } else {
                    String::new()
                };

                let client_name = if fields.len() > 5 {
                    extract_string(&fields[5])
                } else {
                    String::new()
                };

                entries.push(SlowlogEntry {
                    id,
                    timestamp,
                    duration_us,
                    command,
                    client_addr,
                    client_name,
                });
            }
        }
    }

    entries
}

/// Parse INFO output into ServerInfo (pub for testing)
pub(crate) fn parse_server_info(info: &str) -> ServerInfo {
    let mut redis_version = String::new();
    let mut uptime_secs: u64 = 0;
    let mut connected_clients: u64 = 0;
    let mut used_memory: u64 = 0;
    let mut max_memory: u64 = 0;
    let mut keyspace_hits: u64 = 0;
    let mut keyspace_misses: u64 = 0;
    let mut total_keys: u64 = 0;
    let mut ops_per_sec: u64 = 0;

    for line in info.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        if let Some((key, value)) = line.split_once(':') {
            match key {
                "redis_version" => redis_version = value.to_string(),
                "uptime_in_seconds" => uptime_secs = value.parse().unwrap_or(0),
                "connected_clients" => connected_clients = value.parse().unwrap_or(0),
                "used_memory" => used_memory = value.parse().unwrap_or(0),
                "maxmemory" => max_memory = value.parse().unwrap_or(0),
                "keyspace_hits" => keyspace_hits = value.parse().unwrap_or(0),
                "keyspace_misses" => keyspace_misses = value.parse().unwrap_or(0),
                "instantaneous_ops_per_sec" => ops_per_sec = value.parse().unwrap_or(0),
                k if k.starts_with("db") => {
                    // Parse db keys count
                    if let Some(keys_part) = value.split(',').find(|s| s.starts_with("keys=")) {
                        total_keys += keys_part.trim_start_matches("keys=").parse::<u64>().unwrap_or(0);
                    }
                }
                _ => {}
            }
        }
    }

    let hit_rate = if keyspace_hits + keyspace_misses > 0 {
        keyspace_hits as f64 / (keyspace_hits + keyspace_misses) as f64
    } else {
        0.0
    };

    ServerInfo {
        redis_version,
        uptime_secs,
        connected_clients,
        used_memory,
        max_memory,
        hit_rate,
        total_keys,
        ops_per_sec,
    }
}

pub(crate) fn extract_int(value: &redis::Value) -> i64 {
    match value {
        redis::Value::Int(i) => *i,
        redis::Value::BulkString(bytes) => {
            String::from_utf8_lossy(bytes).parse().unwrap_or(0)
        }
        _ => 0,
    }
}

pub(crate) fn extract_string(value: &redis::Value) -> String {
    match value {
        redis::Value::BulkString(bytes) => String::from_utf8_lossy(bytes).to_string(),
        redis::Value::SimpleString(s) => s.clone(),
        redis::Value::Int(i) => i.to_string(),
        _ => String::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ===== extract_int tests =====

    #[test]
    fn test_extract_int_from_int() {
        let val = redis::Value::Int(42);
        assert_eq!(extract_int(&val), 42);
    }

    #[test]
    fn test_extract_int_from_bulk_string() {
        let val = redis::Value::BulkString(b"12345".to_vec());
        assert_eq!(extract_int(&val), 12345);
    }

    #[test]
    fn test_extract_int_from_invalid_bulk_string() {
        let val = redis::Value::BulkString(b"not_a_number".to_vec());
        assert_eq!(extract_int(&val), 0);
    }

    #[test]
    fn test_extract_int_from_nil() {
        let val = redis::Value::Nil;
        assert_eq!(extract_int(&val), 0);
    }

    #[test]
    fn test_extract_int_negative() {
        let val = redis::Value::Int(-100);
        assert_eq!(extract_int(&val), -100);
    }

    // ===== extract_string tests =====

    #[test]
    fn test_extract_string_from_bulk_string() {
        let val = redis::Value::BulkString(b"hello".to_vec());
        assert_eq!(extract_string(&val), "hello");
    }

    #[test]
    fn test_extract_string_from_simple_string() {
        let val = redis::Value::SimpleString("OK".to_string());
        assert_eq!(extract_string(&val), "OK");
    }

    #[test]
    fn test_extract_string_from_int() {
        let val = redis::Value::Int(42);
        assert_eq!(extract_string(&val), "42");
    }

    #[test]
    fn test_extract_string_from_nil() {
        let val = redis::Value::Nil;
        assert_eq!(extract_string(&val), "");
    }

    #[test]
    fn test_extract_string_from_empty_bulk() {
        let val = redis::Value::BulkString(b"".to_vec());
        assert_eq!(extract_string(&val), "");
    }

    // ===== parse_server_info tests =====

    #[test]
    fn test_parse_server_info_full() {
        let info = "\
# Server\n\
redis_version:7.0.11\n\
uptime_in_seconds:86400\n\
\n\
# Clients\n\
connected_clients:10\n\
\n\
# Memory\n\
used_memory:1048576\n\
maxmemory:2097152\n\
\n\
# Stats\n\
keyspace_hits:1000\n\
keyspace_misses:200\n\
instantaneous_ops_per_sec:500\n\
\n\
# Keyspace\n\
db0:keys=100,expires=10,avg_ttl=5000\n\
db1:keys=50,expires=5,avg_ttl=3000\n";

        let info = parse_server_info(info);
        assert_eq!(info.redis_version, "7.0.11");
        assert_eq!(info.uptime_secs, 86400);
        assert_eq!(info.connected_clients, 10);
        assert_eq!(info.used_memory, 1048576);
        assert_eq!(info.max_memory, 2097152);
        assert!((info.hit_rate - 0.8333).abs() < 0.001); // 1000 / 1200
        assert_eq!(info.total_keys, 150); // 100 + 50
        assert_eq!(info.ops_per_sec, 500);
    }

    #[test]
    fn test_parse_server_info_empty() {
        let info = parse_server_info("");
        assert_eq!(info.redis_version, "");
        assert_eq!(info.uptime_secs, 0);
        assert_eq!(info.connected_clients, 0);
        assert_eq!(info.hit_rate, 0.0);
        assert_eq!(info.total_keys, 0);
    }

    #[test]
    fn test_parse_server_info_no_keyspace() {
        let info = "\
redis_version:6.2.6\n\
uptime_in_seconds:3600\n\
connected_clients:1\n\
used_memory:524288\n\
maxmemory:0\n";

        let info = parse_server_info(info);
        assert_eq!(info.redis_version, "6.2.6");
        assert_eq!(info.max_memory, 0);
        assert_eq!(info.total_keys, 0);
    }

    #[test]
    fn test_parse_server_info_zero_hits_misses() {
        let info = "\
keyspace_hits:0\n\
keyspace_misses:0\n";

        let info = parse_server_info(info);
        assert_eq!(info.hit_rate, 0.0);
    }

    #[test]
    fn test_parse_server_info_only_hits() {
        let info = "\
keyspace_hits:500\n\
keyspace_misses:0\n";

        let info = parse_server_info(info);
        assert_eq!(info.hit_rate, 1.0);
    }

    #[test]
    fn test_parse_server_info_comments_and_blanks() {
        let info = "\
# Server\n\
\n\
# This is a comment\n\
redis_version:7.2.0\n\
\n\
# Another section\n";

        let info = parse_server_info(info);
        assert_eq!(info.redis_version, "7.2.0");
    }

    // ===== parse_slowlog_entries tests =====

    #[test]
    fn test_parse_slowlog_entries_empty() {
        let entries = parse_slowlog_entries(&[]);
        assert!(entries.is_empty());
    }

    #[test]
    fn test_parse_slowlog_entries_single() {
        // Simulate: [id=1, timestamp=1619123456, duration=10000, ["SET", "key", "value"], "127.0.0.1:6379", ""]
        let entry = redis::Value::Array(vec![
            redis::Value::Int(1),
            redis::Value::Int(1619123456),
            redis::Value::Int(10000),
            redis::Value::Array(vec![
                redis::Value::BulkString(b"SET".to_vec()),
                redis::Value::BulkString(b"key".to_vec()),
                redis::Value::BulkString(b"value".to_vec()),
            ]),
            redis::Value::BulkString(b"127.0.0.1:6379".to_vec()),
            redis::Value::BulkString(b"my-client".to_vec()),
        ]);

        let entries = parse_slowlog_entries(&[entry]);
        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0].id, 1);
        assert_eq!(entries[0].timestamp, 1619123456);
        assert_eq!(entries[0].duration_us, 10000);
        assert_eq!(entries[0].command, vec!["SET", "key", "value"]);
        assert_eq!(entries[0].client_addr, "127.0.0.1:6379");
        assert_eq!(entries[0].client_name, "my-client");
    }

    #[test]
    fn test_parse_slowlog_entries_multiple() {
        let entry1 = redis::Value::Array(vec![
            redis::Value::Int(2),
            redis::Value::Int(1619123457),
            redis::Value::Int(5000),
            redis::Value::Array(vec![
                redis::Value::BulkString(b"GET".to_vec()),
                redis::Value::BulkString(b"foo".to_vec()),
            ]),
            redis::Value::BulkString(b"10.0.0.1:1234".to_vec()),
            redis::Value::BulkString(b"".to_vec()),
        ]);

        let entry2 = redis::Value::Array(vec![
            redis::Value::Int(1),
            redis::Value::Int(1619123456),
            redis::Value::Int(200000),
            redis::Value::Array(vec![
                redis::Value::BulkString(b"KEYS".to_vec()),
                redis::Value::BulkString(b"*".to_vec()),
            ]),
            redis::Value::BulkString(b"10.0.0.2:5678".to_vec()),
            redis::Value::BulkString(b"worker".to_vec()),
        ]);

        let entries = parse_slowlog_entries(&[entry1, entry2]);
        assert_eq!(entries.len(), 2);
        assert_eq!(entries[0].id, 2);
        assert_eq!(entries[0].duration_us, 5000);
        assert_eq!(entries[1].id, 1);
        assert_eq!(entries[1].duration_us, 200000);
    }

    #[test]
    fn test_parse_slowlog_entries_minimal_fields() {
        // Only 4 fields (no client_addr, no client_name) - older Redis
        let entry = redis::Value::Array(vec![
            redis::Value::Int(0),
            redis::Value::Int(1619123456),
            redis::Value::Int(500),
            redis::Value::Array(vec![
                redis::Value::BulkString(b"PING".to_vec()),
            ]),
        ]);

        let entries = parse_slowlog_entries(&[entry]);
        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0].id, 0);
        assert_eq!(entries[0].command, vec!["PING"]);
        assert_eq!(entries[0].client_addr, "");
        assert_eq!(entries[0].client_name, "");
    }

    #[test]
    fn test_parse_slowlog_entries_skips_malformed() {
        // Too few fields
        let bad_entry = redis::Value::Array(vec![
            redis::Value::Int(0),
            redis::Value::Int(1619123456),
        ]);

        let good_entry = redis::Value::Array(vec![
            redis::Value::Int(1),
            redis::Value::Int(1619123456),
            redis::Value::Int(100),
            redis::Value::Array(vec![
                redis::Value::BulkString(b"SET".to_vec()),
                redis::Value::BulkString(b"k".to_vec()),
                redis::Value::BulkString(b"v".to_vec()),
            ]),
        ]);

        let entries = parse_slowlog_entries(&[bad_entry, good_entry]);
        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0].id, 1);
    }

    #[test]
    fn test_parse_slowlog_entries_non_array_skipped() {
        let entries = parse_slowlog_entries(&[redis::Value::Nil, redis::Value::Int(42)]);
        assert!(entries.is_empty());
    }

    // ===== Phase2 model serialization tests =====

    #[test]
    fn test_server_config_item_serialize() {
        let item = ServerConfigItem {
            key: "maxmemory".to_string(),
            value: "2gb".to_string(),
        };
        let json = serde_json::to_string(&item).unwrap();
        assert!(json.contains("maxmemory"));
        assert!(json.contains("2gb"));
    }

    #[test]
    fn test_server_info_serialize() {
        let info = ServerInfo {
            redis_version: "7.0.0".to_string(),
            uptime_secs: 3600,
            connected_clients: 5,
            used_memory: 1024,
            max_memory: 2048,
            hit_rate: 0.95,
            total_keys: 100,
            ops_per_sec: 50,
        };
        let json = serde_json::to_string(&info).unwrap();
        assert!(json.contains("7.0.0"));
        assert!(json.contains("3600"));
    }

    #[test]
    fn test_slowlog_entry_serialize() {
        let entry = SlowlogEntry {
            id: 42,
            timestamp: 1619123456,
            duration_us: 15000,
            command: vec!["SET".to_string(), "key".to_string(), "value".to_string()],
            client_addr: "127.0.0.1:6379".to_string(),
            client_name: "test".to_string(),
        };
        let json = serde_json::to_string(&entry).unwrap();
        assert!(json.contains("42"));
        assert!(json.contains("15000"));
        assert!(json.contains("SET"));
    }
}
