use serde::{Deserialize, Serialize};

/// Memory statistics for a single key.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyMemoryStat {
    pub key: String,
    pub key_type: String,
    pub memory_bytes: u64,
    pub encoding: String,
    pub element_count: u64,
}

/// Progress event payload for key scan.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScanProgress {
    pub scanned: u64,
    pub total_estimate: u64,
    pub top_keys: Vec<KeyMemoryStat>,
    pub is_done: bool,
}

/// A single TTL distribution bucket.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TtlBucket {
    pub label: String,
    pub count: u64,
    pub percentage: f64,
}

/// TTL distribution analysis result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TtlDistribution {
    pub total_sampled: u64,
    pub buckets: Vec<TtlBucket>,
    pub expiring_soon_count: u64,
    pub expiring_soon_warning: bool,
}

/// Data masking rule stored in SQLite.
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct MaskingRule {
    pub id: String,
    pub pattern: String,
    pub mask_char: String,
    pub enabled: bool,
    pub sort_order: i64,
}
