use std::time::Duration;
use tauri::{AppHandle, Emitter};
use crate::services::connection_manager::SharedConnectionManager;
use crate::models::connection::ConnectionState;

/// Start heartbeat task: PING all active sessions every 30s
pub fn start_heartbeat(app: AppHandle, manager: SharedConnectionManager) {
    tauri::async_runtime::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(30));
        loop {
            interval.tick().await;
            let mgr = manager.lock().await;
            let ids = mgr.active_sessions();
            // Collect SharedSession handles, then drop the manager lock
            let sessions: Vec<_> = ids
                .iter()
                .filter_map(|id| mgr.get_session(id).ok().map(|s| (id.clone(), s)))
                .collect();
            drop(mgr);

            for (id, session) in sessions {
                let mut guard = match session.try_lock() {
                    Ok(g) => g,
                    Err(_) => {
                        tracing::debug!(conn_id = %id, "Session locked, skipping heartbeat PING");
                        continue;
                    }
                };

                let result = redis::cmd("PING")
                    .query_async::<String>(&mut guard.conn)
                    .await;

                let state = match result {
                    Ok(_) => ConnectionState::Connected,
                    Err(_) => ConnectionState::Disconnected,

                };

                // Emit connection:state event to frontend
                let _ = app.emit("connection:state", serde_json::json!({
                    "conn_id": id,
                    "state": state,
                }));

                if state == ConnectionState::Disconnected {
                    tracing::warn!(conn_id = %id, "Heartbeat PING failed, connection lost");
                }
            }
        }
    });
}
