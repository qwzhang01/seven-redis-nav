use std::collections::HashSet;
use std::sync::Arc;
use tokio::sync::Mutex;
use redis::Client;
use tauri::{AppHandle, Emitter};
use futures_util::StreamExt;

use crate::models::phase2::PubSubMessage;
use crate::services::connection_manager::SharedConnectionManager;
use crate::error::IpcResult;

/// Manages Pub/Sub subscriptions for a connection.
/// Each connection can have at most one PubSub session.
pub struct PubSubManager {
    /// Active subscription channels
    channels: HashSet<String>,
    /// Active subscription patterns
    patterns: HashSet<String>,
    /// Cancel token to stop the listener task
    cancel_tx: Option<tokio::sync::oneshot::Sender<()>>,
}

impl PubSubManager {
    pub fn new() -> Self {
        Self {
            channels: HashSet::new(),
            patterns: HashSet::new(),
            cancel_tx: None,
        }
    }

    pub fn is_active(&self) -> bool {
        self.cancel_tx.is_some()
    }

    #[allow(dead_code)]
    pub fn active_channels(&self) -> Vec<String> {
        self.channels.iter().cloned().collect()
    }

    #[allow(dead_code)]
    pub fn active_patterns(&self) -> Vec<String> {
        self.patterns.iter().cloned().collect()
    }
}

/// Thread-safe wrapper
pub type SharedPubSubManager = Arc<Mutex<PubSubManager>>;

pub fn new_shared_pubsub_manager() -> SharedPubSubManager {
    Arc::new(Mutex::new(PubSubManager::new()))
}

/// Subscribe to channels or patterns and start streaming messages as Tauri events.
pub async fn subscribe(
    app_handle: AppHandle,
    mgr: SharedConnectionManager,
    pubsub_mgr: SharedPubSubManager,
    conn_id: &str,
    channels: Vec<String>,
    pattern: bool,
) -> IpcResult<()> {
    let client = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_client(conn_id).await?
    };

    let mut psm = pubsub_mgr.lock().await;

    // If already active, we need to stop the old session first
    if psm.is_active() {
        if let Some(tx) = psm.cancel_tx.take() {
            let _ = tx.send(());
        }
    }

    // Track subscriptions
    if pattern {
        for ch in &channels {
            psm.patterns.insert(ch.clone());
        }
    } else {
        for ch in &channels {
            psm.channels.insert(ch.clone());
        }
    }

    // Collect all subscriptions for the new session
    let all_channels: Vec<String> = psm.channels.iter().cloned().collect();
    let all_patterns: Vec<String> = psm.patterns.iter().cloned().collect();

    let (cancel_tx, cancel_rx) = tokio::sync::oneshot::channel::<()>();
    psm.cancel_tx = Some(cancel_tx);
    drop(psm);

    // Spawn the listener task
    let app = app_handle.clone();
    tauri::async_runtime::spawn(async move {
        if let Err(e) = run_pubsub_listener(app, client, all_channels, all_patterns, cancel_rx).await {
            tracing::error!("PubSub listener error: {}", e);
        }
    });

    Ok(())
}

/// Unsubscribe from channels or patterns.
pub async fn unsubscribe(
    pubsub_mgr: SharedPubSubManager,
    channels: Vec<String>,
    pattern: bool,
) -> IpcResult<()> {
    let mut psm = pubsub_mgr.lock().await;

    if pattern {
        for ch in &channels {
            psm.patterns.remove(ch);
        }
    } else {
        for ch in &channels {
            psm.channels.remove(ch);
        }
    }

    // If no subscriptions remain, stop the listener
    if psm.channels.is_empty() && psm.patterns.is_empty() {
        if let Some(tx) = psm.cancel_tx.take() {
            let _ = tx.send(());
        }
    }

    Ok(())
}

/// PUBLISH — send a message to a channel, returns the number of subscribers that received it
pub async fn publish(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    channel: &str,
    message: &str,
) -> IpcResult<u64> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let receivers: u64 = redis::cmd("PUBLISH")
        .arg(channel)
        .arg(message)
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| crate::error::IpcError::Redis { message: e.to_string() })?;

    Ok(receivers)
}

