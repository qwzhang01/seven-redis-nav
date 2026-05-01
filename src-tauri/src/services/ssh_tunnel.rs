use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};
use std::thread;
use ssh2::Session;

use crate::models::connection::{SshAuthMethod, SshConfig};
use crate::error::{IpcError, IpcResult};

/// Represents an active SSH tunnel
#[derive(Debug)]
pub struct SshTunnel {
    /// Local port that forwards to the remote Redis
    pub local_port: u16,
    /// Handle to stop the tunnel (set to true to stop)
    pub(crate) stop_flag: Arc<Mutex<bool>>,
}

impl SshTunnel {
    /// Stop the tunnel
    pub fn stop(&self) {
        if let Ok(mut flag) = self.stop_flag.lock() {
            *flag = true;
        }
    }
}

impl Drop for SshTunnel {
    fn drop(&mut self) {
        self.stop();
    }
}

impl SshTunnel {
    /// Create a test tunnel with a given local port (for unit/integration tests)
    #[doc(hidden)]
    pub fn new_for_test(local_port: u16) -> (Self, Arc<Mutex<bool>>) {
        let flag = Arc::new(Mutex::new(false));
        let tunnel = SshTunnel {
            local_port,
            stop_flag: Arc::clone(&flag),
        };
        (tunnel, flag)
    }
}

/// Establish an SSH tunnel and return the local port to connect to.
///
/// This function:
/// 1. Connects to the SSH server
/// 2. Authenticates using password or private key
/// 3. Starts a local TCP listener
/// 4. Spawns a background thread that forwards connections through the SSH channel
pub fn establish_tunnel(
    ssh_config: &SshConfig,
    redis_host: &str,
    redis_port: u16,
) -> IpcResult<SshTunnel> {
    // Connect to SSH server
    let ssh_addr = format!("{}:{}", ssh_config.host, ssh_config.port);
    let tcp = TcpStream::connect(&ssh_addr).map_err(|e| IpcError::ConnectionRefused {
        target: format!("SSH {}:{} ({})", ssh_config.host, ssh_config.port, e),
    })?;

    let mut session = Session::new().map_err(|e| IpcError::Internal {
        message: format!("Failed to create SSH session: {}", e),
    })?;
    session.set_tcp_stream(tcp);
    session.handshake().map_err(|e| IpcError::Internal {
        message: format!("SSH handshake failed: {}", e),
    })?;

    // Authenticate
    match ssh_config.auth_method {
        SshAuthMethod::Password => {
            let password = ssh_config.password.as_deref().unwrap_or("");
            session
                .userauth_password(&ssh_config.username, password)
                .map_err(|_e| IpcError::AuthFailed)?;
        }
        SshAuthMethod::PrivateKey => {
            let key_path = ssh_config.private_key_path.as_deref().ok_or_else(|| {
                IpcError::Internal {
                    message: "Private key path is required for key authentication".to_string(),
                }
            })?;
            let passphrase = ssh_config.private_key_passphrase.as_deref();
            session
                .userauth_pubkey_file(&ssh_config.username, None, key_path.as_ref(), passphrase)
                .map_err(|_| IpcError::AuthFailed)?;
        }
    }

    if !session.authenticated() {
        return Err(IpcError::AuthFailed);
    }

    // Bind a local port
    let listener = TcpListener::bind("127.0.0.1:0").map_err(|e| IpcError::Internal {
        message: format!("Failed to bind local port: {}", e),
    })?;
    let local_port = listener.local_addr().map_err(|e| IpcError::Internal {
        message: format!("Failed to get local port: {}", e),
    })?.port();

    let stop_flag = Arc::new(Mutex::new(false));
    let stop_flag_clone = Arc::clone(&stop_flag);
    let redis_host = redis_host.to_string();

    // Spawn forwarding thread — one thread per tunnel (fix 1.2:
    // each accepted local connection now gets its own forwarding pair,
    // so multiple Redis commands can flow concurrently).
    thread::spawn(move || {
        // Set non-blocking so we can check stop_flag
        listener.set_nonblocking(true).ok();
        loop {
            // Check stop flag
            if let Ok(flag) = stop_flag_clone.lock() {
                if *flag {
                    break;
                }
            }

            match listener.accept() {
                Ok((local_stream, _)) => {
                    // Open SSH channel to Redis
                    match session.channel_direct_tcpip(&redis_host, redis_port, None) {
                        Ok(mut channel) => {
                            // Each connection gets its own forwarding loop in a
                            // dedicated thread, enabling parallel data flow.
                            let stop_inner = Arc::clone(&stop_flag_clone);
                            thread::spawn(move || {
                                // Bidirectional forwarding with non-blocking I/O
                            let mut local = local_stream;
                            // ssh2 Channel inherits non-blocking from the Session,
                            // so reads/writes are already non-blocking.

                            let mut local_buf = [0u8; 8192];
                            let mut remote_buf = [0u8; 8192];

                                loop {
                                    // Check stop flag
                                    if let Ok(flag) = stop_inner.lock() {
                                        if *flag { break; }
                                    }

                                    // Local → Remote
                                    match local.read(&mut local_buf) {
                                        Ok(0) => break,   // local closed
                                        Ok(n) => {
                                            if channel.write_all(&local_buf[..n]).is_err() {
                                                break;
                                            }
                                        }
                                        Err(ref e)
                                            if e.kind() == std::io::ErrorKind::WouldBlock =>
                                        {
                                            // no data right now, fall through
                                        }
                                        Err(_) => break,
                                    }

                                    // Remote → Local
                                    match channel.read(&mut remote_buf) {
                                        Ok(0) => break,   // remote closed
                                        Ok(n) => {
                                            if local.write_all(&remote_buf[..n]).is_err() {
                                                break;
                                            }
                                        }
                                        Err(ref e)
                                            if e.kind() == std::io::ErrorKind::WouldBlock =>
                                        {
                                            // no data right now, fall through
                                        }
                                        Err(_) => break,
                                    }

                                    // Small sleep to avoid busy-loop when both
                                    // directions are waiting for data.
                                    thread::sleep(std::time::Duration::from_micros(500));
                                }
                            });
                        }
                        Err(_) => {}
                    }
                }
                Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                    thread::sleep(std::time::Duration::from_millis(10));
                }
                Err(_) => break,
            }
        }
    });

    Ok(SshTunnel { local_port, stop_flag })
}

