use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;
use redis::aio::MultiplexedConnection;

use crate::models::connection::{ConnId, ConnectionConfig, ConnectionState, ConnectionType, DbStat};
use crate::error::{IpcError, IpcResult};
use crate::services::ssh_tunnel::SshTunnel;

/// Holds an active Redis session.
///
/// Wrapped in `Arc<Mutex<..>>` so that per-session Redis operations only lock
/// the individual session, not the entire ConnectionManager (fix 2.1: avoid
/// serialising all Redis operations across different connections).
#[allow(dead_code)]
pub struct Session {
    pub conn: MultiplexedConnection,
    pub config: ConnectionConfig,
    pub state: ConnectionState,
    pub current_db: u8,
    /// SSH tunnel handle (kept alive for SSH connections)
    pub ssh_tunnel: Option<SshTunnel>,
}

/// Thread-safe handle to a single session.
pub type SharedSession = Arc<Mutex<Session>>;

/// Global connection manager (session pool).
///
/// The manager-level Mutex is only held briefly to look up / insert / remove
/// sessions. Once a `SharedSession` is obtained, the caller locks only that
/// session's Mutex for the duration of the Redis command — other sessions
/// proceed concurrently.
pub struct ConnectionManager {
    sessions: HashMap<ConnId, SharedSession>,
}

impl ConnectionManager {
    pub fn new() -> Self {
        Self {
            sessions: HashMap::new(),
        }
    }

    /// Open a new Redis connection and store in session pool
    pub async fn open(&mut self, config: ConnectionConfig) -> IpcResult<()> {
        let id = config.id.clone();
        self.open_with_id(id, config).await
    }

    /// Open a new Redis connection with a custom ConnId (used for temporary connections)
    pub async fn open_with_id(&mut self, id: ConnId, config: ConnectionConfig) -> IpcResult<()> {
        match config.connection_type {
            ConnectionType::Ssh => self.open_ssh_connection(id, config).await,
            ConnectionType::Tls => self.open_tls_connection(id, config).await,
            ConnectionType::Tcp => self.open_tcp_connection(id, config).await,
            ConnectionType::Sentinel => self.open_sentinel_connection(id, config).await,
            ConnectionType::Cluster => self.open_cluster_connection(id, config).await,
        }
    }

    /// Unified post-connect hook: AUTH + SELECT + PING.
    async fn post_connect(
        conn: &mut MultiplexedConnection,
        config: &ConnectionConfig,
        url_carries_auth: bool,
    ) -> IpcResult<()> {
        if !url_carries_auth {
            if let Some(ref pw) = config.password {
                redis::cmd("AUTH")
                    .arg(pw.as_str())
                    .query_async::<()>(&mut *conn)
                    .await
                    .map_err(|_| IpcError::AuthFailed)?;
            }
        }

        if config.auth_db > 0 {
            redis::cmd("SELECT")
                .arg(config.auth_db)
                .query_async::<()>(&mut *conn)
                .await
                .map_err(|e| IpcError::Redis { message: e.to_string() })?;
        }

        redis::cmd("PING")
            .query_async::<String>(&mut *conn)
            .await
            .map_err(|e| IpcError::Redis { message: format!("PING failed: {}", e) })?;

        Ok(())
    }

    /// Helper: insert a newly created session into the pool.
    fn insert_session(
        &mut self,
        id: ConnId,
        conn: MultiplexedConnection,
        config: ConnectionConfig,
        current_db: u8,
        ssh_tunnel: Option<SshTunnel>,
    ) {
        self.sessions.insert(
            id,
            Arc::new(Mutex::new(Session {
                conn,
                config,
                state: ConnectionState::Connected,
                current_db,
                ssh_tunnel,
            })),
        );
    }

    /// Open a plain TCP Redis connection
    async fn open_tcp_connection(&mut self, id: ConnId, config: ConnectionConfig) -> IpcResult<()> {
        let addr = format!("redis://{}:{}", config.host, config.port);
        let client = redis::Client::open(addr.as_str()).map_err(|e| IpcError::ConnectionRefused {
            target: format!("{}:{} ({})", config.host, config.port, e),
        })?;

        let mut conn = client
            .get_multiplexed_async_connection()
            .await
            .map_err(|e| IpcError::ConnectionRefused {
                target: format!("{}:{} ({})", config.host, config.port, e),
            })?;

        Self::post_connect(&mut conn, &config, false).await?;

        let current_db = config.auth_db;
        self.insert_session(id, conn, config, current_db, None);
        Ok(())
    }

