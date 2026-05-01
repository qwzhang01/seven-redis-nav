use redis::aio::MultiplexedConnection;
use crate::error::{IpcError, IpcResult};
use crate::models::data::{KeyDetail, KeyMeta, KeyType, RedisValue, ScanPage};
use crate::utils::redis_utils::bytes_to_display_string;

const SCAN_COUNT: u64 = 200;

/// Default max elements returned for collection types (list / zset / set / hash)
/// when fetching a key detail. Clients can page beyond this via dedicated commands.
const COLLECTION_PREVIEW_LIMIT: isize = 500;

/// SCAN keys with cursor, pattern, and count
pub async fn scan_keys(
    conn: &mut MultiplexedConnection,
    cursor: u64,
    pattern: &str,
    count: u64,
) -> IpcResult<(u64, Vec<String>)> {
    let pattern = if pattern.is_empty() { "*" } else { pattern };

    let (next_cursor, keys): (u64, Vec<String>) = redis::cmd("SCAN")
        .arg(cursor)
        .arg("MATCH")
        .arg(pattern)
        .arg("COUNT")
        .arg(count)
        .query_async(conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok((next_cursor, keys))
}

/// Get metadata for a list of keys.
///
/// Uses a single pipeline to batch `TYPE` / `TTL` / `MEMORY USAGE` /
/// `OBJECT ENCODING` for every key — reduces round-trips from 4·N to 1
/// (fix 2.3).
pub async fn get_key_metas(
    conn: &mut MultiplexedConnection,
    keys: Vec<String>,
) -> IpcResult<Vec<KeyMeta>> {
    if keys.is_empty() {
        return Ok(Vec::new());
    }

    // Build one pipeline: for each key push 4 commands in a stable order.
    let mut pipe = redis::pipe();
    for key in &keys {
        pipe.cmd("TYPE").arg(key);
        pipe.cmd("TTL").arg(key);
        pipe.cmd("MEMORY").arg("USAGE").arg(key);
        pipe.cmd("OBJECT").arg("ENCODING").arg(key);
    }

    // Decode as a flat Vec<redis::Value> so we can tolerate per-command failures
    // (MEMORY USAGE / OBJECT ENCODING may return Nil for newly-created keys or
    // on Redis versions without MEMORY command).
    let raw: Vec<redis::Value> = pipe
        .query_async(conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    if raw.len() != keys.len() * 4 {
        return Err(IpcError::Internal {
            message: format!(
                "pipeline response length mismatch: got {}, expected {}",
                raw.len(),
                keys.len() * 4
            ),
        });
    }

    let mut metas = Vec::with_capacity(keys.len());
    for (i, key) in keys.into_iter().enumerate() {
        let base = i * 4;

        let type_str: String = redis::from_redis_value(&raw[base])
            .unwrap_or_else(|_| "none".to_string());
        let ttl: i64 = redis::from_redis_value(&raw[base + 1]).unwrap_or(-1);
        let size: u64 = redis::from_redis_value(&raw[base + 2]).unwrap_or(0);
        let encoding: String = redis::from_redis_value(&raw[base + 3])
            .unwrap_or_else(|_| "unknown".to_string());

        metas.push(KeyMeta {
            key,
            key_type: KeyType::from(type_str.as_str()),
            ttl,
            size,
            encoding,
        });
    }

    Ok(metas)
}

/// Scan a page of keys with metadata
pub async fn scan_page(
    conn: &mut MultiplexedConnection,
    cursor: u64,
    pattern: &str,
) -> IpcResult<ScanPage> {
    let (next_cursor, keys) = scan_keys(conn, cursor, pattern, SCAN_COUNT).await?;
    let total_scanned = keys.len() as u64;
    let metas = get_key_metas(conn, keys).await?;

    Ok(ScanPage {
        keys: metas,
        cursor: next_cursor,
        total_scanned,
    })
}

/// Get full key detail (value + metadata).
///
/// All value reads are binary-safe (fix 1.7): we fetch raw bytes and
/// fall back to a hex preview when the payload is not valid UTF-8.
pub async fn get_key_detail(
    conn: &mut MultiplexedConnection,
    key: &str,
    db: u8,
) -> IpcResult<KeyDetail> {
    // TYPE
    let type_str: String = redis::cmd("TYPE")
        .arg(key)
        .query_async(conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    if type_str == "none" {
        return Err(IpcError::NotFound { key: key.to_string() });
    }

    let key_type = KeyType::from(type_str.as_str());

    // TTL / MEMORY USAGE / OBJECT ENCODING in one pipeline
    let (ttl, size, encoding): (i64, u64, String) = {
        let raw: Vec<redis::Value> = redis::pipe()
            .cmd("TTL").arg(key)
            .cmd("MEMORY").arg("USAGE").arg(key)
            .cmd("OBJECT").arg("ENCODING").arg(key)
            .query_async(conn)
            .await
            .map_err(|e| IpcError::Redis { message: e.to_string() })?;
        (
            raw.get(0).and_then(|v| redis::from_redis_value(v).ok()).unwrap_or(-1),
            raw.get(1).and_then(|v| redis::from_redis_value(v).ok()).unwrap_or(0),
            raw.get(2).and_then(|v| redis::from_redis_value(v).ok()).unwrap_or_else(|| "unknown".to_string()),
        )
    };

    // Fetch value based on type
    let (value, length) = match key_type {
        KeyType::String => {
            let bytes: Vec<u8> = redis::cmd("GET")
                .arg(key)
                .query_async(conn)
                .await
                .map_err(|e| IpcError::Redis { message: e.to_string() })?;
            let len = bytes.len() as u64;
            (RedisValue::String { value: bytes_to_display_string(&bytes) }, len)
        }
        KeyType::Hash => {
            // HLEN first for true length, then HGETALL (capped display).
            let total: u64 = redis::cmd("HLEN")
                .arg(key)
                .query_async(conn)
                .await
                .unwrap_or(0);
            let raw: Vec<(Vec<u8>, Vec<u8>)> = redis::cmd("HGETALL")
                .arg(key)
                .query_async(conn)
                .await
                .map_err(|e| IpcError::Redis { message: e.to_string() })?;
            let fields: Vec<(String, String)> = raw
                .into_iter()
                .map(|(k, v)| (bytes_to_display_string(&k), bytes_to_display_string(&v)))
                .collect();
            (RedisValue::Hash { fields }, total)
        }
        KeyType::List => {
            let total: u64 = redis::cmd("LLEN")
                .arg(key)
                .query_async(conn)
                .await
                .unwrap_or(0);
            let raw: Vec<Vec<u8>> = redis::cmd("LRANGE")
                .arg(key)
                .arg(0)
                .arg(COLLECTION_PREVIEW_LIMIT - 1)
                .query_async(conn)
                .await
                .map_err(|e| IpcError::Redis { message: e.to_string() })?;
            let items: Vec<String> = raw.into_iter().map(|b| bytes_to_display_string(&b)).collect();
            (RedisValue::List { items }, total)
        }
        KeyType::Set => {
            let total: u64 = redis::cmd("SCARD")
                .arg(key)
                .query_async(conn)
                .await
                .unwrap_or(0);
            // SMEMBERS returns all members; for very large sets we rely on the UI
            // to warn. A future iteration can switch to SSCAN-based paging.
            let raw: Vec<Vec<u8>> = redis::cmd("SMEMBERS")
                .arg(key)
                .query_async(conn)
                .await
                .map_err(|e| IpcError::Redis { message: e.to_string() })?;
            let members: Vec<String> = raw.into_iter().map(|b| bytes_to_display_string(&b)).collect();
            (RedisValue::Set { members }, total)
        }
        KeyType::ZSet => {
            let total: u64 = redis::cmd("ZCARD")
                .arg(key)
                .query_async(conn)
                .await
                .unwrap_or(0);
            let raw: Vec<(Vec<u8>, f64)> = redis::cmd("ZRANGE")
                .arg(key)
                .arg(0)
                .arg(COLLECTION_PREVIEW_LIMIT - 1)
                .arg("WITHSCORES")
                .query_async(conn)
                .await
                .map_err(|e| IpcError::Redis { message: e.to_string() })?;
            let members: Vec<(f64, String)> = raw
                .into_iter()
                .map(|(m, s)| (s, bytes_to_display_string(&m)))
                .collect();
            (RedisValue::ZSet { members }, total)
        }
        KeyType::Stream => {
            // XLEN for total count, then XRANGE to fetch a preview of
            // recent entries (fix 2.13: Stream type was previously lumped
            // into the _ catch-all, returning "unsupported type").
            let total: u64 = redis::cmd("XLEN")
                .arg(key)
                .query_async(conn)
                .await
                .unwrap_or(0);

            // XRANGE - + COUNT N returns the first N entries.
            // We use serde_json::Value to avoid defining a rigid struct
            // for stream entries (field names are user-defined).
            let raw_entries: Vec<(String, Vec<(Vec<u8>, Vec<u8>)>)> = redis::cmd("XRANGE")
                .arg(key)
                .arg("-")
                .arg("+")
                .arg("COUNT")
                .arg(COLLECTION_PREVIEW_LIMIT)
                .query_async(conn)
                .await
                .map_err(|e| IpcError::Redis { message: e.to_string() })?;

            let entries: Vec<serde_json::Value> = raw_entries
                .into_iter()
                .map(|(id, fields)| {
                    let fields_obj: serde_json::Map<String, serde_json::Value> = fields
                        .into_iter()
                        .map(|(k, v)| {
                            (
                                bytes_to_display_string(&k),
                                serde_json::Value::String(bytes_to_display_string(&v)),
                            )
                        })
                        .collect();
                    serde_json::json!({
                        "id": id,
                        "fields": fields_obj,
                    })
                })
                .collect();

            (RedisValue::Stream { entries }, total)
        }
        _ => {
            (RedisValue::String { value: "(unsupported type)".to_string() }, 0)
        }
    };

    Ok(KeyDetail {
        key: key.to_string(),
        key_type,
        ttl,
        size,
        encoding,
        length,
        db,
        value,
    })
}
