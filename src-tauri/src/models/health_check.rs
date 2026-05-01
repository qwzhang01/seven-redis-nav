use serde::{Deserialize, Serialize};

/// Health level for a single indicator.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum HealthLevel {
    Normal,
    Warning,
    Danger,
}

impl HealthLevel {
    /// Score contribution: Normal=10, Warning=5, Danger=0
    pub fn score(&self) -> i32 {
        match self {
            HealthLevel::Normal  => 10,
            HealthLevel::Warning => 5,
            HealthLevel::Danger  => 0,
        }
    }
}

/// A single health check indicator.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthIndicator {
    pub name: String,
    pub value: String,
    pub level: HealthLevel,
    pub score: i32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub suggestion: Option<String>,
}

/// Full health check report.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthReport {
    pub id: String,
    pub connection_id: String,
    /// Overall health score 0-100 (sum of all indicator scores).
    pub score: i32,
    pub indicators: Vec<HealthIndicator>,
    pub created_at: String,
}

impl HealthReport {
    pub fn new(connection_id: &str, indicators: Vec<HealthIndicator>) -> Self {
        let score: i32 = indicators.iter().map(|i| i.score).sum();
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            connection_id: connection_id.to_string(),
            score,
            indicators,
            created_at: chrono::Utc::now().to_rfc3339(),
        }
    }
}