    /// Open a Redis connection through an SSH tunnel
    async fn open_ssh_connection(&mut self, id: ConnId, config: ConnectionConfig) -> IpcResult<()> {
        let ssh_cfg = config.ssh_config.as_ref().ok_or_else(|| IpcError::Internal {
            message: "SSH config is required for SSH connection type".to_string(),
        })?;

        let tunnel = crate::services::ssh_tunnel::establish_tunnel(
            ssh_cfg,
            &config.host,
            config.port,
        )?;

        let local_port = tunnel.local_port;
        let addr = format!("redis://127.0.0.1:{}", local_port);
        let client = redis::Client::open(addr.as_str()).map_err(|e| IpcError::ConnectionRefused {
            target: format!("SSH tunnel -> {}:{} ({})", config.host, config.port, e),
        })?;

        let mut conn = client
            .get_multiplexed_async_connection()
            .await
            .map_err(|e| IpcError::ConnectionRefused {
                target: format!("SSH tunnel -> {}:{} ({})", config.host, config.port, e),
            })?;

        Self::post_connect(&mut conn, &config, false).await?;

        let current_db = config.auth_db;
        self.insert_session(id, conn, config, current_db, Some(tunnel));
        Ok(())
    }

    /// Open a TLS-encrypted Redis connection
    async fn open_tls_connection(&mut self, id: ConnId, config: ConnectionConfig) -> IpcResult<()> {
        let tls_cfg = config.tls_config.as_ref().ok_or_else(|| IpcError::Internal {
            message: "TLS config is required for TLS connection type".to_string(),
        })?;

        crate::services::tls_connection::validate_tls_config(tls_cfg)?;

        let addr = crate::services::tls_connection::build_tls_redis_url(
            &config.host,
            config.port,
            config.password.as_deref(),
        );

        let client = redis::Client::open(addr.as_str()).map_err(|e| IpcError::ConnectionRefused {
            target: format!("TLS {}:{} ({})", config.host, config.port, e),
        })?;

        let mut conn = client
            .get_multiplexed_async_connection()
            .await
            .map_err(|e| IpcError::ConnectionRefused {
                target: format!("TLS {}:{} ({})", config.host, config.port, e),
            })?;

        Self::post_connect(&mut conn, &config, true).await?;

        let current_db = config.auth_db;
        self.insert_session(id, conn, config, current_db, None);
        Ok(())
    }

    /// Open a Sentinel-mode connection
    async fn open_sentinel_connection(
        &mut self,
        id: ConnId,
        config: ConnectionConfig,
    ) -> IpcResult<()> {
        let nodes = config
            .sentinel_nodes
            .as_ref()
            .filter(|v| !v.is_empty())
            .ok_or_else(|| IpcError::Internal {
                message: "Sentinel nodes list is required for Sentinel connection".to_string(),
            })?;
        let master_name = config
            .master_name
            .as_ref()
            .filter(|s| !s.is_empty())
            .ok_or_else(|| IpcError::Internal {
                message: "Master name is required for Sentinel connection".to_string(),
            })?;

        let sentinel_urls: Vec<String> = nodes
            .iter()
            .map(|addr| format!("redis://{}", addr))
            .collect();

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

        Self::post_connect(&mut conn, &config, false).await?;

        let current_db = config.auth_db;
        self.insert_session(id, conn, config, current_db, None);
        Ok(())
    }

