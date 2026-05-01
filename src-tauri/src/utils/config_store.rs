use sqlx::SqlitePool;
use chrono::Utc;
use crate::error::{IpcError, IpcResult};
use crate::models::lua::LuaScript;
use crate::models::key_analyzer::MaskingRule;
use crate::models::health_check::HealthReport;

// ─────────────────────────────────────────────
// Lua Scripts
// ─────────────────────────────────────────────

pub async fn lua_script_save(db: &SqlitePool, script: &str, name: &str) -> IpcResult<LuaScript> {
    let now = Utc::now().to_rfc3339();
    let id = uuid::Uuid::new_v4().to_string();
    sqlx::query(
        "INSERT INTO lua_scripts (id, name, script, created_at, last_used_at) VALUES (?, ?, ?, ?, ?)"
    )
    .bind(&id)
    .bind(name)
    .bind(script)
    .bind(&now)
    .bind(&now)
    .execute(db)
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })?;

    Ok(LuaScript { id, name: name.to_string(), script: script.to_string(), created_at: now.clone(), last_used_at: now })
}

pub async fn lua_script_list(db: &SqlitePool) -> IpcResult<Vec<LuaScript>> {
    sqlx::query_as::<_, LuaScript>(
        "SELECT id, name, script, created_at, last_used_at FROM lua_scripts ORDER BY last_used_at DESC LIMIT 100"
    )
    .fetch_all(db)
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })
}

pub async fn lua_script_delete(db: &SqlitePool, id: &str) -> IpcResult<()> {
    sqlx::query("DELETE FROM lua_scripts WHERE id = ?")
        .bind(id)
        .execute(db)
        .await
        .map_err(|e| IpcError::Internal { message: e.to_string() })?;
    Ok(())
}

pub async fn lua_script_rename(db: &SqlitePool, id: &str, name: &str) -> IpcResult<()> {
    sqlx::query("UPDATE lua_scripts SET name = ? WHERE id = ?")
        .bind(name)
        .bind(id)
        .execute(db)
        .await
        .map_err(|e| IpcError::Internal { message: e.to_string() })?;
    Ok(())
}

#[allow(dead_code)]
pub async fn lua_script_touch(db: &SqlitePool, id: &str) -> IpcResult<()> {
    let now = Utc::now().to_rfc3339();
    sqlx::query("UPDATE lua_scripts SET last_used_at = ? WHERE id = ?")
        .bind(&now)
        .bind(id)
        .execute(db)
        .await
        .map_err(|e| IpcError::Internal { message: e.to_string() })?;
    Ok(())
}

// ─────────────────────────────────────────────
// Shortcut Bindings
// ─────────────────────────────────────────────

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, sqlx::FromRow)]
pub struct ShortcutBinding {
    pub action: String,
    pub binding: String,
    pub updated_at: String,
}

pub async fn shortcut_binding_list(db: &SqlitePool) -> IpcResult<Vec<ShortcutBinding>> {
    sqlx::query_as::<_, ShortcutBinding>(
        "SELECT action, binding, updated_at FROM shortcut_bindings ORDER BY action"
    )
    .fetch_all(db)
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })
}

pub async fn shortcut_binding_save(db: &SqlitePool, action: &str, binding: &str) -> IpcResult<()> {
    let now = Utc::now().to_rfc3339();
    sqlx::query(
        "INSERT INTO shortcut_bindings (action, binding, updated_at) VALUES (?, ?, ?)
         ON CONFLICT(action) DO UPDATE SET binding = excluded.binding, updated_at = excluded.updated_at"
    )
    .bind(action)
    .bind(binding)
    .bind(&now)
    .execute(db)
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })?;
    Ok(())
}

pub async fn shortcut_binding_delete(db: &SqlitePool, action: &str) -> IpcResult<()> {
    sqlx::query("DELETE FROM shortcut_bindings WHERE action = ?")
        .bind(action)
        .execute(db)
        .await
        .map_err(|e| IpcError::Internal { message: e.to_string() })?;
    Ok(())
}

pub async fn shortcut_binding_reset_all(db: &SqlitePool) -> IpcResult<()> {
    sqlx::query("DELETE FROM shortcut_bindings")
        .execute(db)
        .await
        .map_err(|e| IpcError::Internal { message: e.to_string() })?;
    Ok(())
}

// ─────────────────────────────────────────────
// Masking Rules
// ─────────────────────────────────────────────