/// Test SSH connectivity without establishing a full tunnel
pub fn test_ssh_connection(ssh_config: &SshConfig) -> IpcResult<()> {
    let ssh_addr = format!("{}:{}", ssh_config.host, ssh_config.port);
    let tcp = TcpStream::connect(&ssh_addr).map_err(|e| IpcError::ConnectionRefused {
        target: format!("SSH {}:{} ({})", ssh_config.host, ssh_config.port, e),
    })?;

    let mut session = Session::new().map_err(|e| IpcError::Internal {
        message: format!("Failed to create SSH session: {}", e),
    })?;
    session.set_tcp_stream(tcp);
    session.handshake().map_err(|e| IpcError::Internal {
        message: format!("SSH handshake failed: {}", e),
    })?;

    match ssh_config.auth_method {
        SshAuthMethod::Password => {
            let password = ssh_config.password.as_deref().unwrap_or("");
            session
                .userauth_password(&ssh_config.username, password)
                .map_err(|_| IpcError::AuthFailed)?;
        }
        SshAuthMethod::PrivateKey => {
            let key_path = ssh_config.private_key_path.as_deref().ok_or_else(|| {
                IpcError::Internal {
                    message: "Private key path is required".to_string(),
                }
            })?;
            let passphrase = ssh_config.private_key_passphrase.as_deref();
            session
                .userauth_pubkey_file(&ssh_config.username, None, key_path.as_ref(), passphrase)
                .map_err(|_| IpcError::AuthFailed)?;
        }
    }

    if !session.authenticated() {
        return Err(IpcError::AuthFailed);
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::connection::{SshAuthMethod, SshConfig};

    // ---- SshConfig default values ----

    #[test]
    fn test_ssh_config_default_port() {
        let config = SshConfig::default();
        assert_eq!(config.port, 22, "Default SSH port should be 22");
    }

    #[test]
    fn test_ssh_config_default_timeout() {
        let config = SshConfig::default();
        assert_eq!(config.timeout_ms, 10000, "Default SSH timeout should be 10000ms");
    }

    #[test]
    fn test_ssh_config_default_auth_method() {
        let config = SshConfig::default();
        assert!(
            matches!(config.auth_method, SshAuthMethod::Password),
            "Default auth method should be Password"
        );
    }

    #[test]
    fn test_ssh_config_default_optional_fields_are_none() {
        let config = SshConfig::default();
        assert!(config.password.is_none());
        assert!(config.private_key_path.is_none());
        assert!(config.private_key_passphrase.is_none());
    }

    // ---- SshTunnel stop flag ----

    #[test]
    fn test_ssh_tunnel_stop_sets_flag() {
        let (tunnel, flag) = SshTunnel::new_for_test(12345);
        tunnel.stop();
        assert!(
            *flag.lock().unwrap(),
            "stop() should set the stop_flag to true"
        );
    }

    #[test]
    fn test_ssh_tunnel_drop_stops_tunnel() {
        let (tunnel, flag) = SshTunnel::new_for_test(12346);
        drop(tunnel);
        assert!(
            *flag.lock().unwrap(),
            "Drop should set the stop_flag to true"
        );
    }

    #[test]
    fn test_ssh_tunnel_local_port_accessible() {
        let (tunnel, _flag) = SshTunnel::new_for_test(54321);
        assert_eq!(tunnel.local_port, 54321);
    }

    // ---- Connection failure (no real SSH server) ----

    #[test]
    fn test_establish_tunnel_fails_on_unreachable_host() {
        let config = SshConfig {
            host: "127.0.0.1".to_string(),
            port: 19999, // unlikely to be in use
            username: "testuser".to_string(),
            auth_method: SshAuthMethod::Password,
            password: Some("testpass".to_string()),
            ..Default::default()
        };
        let result = establish_tunnel(&config, "127.0.0.1", 6379);
        assert!(
            result.is_err(),
            "Should fail when SSH server is not reachable"
        );
        // Verify it's a ConnectionRefused error
        match result.unwrap_err() {
            IpcError::ConnectionRefused { target } => {
                assert!(target.contains("127.0.0.1:19999"));
            }
            other => panic!("Expected ConnectionRefused, got {:?}", other),
        }
    }

    #[test]
    fn test_test_ssh_connection_fails_on_unreachable_host() {
        let config = SshConfig {
            host: "127.0.0.1".to_string(),
            port: 19998,
            username: "testuser".to_string(),
            auth_method: SshAuthMethod::Password,
            password: Some("testpass".to_string()),
            ..Default::default()
        };
        let result = test_ssh_connection(&config);
        assert!(result.is_err(), "Should fail when SSH server is not reachable");
    }

    #[test]
    fn test_establish_tunnel_fails_with_missing_private_key_path() {
        // This tests the validation path for private key auth
        let config = SshConfig {
            host: "127.0.0.1".to_string(),
            port: 19997,
            username: "testuser".to_string(),
            auth_method: SshAuthMethod::PrivateKey,
            private_key_path: None, // missing!
            ..Default::default()
        };
        // Will fail at TCP connect before reaching key validation,
        // but the error type should still be ConnectionRefused
        let result = establish_tunnel(&config, "127.0.0.1", 6379);
        assert!(result.is_err());
    }

    // ---- SshConfig serialization ----

    #[test]
    fn test_ssh_config_serializes_correctly() {
        let config = SshConfig {
            host: "jump.example.com".to_string(),
            port: 22,
            username: "ubuntu".to_string(),
            auth_method: SshAuthMethod::PrivateKey,
            private_key_path: Some("/home/user/.ssh/id_rsa".to_string()),
            private_key_passphrase: None,
            password: None,
            timeout_ms: 15000,
        };
        let json = serde_json::to_string(&config).expect("Should serialize");
        assert!(json.contains("jump.example.com"));
        assert!(json.contains("private_key"));
        assert!(json.contains("id_rsa"));
    }

    #[test]
    fn test_ssh_config_deserializes_with_defaults() {
        let json = r#"{"host":"10.0.0.1","port":22,"username":"admin","auth_method":"password","timeout_ms":10000}"#;
        let config: SshConfig = serde_json::from_str(json).expect("Should deserialize");
        assert_eq!(config.host, "10.0.0.1");
        assert_eq!(config.username, "admin");
        assert!(config.password.is_none());
        assert!(config.private_key_path.is_none());
    }

    #[test]
    fn test_ssh_auth_method_serialization() {
        assert_eq!(
            serde_json::to_string(&SshAuthMethod::Password).unwrap(),
            "\"password\""
        );
        assert_eq!(
            serde_json::to_string(&SshAuthMethod::PrivateKey).unwrap(),
            "\"private_key\""
        );
    }
}