    /// Open a Cluster-mode connection.
    async fn open_cluster_connection(
        &mut self,
        id: ConnId,
        config: ConnectionConfig,
    ) -> IpcResult<()> {
        let nodes = config
            .cluster_nodes
            .as_ref()
            .filter(|v| !v.is_empty())
            .ok_or_else(|| IpcError::Internal {
                message: "Cluster nodes list is required for Cluster connection".to_string(),
            })?;

        let mut last_err: Option<String> = None;
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
                    continue;
                }
            };

            match client.get_multiplexed_async_connection().await {
                Ok(mut conn) => {
                    let url_carries_auth = config.password.is_some();
                    Self::post_connect(&mut conn, &config, url_carries_auth).await?;

                    let current_db = config.auth_db;
                    self.insert_session(id, conn, config, current_db, None);
                    return Ok(());
                }
                Err(e) => {
                    last_err = Some(format!("{}: {}", seed, e));
                }
            }
        }

        Err(IpcError::ConnectionRefused {
            target: format!(
                "All cluster seed nodes unreachable: {}",
                last_err.unwrap_or_else(|| "unknown".to_string())
            ),
        })
    }

    /// Close a session and remove from pool
    pub fn close(&mut self, conn_id: &str) {
        self.sessions.remove(conn_id);
    }

    /// Obtain the `SharedSession` handle for a connection.
    ///
    /// The caller can then `lock().await` the handle to perform Redis
    /// operations — other sessions are **not** blocked.
    pub fn get_session(&self, conn_id: &str) -> IpcResult<SharedSession> {
        self.sessions
            .get(conn_id)
            .cloned()
            .ok_or_else(|| IpcError::NotFound { key: conn_id.to_string() })
    }

    /// Get session config (cloned) — no session lock needed for clone
    #[allow(dead_code)]
    pub async fn get_config(&self, conn_id: &str) -> IpcResult<ConnectionConfig> {
        let session = self.get_session(conn_id)?;
        let guard = session.lock().await;
        Ok(guard.config.clone())
    }

    /// Get current DB for a session
    pub async fn get_current_db(&self, conn_id: &str) -> IpcResult<u8> {
        let session = self.get_session(conn_id)?;
        let guard = session.lock().await;
        Ok(guard.current_db)
    }

    /// Update current DB for a session
    pub async fn set_current_db(&self, conn_id: &str, db: u8) -> IpcResult<()> {
        let session = self.get_session(conn_id)?;
        let mut guard = session.lock().await;
        guard.current_db = db;
        Ok(())
    }

    /// List all active session IDs
    pub fn active_sessions(&self) -> Vec<ConnId> {
        self.sessions.keys().cloned().collect()
    }

    /// Check if a session is active
    #[allow(dead_code)]
    pub fn is_connected(&self, conn_id: &str) -> bool {
        self.sessions.contains_key(conn_id)
    }

    /// Parse INFO keyspace output into DbStat list
    pub fn parse_keyspace(info: &str) -> Vec<DbStat> {
        let mut stats = Vec::new();
        for line in info.lines() {
            if line.starts_with("db") {
                let parts: Vec<&str> = line.splitn(2, ':').collect();
                if parts.len() == 2 {
                    let db_index: u8 = parts[0].trim_start_matches("db").parse().unwrap_or(0);
                    let key_count = parts[1]
                        .split(',')
                        .find(|s| s.starts_with("keys="))
                        .and_then(|s| s.trim_start_matches("keys=").parse().ok())
                        .unwrap_or(0);
                    stats.push(DbStat { index: db_index, key_count });
                }
            }
        }
        stats
    }

    /// Get a Redis Client for a session (used to create PubSub/Monitor connections).
    pub async fn get_client(&self, conn_id: &str) -> IpcResult<redis::Client> {
        let session = self.get_session(conn_id)?;
        let guard = session.lock().await;
        let config = &guard.config;

        let addr = match config.connection_type {
            ConnectionType::Tls => {
                crate::services::tls_connection::build_tls_redis_url(
                    &config.host,
                    config.port,
                    config.password.as_deref(),
                )
            }
            ConnectionType::Ssh => {
                if let Some(ref tunnel) = guard.ssh_tunnel {
                    if let Some(ref pw) = config.password {
                        format!("redis://:{}@127.0.0.1:{}", pw, tunnel.local_port)
                    } else {
                        format!("redis://127.0.0.1:{}", tunnel.local_port)
                    }
                } else {
                    if let Some(ref pw) = config.password {
                        format!("redis://:{}@{}:{}", pw, config.host, config.port)
                    } else {
                        format!("redis://{}:{}", config.host, config.port)
                    }
                }
            }
            ConnectionType::Tcp | ConnectionType::Sentinel | ConnectionType::Cluster => {
                if let Some(ref pw) = config.password {
                    format!("redis://:{}@{}:{}", pw, config.host, config.port)
                } else {
                    format!("redis://{}:{}", config.host, config.port)
                }
            }
        };

        redis::Client::open(addr.as_str()).map_err(|e| IpcError::ConnectionRefused {
            target: format!("{}:{} ({})", config.host, config.port, e),
        })
    }

    /// Get session config (cloned) for creating dedicated connections with auth
    #[allow(dead_code)]
    pub async fn get_config_cloned(&self, conn_id: &str) -> IpcResult<ConnectionConfig> {
        self.get_config(conn_id).await
    }
}

