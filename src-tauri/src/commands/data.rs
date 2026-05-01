use tauri::State;
use crate::error::IpcResult;
use crate::models::connection::ConnId;
use crate::models::data::{KeyDetail, ScanPage, BulkResult};
use crate::services;
use crate::services::connection_manager::SharedConnectionManager;

/// Scan keys with cursor and pattern
#[tauri::command]
pub async fn keys_scan(
    conn_id: ConnId,
    cursor: u64,
    pattern: String,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<ScanPage> {
    tracing::info!(command = "keys_scan", conn_id = %conn_id, cursor, pattern = %pattern, "IPC call");

    // Brief manager lock → get session handle → drop manager lock
    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;
    services::key_browser::scan_page(&mut guard.conn, cursor, &pattern).await
}

/// Get full key detail
#[tauri::command]
pub async fn key_get(
    conn_id: ConnId,
    key: String,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<KeyDetail> {
    tracing::info!(command = "key_get", conn_id = %conn_id, key = %key, "IPC call");

    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;
    let db = guard.current_db;
    services::key_browser::get_key_detail(&mut guard.conn, &key, db).await
}

/// Set / create a key
#[tauri::command]
pub async fn key_set(
    conn_id: ConnId,
    key: String,
    value: serde_json::Value,
    key_type: String,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<()> {
    tracing::info!(command = "key_set", conn_id = %conn_id, key = %key, "IPC call");

    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;
    services::data_ops::key_set(&mut guard.conn, &key, &key_type, value).await
}

/// Delete a key
#[tauri::command]
pub async fn key_delete(
    conn_id: ConnId,
    key: String,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<()> {
    tracing::info!(command = "key_delete", conn_id = %conn_id, key = %key, "IPC call");

    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;
    services::data_ops::key_delete(&mut guard.conn, &key).await
}

/// Rename a key
#[tauri::command]
pub async fn key_rename(
    conn_id: ConnId,
    old_key: String,
    new_key: String,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<()> {
    tracing::info!(command = "key_rename", conn_id = %conn_id, old_key = %old_key, new_key = %new_key, "IPC call");

    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;
    services::data_ops::key_rename(&mut guard.conn, &old_key, &new_key).await
}

/// Set TTL for a key
#[tauri::command]
pub async fn key_ttl_set(
    conn_id: ConnId,
    key: String,
    ttl_seconds: i64,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<()> {
    tracing::info!(command = "key_ttl_set", conn_id = %conn_id, key = %key, ttl = ttl_seconds, "IPC call");

    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;
    services::data_ops::key_ttl_set(&mut guard.conn, &key, ttl_seconds).await
}

/// Bulk delete multiple keys (batched, returns success/failure counts)
#[tauri::command]
pub async fn keys_bulk_delete(
    conn_id: ConnId,
    keys: Vec<String>,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<BulkResult> {
    tracing::info!(
        command = "keys_bulk_delete",
        conn_id = %conn_id,
        count = keys.len(),
        "IPC call"
    );

    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;
    services::data_ops::keys_bulk_delete(&mut guard.conn, &keys).await
}

/// Bulk set / remove TTL for multiple keys.
#[tauri::command]
pub async fn keys_bulk_ttl(
    conn_id: ConnId,
    keys: Vec<String>,
    ttl_seconds: Option<i64>,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<BulkResult> {
    tracing::info!(
        command = "keys_bulk_ttl",
        conn_id = %conn_id,
        count = keys.len(),
        ttl = ?ttl_seconds,
        "IPC call"
    );

    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;
    services::data_ops::keys_bulk_ttl(&mut guard.conn, &keys, ttl_seconds).await
}
