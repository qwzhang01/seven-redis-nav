use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;
use redis::Client;
use tauri::{AppHandle, Emitter};

use crate::models::phase2::{MonitorCommand, MetricsSnapshot, MetricsServerInfo, DbKeyspace, ClientEntry};
use crate::services::connection_manager::SharedConnectionManager;
use crate::error::IpcResult;

/// Manages a Monitor session for a connection.
pub struct MonitorManager {
    /// Whether monitor is currently active
    active: bool,
    /// Cancel token to stop the monitor task
    cancel_tx: Option<tokio::sync::oneshot::Sender<()>>,
    /// Cancel token to stop the metrics sampling task
    metrics_cancel_tx: Option<tokio::sync::oneshot::Sender<()>>,
}

impl MonitorManager {
    pub fn new() -> Self {
        Self {
            active: false,
            cancel_tx: None,
            metrics_cancel_tx: None,
        }
    }

    #[allow(dead_code)]
    pub fn is_active(&self) -> bool {
        self.active
    }
}

/// Thread-safe wrapper
pub type SharedMonitorManager = Arc<Mutex<MonitorManager>>;

pub fn new_shared_monitor_manager() -> SharedMonitorManager {
    Arc::new(Mutex::new(MonitorManager::new()))
}

/// Start a MONITOR session
pub async fn start(
    app_handle: AppHandle,
    mgr: SharedConnectionManager,
    monitor_mgr: SharedMonitorManager,
    conn_id: &str,
) -> IpcResult<()> {
    let client = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_client(conn_id).await?
    };

    let mut mm = monitor_mgr.lock().await;

    // If already active, stop the old session
    if mm.active {
        if let Some(tx) = mm.cancel_tx.take() {
            let _ = tx.send(());
        }
    }

    let (cancel_tx, cancel_rx) = tokio::sync::oneshot::channel::<()>();
    mm.active = true;
    mm.cancel_tx = Some(cancel_tx);
    drop(mm);

    // Spawn the monitor listener task
    let app = app_handle.clone();
    let monitor_mgr_clone = monitor_mgr.clone();
    tauri::async_runtime::spawn(async move {
        if let Err(e) = run_monitor_listener(app, client, cancel_rx).await {
            tracing::error!("Monitor listener error: {}", e);
        }
        // Mark as inactive when done
        let mut mm = monitor_mgr_clone.lock().await;
        mm.active = false;
        mm.cancel_tx = None;
    });

    Ok(())
}

/// Stop the MONITOR session
pub async fn stop(monitor_mgr: SharedMonitorManager) -> IpcResult<()> {
    let mut mm = monitor_mgr.lock().await;
    if let Some(tx) = mm.cancel_tx.take() {
        let _ = tx.send(());
    }
    mm.active = false;
    Ok(())
}

/// Internal: run the MONITOR listener loop
async fn run_monitor_listener(
    app: AppHandle,
    client: Client,
    cancel_rx: tokio::sync::oneshot::Receiver<()>,
) -> Result<(), String> {
    use futures_util::StreamExt;

    // Get a dedicated Monitor connection
    let mut monitor = client.get_async_monitor().await.map_err(|e| e.to_string())?;

    // Start MONITOR mode
    monitor.monitor().await.map_err(|e| e.to_string())?;

    // Get the stream of monitor events (each item is a String)
    let mut stream = monitor.into_on_message::<String>();
    let mut cancel = cancel_rx;

    loop {
        tokio::select! {
            item = stream.next() => {
                match item {
                    Some(raw) => {
                        let parsed = parse_monitor_line(&raw);
                        if let Err(e) = app.emit("monitor:command", &parsed) {
                            tracing::warn!("Failed to emit monitor:command: {}", e);
                        }
                    }
                    None => break,
                }
            }
            _ = &mut cancel => {
                break;
            }
        }
    }

    Ok(())
}

