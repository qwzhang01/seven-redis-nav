use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;
use chrono::Utc;

use crate::error::{IpcError, IpcResult};

/// State for a single CLI tab session.
pub struct CliTabSession {
    pub tab_id: String,
    pub name: String,
    pub conn: redis::aio::MultiplexedConnection,
    pub current_db: u8,
    pub is_connected: bool,
    pub last_used: i64,
    pub history: Vec<String>,
}

/// Thread-safe handle to a CLI tab session.
pub type SharedCliTab = Arc<Mutex<CliTabSession>>;

/// Manager for multiple CLI tab sessions.
pub struct CliSessionManager {
    tabs: HashMap<String, SharedCliTab>,
}

impl CliSessionManager {
    pub fn new() -> Self {
        Self { tabs: HashMap::new() }
    }

    pub fn add_tab(&mut self, tab: CliTabSession) -> String {
        let id = tab.tab_id.clone();
        self.tabs.insert(id.clone(), Arc::new(Mutex::new(tab)));
        id
    }

    pub fn get_tab(&self, tab_id: &str) -> IpcResult<SharedCliTab> {
        self.tabs.get(tab_id)
            .cloned()
        .ok_or_else(|| IpcError::NotFound { key: format!("CLI tab {tab_id}") })
    }

    pub fn remove_tab(&mut self, tab_id: &str) -> bool {
        self.tabs.remove(tab_id).is_some()
    }

    pub fn tab_count(&self) -> usize {
        self.tabs.len()
    }

    pub fn tab_ids(&self) -> Vec<String> {
        self.tabs.keys().cloned().collect()
    }
}

pub type SharedCliSessionManager = Arc<Mutex<CliSessionManager>>;

pub fn new_shared_cli_session_manager() -> SharedCliSessionManager {
    Arc::new(Mutex::new(CliSessionManager::new()))
}

/// Idle timeout in seconds (30 minutes)
const IDLE_TIMEOUT_SECS: i64 = 30 * 60;

/// Collect tab IDs that have been idle for more than IDLE_TIMEOUT_SECS.
pub async fn collect_idle_tabs(manager: &SharedCliSessionManager) -> Vec<String> {
    let mgr = manager.lock().await;
    let now = Utc::now().timestamp();
    let mut idle = Vec::new();
    for (tab_id, tab_arc) in &mgr.tabs {
        let tab = tab_arc.lock().await;
        if tab.is_connected && (now - tab.last_used) > IDLE_TIMEOUT_SECS {
            idle.push(tab_id.clone());
        }
    }
    idle
}

/// Mark a tab as disconnected (without removing it).
pub async fn mark_tab_disconnected(manager: &SharedCliSessionManager, tab_id: &str) {
    let mgr = manager.lock().await;
    if let Some(tab_arc) = mgr.tabs.get(tab_id) {
        let mut tab = tab_arc.lock().await;
        tab.is_connected = false;
    }
}

/// Info about a CLI tab (returned to frontend).
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct CliTabInfo {
    pub tab_id: String,
    pub name: String,
    pub db: u8,
    pub is_connected: bool,
}
