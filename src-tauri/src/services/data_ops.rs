use redis::aio::MultiplexedConnection;
use crate::error::{IpcError, IpcResult};
use crate::models::data::BulkResult;

/// Set / create a key by type
pub async fn key_set(
    conn: &mut MultiplexedConnection,
    key: &str,
    key_type: &str,
    value: serde_json::Value,
) -> IpcResult<()> {
    match key_type.to_lowercase().as_str() {
        "string" => {
            let v = value.as_str().unwrap_or("").to_string();
            redis::cmd("SET")
                .arg(key)
                .arg(v)
                .query_async::<()>(conn)
                .await
                .map_err(|e| IpcError::Redis { message: e.to_string() })?;
        }
        "hash" => {
            // value: { "field": "value", ... }
            if let Some(obj) = value.as_object() {
                for (field, val) in obj {
                    let v = val.as_str().unwrap_or("").to_string();
                    redis::cmd("HSET")
                        .arg(key)
                        .arg(field)
                        .arg(v)
                        .query_async::<()>(conn)
                        .await
                        .map_err(|e| IpcError::Redis { message: e.to_string() })?;
                }
            }
        }
        "list" => {
            // value: ["item1", "item2", ...]
            if let Some(arr) = value.as_array() {
                for item in arr {
                    let v = item.as_str().unwrap_or("").to_string();
                    redis::cmd("RPUSH")
                        .arg(key)
                        .arg(v)
                        .query_async::<()>(conn)
                        .await
                        .map_err(|e| IpcError::Redis { message: e.to_string() })?;
                }
            }
        }
        "set" => {
            // value: ["member1", "member2", ...]
            if let Some(arr) = value.as_array() {
                for item in arr {
                    let v = item.as_str().unwrap_or("").to_string();
                    redis::cmd("SADD")
                        .arg(key)
                        .arg(v)
                        .query_async::<()>(conn)
                        .await
                        .map_err(|e| IpcError::Redis { message: e.to_string() })?;
                }
            }
        }
        "zset" => {
            // value: [{ "score": 1.0, "member": "m1" }, ...]
            if let Some(arr) = value.as_array() {
                for item in arr {
                    let score = item["score"].as_f64().unwrap_or(0.0);
                    let member = item["member"].as_str().unwrap_or("").to_string();
                    redis::cmd("ZADD")
                        .arg(key)
                        .arg(score)
                        .arg(member)
                        .query_async::<()>(conn)
                        .await
                        .map_err(|e| IpcError::Redis { message: e.to_string() })?;
                }
            }
        }
        _ => {
            return Err(IpcError::InvalidArgument {
                field: "key_type".to_string(),
                reason: format!("unsupported type: {key_type}"),
            });
        }
    }
    Ok(())
}

/// Delete a key
pub async fn key_delete(conn: &mut MultiplexedConnection, key: &str) -> IpcResult<()> {
    redis::cmd("DEL")
        .arg(key)
        .query_async::<()>(conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })
}

/// Rename a key
pub async fn key_rename(
    conn: &mut MultiplexedConnection,
    old_key: &str,
    new_key: &str,
) -> IpcResult<()> {
    redis::cmd("RENAME")
        .arg(old_key)
        .arg(new_key)
        .query_async::<()>(conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })
}

/// Set TTL for a key (-1 = persist)
pub async fn key_ttl_set(
    conn: &mut MultiplexedConnection,
    key: &str,
    ttl_seconds: i64,
) -> IpcResult<()> {
    if ttl_seconds < 0 {
        redis::cmd("PERSIST")
            .arg(key)
            .query_async::<()>(conn)
            .await
            .map_err(|e| IpcError::Redis { message: e.to_string() })
    } else {
        redis::cmd("EXPIRE")
            .arg(key)
            .arg(ttl_seconds)
            .query_async::<()>(conn)
            .await
            .map_err(|e| IpcError::Redis { message: e.to_string() })
    }
}

/// Bulk delete keys in batches of 100 to avoid blocking Redis main thread.
/// Returns the count of successfully deleted keys and a list of failed keys.
pub async fn keys_bulk_delete(
    conn: &mut MultiplexedConnection,
    keys: &[String],
) -> IpcResult<BulkResult> {
    const BATCH_SIZE: usize = 100;
    let mut success: u64 = 0;
    let mut failed: Vec<String> = Vec::new();

    for chunk in keys.chunks(BATCH_SIZE) {
        let mut cmd = redis::cmd("DEL");
        for k in chunk {
            cmd.arg(k);
        }
        match cmd.query_async::<u64>(conn).await {
            Ok(deleted) => {
                success += deleted;
                // Keys that were in the chunk but not deleted (didn't exist) are not treated as failures
            }
            Err(_e) => {
                // Whole batch failed -> add all to failed list, then try per-key to salvage
                for k in chunk {
                    match redis::cmd("DEL").arg(k).query_async::<u64>(conn).await {
                        Ok(n) => success += n,
                        Err(_) => failed.push(k.clone()),
                    }
                }
            }
        }
        // Small yield between batches to keep Redis responsive on very large sets
        tokio::time::sleep(std::time::Duration::from_millis(10)).await;
    }

    Ok(BulkResult { success, failed })
}

/// Bulk set TTL (or PERSIST when ttl_seconds is None) for a list of keys.
pub async fn keys_bulk_ttl(
    conn: &mut MultiplexedConnection,
    keys: &[String],
    ttl_seconds: Option<i64>,
) -> IpcResult<BulkResult> {
    let mut success: u64 = 0;
    let mut failed: Vec<String> = Vec::new();

    for k in keys {
        let result = match ttl_seconds {
            None => redis::cmd("PERSIST").arg(k).query_async::<u64>(conn).await,
            Some(secs) if secs < 0 => redis::cmd("PERSIST").arg(k).query_async::<u64>(conn).await,
            Some(secs) => redis::cmd("EXPIRE").arg(k).arg(secs).query_async::<u64>(conn).await,
        };
        match result {
            Ok(n) if n >= 1 => success += 1,
            // n == 0 typically means key didn't exist; count as failure for caller visibility
            Ok(_) => failed.push(k.clone()),
            Err(_) => failed.push(k.clone()),
        }
    }

    Ok(BulkResult { success, failed })
}
