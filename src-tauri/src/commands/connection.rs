use crate::error::{IpcError, IpcResult};
use crate::models::connection::{
    ConnectionConfig, ConnectionMeta, ConnId, DbStat,
};
use crate::services;
use crate::services::connection_manager::SharedConnectionManager;
use sqlx::SqlitePool;
use tauri::{State};
use uuid::Uuid;
use chrono::Utc;

// ---- Phase 0: connection_test (kept) ----

use crate::models::connection::{ConnectionTestReq, PingResult};

#[tauri::command]
pub async fn connection_test(req: ConnectionTestReq) -> IpcResult<PingResult> {
    tracing::info!(
        command = "connection_test",
        host = %req.host,
        port = req.port,
        password = if req.password.is_some() { "***" } else { "(none)" },
        "IPC call"
    );
    services::connection::ping(&req).await
}

// ---- Phase 1: connection management ----

/// Open a Redis connection (create session)
#[tauri::command]
pub async fn connection_open(
    conn_id: ConnId,
    manager: State<'_, SharedConnectionManager>,
    db: State<'_, SqlitePool>,
) -> IpcResult<()> {
    tracing::info!(command = "connection_open", conn_id = %conn_id, "IPC call");

    // Load config from SQLite
    let meta = sqlx::query_as::<_, ConnectionMeta>(
        "SELECT * FROM connections WHERE id = ?",
    )
    .bind(&conn_id)
    .fetch_optional(db.inner())
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })?
    .ok_or_else(|| IpcError::NotFound { key: conn_id.clone() })?;

    // Load password from Keychain
    let password = if let Some(ref kk) = meta.keychain_key {
        crate::utils::keychain::get_password(kk)
            .map_err(|e| {
                // Distinguish user cancellation from real errors (fix 1.3).
                if e.contains("cancelled") {
                    IpcError::AuthCancelled
                } else {
                    IpcError::Internal { message: e }
                }
            })?
    } else {
        None
    };

    let config = ConnectionConfig {
        id: meta.id.clone(),
        name: meta.name.clone(),
        group_name: meta.group_name.clone(),
        host: meta.host.clone(),
        port: meta.port as u16,
        password,
        has_password: meta.keychain_key.is_some(),
        auth_db: meta.auth_db as u8,
        timeout_ms: meta.timeout_ms as u64,
        sort_order: meta.sort_order as i32,
        connection_type: meta.connection_type
            .as_deref()
            .and_then(|s| serde_json::from_str(&format!("\"{}\"", s)).ok())
            .unwrap_or_default(),
        ssh_config: meta.ssh_config
            .as_deref()
            .and_then(|s| serde_json::from_str(s).ok()),
        tls_config: meta.tls_config
            .as_deref()
            .and_then(|s| serde_json::from_str(s).ok()),
        sentinel_nodes: meta.sentinel_nodes
            .as_deref()
            .and_then(|s| serde_json::from_str(s).ok()),
        master_name: meta.master_name,
        cluster_nodes: meta.cluster_nodes
            .as_deref()
            .and_then(|s| serde_json::from_str(s).ok()),
    };

    let mut mgr = manager.lock().await;
    mgr.open(config).await
}

