use crate::error::IpcResult;
use crate::models::phase2::{SlowlogEntry, ServerConfigItem, ServerInfo};
use crate::services::connection_manager::SharedConnectionManager;
use tauri::State;

#[tauri::command]
pub async fn slowlog_get(
    conn_id: String,
    count: Option<u32>,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<Vec<SlowlogEntry>> {
    tracing::info!(command = "slowlog_get", conn_id = %conn_id, count = ?count, "IPC call");
    crate::services::server_config::slowlog_get(mgr.inner(), &conn_id, count).await
}

#[tauri::command]
pub async fn slowlog_reset(
    conn_id: String,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<()> {
    tracing::info!(command = "slowlog_reset", conn_id = %conn_id, "IPC call");
    crate::services::server_config::slowlog_reset(mgr.inner(), &conn_id).await
}

#[tauri::command]
pub async fn config_get_all(
    conn_id: String,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<Vec<ServerConfigItem>> {
    tracing::info!(command = "config_get_all", conn_id = %conn_id, "IPC call");
    crate::services::server_config::config_get_all(mgr.inner(), &conn_id).await
}

#[tauri::command]
pub async fn config_set(
    conn_id: String,
    key: String,
    value: String,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<()> {
    tracing::info!(command = "config_set", conn_id = %conn_id, key = %key, "IPC call");
    crate::services::server_config::config_set(mgr.inner(), &conn_id, &key, &value).await
}

#[tauri::command]
pub async fn server_info(
    conn_id: String,
    section: Option<String>,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<ServerInfo> {
    tracing::info!(command = "server_info", conn_id = %conn_id, section = ?section, "IPC call");
    crate::services::server_config::server_info(mgr.inner(), &conn_id, section.as_deref()).await
}

/// CONFIG REWRITE — persist config to disk
#[tauri::command]
pub async fn config_rewrite(
    conn_id: String,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<()> {
    tracing::info!(command = "config_rewrite", conn_id = %conn_id, "IPC call");
    crate::services::server_config::config_rewrite(mgr.inner(), &conn_id).await
}

/// CONFIG RESETSTAT — reset statistics counters
#[tauri::command]
pub async fn config_resetstat(
    conn_id: String,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<()> {
    tracing::info!(command = "config_resetstat", conn_id = %conn_id, "IPC call");
    crate::services::server_config::config_resetstat(mgr.inner(), &conn_id).await
}

/// Get notify-keyspace-events configuration
#[tauri::command]
pub async fn config_get_notify_keyspace_events(
    conn_id: String,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<String> {
    tracing::info!(command = "config_get_notify_keyspace_events", conn_id = %conn_id, "IPC call");
    crate::services::server_config::config_get_notify_keyspace_events(mgr.inner(), &conn_id).await
}
