use sqlx::SqlitePool;
use tauri::State;
use uuid::Uuid;

use crate::error::{IpcError, IpcResult};
use crate::models::connection::ConnId;
use crate::services::cli_session_manager::{
    CliTabInfo, CliTabSession, SharedCliSessionManager,
};
use crate::services::connection_manager::SharedConnectionManager;
use crate::services::terminal::cli_exec as single_cli_exec;
use crate::models::terminal::CliReply;

const MAX_CLI_TABS: usize = 8;

/// Create a new CLI tab with an independent Redis connection.
#[tauri::command]
pub async fn cli_tab_create(
    conn_id: ConnId,
    manager: State<'_, SharedConnectionManager>,
    cli_manager: State<'_, SharedCliSessionManager>,
) -> IpcResult<CliTabInfo> {
    // Check tab limit
    {
        let cli_mgr = cli_manager.lock().await;
        if cli_mgr.tab_count() >= MAX_CLI_TABS {
            return Err(IpcError::InvalidArgument {
                field: "tab_count".to_string(),
                reason: format!("最多支持 {MAX_CLI_TABS} 个终端标签页"),
            });
        }
    }

    // Get a new dedicated connection
    let client = {
        let mgr = manager.lock().await;
        mgr.get_client(&conn_id).await?
    };
    let conn = client
        .get_multiplexed_async_connection()
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    let tab_id = Uuid::new_v4().to_string();
    let tab_count = {
        let cli_mgr = cli_manager.lock().await;
        cli_mgr.tab_count() + 1
    };
    let name = format!("终端 {}", tab_count);

    let tab = CliTabSession {
        tab_id: tab_id.clone(),
        name: name.clone(),
        conn,
        current_db: 0,
        is_connected: true,
        last_used: chrono::Utc::now().timestamp(),
        history: Vec::new(),
    };

    {
        let mut cli_mgr = cli_manager.lock().await;
        cli_mgr.add_tab(tab);
    }

    Ok(CliTabInfo { tab_id, name, db: 0, is_connected: true })
}

/// Close a CLI tab and release its Redis connection.
#[tauri::command]
pub async fn cli_tab_close(
    tab_id: String,
    cli_manager: State<'_, SharedCliSessionManager>,
) -> IpcResult<()> {
    let mut cli_mgr = cli_manager.lock().await;
    cli_mgr.remove_tab(&tab_id);
    Ok(())
}

/// Execute a command in a specific CLI tab.
#[tauri::command]
pub async fn cli_exec_tab(
    tab_id: String,
    raw_command: String,
    confirm_token: Option<String>,
    cli_manager: State<'_, SharedCliSessionManager>,
    db: State<'_, SqlitePool>,
) -> IpcResult<CliReply> {
    let tab = {
        let cli_mgr = cli_manager.lock().await;
        cli_mgr.get_tab(&tab_id)?
    };
    let mut guard = tab.lock().await;
    guard.last_used = chrono::Utc::now().timestamp();

    let reply = single_cli_exec(
        &mut guard.conn,
        &db,
        &raw_command,
        confirm_token.as_deref(),
    ).await?;

    // Persist command to SQLite with tab_id for multi-tab history
    let now = chrono::Utc::now().to_rfc3339();
    let _ = sqlx::query(
        "INSERT INTO cli_history (command, created_at, tab_id) VALUES (?, ?, ?)"
    )
    .bind(&raw_command)
    .bind(&now)
    .bind(&tab_id)
    .execute(db.inner())
    .await;

    // Trim per-tab history to 200 entries
    let _ = sqlx::query(
        "DELETE FROM cli_history WHERE tab_id = ? AND id NOT IN \
         (SELECT id FROM cli_history WHERE tab_id = ? ORDER BY id DESC LIMIT 200)"
    )
    .bind(&tab_id)
    .bind(&tab_id)
    .execute(db.inner())
    .await;

    Ok(reply)
}

/// Get command history for a specific CLI tab (from SQLite, persistent).
#[tauri::command]
pub async fn cli_history_get_tab(
    tab_id: String,
    db: State<'_, SqlitePool>,
    _cli_manager: State<'_, SharedCliSessionManager>,
) -> IpcResult<Vec<String>> {
    let rows = sqlx::query_as::<_, (String,)>(
        "SELECT command FROM cli_history WHERE tab_id = ? ORDER BY id DESC LIMIT 200"
    )
    .bind(&tab_id)
    .fetch_all(db.inner())
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })?;
    Ok(rows.into_iter().map(|(cmd,)| cmd).collect())
}