/// Parse a MONITOR output line into a MonitorCommand (pub for testing)
pub(crate) fn parse_monitor_line(line: &str) -> MonitorCommand {
    // Format: "1619123456.789012 [0 127.0.0.1:6379] \"SET\" \"key\" \"value\""
    let mut timestamp = 0.0f64;
    let mut db: u8 = 0;
    let mut client = String::new();
    let mut command = String::new();
    let mut args: Vec<String> = Vec::new();

    // Try to parse timestamp
    if let Some(space_idx) = line.find(' ') {
        if let Ok(ts) = line[..space_idx].parse::<f64>() {
            timestamp = ts;
        }

        let rest = &line[space_idx + 1..];

        // Parse [db client]
        if let (Some(bracket_start), Some(bracket_end)) = (rest.find('['), rest.find(']')) {
            let bracket_content = &rest[bracket_start + 1..bracket_end];
            let parts: Vec<&str> = bracket_content.splitn(2, ' ').collect();
            if parts.len() >= 1 {
                db = parts[0].parse().unwrap_or(0);
            }
            if parts.len() >= 2 {
                client = parts[1].to_string();
            }

            // Parse command and args after the bracket using a proper
            // tokenizer that handles escaped quotes (fix 2.5).
            let cmd_part = &rest[bracket_end + 2..]; // skip "] "
            let tokens = tokenize_quoted(cmd_part);

            if !tokens.is_empty() {
                command = tokens[0].clone();
                args = tokens[1..].to_vec();
            }
        }
    }

    MonitorCommand {
        timestamp,
        client,
        db,
        command,
        args,
    }
}

/// Tokenize a string of double-quoted arguments, respecting `\"` and `\\`
/// escape sequences inside quotes.
///
/// Example input:  `"SET" "mykey" "value with \"quotes\""`
/// Produces:       `["SET", "mykey", "value with \"quotes\""]`
fn tokenize_quoted(input: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut chars = input.chars().peekable();
    let mut current = String::new();
    let mut in_quotes = false;

    while let Some(ch) = chars.next() {
        if in_quotes {
            match ch {
                '\\' => {
                    // Consume the escaped character (e.g. \" or \\)
                    if let Some(escaped) = chars.next() {
                        current.push('\\');
                        current.push(escaped);
                    }
                }
                '"' => {
                    // End of quoted token
                    tokens.push(std::mem::take(&mut current));
                    in_quotes = false;
                }
                _ => {
                    current.push(ch);
                }
            }
        } else {
            match ch {
                '"' => {
                    in_quotes = true;
                }
                ' ' | '\t' => {
                    // Whitespace between tokens; ignore
                }
                _ => {
                    // Unquoted token (unlikely in MONITOR output but handle)
                    current.push(ch);
                    // Consume until whitespace
                    while let Some(&next) = chars.peek() {
                        if next.is_whitespace() {
                            break;
                        }
                        current.push(chars.next().unwrap());
                    }
                    tokens.push(std::mem::take(&mut current));
                }
            }
        }
    }

    // If we ended mid-quote, push whatever we have
    if !current.is_empty() {
        tokens.push(current);
    }

    tokens
}

/// Start periodic metrics sampling
pub async fn metrics_start(
    app_handle: AppHandle,
    mgr: SharedConnectionManager,
    monitor_mgr: SharedMonitorManager,
    conn_id: &str,
    interval_ms: u64,
) -> IpcResult<String> {
    let client = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_client(conn_id).await?
    };

    let mut mm = monitor_mgr.lock().await;

    // If metrics sampling is already active, stop the old task
    if let Some(tx) = mm.metrics_cancel_tx.take() {
        let _ = tx.send(());
    }

    let task_id = format!("metrics-{}", uuid::Uuid::new_v4());
    let (cancel_tx, cancel_rx) = tokio::sync::oneshot::channel::<()>();
    mm.metrics_cancel_tx = Some(cancel_tx);
    drop(mm);

    let app = app_handle.clone();
    let monitor_mgr_clone = monitor_mgr.clone();
    let task_id_clone = task_id.clone();
    tauri::async_runtime::spawn(async move {
        if let Err(e) = run_metrics_sampler(app, client, cancel_rx, interval_ms).await {
            tracing::error!("Metrics sampler error: {}", e);
        }
        // Clean up cancel token when done
        let mut mm = monitor_mgr_clone.lock().await;
        mm.metrics_cancel_tx = None;
    });

    Ok(task_id_clone)
}