/// Internal: run the PubSub listener loop
async fn run_pubsub_listener(
    app: AppHandle,
    client: Client,
    channels: Vec<String>,
    patterns: Vec<String>,
    cancel_rx: tokio::sync::oneshot::Receiver<()>,
) -> Result<(), String> {
    // Get a dedicated PubSub connection (auth is handled by the client URL)
    let mut pubsub = client.get_async_pubsub().await.map_err(|e| e.to_string())?;

    // Subscribe to channels
    for ch in &channels {
        pubsub.subscribe(ch).await.map_err(|e| e.to_string())?;
    }

    // Subscribe to patterns
    for pat in &patterns {
        pubsub.psubscribe(pat).await.map_err(|e| e.to_string())?;
    }

    let mut stream = pubsub.on_message();
    let mut cancel = cancel_rx;

    loop {
        tokio::select! {
            msg = stream.next() => {
                match msg {
                    Some(msg) => {
                        let channel: String = msg.get_channel_name().to_string();
                        let payload: String = msg.get_payload().unwrap_or_default();
                        let pattern: Option<String> = msg.get_pattern().ok();
                        let timestamp = chrono::Utc::now().to_rfc3339();

                        let event = PubSubMessage {
                            channel,
                            pattern,
                            message: payload,
                            timestamp,
                        };

                        if let Err(e) = app.emit("pubsub:message", &event) {
                            tracing::warn!("Failed to emit pubsub:message: {}", e);
                        }
                    }
                    None => {
                        // Stream ended (connection closed)
                        break;
                    }
                }
            }
            _ = &mut cancel => {
                // Cancelled by user
                break;
            }
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    // ===== PubSubManager state tests =====

    #[test]
    fn test_new_pubsub_manager_is_inactive() {
        let psm = PubSubManager::new();
        assert!(!psm.is_active());
        assert!(psm.channels.is_empty());
        assert!(psm.patterns.is_empty());
    }

    #[test]
    fn test_active_channels_empty() {
        let psm = PubSubManager::new();
        assert!(psm.active_channels().is_empty());
    }

    #[test]
    fn test_active_patterns_empty() {
        let psm = PubSubManager::new();
        assert!(psm.active_patterns().is_empty());
    }

    #[test]
    fn test_channels_tracking() {
        let mut psm = PubSubManager::new();
        psm.channels.insert("ch1".to_string());
        psm.channels.insert("ch2".to_string());

        let channels = psm.active_channels();
        assert_eq!(channels.len(), 2);
        assert!(channels.contains(&"ch1".to_string()));
        assert!(channels.contains(&"ch2".to_string()));
    }

    #[test]
    fn test_patterns_tracking() {
        let mut psm = PubSubManager::new();
        psm.patterns.insert("news.*".to_string());
        psm.patterns.insert("events.*".to_string());

        let patterns = psm.active_patterns();
        assert_eq!(patterns.len(), 2);
        assert!(patterns.contains(&"news.*".to_string()));
        assert!(patterns.contains(&"events.*".to_string()));
    }

    #[test]
    fn test_is_active_with_cancel_tx() {
        let mut psm = PubSubManager::new();
        assert!(!psm.is_active());

        let (tx, _rx) = tokio::sync::oneshot::channel::<()>();
        psm.cancel_tx = Some(tx);
        assert!(psm.is_active());
    }

    #[test]
    fn test_channel_dedup() {
        let mut psm = PubSubManager::new();
        psm.channels.insert("ch1".to_string());
        psm.channels.insert("ch1".to_string()); // duplicate
        assert_eq!(psm.channels.len(), 1);
    }

    #[test]
    fn test_channel_removal() {
        let mut psm = PubSubManager::new();
        psm.channels.insert("ch1".to_string());
        psm.channels.insert("ch2".to_string());
        psm.channels.remove("ch1");
        assert_eq!(psm.channels.len(), 1);
        assert!(!psm.channels.contains("ch1"));
        assert!(psm.channels.contains("ch2"));
    }

    #[test]
    fn test_pattern_removal() {
        let mut psm = PubSubManager::new();
        psm.patterns.insert("news.*".to_string());
        psm.patterns.insert("events.*".to_string());
        psm.patterns.remove("news.*");
        assert_eq!(psm.patterns.len(), 1);
        assert!(!psm.patterns.contains("news.*"));
    }

    // ===== SharedPubSubManager tests =====

    #[test]
    fn test_new_shared_pubsub_manager() {
        let mgr = new_shared_pubsub_manager();
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let psm = mgr.lock().await;
            assert!(!psm.is_active());
            assert!(psm.channels.is_empty());
        });
    }

    // ===== Unsubscribe logic tests =====

    #[tokio::test]
    async fn test_unsubscribe_removes_channels() {
        let psm = new_shared_pubsub_manager();
        {
            let mut lock = psm.lock().await;
            lock.channels.insert("ch1".to_string());
            lock.channels.insert("ch2".to_string());
            lock.channels.insert("ch3".to_string());
        }

        unsubscribe(psm.clone(), vec!["ch1".to_string(), "ch2".to_string()], false)
            .await
            .unwrap();

        let lock = psm.lock().await;
        assert_eq!(lock.channels.len(), 1);
        assert!(lock.channels.contains("ch3"));
    }

    #[tokio::test]
    async fn test_unsubscribe_removes_patterns() {
        let psm = new_shared_pubsub_manager();
        {
            let mut lock = psm.lock().await;
            lock.patterns.insert("news.*".to_string());
            lock.patterns.insert("events.*".to_string());
        }

        unsubscribe(psm.clone(), vec!["news.*".to_string()], true)
            .await
            .unwrap();

        let lock = psm.lock().await;
        assert_eq!(lock.patterns.len(), 1);
        assert!(lock.patterns.contains("events.*"));
    }

    #[tokio::test]
    async fn test_unsubscribe_all_stops_listener() {
        let psm = new_shared_pubsub_manager();
        {
            let mut lock = psm.lock().await;
            lock.channels.insert("ch1".to_string());
            let (tx, _rx) = tokio::sync::oneshot::channel::<()>();
            lock.cancel_tx = Some(tx);
        }

        unsubscribe(psm.clone(), vec!["ch1".to_string()], false)
            .await
            .unwrap();

        let lock = psm.lock().await;
        assert!(lock.channels.is_empty());
        assert!(!lock.is_active()); // cancel_tx should be taken
    }
}
