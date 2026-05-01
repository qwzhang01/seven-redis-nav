use crate::error::IpcResult;
use crate::services::connection_manager::SharedConnectionManager;
use crate::services::pubsub::SharedPubSubManager;
use tauri::{AppHandle, State};

#[tauri::command]
pub async fn pubsub_subscribe(
    app_handle: AppHandle,
    conn_id: String,
    channels: Vec<String>,
    pattern: bool,
    mgr: State<'_, SharedConnectionManager>,
    pubsub_mgr: State<'_, SharedPubSubManager>,
) -> IpcResult<()> {
    tracing::info!(
        command = "pubsub_subscribe",
        conn_id = %conn_id,
        channels = ?channels,
        pattern = pattern,
        "IPC call"
    );
    crate::services::pubsub::subscribe(
        app_handle,
        mgr.inner().clone(),
        pubsub_mgr.inner().clone(),
        &conn_id,
        channels,
        pattern,
    )
    .await
}

#[tauri::command]
pub async fn pubsub_unsubscribe(
    conn_id: String,
    channels: Vec<String>,
    pattern: bool,
    pubsub_mgr: State<'_, SharedPubSubManager>,
) -> IpcResult<()> {
    tracing::info!(
        command = "pubsub_unsubscribe",
        conn_id = %conn_id,
        channels = ?channels,
        pattern = pattern,
        "IPC call"
    );
    crate::services::pubsub::unsubscribe(
        pubsub_mgr.inner().clone(),
        channels,
        pattern,
    )
    .await
}

/// PUBLISH — send a message to a channel
#[tauri::command]
pub async fn pubsub_publish(
    conn_id: String,
    channel: String,
    message: String,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<u64> {
    tracing::info!(
        command = "pubsub_publish",
        conn_id = %conn_id,
        channel = %channel,
        "IPC call"
    );
    crate::services::pubsub::publish(mgr.inner(), &conn_id, &channel, &message).await
}