/// Stop the metrics sampling task
pub async fn metrics_stop(monitor_mgr: SharedMonitorManager) -> IpcResult<()> {
    let mut mm = monitor_mgr.lock().await;
    if let Some(tx) = mm.metrics_cancel_tx.take() {
        let _ = tx.send(());
    }
    Ok(())
}

/// Internal: run the periodic metrics sampler
async fn run_metrics_sampler(
    app: AppHandle,
    client: Client,
    cancel_rx: tokio::sync::oneshot::Receiver<()>,
    interval_ms: u64,
) -> Result<(), String> {
    let mut cancel = cancel_rx;
    let interval = std::time::Duration::from_millis(interval_ms);

    loop {
        let start = std::time::Instant::now();

        match sample_metrics(&client).await {
            Ok(snapshot) => {
                if let Err(e) = app.emit("monitor:metrics", &snapshot) {
                    tracing::warn!("Failed to emit monitor:metrics: {}", e);
                }
            }
            Err(e) => {
                tracing::warn!("Metrics sampling failed: {}", e);
            }
        }

        let elapsed = start.elapsed();
        let sleep = interval.saturating_sub(elapsed);

        tokio::select! {
            _ = tokio::time::sleep(sleep) => {},
            _ = &mut cancel => {
                break;
            }
        }
    }

    Ok(())
}

/// Sample metrics from Redis via INFO all + CLIENT LIST
async fn sample_metrics(client: &Client) -> Result<MetricsSnapshot, String> {
    let mut conn = client
        .get_multiplexed_async_connection()
        .await
        .map_err(|e| e.to_string())?;

    // Execute INFO all
    let info_all: String = redis::cmd("INFO")
        .arg("all")
        .query_async(&mut conn)
        .await
        .map_err(|e| e.to_string())?;

    // Execute CLIENT LIST
    let client_list: String = redis::cmd("CLIENT")
        .arg("LIST")
        .query_async(&mut conn)
        .await
        .map_err(|e| e.to_string())?;

    parse_metrics_snapshot(&info_all, &client_list)
}

/// Parse INFO all + CLIENT LIST output into MetricsSnapshot
fn parse_metrics_snapshot(info: &str, client_list: &str) -> Result<MetricsSnapshot, String> {
    let sections = parse_info_sections(info);

    let ops_per_sec = sections.get("instantaneous_ops_per_sec")
        .and_then(|v| v.parse::<f64>().ok())
        .unwrap_or(0.0);

    let used_memory_bytes = sections.get("used_memory")
        .and_then(|v| v.parse::<u64>().ok())
        .unwrap_or(0);

    let connected_clients = sections.get("connected_clients")
        .and_then(|v| v.parse::<u64>().ok())
        .unwrap_or(0);

    let keyspace_hits = sections.get("keyspace_hits")
        .and_then(|v| v.parse::<u64>().ok())
        .unwrap_or(0);

    let keyspace_misses = sections.get("keyspace_misses")
        .and_then(|v| v.parse::<u64>().ok())
        .unwrap_or(0);

    let server_info = MetricsServerInfo {
        redis_version: sections.get("redis_version")
            .cloned()
            .unwrap_or_default(),
        os: sections.get("os")
            .cloned()
            .unwrap_or_default(),
        process_id: sections.get("process_id")
            .and_then(|v| v.parse::<u64>().ok())
            .unwrap_or(0),
        tcp_port: sections.get("tcp_port")
            .and_then(|v| v.parse::<u64>().ok())
            .unwrap_or(6379),
        uptime_secs: sections.get("uptime_in_seconds")
            .and_then(|v| v.parse::<u64>().ok())
            .unwrap_or(0),
        role: sections.get("role")
            .cloned()
            .unwrap_or_else(|| "master".to_string()),
        connected_slaves: sections.get("connected_slaves")
            .and_then(|v| v.parse::<u64>().ok())
            .unwrap_or(0),
        aof_enabled: sections.get("aof_enabled")
            .and_then(|v| v.parse::<u64>().ok())
            .map(|v| v == 1)
            .unwrap_or(false),
        last_rdb_save_ts: sections.get("rdb_last_save_timestamp")
            .and_then(|v| v.parse::<i64>().ok())
            .unwrap_or(0),
    };

    // Parse keyspace
    let keyspace = parse_keyspace(&sections);

    // Parse client list
    let clients = parse_client_list(client_list);

    let timestamp = chrono::Utc::now().to_rfc3339();

    Ok(MetricsSnapshot {
        ops_per_sec,
        used_memory_bytes,
        connected_clients,
        keyspace_hits,
        keyspace_misses,
        server_info,
        keyspace,
        clients,
        timestamp,
    })
}