/// Close a Redis connection (remove session)
#[tauri::command]
pub async fn connection_close(
    conn_id: ConnId,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<()> {
    tracing::info!(command = "connection_close", conn_id = %conn_id, "IPC call");
    let mut mgr = manager.lock().await;
    mgr.close(&conn_id);
    Ok(())
}

/// Save a connection config to SQLite + Keychain
#[tauri::command]
pub async fn connection_save(
    config: ConnectionConfig,
    db: State<'_, SqlitePool>,
) -> IpcResult<ConnId> {
    tracing::info!(command = "connection_save", name = %config.name, "IPC call");

    let now = Utc::now().to_rfc3339();
    let id = if config.id.is_empty() {
        Uuid::new_v4().to_string()
    } else {
        config.id.clone()
    };

    // Determine the keychain key to use for this connection
    let existing_keychain_key: Option<String> = if !config.id.is_empty() {
        sqlx::query_scalar::<_, Option<String>>("SELECT keychain_key FROM connections WHERE id = ?")
            .bind(&config.id)
            .fetch_optional(db.inner())
            .await
            .map_err(|e| IpcError::Internal { message: e.to_string() })?
            .flatten()
    } else {
        None
    };

    // Store password in Keychain based on what was provided:
    // - Some(non-empty) → write new password with biometric access control
    // - Some("")        → user explicitly cleared the password; delete Keychain entry
    // - None            → no change; preserve existing Keychain entry
    let keychain_key = match &config.password {
        Some(pw) if !pw.is_empty() => {
            let kk = format!("conn-{}", id);
            crate::utils::keychain::save_password(&kk, pw)
                .map_err(|e| IpcError::Internal { message: e })?;
            Some(kk)
        }
        Some(_) => {
            // Empty string → clear password
            if let Some(ref kk) = existing_keychain_key {
                crate::utils::keychain::delete_password(kk)
                    .map_err(|e| IpcError::Internal { message: e })?;
            }
            None
        }
        None => {
            // No password provided → keep existing Keychain entry unchanged
            existing_keychain_key
        }
    };

    // Upsert into SQLite
    sqlx::query(
        r#"INSERT INTO connections (id, name, group_name, host, port, auth_db, timeout_ms, keychain_key, sort_order, connection_type, ssh_config, tls_config, sentinel_nodes, master_name, cluster_nodes, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
             name = excluded.name,
             group_name = excluded.group_name,
             host = excluded.host,
             port = excluded.port,
             auth_db = excluded.auth_db,
             timeout_ms = excluded.timeout_ms,
             keychain_key = excluded.keychain_key,
             sort_order = excluded.sort_order,
             connection_type = excluded.connection_type,
             ssh_config = excluded.ssh_config,
             tls_config = excluded.tls_config,
             sentinel_nodes = excluded.sentinel_nodes,
             master_name = excluded.master_name,
             cluster_nodes = excluded.cluster_nodes,
             updated_at = excluded.updated_at"#,
    )
    .bind(&id)
    .bind(&config.name)
    .bind(&config.group_name)
    .bind(&config.host)
    .bind(config.port as i64)
    .bind(config.auth_db as i64)
    .bind(config.timeout_ms as i64)
    .bind(&keychain_key)
    .bind(config.sort_order as i64)
    .bind(serde_json::to_string(&config.connection_type).ok().as_deref().map(|s| s.trim_matches('"').to_string()))
    .bind(config.ssh_config.as_ref().and_then(|c| serde_json::to_string(c).ok()))
    .bind(config.tls_config.as_ref().and_then(|c| serde_json::to_string(c).ok()))
    .bind(config.sentinel_nodes.as_ref().and_then(|v| serde_json::to_string(v).ok()))
    .bind(&config.master_name)
    .bind(config.cluster_nodes.as_ref().and_then(|v| serde_json::to_string(v).ok()))
    .bind(&now)
    .bind(&now)
    .execute(db.inner())
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })?;

    Ok(id)
}

