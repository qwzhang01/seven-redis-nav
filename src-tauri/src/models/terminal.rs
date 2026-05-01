use serde::{Deserialize, Serialize};

/// CLI command reply
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CliReply {
    pub output: String,
    pub is_error: bool,
}

/// CLI history entry
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct CliHistoryEntry {
    pub id: i64,
    pub command: String,
    pub created_at: String,
}

/// Dangerous commands that require confirmation
pub const DANGEROUS_COMMANDS: &[&str] = &[
    "FLUSHDB",
    "FLUSHALL",
    "SHUTDOWN",
    "DEBUG",
    "CONFIG",  // CONFIG SET requirepass
];