/// Thread-safe wrapper around ConnectionManager
pub type SharedConnectionManager = Arc<Mutex<ConnectionManager>>;

pub fn new_shared_manager() -> SharedConnectionManager {
    Arc::new(Mutex::new(ConnectionManager::new()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_manager_has_no_sessions() {
        let mgr = ConnectionManager::new();
        assert!(mgr.active_sessions().is_empty());
    }

    #[test]
    fn test_close_nonexistent_session_does_not_panic() {
        let mut mgr = ConnectionManager::new();
        mgr.close("nonexistent-id");
    }

    #[test]
    fn test_get_conn_mut_nonexistent_returns_not_found() {
        let rt = tokio::runtime::Runtime::new().unwrap();
        let mgr = ConnectionManager::new();
        rt.block_on(async {
            let result = mgr.get_session("nonexistent-id");
            assert!(result.is_err());
        });
    }

    #[test]
    fn test_get_current_db_nonexistent_returns_not_found() {
        let rt = tokio::runtime::Runtime::new().unwrap();
        let mgr = ConnectionManager::new();
        rt.block_on(async {
            let result = mgr.get_current_db("nonexistent-id").await;
            assert!(result.is_err());
        });
    }

    #[test]
    fn test_set_current_db_nonexistent_returns_not_found() {
        let rt = tokio::runtime::Runtime::new().unwrap();
        let mgr = ConnectionManager::new();
        rt.block_on(async {
            let result = mgr.set_current_db("nonexistent-id", 5).await;
            assert!(result.is_err());
        });
    }

    #[test]
    fn test_is_connected_returns_false_for_nonexistent() {
        let mgr = ConnectionManager::new();
        assert!(!mgr.is_connected("nonexistent-id"));
    }

    #[test]
    fn test_parse_keyspace_empty() {
        let info = "# Keyspace\n";
        let stats = ConnectionManager::parse_keyspace(info);
        assert!(stats.is_empty());
    }

    #[test]
    fn test_parse_keyspace_single_db() {
        let info = "# Keyspace\ndb0:keys=12847,expires=0,avg_ttl=0\n";
        let stats = ConnectionManager::parse_keyspace(info);
        assert_eq!(stats.len(), 1);
        assert_eq!(stats[0].index, 0);
        assert_eq!(stats[0].key_count, 12847);
    }

    #[test]
    fn test_parse_keyspace_multiple_dbs() {
        let info = "# Keyspace\ndb0:keys=100,expires=5,avg_ttl=1000\ndb1:keys=50,expires=2,avg_ttl=500\ndb15:keys=1,expires=0,avg_ttl=0\n";
        let stats = ConnectionManager::parse_keyspace(info);
        assert_eq!(stats.len(), 3);
        assert_eq!(stats[0].index, 0);
        assert_eq!(stats[0].key_count, 100);
        assert_eq!(stats[1].index, 1);
        assert_eq!(stats[1].key_count, 50);
        assert_eq!(stats[2].index, 15);
        assert_eq!(stats[2].key_count, 1);
    }

    #[test]
    fn test_parse_keyspace_ignores_non_db_lines() {
        let info = "# Keyspace\nsome_other_line\ndb0:keys=42,expires=0,avg_ttl=0\n# Comment\n";
        let stats = ConnectionManager::parse_keyspace(info);
        assert_eq!(stats.len(), 1);
        assert_eq!(stats[0].key_count, 42);
    }

    #[test]
    fn test_parse_keyspace_handles_large_key_count() {
        let info = "db0:keys=9999999,expires=100000,avg_ttl=5000\n";
        let stats = ConnectionManager::parse_keyspace(info);
        assert_eq!(stats.len(), 1);
        assert_eq!(stats[0].key_count, 9999999);
    }

    #[test]
    fn test_parse_keyspace_malformed_line() {
        let info = "db0keys=100,expires=0,avg_ttl=0\n";
        let stats = ConnectionManager::parse_keyspace(info);
        assert!(stats.is_empty());
    }

    #[test]
    fn test_new_shared_manager_creates_arc_mutex() {
        let mgr = new_shared_manager();
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let locked = mgr.lock().await;
            assert!(locked.active_sessions().is_empty());
        });
    }
}