/// Parse INFO output into a flat key-value map
fn parse_info_sections(info: &str) -> HashMap<String, String> {
    let mut map = HashMap::new();
    for line in info.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        if let Some((key, value)) = line.split_once(':') {
            map.insert(key.to_string(), value.to_string());
        }
    }
    map
}

/// Parse keyspace info (db0:keys=100,expires=20,avg_ttl=300000)
fn parse_keyspace(sections: &HashMap<String, String>) -> Vec<DbKeyspace> {
    let mut result = Vec::new();

    for (key, value) in sections {
        if !key.starts_with("db") {
            continue;
        }
        let db_idx: u64 = key[2..].parse().unwrap_or(0);

        // Parse: keys=100,expires=20,avg_ttl=300000
        let mut keys = 0u64;
        let mut expires = 0u64;
        let mut avg_ttl = 0.0f64;

        for part in value.split(',') {
            if let Some((k, v)) = part.split_once('=') {
                match k {
                    "keys" => keys = v.parse().unwrap_or(0),
                    "expires" => expires = v.parse().unwrap_or(0),
                    "avg_ttl" => avg_ttl = v.parse().unwrap_or(0.0),
                    _ => {}
                }
            }
        }

        // avg_ttl is in milliseconds, convert to seconds
        let avg_ttl_secs = avg_ttl / 1000.0;

        result.push(DbKeyspace {
            db: db_idx,
            keys,
            expires,
            avg_ttl_secs,
        });
    }

    result.sort_by_key(|k| k.db);
    result
}

/// Parse CLIENT LIST output
fn parse_client_list(raw: &str) -> Vec<ClientEntry> {
    let mut entries = Vec::new();

    for line in raw.lines().take(10) {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }

        let mut id = 0u64;
        let mut addr = String::new();
        let mut name = String::new();
        let mut cmd = String::new();
        let mut age_secs = 0u64;
        let mut db = 0u64;

        for field in line.split(' ') {
            if let Some((k, v)) = field.split_once('=') {
                match k {
                    "id" => id = v.parse().unwrap_or(0),
                    "addr" => addr = v.to_string(),
                    "name" => name = v.to_string(),
                    "cmd" => cmd = v.to_string(),
                    "age" => age_secs = v.parse().unwrap_or(0),
                    "db" => db = v.parse().unwrap_or(0),
                    _ => {}
                }
            }
        }

        entries.push(ClientEntry {
            id,
            addr,
            name,
            cmd,
            age_secs,
            db,
        });
    }

    entries
}

#[cfg(test)]
mod tests {
    use super::*;

    // ===== MonitorManager state tests =====

    #[test]
    fn test_new_monitor_manager_is_inactive() {
        let mm = MonitorManager::new();
        assert!(!mm.is_active());
        assert!(mm.cancel_tx.is_none());
    }

    #[test]
    fn test_monitor_manager_active_state() {
        let mut mm = MonitorManager::new();
        mm.active = true;
        assert!(mm.is_active());
    }

    // ===== parse_monitor_line tests =====

