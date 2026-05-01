use serde::{Deserialize, Serialize};

// ---- Phase 0 types (kept for connection_test) ----

#[derive(Debug, Deserialize)]
pub struct ConnectionTestReq {
    pub host: String,
    pub port: u16,
    pub password: Option<String>,
    pub timeout_ms: Option<u64>,
}

#[derive(Debug, Serialize)]
pub struct PingResult {
    pub latency_ms: u32,
    pub server_version: Option<String>,
}

// ---- Phase 1 types ----

/// Unique connection config ID (UUID v4 string)
pub type ConnId = String;

// ---- Phase 2: SSH/TLS connection types ----

/// Connection type selector
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(rename_all = "snake_case")]
pub enum ConnectionType {
    #[default]
    Tcp,
    Ssh,
    Tls,
    Sentinel,
    Cluster,
}

/// SSH authentication method
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(rename_all = "snake_case")]
pub enum SshAuthMethod {
    #[default]
    Password,
    PrivateKey,
}

/// SSH tunnel configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SshConfig {
    /// SSH server host
    pub host: String,
    /// SSH server port (default: 22)
    #[serde(default = "default_ssh_port")]
    pub port: u16,
    /// SSH username
    pub username: String,
    /// Authentication method
    #[serde(default)]
    pub auth_method: SshAuthMethod,
    /// Password (used when auth_method = Password)
    pub password: Option<String>,
    /// Path to private key file (used when auth_method = PrivateKey)
    pub private_key_path: Option<String>,
    /// Passphrase for private key (if encrypted)
    pub private_key_passphrase: Option<String>,
    /// Connection timeout in milliseconds
    #[serde(default = "default_ssh_timeout")]
    pub timeout_ms: u64,
}

impl Default for SshConfig {
    fn default() -> Self {
        Self {
            host: String::new(),
            port: default_ssh_port(),
            username: String::new(),
            auth_method: SshAuthMethod::default(),
            password: None,
            private_key_path: None,
            private_key_passphrase: None,
            timeout_ms: default_ssh_timeout(),
        }
    }
}

fn default_ssh_port() -> u16 { 22 }
fn default_ssh_timeout() -> u64 { 10000 }

/// TLS encryption configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TlsConfig {
    /// Whether to verify server certificate (default: true)
    #[serde(default = "default_true")]
    pub verify_cert: bool,
    /// Path to CA certificate file (PEM format)
    pub ca_cert_path: Option<String>,
    /// Path to client certificate file (PEM format)
    pub client_cert_path: Option<String>,
    /// Path to client private key file (PEM format)
    pub client_key_path: Option<String>,
    /// Minimum TLS version ("tls1.2" or "tls1.3")
    pub min_tls_version: Option<String>,
    /// Server name for SNI (if different from host)
    pub server_name: Option<String>,
}

impl Default for TlsConfig {
    fn default() -> Self {
        Self {
            verify_cert: default_true(),
            ca_cert_path: None,
            client_cert_path: None,
            client_key_path: None,
            min_tls_version: None,
            server_name: None,
        }
    }
}

fn default_true() -> bool { true }

/// Full connection configuration (includes password for in-memory use)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectionConfig {
    pub id: ConnId,
    pub name: String,
    pub group_name: String,
    pub host: String,
    pub port: u16,
    pub password: Option<String>,
    /// Whether a password is stored in Keychain for this connection.
    /// Set to `true` in list responses; `password` will be `None` in that case.
    #[serde(default)]
    pub has_password: bool,
    pub auth_db: u8,
    pub timeout_ms: u64,
    pub sort_order: i32,
    // ---- Phase 2: advanced connection fields ----
    /// Connection type (TCP / SSH / TLS / Sentinel / Cluster)
    #[serde(default)]
    pub connection_type: ConnectionType,
    /// SSH tunnel configuration (present when connection_type = Ssh)
    pub ssh_config: Option<SshConfig>,
    /// TLS encryption configuration (present when connection_type = Tls)
    pub tls_config: Option<TlsConfig>,
    /// Sentinel node addresses ("host:port") — required when connection_type = Sentinel
    #[serde(default)]
    pub sentinel_nodes: Option<Vec<String>>,
    /// Sentinel master name — required when connection_type = Sentinel
    #[serde(default)]
    pub master_name: Option<String>,
    /// Cluster seed node addresses ("host:port") — required when connection_type = Cluster
    #[serde(default)]
    pub cluster_nodes: Option<Vec<String>>,
}

/// Connection metadata stored in SQLite (no password)
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct ConnectionMeta {
    pub id: ConnId,
    pub name: String,
    pub group_name: String,
    pub host: String,
    pub port: i64,
    pub auth_db: i64,
    pub timeout_ms: i64,
    pub keychain_key: Option<String>,
    pub sort_order: i64,
    pub created_at: String,
    pub updated_at: String,
    // Phase 2 fields
    #[sqlx(default)]
    pub connection_type: Option<String>,
    #[sqlx(default)]
    pub ssh_config: Option<String>,   // JSON blob
    #[sqlx(default)]
    pub tls_config: Option<String>,   // JSON blob
    #[sqlx(default)]
    pub sentinel_nodes: Option<String>, // JSON blob: Vec<String>
    #[sqlx(default)]
    pub master_name: Option<String>,
    #[sqlx(default)]
    pub cluster_nodes: Option<String>, // JSON blob: Vec<String>
}

/// Database statistics from INFO keyspace
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DbStat {
    pub index: u8,
    pub key_count: u64,
}

/// Connection session state
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum ConnectionState {
    Connected,
    Disconnected,
    Reconnecting,
}
