use crate::error::IpcResult;
use crate::models::phase3::HllStats;
use crate::services::connection_manager::SharedConnectionManager;
use tauri::State;

/// PFADD — add elements to a HyperLogLog
#[tauri::command]
pub async fn hll_add(
    conn_id: String,
    key: String,
    elements: Vec<String>,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<bool> {
    tracing::info!(
        command = "hll_add",
        conn_id = %conn_id,
        key = %key,
        count = elements.len(),
        "IPC call"
    );
    crate::services::hll::hll_add(mgr.inner(), &conn_id, &key, &elements).await
}

/// PFCOUNT — get estimated cardinality of a HyperLogLog
#[tauri::command]
pub async fn hll_count(
    conn_id: String,
    key: String,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<HllStats> {
    tracing::info!(
        command = "hll_count",
        conn_id = %conn_id,
        key = %key,
        "IPC call"
    );
    crate::services::hll::hll_count(mgr.inner(), &conn_id, &key).await
}

/// PFMERGE — merge multiple HyperLogLog keys
#[tauri::command]
pub async fn hll_merge(
    conn_id: String,
    dest_key: String,
    source_keys: Vec<String>,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<()> {
    tracing::info!(
        command = "hll_merge",
        conn_id = %conn_id,
        dest_key = %dest_key,
        source_keys = ?source_keys,
        "IPC call"
    );
    crate::services::hll::hll_merge(mgr.inner(), &conn_id, &dest_key, &source_keys).await
}