/// List all saved connections.
/// Passwords are NOT read from Keychain here — only `has_password` is set.
/// This avoids triggering macOS authorization dialogs on every app launch.
#[tauri::command]
pub async fn connection_list(
    db: State<'_, SqlitePool>,
) -> IpcResult<Vec<ConnectionConfig>> {
    tracing::info!(command = "connection_list", "IPC call");

    let metas = sqlx::query_as::<_, ConnectionMeta>(
        "SELECT * FROM connections ORDER BY sort_order ASC, created_at ASC",
    )
    .fetch_all(db.inner())
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })?;

    let configs = metas
        .into_iter()
        .map(|meta| ConnectionConfig {
            has_password: meta.keychain_key.is_some(),
            id: meta.id,
            name: meta.name,
            group_name: meta.group_name,
            host: meta.host,
            port: meta.port as u16,
            password: None, // never expose plaintext in list
            auth_db: meta.auth_db as u8,
            timeout_ms: meta.timeout_ms as u64,
            sort_order: meta.sort_order as i32,
            connection_type: meta.connection_type
                .as_deref()
                .and_then(|s| serde_json::from_str(&format!("\"{}\"", s)).ok())
                .unwrap_or_default(),
            ssh_config: meta.ssh_config
                .as_deref()
                .and_then(|s| serde_json::from_str(s).ok()),
            tls_config: meta.tls_config
                .as_deref()
                .and_then(|s| serde_json::from_str(s).ok()),
            sentinel_nodes: meta.sentinel_nodes
                .as_deref()
                .and_then(|s| serde_json::from_str(s).ok()),
            master_name: meta.master_name,
            cluster_nodes: meta.cluster_nodes
                .as_deref()
                .and_then(|s| serde_json::from_str(s).ok()),
        })
        .collect();

    Ok(configs)
}

/// Delete a connection config from SQLite + Keychain
#[tauri::command]
pub async fn connection_delete(
    conn_id: ConnId,
    db: State<'_, SqlitePool>,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<()> {
    tracing::info!(command = "connection_delete", conn_id = %conn_id, "IPC call");

    // Get keychain_key before deleting
    let meta = sqlx::query_as::<_, ConnectionMeta>(
        "SELECT * FROM connections WHERE id = ?",
    )
    .bind(&conn_id)
    .fetch_optional(db.inner())
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })?;

    if let Some(m) = meta {
        // Delete from Keychain
        if let Some(ref kk) = m.keychain_key {
            crate::utils::keychain::delete_password(kk)
                .map_err(|e| IpcError::Internal { message: e })?;
        }
    }

    // Delete from SQLite
    sqlx::query("DELETE FROM connections WHERE id = ?")
        .bind(&conn_id)
        .execute(db.inner())
        .await
        .map_err(|e| IpcError::Internal { message: e.to_string() })?;

    // Close session if open
    let mut mgr = manager.lock().await;
    mgr.close(&conn_id);

    Ok(())
}

