use serde::{Deserialize, Serialize};
use crate::models::data::RedisValue;

/// Connection info embedded in export file.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportConnectionInfo {
    pub host: String,
    pub port: u16,
    pub db: u8,
}

/// A single exported key entry.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportKey {
    pub key: String,
    #[serde(rename = "type")]
    pub key_type: String,
    pub ttl: i64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub value: Option<RedisValue>,
    /// Set to true when value was truncated due to size limit.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub truncated: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub size_bytes: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub preview: Option<String>,
}

/// Top-level export file structure.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RedisExport {
    pub version: String,
    pub connection: ExportConnectionInfo,
    pub exported_at: String,
    pub keys: Vec<ExportKey>,
}

impl RedisExport {
    pub fn new(host: &str, port: u16, db: u8) -> Self {
        Self {
            version: "1.0".to_string(),
            connection: ExportConnectionInfo { host: host.to_string(), port, db },
            exported_at: chrono::Utc::now().to_rfc3339(),
            keys: Vec::new(),
        }
    }
}

/// Result of an import operation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportResult {
    pub success: u64,
    pub skipped: u64,
    pub failed: u64,
    pub errors: Vec<String>,
}