    #[test]
    fn test_parse_standard_set_command() {
        let line = r#"1619123456.789012 [0 127.0.0.1:6379] "SET" "mykey" "myvalue""#;
        let cmd = parse_monitor_line(line);

        assert!((cmd.timestamp - 1619123456.789012).abs() < 0.001);
        assert_eq!(cmd.db, 0);
        assert_eq!(cmd.client, "127.0.0.1:6379");
        assert_eq!(cmd.command, "SET");
        assert_eq!(cmd.args, vec!["mykey", "myvalue"]);
    }

    #[test]
    fn test_parse_get_command() {
        let line = r#"1619123456.000000 [0 127.0.0.1:6379] "GET" "foo""#;
        let cmd = parse_monitor_line(line);

        assert_eq!(cmd.command, "GET");
        assert_eq!(cmd.args, vec!["foo"]);
        assert_eq!(cmd.db, 0);
    }

    #[test]
    fn test_parse_different_db() {
        let line = r#"1619123456.000000 [3 10.0.0.1:12345] "HGET" "hash" "field""#;
        let cmd = parse_monitor_line(line);

        assert_eq!(cmd.db, 3);
        assert_eq!(cmd.client, "10.0.0.1:12345");
        assert_eq!(cmd.command, "HGET");
        assert_eq!(cmd.args, vec!["hash", "field"]);
    }

    #[test]
    fn test_parse_command_no_args() {
        let line = r#"1619123456.000000 [0 127.0.0.1:6379] "PING""#;
        let cmd = parse_monitor_line(line);

        assert_eq!(cmd.command, "PING");
        assert!(cmd.args.is_empty());
    }

    #[test]
    fn test_parse_empty_line() {
        let cmd = parse_monitor_line("");
        assert_eq!(cmd.timestamp, 0.0);
        assert_eq!(cmd.command, "");
        assert!(cmd.args.is_empty());
    }

    #[test]
    fn test_parse_malformed_line_no_brackets() {
        let line = "1619123456.000000 some random text";
        let cmd = parse_monitor_line(line);
        // Should not panic, just return defaults for unparseable parts
        assert!((cmd.timestamp - 1619123456.0).abs() < 0.001);
    }

    #[test]
    fn test_parse_multi_arg_command() {
        let line = r#"1619123456.000000 [0 127.0.0.1:6379] "MSET" "k1" "v1" "k2" "v2""#;
        let cmd = parse_monitor_line(line);

        assert_eq!(cmd.command, "MSET");
        assert_eq!(cmd.args, vec!["k1", "v1", "k2", "v2"]);
    }

    #[test]
    fn test_parse_command_with_escaped_quotes() {
        // Fix 2.5: value containing escaped double-quotes should not be split
        let line = r#"1619123456.000000 [0 127.0.0.1:6379] "SET" "key" "value with \"quotes\"""#;
        let cmd = parse_monitor_line(line);

        assert_eq!(cmd.command, "SET");
        assert_eq!(cmd.args[0], "key");
        assert!(cmd.args[1].contains("quotes"), "Expected escaped quotes preserved in: {}", cmd.args[1]);
    }

    // ===== tokenize_quoted tests =====

    #[test]
    fn test_tokenize_simple() {
        let tokens = tokenize_quoted(r#""SET" "key" "value""#);
        assert_eq!(tokens, vec!["SET", "key", "value"]);
    }

    #[test]
    fn test_tokenize_escaped_quotes() {
        let tokens = tokenize_quoted(r#""SET" "k" "v\"with\"quotes""#);
        assert_eq!(tokens.len(), 3);
        assert_eq!(tokens[0], "SET");
        assert!(tokens[2].contains("quotes"));
    }

    #[test]
    fn test_tokenize_empty() {
        let tokens = tokenize_quoted("");
        assert!(tokens.is_empty());
    }

    // ===== SharedMonitorManager tests =====

    #[test]
    fn test_new_shared_monitor_manager() {
        let mgr = new_shared_monitor_manager();
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let mm = mgr.lock().await;
            assert!(!mm.is_active());
        });
    }
}
