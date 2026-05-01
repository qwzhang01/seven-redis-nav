use crate::error::{IpcError, IpcResult};
use crate::models::phase3::{StreamEntry, StreamGroup, PendingEntry, FieldValuePair, StreamInfo};
use crate::services::connection_manager::SharedConnectionManager;
use crate::services::server_config::{extract_int, extract_string};

/// XRANGE — read entries from a stream in ascending order
pub async fn stream_range(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    key: &str,
    start: &str,
    end: &str,
    count: Option<u64>,
) -> IpcResult<Vec<StreamEntry>> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let count = count.unwrap_or(100);
    let result: Vec<(String, Vec<(String, String)>)> = redis::cmd("XRANGE")
        .arg(key)
        .arg(start)
        .arg(end)
        .arg("COUNT")
        .arg(count)
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(result.into_iter().map(parse_stream_entry).collect())
}

/// XREVRANGE — read entries from a stream in descending order
pub async fn stream_rev_range(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    key: &str,
    start: &str,
    end: &str,
    count: Option<u64>,
) -> IpcResult<Vec<StreamEntry>> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let count = count.unwrap_or(100);
    let result: Vec<(String, Vec<(String, String)>)> = redis::cmd("XREVRANGE")
        .arg(key)
        .arg(start)
        .arg(end)
        .arg("COUNT")
        .arg(count)
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(result.into_iter().map(parse_stream_entry).collect())
}

/// XADD — add an entry to a stream
pub async fn stream_add(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    key: &str,
    fields: Vec<(String, String)>,
    id: Option<&str>,
    maxlen: Option<u64>,
    approx: bool,
) -> IpcResult<String> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let mut cmd = redis::cmd("XADD");
    cmd.arg(key);

    if let Some(maxlen) = maxlen {
        if approx {
            cmd.arg("MAXLEN").arg("~").arg(maxlen);
        } else {
            cmd.arg("MAXLEN").arg(maxlen);
        }
    }

    let entry_id = id.unwrap_or("*");
    cmd.arg(entry_id);

    for (field, value) in &fields {
        cmd.arg(field).arg(value);
    }

    let result: String = cmd
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(result)
}

/// XDEL — delete entries from a stream
pub async fn stream_del(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    key: &str,
    ids: &[String],
) -> IpcResult<u64> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let mut cmd = redis::cmd("XDEL");
    cmd.arg(key);
    for id in ids {
        cmd.arg(id);
    }

    let deleted: u64 = cmd
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(deleted)
}

/// XINFO STREAM — get stream metadata
pub async fn stream_info(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    key: &str,
) -> IpcResult<StreamInfo> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let result: Vec<redis::Value> = redis::cmd("XINFO")
        .arg("STREAM")
        .arg(key)
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(parse_stream_info(&result))
}

/// XINFO GROUPS — get consumer groups of a stream
pub async fn stream_groups(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    key: &str,
) -> IpcResult<Vec<StreamGroup>> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let result: Vec<redis::Value> = redis::cmd("XINFO")
        .arg("GROUPS")
        .arg(key)
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(parse_stream_groups(&result))
}

/// XPENDING — get pending entries summary for a consumer group
pub async fn stream_pending(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    key: &str,
    group: &str,
) -> IpcResult<Vec<PendingEntry>> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    // XPENDING key group - returns [count, start_id, end_id, [[consumer, count], ...]]
    let result: redis::Value = redis::cmd("XPENDING")
        .arg(key)
        .arg(group)
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(parse_pending_summary(&result))
}

/// Parse a raw XRANGE/XREVRANGE entry into a StreamEntry
fn parse_stream_entry(raw: (String, Vec<(String, String)>)) -> StreamEntry {
    let id = raw.0;
    let timestamp_ms = parse_timestamp_ms(&id);
    let fields: Vec<FieldValuePair> = raw
        .1
        .into_iter()
        .map(|(field, value)| FieldValuePair { field, value })
        .collect();

    StreamEntry {
        id,
        fields,
        timestamp_ms,
    }
}

