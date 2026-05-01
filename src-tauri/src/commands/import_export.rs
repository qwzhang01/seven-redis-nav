use redis::aio::MultiplexedConnection;
use tauri::State;
use chrono::Utc;

use crate::error::{IpcError, IpcResult};
use crate::models::connection::ConnId;
use crate::models::data::RedisValue;
use crate::models::import_export::{ExportKey, ImportResult, RedisExport};
use crate::services::connection_manager::SharedConnectionManager;
use crate::services::key_browser;

const MAX_VALUE_BYTES: u64 = 1_048_576; // 1 MB

// ─────────────────────────────────────────────
// Export helpers
// ─────────────────────────────────────────────

async fn export_single_key(
    conn: &mut MultiplexedConnection,
    key: &str,
) -> IpcResult<ExportKey> {
    // Get type
    let key_type_str: String = redis::cmd("TYPE")
        .arg(key)
        .query_async(conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    // Get TTL
    let ttl: i64 = redis::cmd("TTL")
        .arg(key)
        .query_async(conn)
        .await
        .unwrap_or(-1);

    // Get memory size
    let size: u64 = redis::cmd("MEMORY")
        .arg("USAGE")
        .arg(key)
        .arg("SAMPLES")
        .arg(0)
        .query_async(conn)
        .await
        .unwrap_or(0);

    // Truncate large values
    if size > MAX_VALUE_BYTES {
        let preview: String = redis::cmd("GETRANGE")
            .arg(key)
            .arg(0)
            .arg(99)
            .query_async(conn)
            .await
            .unwrap_or_default();
        return Ok(ExportKey {
            key: key.to_string(),
            key_type: key_type_str,
            ttl,
            value: None,
            truncated: Some(true),
            size_bytes: Some(size),
            preview: Some(preview),
        });
    }

    // Get full value via key_browser
    let detail = key_browser::get_key_detail(conn, key, 0).await?;
    Ok(ExportKey {
        key: key.to_string(),
        key_type: key_type_str,
        ttl,
        value: Some(detail.value),
        truncated: None,
        size_bytes: None,
        preview: None,
    })
}

// ─────────────────────────────────────────────
// Commands
// ─────────────────────────────────────────────

/// Export selected keys to a RedisExport structure.
#[tauri::command]
pub async fn export_keys_json(
    conn_id: ConnId,
    keys: Vec<String>,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<RedisExport> {
    // Acquire config first, then release manager lock before acquiring session lock
    // to avoid lock nesting (manager → session) which could deadlock.
    let (session, config) = {
        let mgr = manager.lock().await;
        let session = mgr.get_session(&conn_id)?;
        let config = mgr.get_config_cloned(&conn_id).await?;
        (session, config)
    };
    let mut guard = session.lock().await;

    let mut export = RedisExport::new(&config.host, config.port, guard.current_db);

    for key in &keys {
        match export_single_key(&mut guard.conn, key).await {
            Ok(entry) => export.keys.push(entry),
            Err(_) => {} // skip failed keys silently
        }
    }

    Ok(export)
}

/// Export entire DB to a RedisExport structure (with Tauri event progress).
#[tauri::command]
pub async fn export_db_json(
    conn_id: ConnId,
    manager: State<'_, SharedConnectionManager>,
    app: tauri::AppHandle,
) -> IpcResult<RedisExport> {
    use tauri::Emitter;

    // Acquire config and session in one lock scope to avoid nesting.
    let (session, config) = {
        let mgr = manager.lock().await;
        let session = mgr.get_session(&conn_id)?;
        let config = mgr.get_config_cloned(&conn_id).await?;
        (session, config)
    };

    // Hold the session lock for the entire export to avoid N lock acquisitions.
    let mut guard = session.lock().await;
    let db = guard.current_db;
    let mut export = RedisExport::new(&config.host, config.port, db);

    // Scan all keys first, then export — all within the same lock guard.
    let mut cursor: u64 = 0;
    let mut all_keys: Vec<String> = Vec::new();
    loop {
        let result: (u64, Vec<String>) = redis::cmd("SCAN")
            .arg(cursor)
            .arg("COUNT")
            .arg(100)
            .query_async(&mut guard.conn)
            .await
            .map_err(|e| IpcError::Redis { message: e.to_string() })?;
        cursor = result.0;
        all_keys.extend(result.1);
        if cursor == 0 { break; }
    }

    let total = all_keys.len();
    for (i, key) in all_keys.iter().enumerate() {
        match export_single_key(&mut guard.conn, key).await {
            Ok(entry) => export.keys.push(entry),
            Err(_) => {}
        }
        if (i + 1) % 100 == 0 {
            let _ = app.emit("export_db:progress", serde_json::json!({
                "exported": i + 1,
                "total": total
            }));
        }
    }

    Ok(export)
}

/// Import keys from a RedisExport structure.
#[tauri::command]
pub async fn import_keys_json(
    conn_id: ConnId,
    data: RedisExport,
    overwrite: bool,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<ImportResult> {
    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };

    let mut result = ImportResult { success: 0, skipped: 0, failed: 0, errors: Vec::new() };

    for entry in &data.keys {
        let mut guard = session.lock().await;

        // Check if key exists
        let exists: i64 = redis::cmd("EXISTS")
            .arg(&entry.key)
            .query_async(&mut guard.conn)
            .await
            .unwrap_or(0);

        if exists > 0 && !overwrite {
            result.skipped += 1;
            continue;
        }

        // Skip truncated entries
        if entry.truncated.unwrap_or(false) {
            result.skipped += 1;
            continue;
        }

        let value = match &entry.value {
            Some(v) => v,
            None => { result.skipped += 1; continue; }
        };

        let write_result = write_key(&mut guard.conn, &entry.key, value, entry.ttl).await;
        match write_result {
            Ok(_) => result.success += 1,
            Err(e) => {
                result.failed += 1;
                result.errors.push(format!("{}: {}", entry.key, e));
            }
        }
    }

    Ok(result)
}

async fn write_key(
    conn: &mut MultiplexedConnection,
    key: &str,
    value: &RedisValue,
    ttl: i64,
) -> IpcResult<()> {
    match value {
        RedisValue::String { value: v } => {
            redis::cmd("SET").arg(key).arg(v).query_async::<()>(conn).await
                .map_err(|e| IpcError::Redis { message: e.to_string() })?;
        }
        RedisValue::Hash { fields } => {
            redis::cmd("DEL").arg(key).query_async::<()>(conn).await.ok();
            for (f, v) in fields {
                redis::cmd("HSET").arg(key).arg(f).arg(v).query_async::<()>(conn).await
                    .map_err(|e| IpcError::Redis { message: e.to_string() })?;
            }
        }
        RedisValue::List { items } => {
            redis::cmd("DEL").arg(key).query_async::<()>(conn).await.ok();
            for item in items {
                redis::cmd("RPUSH").arg(key).arg(item).query_async::<()>(conn).await
                    .map_err(|e| IpcError::Redis { message: e.to_string() })?;
            }
        }
        RedisValue::Set { members } => {
            redis::cmd("DEL").arg(key).query_async::<()>(conn).await.ok();
            for m in members {
                redis::cmd("SADD").arg(key).arg(m).query_async::<()>(conn).await
                    .map_err(|e| IpcError::Redis { message: e.to_string() })?;
            }
        }
        RedisValue::ZSet { members } => {
            redis::cmd("DEL").arg(key).query_async::<()>(conn).await.ok();
            for (score, member) in members {
                redis::cmd("ZADD").arg(key).arg(score).arg(member).query_async::<()>(conn).await
                    .map_err(|e| IpcError::Redis { message: e.to_string() })?;
            }
        }
        RedisValue::Stream { .. } => {
            // Skip stream import (complex structure)
            return Err(IpcError::InvalidArgument { field: "key_type".to_string(), reason: "Stream import not supported".to_string() });
        }
    }

    // Set TTL if applicable
    if ttl > 0 {
        redis::cmd("EXPIRE").arg(key).arg(ttl).query_async::<()>(conn).await
            .map_err(|e| IpcError::Redis { message: e.to_string() })?;
    }

    Ok(())
}

/// Parse a local RDB file (read-only) and return as RedisExport.
#[tauri::command]
pub async fn rdb_parse_file(file_path: String) -> IpcResult<RedisExport> {

    let file = std::fs::File::open(&file_path)
        .map_err(|e| IpcError::Internal { message: format!("Cannot open RDB file: {e}") })?;

    let _collector_unused = ();
    let filter = rdb::Simple::new();

    // rdb::parse takes ownership of formatter, so we use a wrapper to get results back
    // We use a shared reference via Arc<Mutex> to collect results
    use std::sync::{Arc, Mutex};

    struct SharedCollector(Arc<Mutex<Vec<ExportKey>>>);

    impl rdb::formatter::Formatter for SharedCollector {
        fn string(&mut self, key: &[u8], value: &[u8], expiry: &Option<u64>) {
            let k = String::from_utf8_lossy(key).to_string();
            let v = String::from_utf8_lossy(value).to_string();
            let ttl = expiry.map(|e| {
                let now_ms = chrono::Utc::now().timestamp_millis() as u64;
                if e > now_ms { ((e - now_ms) / 1000) as i64 } else { -2 }
            }).unwrap_or(-1);
            if let Ok(mut keys) = self.0.lock() {
                keys.push(ExportKey {
                    key: k, key_type: "string".to_string(), ttl,
                    value: Some(RedisValue::String { value: v }),
                    truncated: None, size_bytes: None, preview: None,
                });
            }
        }

        fn hash(&mut self, key: &[u8], values: &indexmap::map::IndexMap<Vec<u8>, Vec<u8>>, expiry: &Option<u64>) {
            let k = String::from_utf8_lossy(key).to_string();
            let fields: Vec<(String, String)> = values.iter()
                .map(|(f, v)| (String::from_utf8_lossy(f).to_string(), String::from_utf8_lossy(v).to_string()))
                .collect();
            let ttl = expiry.map(|e| {
                let now_ms = chrono::Utc::now().timestamp_millis() as u64;
                if e > now_ms { ((e - now_ms) / 1000) as i64 } else { -2 }
            }).unwrap_or(-1);
            if let Ok(mut keys) = self.0.lock() {
                keys.push(ExportKey {
                    key: k, key_type: "hash".to_string(), ttl,
                    value: Some(RedisValue::Hash { fields }),
                    truncated: None, size_bytes: None, preview: None,
                });
            }
        }

        fn list(&mut self, key: &[u8], values: &[Vec<u8>], expiry: &Option<u64>) {
            let k = String::from_utf8_lossy(key).to_string();
            let items: Vec<String> = values.iter().map(|v| String::from_utf8_lossy(v).to_string()).collect();
            let ttl = expiry.map(|e| {
                let now_ms = chrono::Utc::now().timestamp_millis() as u64;
                if e > now_ms { ((e - now_ms) / 1000) as i64 } else { -2 }
            }).unwrap_or(-1);
            if let Ok(mut keys) = self.0.lock() {
                keys.push(ExportKey {
                    key: k, key_type: "list".to_string(), ttl,
                    value: Some(RedisValue::List { items }),
                    truncated: None, size_bytes: None, preview: None,
                });
            }
        }

        fn set(&mut self, key: &[u8], values: &[Vec<u8>], expiry: &Option<u64>) {
            let k = String::from_utf8_lossy(key).to_string();
            let members: Vec<String> = values.iter().map(|v| String::from_utf8_lossy(v).to_string()).collect();
            let ttl = expiry.map(|e| {
                let now_ms = chrono::Utc::now().timestamp_millis() as u64;
                if e > now_ms { ((e - now_ms) / 1000) as i64 } else { -2 }
            }).unwrap_or(-1);
            if let Ok(mut keys) = self.0.lock() {
                keys.push(ExportKey {
                    key: k, key_type: "set".to_string(), ttl,
                    value: Some(RedisValue::Set { members }),
                    truncated: None, size_bytes: None, preview: None,
                });
            }
        }

        fn sorted_set(&mut self, key: &[u8], values: &[(f64, Vec<u8>)], expiry: &Option<u64>) {
            let k = String::from_utf8_lossy(key).to_string();
            let members: Vec<(f64, String)> = values.iter()
                .map(|(score, member)| (*score, String::from_utf8_lossy(member).to_string()))
                .collect();
            let ttl = expiry.map(|e| {
                let now_ms = chrono::Utc::now().timestamp_millis() as u64;
                if e > now_ms { ((e - now_ms) / 1000) as i64 } else { -2 }
            }).unwrap_or(-1);
            if let Ok(mut keys) = self.0.lock() {
                keys.push(ExportKey {
                    key: k, key_type: "zset".to_string(), ttl,
                    value: Some(RedisValue::ZSet { members }),
                    truncated: None, size_bytes: None, preview: None,
                });
            }
        }
    }

    let shared_keys: Arc<Mutex<Vec<ExportKey>>> = Arc::new(Mutex::new(Vec::new()));
    let shared_collector = SharedCollector(shared_keys.clone());

    rdb::parse(file, shared_collector, filter)
        .map_err(|e| IpcError::Internal { message: format!("RDB parse error: {e}") })?;

    let keys = Arc::try_unwrap(shared_keys)
        .map_err(|_| IpcError::Internal { message: "Failed to unwrap RDB results".to_string() })?
        .into_inner()
        .map_err(|_| IpcError::Internal { message: "Mutex poisoned".to_string() })?;

    Ok(RedisExport {
        version: "1.0".to_string(),
        connection: crate::models::import_export::ExportConnectionInfo {
            host: "rdb-file".to_string(),
            port: 0,
            db: 0,
        },
        exported_at: Utc::now().to_rfc3339(),
        keys,
    })
}