pub async fn masking_rule_list(db: &SqlitePool) -> IpcResult<Vec<MaskingRule>> {
    sqlx::query_as::<_, MaskingRule>(
        "SELECT id, pattern, mask_char, enabled, sort_order FROM masking_rules ORDER BY sort_order ASC"
    )
    .fetch_all(db)
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })
}

pub async fn masking_rule_save(db: &SqlitePool, rule: &MaskingRule) -> IpcResult<()> {
    sqlx::query(
        "INSERT INTO masking_rules (id, pattern, mask_char, enabled, sort_order) VALUES (?, ?, ?, ?, ?)
         ON CONFLICT(id) DO UPDATE SET pattern = excluded.pattern, mask_char = excluded.mask_char,
         enabled = excluded.enabled, sort_order = excluded.sort_order"
    )
    .bind(&rule.id)
    .bind(&rule.pattern)
    .bind(&rule.mask_char)
    .bind(rule.enabled)
    .bind(rule.sort_order)
    .execute(db)
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })?;
    Ok(())
}

pub async fn masking_rule_delete(db: &SqlitePool, id: &str) -> IpcResult<()> {
    sqlx::query("DELETE FROM masking_rules WHERE id = ?")
        .bind(id)
        .execute(db)
        .await
        .map_err(|e| IpcError::Internal { message: e.to_string() })?;
    Ok(())
}

pub async fn masking_rule_reorder(db: &SqlitePool, ids: &[String]) -> IpcResult<()> {
    let mut tx = db.begin().await
        .map_err(|e| IpcError::Internal { message: e.to_string() })?;
    for (i, id) in ids.iter().enumerate() {
        sqlx::query("UPDATE masking_rules SET sort_order = ? WHERE id = ?")
            .bind(i as i64)
            .bind(id)
            .execute(&mut *tx)
            .await
            .map_err(|e| IpcError::Internal { message: e.to_string() })?;
    }
    tx.commit().await
        .map_err(|e| IpcError::Internal { message: e.to_string() })?;
    Ok(())
}

// ─────────────────────────────────────────────
// Health Reports
// ─────────────────────────────────────────────

pub async fn health_report_save(db: &SqlitePool, report: &HealthReport) -> IpcResult<()> {
    let report_json = serde_json::to_string(report)
        .map_err(|e| IpcError::Internal { message: e.to_string() })?;
    let now = Utc::now().to_rfc3339();
    sqlx::query(
        "INSERT INTO health_reports (id, connection_id, score, report_json, created_at) VALUES (?, ?, ?, ?, ?)"
    )
    .bind(&report.id)
    .bind(&report.connection_id)
    .bind(report.score)
    .bind(&report_json)
    .bind(&now)
    .execute(db)
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })?;

    // Keep only 30 most recent reports
    sqlx::query(
        "DELETE FROM health_reports WHERE id NOT IN (SELECT id FROM health_reports ORDER BY created_at DESC LIMIT 30)"
    )
    .execute(db)
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })?;

    Ok(())
}

pub async fn health_report_list(db: &SqlitePool) -> IpcResult<Vec<HealthReport>> {
    let rows = sqlx::query_as::<_, (String, String, i64, String, String)>(
        "SELECT id, connection_id, score, report_json, created_at FROM health_reports ORDER BY created_at DESC LIMIT 30"
    )
    .fetch_all(db)
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })?;

    let mut reports = Vec::new();
    for (id, connection_id, score, report_json, created_at) in rows {
        let mut report: HealthReport = serde_json::from_str(&report_json)
            .map_err(|e| IpcError::Internal { message: e.to_string() })?;
        report.id = id;
        report.connection_id = connection_id;
        report.score = score as i32;
        report.created_at = created_at;
        reports.push(report);
    }
    Ok(reports)
}

pub async fn health_report_get(db: &SqlitePool, id: &str) -> IpcResult<HealthReport> {
    let row = sqlx::query_as::<_, (String, String, i64, String, String)>(
        "SELECT id, connection_id, score, report_json, created_at FROM health_reports WHERE id = ?"
    )
    .bind(id)
    .fetch_one(db)
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })?;

    let (id, connection_id, score, report_json, created_at) = row;
    let mut report: HealthReport = serde_json::from_str(&report_json)
        .map_err(|e| IpcError::Internal { message: e.to_string() })?;
    report.id = id;
    report.connection_id = connection_id;
    report.score = score as i32;
    report.created_at = created_at;
    Ok(report)
}