/// Parse entry ID to extract timestamp in milliseconds
fn parse_timestamp_ms(id: &str) -> u64 {
    id.split('-')
        .next()
        .and_then(|s| s.parse::<u64>().ok())
        .unwrap_or(0)
}

/// Parse XINFO STREAM result
fn parse_stream_info(values: &[redis::Value]) -> StreamInfo {
    let mut length: u64 = 0;
    let mut radix_nodes: u64 = 0;
    let mut radix_levels: u64 = 0;
    let mut last_id = String::new();
    let mut max_length: u64 = 0;
    let mut groups: u64 = 0;
    let mut first_entry_id = String::new();

    // XINFO STREAM returns an array of key-value pairs:
    // [length, <n>, radix-nodes, <n>, radix-levels, <n>, last-id, <id>, max-length, <n>, groups, <n>, first-entry, [id, [field, value...]], ...]
    if let redis::Value::Array(ref fields) = values.get(0).unwrap_or(&redis::Value::Nil) {
        let mut i = 0;
        while i + 1 < fields.len() {
            let key = extract_string(&fields[i]);
            match key.as_str() {
                "length" => length = extract_int(&fields[i + 1]) as u64,
                "radix-nodes" => radix_nodes = extract_int(&fields[i + 1]) as u64,
                "radix-levels" => radix_levels = extract_int(&fields[i + 1]) as u64,
                "last-id" => last_id = extract_string(&fields[i + 1]),
                "max-length" => max_length = extract_int(&fields[i + 1]) as u64,
                "groups" => groups = extract_int(&fields[i + 1]) as u64,
                _ => {}
            }
            i += 2;
        }
    }

    // Extract first-entry ID if present
    // first-entry is a nested array: [id, [field1, val1, field2, val2, ...]]
    // We only need the ID part
    if let redis::Value::Array(ref fields) = values.get(0).unwrap_or(&redis::Value::Nil) {
        let mut i = 0;
        while i + 1 < fields.len() {
            let key = extract_string(&fields[i]);
            if key == "first-entry" {
                if let redis::Value::Array(ref entry) = fields[i + 1] {
                    if !entry.is_empty() {
                        first_entry_id = extract_string(&entry[0]);
                    }
                }
            }
            i += 2;
        }
    }

    StreamInfo {
        length,
        radix_nodes,
        radix_levels,
        last_id,
        max_length,
        groups,
        first_entry_id,
    }
}

/// Parse XINFO GROUPS result
fn parse_stream_groups(values: &[redis::Value]) -> Vec<StreamGroup> {
    let mut groups = Vec::new();

    for value in values {
        if let redis::Value::Array(ref fields) = value {
            // XINFO GROUPS returns an array of key-value pairs per group:
            // [name, <name>, consumers, <count>, pending, <count>, ...]
            let mut name = String::new();
            let mut consumers: u64 = 0;
            let mut pending: u64 = 0;
            let mut last_delivered_id = String::new();

            let mut i = 0;
            while i + 1 < fields.len() {
                let key = extract_string(&fields[i]);
                match key.as_str() {
                    "name" => name = extract_string(&fields[i + 1]),
                    "consumers" => consumers = extract_int(&fields[i + 1]) as u64,
                    "pending" => pending = extract_int(&fields[i + 1]) as u64,
                    "last-delivered-id" => last_delivered_id = extract_string(&fields[i + 1]),
                    _ => {}
                }
                i += 2;
            }

            groups.push(StreamGroup {
                name,
                consumers,
                pending,
                last_delivered_id,
            });
        }
    }

    groups
}

