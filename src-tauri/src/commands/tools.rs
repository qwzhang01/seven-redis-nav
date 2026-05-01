use sqlx::SqlitePool;
use tauri::State;
use uuid::Uuid;

use crate::error::{IpcError, IpcResult};
use crate::models::connection::ConnId;
use crate::models::health_check::HealthReport;
use crate::models::key_analyzer::{MaskingRule, TtlDistribution};
use crate::services::connection_manager::SharedConnectionManager;
use crate::services::key_analyzer::{run_key_scan, analyze_ttl_distribution, SharedScanRegistry, SharedScanResults};
use crate::services::health_check::{export_to_markdown, generate_health_report};
use crate::utils::config_store;
use crate::utils::config_store::ShortcutBinding;

// ─────────────────────────────────────────────
// Key Analyzer
// ─────────────────────────────────────────────

/// Start a background key memory scan. Returns a task_id for progress tracking.
#[tauri::command]
pub async fn key_scan_memory_start(
    conn_id: ConnId,
    low_impact: bool,
    manager: State<'_, SharedConnectionManager>,
    registry: State<'_, SharedScanRegistry>,
    results: State<'_, SharedScanResults>,
    app: tauri::AppHandle,
) -> IpcResult<String> {
    let _session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };

    // Get a dedicated connection for the scan
    let client = {
        let mgr = manager.lock().await;
        mgr.get_client(&conn_id).await?
    };
    let scan_conn = client
        .get_multiplexed_async_connection()
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    let task_id = Uuid::new_v4().to_string();
    let (cancel_tx, cancel_rx) = tokio::sync::oneshot::channel();

    {
        let mut reg = registry.lock().map_err(|_| IpcError::Internal { message: "Registry lock failed".to_string() })?;
        reg.insert(task_id.clone(), crate::services::key_analyzer::ScanTask { cancel_tx });
    }

    let task_id_clone = task_id.clone();
    let registry_clone = registry.inner().clone();
    let results_clone = results.inner().clone();
    tauri::async_runtime::spawn(async move {
        run_key_scan(scan_conn, task_id_clone, low_impact, app, registry_clone, results_clone, cancel_rx).await;
    });

    Ok(task_id)
}

/// Stop a running key memory scan.
#[tauri::command]
pub async fn key_scan_memory_stop(
    task_id: String,
    registry: State<'_, SharedScanRegistry>,
) -> IpcResult<()> {
    let mut reg = registry.lock().map_err(|_| IpcError::Internal { message: "Registry lock failed".to_string() })?;
    if let Some(task) = reg.remove(&task_id) {
        let _ = task.cancel_tx.send(());
    }
    Ok(())
}

/// Analyze TTL distribution for the current DB.
#[tauri::command]
pub async fn key_ttl_distribution(
    conn_id: ConnId,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<TtlDistribution> {
    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;
    analyze_ttl_distribution(&mut guard.conn).await
}

/// Export scan results as CSV string.
#[tauri::command]
pub async fn key_scan_memory_export_csv(
    task_id: String,
    results: State<'_, SharedScanResults>,
) -> IpcResult<String> {
    let res = results.lock().map_err(|_| IpcError::Internal { message: "Results lock failed".to_string() })?;
    let top_keys = res.get(&task_id).cloned().unwrap_or_default();

    let mut csv = String::from("key,type,memory_bytes,encoding,element_count\n");
    for stat in &top_keys {
        // Escape commas in key names by quoting
        let key_escaped = if stat.key.contains(',') {
            format!("\"{}\"", stat.key.replace('"', "\"\""))
        } else {
            stat.key.clone()
        };
        csv.push_str(&format!("{},{},{},{},{}\n",
            key_escaped,
            stat.key_type,
            stat.memory_bytes,
            stat.encoding,
            stat.element_count,
        ));
    }
    Ok(csv)
}

// ─────────────────────────────────────────────
// Health Check
// ─────────────────────────────────────────────

/// Generate a health check report and save to SQLite.
#[tauri::command]
pub async fn health_check_generate(
    conn_id: ConnId,
    manager: State<'_, SharedConnectionManager>,
    db: State<'_, SqlitePool>,
) -> IpcResult<HealthReport> {
    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;

    let mut report = generate_health_report(&mut guard.conn, &conn_id).await?;
    report.connection_id = conn_id.clone();

    config_store::health_report_save(&db, &report).await?;
    Ok(report)
}

/// List health check report history.
#[tauri::command]
pub async fn health_check_history_list(db: State<'_, SqlitePool>) -> IpcResult<Vec<HealthReport>> {
    config_store::health_report_list(&db).await
}

/// Get a specific health check report by ID.
#[tauri::command]
pub async fn health_check_history_get(id: String, db: State<'_, SqlitePool>) -> IpcResult<HealthReport> {
    config_store::health_report_get(&db, &id).await
}

/// Export a health report as Markdown text.
#[tauri::command]
pub async fn health_check_export_markdown(
    report: HealthReport,
    conn_id: ConnId,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<String> {
    let host = {
        let mgr = manager.lock().await;
        mgr.get_config_cloned(&conn_id).await
            .map(|c| format!("{}:{}", c.host, c.port))
            .unwrap_or_else(|_| conn_id.clone())
    };
    Ok(export_to_markdown(&report, &host))
}

// ─────────────────────────────────────────────
// Data Masking
// ─────────────────────────────────────────────

#[tauri::command]
pub async fn masking_rule_list(db: State<'_, SqlitePool>) -> IpcResult<Vec<MaskingRule>> {
    config_store::masking_rule_list(&db).await
}

#[tauri::command]
pub async fn masking_rule_save(rule: MaskingRule, db: State<'_, SqlitePool>) -> IpcResult<()> {
    config_store::masking_rule_save(&db, &rule).await
}

#[tauri::command]
pub async fn masking_rule_delete(id: String, db: State<'_, SqlitePool>) -> IpcResult<()> {
    config_store::masking_rule_delete(&db, &id).await
}

#[tauri::command]
pub async fn masking_rule_reorder(ids: Vec<String>, db: State<'_, SqlitePool>) -> IpcResult<()> {
    config_store::masking_rule_reorder(&db, &ids).await
}

// ─────────────────────────────────────────────
// Shortcut Bindings
// ─────────────────────────────────────────────

#[tauri::command]
pub async fn shortcut_binding_list(db: State<'_, SqlitePool>) -> IpcResult<Vec<ShortcutBinding>> {
    config_store::shortcut_binding_list(&db).await
}

#[tauri::command]
pub async fn shortcut_binding_save(action: String, binding: String, db: State<'_, SqlitePool>) -> IpcResult<()> {
    config_store::shortcut_binding_save(&db, &action, &binding).await
}

#[tauri::command]
pub async fn shortcut_binding_delete(action: String, db: State<'_, SqlitePool>) -> IpcResult<()> {
    config_store::shortcut_binding_delete(&db, &action).await
}

#[tauri::command]
pub async fn shortcut_binding_reset_all(db: State<'_, SqlitePool>) -> IpcResult<()> {
    config_store::shortcut_binding_reset_all(&db).await
}
