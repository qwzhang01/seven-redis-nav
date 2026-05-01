use serde::{Deserialize, Serialize};

/// A saved Lua script entry in SQLite.
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct LuaScript {
    pub id: String,
    pub name: String,
    pub script: String,
    pub created_at: String,
    pub last_used_at: String,
}

/// Result of a Lua EVAL / EVALSHA execution.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LuaEvalResult {
    /// Human-readable output (formatted Redis value or error message).
    pub output: String,
    /// Whether the execution resulted in an error.
    pub is_error: bool,
    /// SHA1 hash — populated only when the command was SCRIPT LOAD.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub sha1: Option<String>,
}