/// Parse XPENDING summary result
fn parse_pending_summary(value: &redis::Value) -> Vec<PendingEntry> {
    let mut entries = Vec::new();

    // XPENDING returns: [count, start_id, end_id, [[consumer, count], ...]]
    if let redis::Value::Array(ref fields) = value {
        if fields.len() >= 4 {
            if let redis::Value::Array(ref consumers) = fields[3] {
                for consumer_entry in consumers {
                    if let redis::Value::Array(ref parts) = consumer_entry {
                        if parts.len() >= 2 {
                            entries.push(PendingEntry {
                                consumer_name: extract_string(&parts[0]),
                                pending_count: extract_int(&parts[1]) as u64,
                                idle_ms: 0, // Not available in summary
                                last_delivered_id: String::new(), // Not available in summary
                            });
                        }
                    }
                }
            }
        }
    }

    entries
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_timestamp_ms() {
        assert_eq!(parse_timestamp_ms("1619123456789-0"), 1619123456789);
        assert_eq!(parse_timestamp_ms("0-1"), 0);
        assert_eq!(parse_timestamp_ms("1234567890123-42"), 1234567890123);
    }

    #[test]
    fn test_parse_timestamp_ms_invalid() {
        assert_eq!(parse_timestamp_ms("invalid"), 0);
    }

    #[test]
    fn test_parse_stream_entry() {
        let raw = (
            "1619123456789-0".to_string(),
            vec![
                ("temp".to_string(), "22.5".to_string()),
                ("hum".to_string(), "45".to_string()),
            ],
        );
        let entry = parse_stream_entry(raw);
        assert_eq!(entry.id, "1619123456789-0");
        assert_eq!(entry.timestamp_ms, 1619123456789);
        assert_eq!(entry.fields.len(), 2);
        assert_eq!(entry.fields[0].field, "temp");
        assert_eq!(entry.fields[0].value, "22.5");
    }

    #[test]
    fn test_parse_stream_groups_empty() {
        let groups = parse_stream_groups(&[]);
        assert!(groups.is_empty());
    }

    #[test]
    fn test_parse_stream_groups_single() {
        let value = redis::Value::Array(vec![
            redis::Value::BulkString(b"name".to_vec()),
            redis::Value::BulkString(b"mygroup".to_vec()),
            redis::Value::BulkString(b"consumers".to_vec()),
            redis::Value::Int(3),
            redis::Value::BulkString(b"pending".to_vec()),
            redis::Value::Int(10),
            redis::Value::BulkString(b"last-delivered-id".to_vec()),
            redis::Value::BulkString(b"1619123456789-0".to_vec()),
        ]);

        let groups = parse_stream_groups(&[value]);
        assert_eq!(groups.len(), 1);
        assert_eq!(groups[0].name, "mygroup");
        assert_eq!(groups[0].consumers, 3);
        assert_eq!(groups[0].pending, 10);
        assert_eq!(groups[0].last_delivered_id, "1619123456789-0");
    }

    #[test]
    fn test_parse_pending_summary_empty() {
        let value = redis::Value::Array(vec![
            redis::Value::Int(0),
            redis::Value::Nil,
            redis::Value::Nil,
            redis::Value::Array(vec![]),
        ]);
        let entries = parse_pending_summary(&value);
        assert!(entries.is_empty());
    }

    #[test]
    fn test_parse_pending_summary_with_consumers() {
        let value = redis::Value::Array(vec![
            redis::Value::Int(15),
            redis::Value::BulkString(b"1619123456789-0".to_vec()),
            redis::Value::BulkString(b"1619123499999-0".to_vec()),
            redis::Value::Array(vec![
                redis::Value::Array(vec![
                    redis::Value::BulkString(b"worker-1".to_vec()),
                    redis::Value::Int(10),
                ]),
                redis::Value::Array(vec![
                    redis::Value::BulkString(b"worker-2".to_vec()),
                    redis::Value::Int(5),
                ]),
            ]),
        ]);
        let entries = parse_pending_summary(&value);
        assert_eq!(entries.len(), 2);
        assert_eq!(entries[0].consumer_name, "worker-1");
        assert_eq!(entries[0].pending_count, 10);
        assert_eq!(entries[1].consumer_name, "worker-2");
        assert_eq!(entries[1].pending_count, 5);
    }
}
