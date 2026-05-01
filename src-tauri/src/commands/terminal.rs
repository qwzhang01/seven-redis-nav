use tauri::State;
use sqlx::SqlitePool;
use crate::error::IpcResult;
use crate::models::connection::ConnId;
use crate::models::terminal::{CliHistoryEntry, CliReply};
use crate::services;
use crate::services::connection_manager::SharedConnectionManager;

/// Execute a CLI command
#[tauri::command]
pub async fn cli_exec(
    conn_id: ConnId,
    command: String,
    confirm_token: Option<String>,
    manager: State<'_, SharedConnectionManager>,
    db: State<'_, SqlitePool>,
) -> IpcResult<CliReply> {
    tracing::info!(command = "cli_exec", conn_id = %conn_id, cmd = %command, "IPC call");

    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;
    services::terminal::cli_exec(&mut guard.conn, db.inner(), &command, confirm_token.as_deref()).await
}

/// Get CLI history
#[tauri::command]
pub async fn cli_history_get(
    db: State<'_, SqlitePool>,
) -> IpcResult<Vec<CliHistoryEntry>> {
    tracing::info!(command = "cli_history_get", "IPC call");
    services::terminal::cli_history_get(db.inner()).await
}
