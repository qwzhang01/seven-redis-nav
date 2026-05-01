use crate::error::IpcResult;
use crate::services::connection_manager::SharedConnectionManager;
use crate::services::monitor::SharedMonitorManager;
use tauri::{AppHandle, State};

#[tauri::command]
pub async fn monitor_start(
    app_handle: AppHandle,
    conn_id: String,
    mgr: State<'_, SharedConnectionManager>,
    monitor_mgr: State<'_, SharedMonitorManager>,
) -> IpcResult<()> {
    tracing::info!(command = "monitor_start", conn_id = %conn_id, "IPC call");
    crate::services::monitor::start(
        app_handle,
        mgr.inner().clone(),
        monitor_mgr.inner().clone(),
        &conn_id,
    )
    .await
}

#[tauri::command]
pub async fn monitor_stop(
    monitor_mgr: State<'_, SharedMonitorManager>,
) -> IpcResult<()> {
    tracing::info!(command = "monitor_stop", "IPC call");
    crate::services::monitor::stop(monitor_mgr.inner().clone()).await
}

#[tauri::command]
pub async fn monitor_metrics_start(
    app_handle: AppHandle,
    conn_id: String,
    interval_ms: u64,
    mgr: State<'_, SharedConnectionManager>,
    monitor_mgr: State<'_, SharedMonitorManager>,
) -> IpcResult<String> {
    tracing::info!(command = "monitor_metrics_start", conn_id = %conn_id, interval_ms, "IPC call");
    crate::services::monitor::metrics_start(
        app_handle,
        mgr.inner().clone(),
        monitor_mgr.inner().clone(),
        &conn_id,
        interval_ms,
    )
    .await
}

#[tauri::command]
pub async fn monitor_metrics_stop(
    monitor_mgr: State<'_, SharedMonitorManager>,
) -> IpcResult<()> {
    tracing::info!(command = "monitor_metrics_stop", "IPC call");
    crate::services::monitor::metrics_stop(monitor_mgr.inner().clone()).await
}
