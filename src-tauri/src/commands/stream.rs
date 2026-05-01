use crate::error::IpcResult;
use crate::models::phase3::{StreamEntry, StreamGroup, PendingEntry, StreamInfo};
use crate::services::connection_manager::SharedConnectionManager;
use tauri::State;

/// XRANGE — read entries from a stream in ascending order
#[tauri::command]
pub async fn stream_range(
    conn_id: String,
    key: String,
    start: String,
    end: String,
    count: Option<u64>,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<Vec<StreamEntry>> {
    tracing::info!(
        command = "stream_range",
        conn_id = %conn_id,
        key = %key,
        start = %start,
        end = %end,
        count = ?count,
        "IPC call"
    );
    crate::services::stream::stream_range(mgr.inner(), &conn_id, &key, &start, &end, count).await
}

/// XREVRANGE — read entries from a stream in descending order
#[tauri::command]
pub async fn stream_rev_range(
    conn_id: String,
    key: String,
    start: String,
    end: String,
    count: Option<u64>,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<Vec<StreamEntry>> {
    tracing::info!(
        command = "stream_rev_range",
        conn_id = %conn_id,
        key = %key,
        start = %start,
        end = %end,
        count = ?count,
        "IPC call"
    );
    crate::services::stream::stream_rev_range(mgr.inner(), &conn_id, &key, &start, &end, count).await
}

/// XADD — add an entry to a stream
#[tauri::command]
pub async fn stream_add(
    conn_id: String,
    key: String,
    fields: Vec<(String, String)>,
    id: Option<String>,
    maxlen: Option<u64>,
    approx: Option<bool>,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<String> {
    tracing::info!(
        command = "stream_add",
        conn_id = %conn_id,
        key = %key,
        id = ?id,
        maxlen = ?maxlen,
        "IPC call"
    );
    crate::services::stream::stream_add(mgr.inner(), &conn_id, &key, fields, id.as_deref(), maxlen, approx.unwrap_or(false)).await
}

/// XDEL — delete entries from a stream
#[tauri::command]
pub async fn stream_del(
    conn_id: String,
    key: String,
    ids: Vec<String>,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<u64> {
    tracing::info!(
        command = "stream_del",
        conn_id = %conn_id,
        key = %key,
        ids = ?ids,
        "IPC call"
    );
    crate::services::stream::stream_del(mgr.inner(), &conn_id, &key, &ids).await
}

/// XINFO GROUPS — get consumer groups of a stream
#[tauri::command]
pub async fn stream_groups(
    conn_id: String,
    key: String,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<Vec<StreamGroup>> {
    tracing::info!(
        command = "stream_groups",
        conn_id = %conn_id,
        key = %key,
        "IPC call"
    );
    crate::services::stream::stream_groups(mgr.inner(), &conn_id, &key).await
}

/// XPENDING — get pending entries summary for a consumer group
#[tauri::command]
pub async fn stream_pending(
    conn_id: String,
    key: String,
    group: String,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<Vec<PendingEntry>> {
    tracing::info!(
        command = "stream_pending",
        conn_id = %conn_id,
        key = %key,
        group = %group,
        "IPC call"
    );
    crate::services::stream::stream_pending(mgr.inner(), &conn_id, &key, &group).await
}

/// XINFO STREAM — get stream metadata
#[tauri::command]
pub async fn stream_info(
    conn_id: String,
    key: String,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<StreamInfo> {
    tracing::info!(
        command = "stream_info",
        conn_id = %conn_id,
        key = %key,
        "IPC call"
    );
    crate::services::stream::stream_info(mgr.inner(), &conn_id, &key).await
}
