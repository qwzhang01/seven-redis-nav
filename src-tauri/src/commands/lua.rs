use redis::Value as RedisValue;
use sqlx::SqlitePool;
use tauri::State;

use crate::error::{IpcError, IpcResult};
use crate::models::connection::ConnId;
use crate::models::lua::{LuaEvalResult, LuaScript};
use crate::services::connection_manager::SharedConnectionManager;
use crate::services::terminal::format_redis_value;
use crate::utils::config_store;

// ─────────────────────────────────────────────
// EVAL / EVALSHA
// ─────────────────────────────────────────────

/// Execute a Lua script via EVAL.
#[tauri::command]
pub async fn lua_eval(
    conn_id: ConnId,
    script: String,
    keys: Vec<String>,
    argv: Vec<String>,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<LuaEvalResult> {
    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;

    let num_keys = keys.len();
    let mut cmd = redis::cmd("EVAL");
    cmd.arg(&script).arg(num_keys);
    for k in &keys { cmd.arg(k); }
    for a in &argv { cmd.arg(a); }

    let result: Result<RedisValue, _> = cmd.query_async(&mut guard.conn).await;
    Ok(match result {
        Ok(val) => LuaEvalResult { output: format_redis_value(&val, 0), is_error: false, sha1: None },
        Err(e)  => LuaEvalResult { output: format!("(error) {e}"), is_error: true, sha1: None },
    })
}

/// Execute a Lua script via EVALSHA.
#[tauri::command]
pub async fn lua_evalsha(
    conn_id: ConnId,
    sha1: String,
    keys: Vec<String>,
    argv: Vec<String>,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<LuaEvalResult> {
    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;

    let num_keys = keys.len();
    let mut cmd = redis::cmd("EVALSHA");
    cmd.arg(&sha1).arg(num_keys);
    for k in &keys { cmd.arg(k); }
    for a in &argv { cmd.arg(a); }

    let result: Result<RedisValue, _> = cmd.query_async(&mut guard.conn).await;
    Ok(match result {
        Ok(val) => LuaEvalResult { output: format_redis_value(&val, 0), is_error: false, sha1: Some(sha1) },
        Err(e)  => LuaEvalResult { output: format!("(error) {e}"), is_error: true, sha1: None },
    })
}

/// Load a Lua script into Redis script cache, returns SHA1.
#[tauri::command]
pub async fn lua_script_load(
    conn_id: ConnId,
    script: String,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<String> {
    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;

    let sha1: String = redis::cmd("SCRIPT")
        .arg("LOAD")
        .arg(&script)
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(sha1)
}

/// Check if a script SHA1 exists in Redis script cache.
#[tauri::command]
pub async fn lua_script_exists(
    conn_id: ConnId,
    sha1: String,
    manager: State<'_, SharedConnectionManager>,
) -> IpcResult<bool> {
    let session = {
        let mgr = manager.lock().await;
        mgr.get_session(&conn_id)?
    };
    let mut guard = session.lock().await;

    let result: Vec<i64> = redis::cmd("SCRIPT")
        .arg("EXISTS")
        .arg(&sha1)
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(result.first().copied().unwrap_or(0) == 1)
}

// ─────────────────────────────────────────────
// History (SQLite)
// ─────────────────────────────────────────────

/// Save a Lua script to history.
#[tauri::command]
pub async fn lua_history_save(
    script: String,
    name: String,
    db: State<'_, SqlitePool>,
) -> IpcResult<LuaScript> {
    config_store::lua_script_save(&db, &script, &name).await
}

/// List Lua script history (latest 100).
#[tauri::command]
pub async fn lua_history_list(db: State<'_, SqlitePool>) -> IpcResult<Vec<LuaScript>> {
    config_store::lua_script_list(&db).await
}

/// Delete a Lua script from history.
#[tauri::command]
pub async fn lua_history_delete(id: String, db: State<'_, SqlitePool>) -> IpcResult<()> {
    config_store::lua_script_delete(&db, &id).await
}

/// Rename a Lua script in history.
#[tauri::command]
pub async fn lua_history_rename(id: String, name: String, db: State<'_, SqlitePool>) -> IpcResult<()> {
    config_store::lua_script_rename(&db, &id, &name).await
}