/// Open a temporary Redis connection (not persisted to SQLite)
#[tauri::command]
pub async fn connection_open_temp(
    host: String,
    port: u16,
    password: Option<String>,
    timeout_ms: Option<u64>,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<ConnId> {
    tracing::info!(command = "connection_open_temp", host = %host, port = port, "IPC call");

    let temp_id = format!("temp-{}", Uuid::new_v4());

    let config = ConnectionConfig {
        id: temp_id.clone(),
        name: format!("{}:{}", host, port),
        group_name: String::new(),
        host,
        port,
        password,
        has_password: false,
        auth_db: 0,
        timeout_ms: timeout_ms.unwrap_or(5000),
        sort_order: 0,
        connection_type: crate::models::connection::ConnectionType::Tcp,
        ssh_config: None,
        tls_config: None,
        sentinel_nodes: None,
        master_name: None,
        cluster_nodes: None,
    };

    let mut mgr = manager.lock().await;
    mgr.open_with_id(temp_id.clone(), config).await?;

    Ok(temp_id)
}

/// Select a DB and return keyspace stats
#[tauri::command]
pub async fn db_select(
    conn_id: ConnId,
    db_index: u8,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<Vec<DbStat>> {
    tracing::info!(command = "db_select", conn_id = %conn_id, db = db_index, "IPC call");

    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;

    // SELECT db
    redis::cmd("SELECT")
        .arg(db_index)
        .query_async::<()>(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    // Get keyspace info
    let info: String = redis::cmd("INFO")
        .arg("keyspace")
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    guard.current_db = db_index;

    let stats = crate::services::connection_manager::ConnectionManager::parse_keyspace(&info);
    Ok(stats)
}

// ---- Phase 2: SSH/TLS connection test commands ----

/// Test result for advanced connection types
#[derive(Debug, serde::Serialize)]
pub struct AdvancedConnectionTestResult {
    /// Whether the overall connection succeeded
    pub success: bool,
    /// SSH layer result (for SSH connections)
    pub ssh_ok: Option<bool>,
    /// Redis layer result
    pub redis_ok: Option<bool>,
    /// TLS layer result (for TLS connections)
    pub tls_ok: Option<bool>,
    /// Latency in milliseconds
    pub latency_ms: Option<u32>,
    /// Error message if failed
    pub error: Option<String>,
    /// Diagnostic details
    pub details: Vec<String>,
}

/// Test an SSH tunnel connection
#[tauri::command]
pub async fn connection_test_ssh(config: crate::models::connection::ConnectionConfig) -> IpcResult<AdvancedConnectionTestResult> {
    tracing::info!(command = "connection_test_ssh", name = %config.name, "IPC call");

    let ssh_cfg = match &config.ssh_config {
        Some(c) => c,
        None => return Ok(AdvancedConnectionTestResult {
            success: false,
            ssh_ok: None,
            redis_ok: None,
            tls_ok: None,
            latency_ms: None,
            error: Some("SSH config is missing".to_string()),
            details: vec![],
        }),
    };

    let mut details = Vec::new();

    // Test SSH connection
    let ssh_result = crate::services::ssh_tunnel::test_ssh_connection(ssh_cfg);
    let ssh_ok = ssh_result.is_ok();
    if ssh_ok {
        details.push(format!("✓ SSH connection to {}:{} succeeded", ssh_cfg.host, ssh_cfg.port));
    } else {
        let err_msg = ssh_result.unwrap_err().to_string();
        details.push(format!("✗ SSH connection failed: {}", err_msg));
        return Ok(AdvancedConnectionTestResult {
            success: false,
            ssh_ok: Some(false),
            redis_ok: None,
            tls_ok: None,
            latency_ms: None,
            error: Some(err_msg),
            details,
        });
    }

    // Test Redis via SSH tunnel
    let start = std::time::Instant::now();
    let tunnel_result = crate::services::ssh_tunnel::establish_tunnel(ssh_cfg, &config.host, config.port);
    match tunnel_result {
        Ok(tunnel) => {
            let local_port = tunnel.local_port;
            let addr = format!("redis://127.0.0.1:{}", local_port);
            match redis::Client::open(addr.as_str()) {
                Ok(client) => {
                    match client.get_multiplexed_async_connection().await {
                        Ok(mut conn) => {
                            let ping_result: Result<String, _> = redis::cmd("PING").query_async(&mut conn).await;
                            let latency = start.elapsed().as_millis() as u32;
                            if ping_result.is_ok() {
                                details.push(format!("✓ Redis PING via SSH tunnel succeeded ({}ms)", latency));
                                Ok(AdvancedConnectionTestResult {
                                    success: true,
                                    ssh_ok: Some(true),
                                    redis_ok: Some(true),
                                    tls_ok: None,
                                    latency_ms: Some(latency),
                                    error: None,
                                    details,
                                })
                            } else {
                                details.push("✗ Redis PING failed".to_string());
                                Ok(AdvancedConnectionTestResult {
                                    success: false,
                                    ssh_ok: Some(true),
                                    redis_ok: Some(false),
                                    tls_ok: None,
                                    latency_ms: Some(latency),
                                    error: Some("Redis PING failed".to_string()),
                                    details,
                                })
                            }
                        }
                        Err(e) => {
                            details.push(format!("✗ Redis connection via tunnel failed: {}", e));
                            Ok(AdvancedConnectionTestResult {
                                success: false,
                                ssh_ok: Some(true),
                                redis_ok: Some(false),
                                tls_ok: None,
                                latency_ms: None,
                                error: Some(e.to_string()),
                                details,
                            })
                        }
                    }
                }
                Err(e) => {
                    Ok(AdvancedConnectionTestResult {
                        success: false,
                        ssh_ok: Some(true),
                        redis_ok: Some(false),
                        tls_ok: None,
                        latency_ms: None,
                        error: Some(e.to_string()),
                        details,
                    })
                }
            }
        }
        Err(e) => {
            Ok(AdvancedConnectionTestResult {
                success: false,
                ssh_ok: Some(false),
                redis_ok: None,
                tls_ok: None,
                latency_ms: None,
                error: Some(e.to_string()),
                details,
            })
        }
    }
}

/// Test a TLS-encrypted connection
#[tauri::command]
pub async fn connection_test_tls(config: crate::models::connection::ConnectionConfig) -> IpcResult<AdvancedConnectionTestResult> {
    tracing::info!(command = "connection_test_tls", name = %config.name, "IPC call");

    let tls_cfg = match &config.tls_config {
        Some(c) => c,
        None => return Ok(AdvancedConnectionTestResult {
            success: false,
            ssh_ok: None,
            redis_ok: None,
            tls_ok: None,
            latency_ms: None,
            error: Some("TLS config is missing".to_string()),
            details: vec![],
        }),
    };

    let mut details = Vec::new();

    // Validate TLS config
    match crate::services::tls_connection::validate_tls_config(tls_cfg) {
        Ok(warnings) => {
            for w in &warnings {
                details.push(format!("⚠ {}", w));
            }
            details.push("✓ TLS configuration validated".to_string());
        }
        Err(e) => {
            return Ok(AdvancedConnectionTestResult {
                success: false,
                ssh_ok: None,
                redis_ok: None,
                tls_ok: Some(false),
                latency_ms: None,
                error: Some(e.to_string()),
                details,
            });
        }
    }

    // Test Redis TLS connection
    let start = std::time::Instant::now();
    let addr = crate::services::tls_connection::build_tls_redis_url(
        &config.host,
        config.port,
        config.password.as_deref(),
    );

    match redis::Client::open(addr.as_str()) {
        Ok(client) => {
            match client.get_multiplexed_async_connection().await {
                Ok(mut conn) => {
                    let ping_result: Result<String, _> = redis::cmd("PING").query_async(&mut conn).await;
                    let latency = start.elapsed().as_millis() as u32;
                    if ping_result.is_ok() {
                        details.push(format!("✓ Redis TLS PING succeeded ({}ms)", latency));
                        Ok(AdvancedConnectionTestResult {
                            success: true,
                            ssh_ok: None,
                            redis_ok: Some(true),
                            tls_ok: Some(true),
                            latency_ms: Some(latency),
                            error: None,
                            details,
                        })
                    } else {
                        details.push("✗ Redis PING failed".to_string());
                        Ok(AdvancedConnectionTestResult {
                            success: false,
                            ssh_ok: None,
                            redis_ok: Some(false),
                            tls_ok: Some(true),
                            latency_ms: Some(latency),
                            error: Some("Redis PING failed".to_string()),
                            details,
                        })
                    }
                }
                Err(e) => {
                    details.push(format!("✗ TLS connection failed: {}", e));
                    Ok(AdvancedConnectionTestResult {
                        success: false,
                        ssh_ok: None,
                        redis_ok: Some(false),
                        tls_ok: Some(false),
                        latency_ms: None,
                        error: Some(e.to_string()),
                        details,
                    })
                }
            }
        }
        Err(e) => {
            Ok(AdvancedConnectionTestResult {
                success: false,
                ssh_ok: None,
                redis_ok: None,
                tls_ok: Some(false),
                latency_ms: None,
                error: Some(e.to_string()),
                details,
            })
        }
    }
}

// ---- Phase 2: Configuration import/export ----

/// Export all connection configurations as JSON (passwords excluded)
#[tauri::command]
pub async fn connection_export(
    db: State<'_, SqlitePool>,
) -> IpcResult<String> {
    tracing::info!(command = "connection_export", "IPC call");

    let metas = sqlx::query_as::<_, ConnectionMeta>(
        "SELECT * FROM connections ORDER BY sort_order ASC, created_at ASC",
    )
    .fetch_all(db.inner())
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })?;

    let configs: Vec<ConnectionConfig> = metas
        .into_iter()
        .map(|meta| ConnectionConfig {
            has_password: meta.keychain_key.is_some(),
            id: meta.id,
            name: meta.name,
            group_name: meta.group_name,
            host: meta.host,
            port: meta.port as u16,
            password: None,
            auth_db: meta.auth_db as u8,
            timeout_ms: meta.timeout_ms as u64,
            sort_order: meta.sort_order as i32,
            connection_type: meta.connection_type
                .as_deref()
                .and_then(|s| serde_json::from_str(&format!("\"{}\"", s)).ok())
                .unwrap_or_default(),
            ssh_config: meta.ssh_config
                .as_deref()
                .and_then(|s| serde_json::from_str(s).ok()),
            tls_config: meta.tls_config
                .as_deref()
                .and_then(|s| serde_json::from_str(s).ok()),
            sentinel_nodes: meta.sentinel_nodes
                .as_deref()
                .and_then(|s| serde_json::from_str(s).ok()),
            master_name: meta.master_name,
            cluster_nodes: meta.cluster_nodes
                .as_deref()
                .and_then(|s| serde_json::from_str(s).ok()),
        })
        .collect();

    serde_json::to_string_pretty(&configs)
        .map_err(|e| IpcError::Internal { message: e.to_string() })
}

/// Import connection configurations from JSON string.
///
/// Behavior:
/// - Always generate a fresh UUID for each imported row (fix 1.5): this avoids
///   accidentally overwriting a local connection that happens to share an id
///   with an exported file from another machine. `keychain_key` is intentionally
///   set to NULL — the importing user must re-enter the password, because
///   Keychain entries live on the originating device.
/// - Validate host / port / auth_db / timeout_ms before insert; malformed
///   entries are skipped and counted, not aborted (best-effort import).
/// - Return the number of rows actually inserted, based on `rows_affected()`
///   (fix 1.4).
#[tauri::command]
pub async fn connection_import(
    json: String,
    db: State<'_, SqlitePool>,
) -> IpcResult<u32> {
    tracing::info!(command = "connection_import", "IPC call");

    let configs: Vec<ConnectionConfig> = serde_json::from_str(&json)
        .map_err(|e| IpcError::Internal {
            message: format!("Invalid JSON format: {}", e),
        })?;

    let now = Utc::now().to_rfc3339();
    let mut imported = 0u32;
    let mut skipped = 0u32;

    for config in configs {
        // ---- Basic validation (fix 1.5) ----
        if config.host.trim().is_empty() {
            tracing::warn!("connection_import: skip entry with empty host (name={})", config.name);
            skipped += 1;
            continue;
        }
        if config.port == 0 {
            tracing::warn!(
                "connection_import: skip entry with invalid port 0 (name={})",
                config.name
            );
            skipped += 1;
            continue;
        }
        if config.auth_db > 15 {
            tracing::warn!(
                "connection_import: skip entry with auth_db > 15 (name={}, db={})",
                config.name,
                config.auth_db
            );
            skipped += 1;
            continue;
        }

        // Clamp timeout to a sane range [200ms, 120s]; out-of-range values are
        // corrected, not fatal — this preserves the best-effort import contract.
        let timeout_ms = config.timeout_ms.clamp(200, 120_000);

        // Always mint a new id on import; never trust the exported one.
        let id = Uuid::new_v4().to_string();
        let name = if config.name.trim().is_empty() {
            format!("{}:{}", config.host, config.port)
        } else {
            config.name.clone()
        };

        let result = sqlx::query(
            r#"INSERT INTO connections
               (id, name, group_name, host, port, auth_db, timeout_ms, keychain_key, sort_order, connection_type, ssh_config, tls_config, sentinel_nodes, master_name, cluster_nodes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)"#,
        )
        .bind(&id)
        .bind(&name)
        .bind(&config.group_name)
        .bind(&config.host)
        .bind(config.port as i64)
        .bind(config.auth_db as i64)
        .bind(timeout_ms as i64)
        .bind(config.sort_order as i64)
        .bind(serde_json::to_string(&config.connection_type).ok().as_deref().map(|s| s.trim_matches('"').to_string()))
        .bind(config.ssh_config.as_ref().and_then(|c| serde_json::to_string(c).ok()))
        .bind(config.tls_config.as_ref().and_then(|c| serde_json::to_string(c).ok()))
        .bind(config.sentinel_nodes.as_ref().and_then(|v| serde_json::to_string(v).ok()))
        .bind(&config.master_name)
        .bind(config.cluster_nodes.as_ref().and_then(|v| serde_json::to_string(v).ok()))
        .bind(&now)
        .bind(&now)
        .execute(db.inner())
        .await
        .map_err(|e| IpcError::Internal { message: e.to_string() })?;

        if result.rows_affected() == 1 {
            imported += 1;
        } else {
            skipped += 1;
        }
    }

    tracing::info!(
        "connection_import: imported={}, skipped={}",
        imported,
        skipped
    );
    Ok(imported)
}

// ---- Phase 2: Sentinel/Cluster connection test commands ----

/// Test a Sentinel-mode connection: resolve master via sentinel nodes, then PING.
#[tauri::command]
pub async fn connection_test_sentinel(
    config: ConnectionConfig,
) -> IpcResult<AdvancedConnectionTestResult> {
    tracing::info!(command = "connection_test_sentinel", name = %config.name, "IPC call");

    let nodes = config
        .sentinel_nodes
        .as_ref()
        .filter(|v| !v.is_empty())
        .ok_or_else(|| IpcError::InvalidArgument {
            field: "sentinel_nodes".to_string(),
            reason: "Sentinel nodes list is required".to_string(),
        })?;
    let master_name = config
        .master_name
        .as_ref()
        .filter(|s| !s.is_empty())
        .ok_or_else(|| IpcError::InvalidArgument {
            field: "master_name".to_string(),
            reason: "Master name is required for Sentinel connection".to_string(),
        })?;

    let mut details = Vec::new();

    // Build sentinel client URLs
    let sentinel_urls: Vec<String> = nodes
        .iter()
        .map(|addr| format!("redis://{}", addr))
        .collect();

    details.push(format!("Contacting {} sentinel node(s)...", sentinel_urls.len()));

    let start = std::time::Instant::now();

    // Build sentinel and discover master
    let mut sentinel = redis::sentinel::Sentinel::build(sentinel_urls.clone())
        .map_err(|e| IpcError::ConnectionRefused {
            target: format!("Sentinel init failed: {}", e),
        })?;

    let master_client = sentinel
        .async_master_for(master_name, None)
        .await
        .map_err(|e| IpcError::ConnectionRefused {
            target: format!("Sentinel master lookup failed ({}): {}", master_name, e),
        })?;

    let mut conn = master_client
        .get_multiplexed_async_connection()
        .await
        .map_err(|e| IpcError::ConnectionRefused {
            target: format!("Connect to Sentinel master failed: {}", e),
        })?;

    // AUTH if needed
    if let Some(ref pw) = config.password {
        redis::cmd("AUTH")
            .arg(pw.as_str())
            .query_async::<()>(&mut conn)
            .await
            .map_err(|_| IpcError::AuthFailed)?;
    }

    // PING
    let ping_result: Result<String, _> = redis::cmd("PING").query_async(&mut conn).await;
    let latency = start.elapsed().as_millis() as u32;

    match ping_result {
        Ok(_) => {
            // Try to get resolved master address via ROLE command
            let role_info: Result<String, _> = redis::cmd("INFO")
                .arg("server")
                .query_async(&mut conn)
                .await;
            let master_addr = if let Ok(info) = role_info {
                info.lines()
                    .find(|l| l.starts_with("tcp_port:"))
                    .map(|l| l.trim_start_matches("tcp_port:").to_string())
                    .unwrap_or_else(|| "unknown".to_string())
            } else {
                "unknown".to_string()
            };

            details.push(format!("✓ Sentinel master discovered: {}", master_addr));
            details.push(format!("✓ Redis PING succeeded ({}ms)", latency));

            Ok(AdvancedConnectionTestResult {
                success: true,
                ssh_ok: None,
                redis_ok: Some(true),
                tls_ok: None,
                latency_ms: Some(latency),
                error: None,
                details,
            })
        }
        Err(e) => {
            details.push(format!("✗ Redis PING failed: {}", e));
            Ok(AdvancedConnectionTestResult {
                success: false,
                ssh_ok: None,
                redis_ok: Some(false),
                tls_ok: None,
                latency_ms: Some(latency),
                error: Some(format!("Redis PING failed: {}", e)),
                details,
            })
        }
    }
}

/// Test a Cluster-mode connection: connect to seed nodes, discover cluster topology,
/// PING each shard master, and report the number of master nodes.
#[tauri::command]
pub async fn connection_test_cluster(
    config: ConnectionConfig,
) -> IpcResult<AdvancedConnectionTestResult> {
    tracing::info!(command = "connection_test_cluster", name = %config.name, "IPC call");

    let nodes = config
        .cluster_nodes
        .as_ref()
        .filter(|v| !v.is_empty())
        .ok_or_else(|| IpcError::InvalidArgument {
            field: "cluster_nodes".to_string(),
            reason: "Cluster nodes list is required".to_string(),
        })?;

    let mut details = Vec::new();
    let mut master_count = 0u32;
    let mut last_err: Option<String> = None;

    details.push(format!("Testing {} cluster seed node(s)...", nodes.len()));

    let start = std::time::Instant::now();

    for seed in nodes {
        let addr = if let Some(ref pw) = config.password {
            format!("redis://:{}@{}", pw, seed)
        } else {
            format!("redis://{}", seed)
        };

        let client = match redis::Client::open(addr.as_str()) {
            Ok(c) => c,
            Err(e) => {
                last_err = Some(format!("{}: {}", seed, e));
                details.push(format!("✗ Seed node {} client open failed: {}", seed, e));
                continue;
            }
        };

        match client.get_multiplexed_async_connection().await {
            Ok(mut conn) => {
                // PING this node
                let ping_result: Result<String, _> = redis::cmd("PING").query_async(&mut conn).await;

                if ping_result.is_ok() {
                    // Try CLUSTER INFO to check cluster state
                    let cluster_info: Result<String, _> = redis::cmd("CLUSTER")
                        .arg("INFO")
                        .query_async(&mut conn)
                        .await;

                    let is_cluster_ok = cluster_info
                        .as_ref()
                        .map(|info| info.contains("cluster_state:ok"))
                        .unwrap_or(false);

                    if is_cluster_ok {
                        // Get number of master nodes
                        let nodes_info: Result<String, _> = redis::cmd("CLUSTER")
                            .arg("NODES")
                            .query_async(&mut conn)
                            .await;

                        if let Ok(ni) = nodes_info {
                            master_count = ni
                                .lines()
                                .filter(|l| l.contains("master") || l.contains("myself,master"))
                                .count() as u32;
                        }

                        details.push(format!("✓ Seed node {} reachable, cluster_state:ok", seed));
                    } else {
                        details.push(format!("⚠ Seed node {} reachable but cluster_state NOT ok", seed));
                    }
                } else {
                    last_err = Some(format!("{}: PING failed", seed));
                    details.push(format!("✗ Seed node {} PING failed", seed));
                }
            }
            Err(e) => {
                last_err = Some(format!("{}: {}", seed, e));
                details.push(format!("✗ Seed node {} connection failed: {}", seed, e));
            }
        }
    }

    let latency = start.elapsed().as_millis() as u32;
    let success = master_count > 0;

    if success {
        details.push(format!("✓ Cluster has {} master node(s)", master_count));
    }

    Ok(AdvancedConnectionTestResult {
        success,
        ssh_ok: None,
        redis_ok: Some(success),
        tls_ok: None,
        latency_ms: Some(latency),
        error: if success { None } else { last_err },
        details,
    })
}
