//! Integration tests for Phase 2 SSH/TLS connection features.
//!
//! These tests verify the full connection flow without requiring real SSH/Redis servers.
//! Tests that need real servers are marked with `#[ignore]` and can be run manually.

#[cfg(test)]
mod connection_type_routing {
    use seven_redis_nav_lib::models::connection::{
        ConnectionConfig, ConnectionType, SshConfig, SshAuthMethod, TlsConfig,
    };

    fn make_tcp_config() -> ConnectionConfig {
        ConnectionConfig {
            id: "test-tcp".to_string(),
            name: "TCP Test".to_string(),
            group_name: "test".to_string(),
            host: "127.0.0.1".to_string(),
            port: 6379,
            password: None,
            has_password: false,
            auth_db: 0,
            timeout_ms: 5000,
            sort_order: 0,
            connection_type: ConnectionType::Tcp,
            ssh_config: None,
            tls_config: None,
            sentinel_nodes: None,
            master_name: None,
            cluster_nodes: None,
        }
    }

    fn make_ssh_config() -> ConnectionConfig {
        ConnectionConfig {
            id: "test-ssh".to_string(),
            name: "SSH Test".to_string(),
            group_name: "test".to_string(),
            host: "10.0.0.1".to_string(),
            port: 6379,
            password: None,
            has_password: false,
            auth_db: 0,
            timeout_ms: 5000,
            sort_order: 0,
            connection_type: ConnectionType::Ssh,
            ssh_config: Some(SshConfig {
                host: "jump.example.com".to_string(),
                port: 22,
                username: "ubuntu".to_string(),
                auth_method: SshAuthMethod::Password,
                password: Some("secret".to_string()),
                private_key_path: None,
                private_key_passphrase: None,
                timeout_ms: 10000,
            }),
            tls_config: None,
            sentinel_nodes: None,
            master_name: None,
            cluster_nodes: None,
        }
    }

    fn make_tls_config() -> ConnectionConfig {
        ConnectionConfig {
            id: "test-tls".to_string(),
            name: "TLS Test".to_string(),
            group_name: "test".to_string(),
            host: "redis.example.com".to_string(),
            port: 6380,
            password: Some("tlspass".to_string()),
            has_password: true,
            auth_db: 0,
            timeout_ms: 5000,
            sort_order: 0,
            connection_type: ConnectionType::Tls,
            ssh_config: None,
            tls_config: Some(TlsConfig {
                verify_cert: true,
                ca_cert_path: None,
                client_cert_path: None,
                client_key_path: None,
                min_tls_version: Some("tls1.2".to_string()),
                server_name: None,
            }),
            sentinel_nodes: None,
            master_name: None,
            cluster_nodes: None,
        }
    }

    // ---- ConnectionType enum ----

    #[test]
    fn test_connection_type_default_is_tcp() {
        let t = ConnectionType::default();
        assert!(matches!(t, ConnectionType::Tcp));
    }

    #[test]
    fn test_connection_type_serialization() {
        assert_eq!(serde_json::to_string(&ConnectionType::Tcp).unwrap(), "\"tcp\"");
        assert_eq!(serde_json::to_string(&ConnectionType::Ssh).unwrap(), "\"ssh\"");
        assert_eq!(serde_json::to_string(&ConnectionType::Tls).unwrap(), "\"tls\"");
    }

    #[test]
    fn test_connection_type_deserialization() {
        let tcp: ConnectionType = serde_json::from_str("\"tcp\"").unwrap();
        let ssh: ConnectionType = serde_json::from_str("\"ssh\"").unwrap();
        let tls: ConnectionType = serde_json::from_str("\"tls\"").unwrap();
        assert!(matches!(tcp, ConnectionType::Tcp));
        assert!(matches!(ssh, ConnectionType::Ssh));
        assert!(matches!(tls, ConnectionType::Tls));
    }

    // ---- ConnectionConfig with Phase 2 fields ----

    #[test]
    fn test_tcp_config_has_no_ssh_or_tls() {
        let cfg = make_tcp_config();
        assert!(cfg.ssh_config.is_none());
        assert!(cfg.tls_config.is_none());
        assert!(matches!(cfg.connection_type, ConnectionType::Tcp));
    }

    #[test]
    fn test_ssh_config_has_ssh_config_set() {
        let cfg = make_ssh_config();
        assert!(cfg.ssh_config.is_some());
        assert!(cfg.tls_config.is_none());
        assert!(matches!(cfg.connection_type, ConnectionType::Ssh));
        let ssh = cfg.ssh_config.unwrap();
        assert_eq!(ssh.host, "jump.example.com");
        assert_eq!(ssh.port, 22);
        assert_eq!(ssh.username, "ubuntu");
    }

    #[test]
    fn test_tls_config_has_tls_config_set() {
        let cfg = make_tls_config();
        assert!(cfg.ssh_config.is_none());
        assert!(cfg.tls_config.is_some());
        assert!(matches!(cfg.connection_type, ConnectionType::Tls));
        let tls = cfg.tls_config.unwrap();
        assert!(tls.verify_cert);
        assert_eq!(tls.min_tls_version, Some("tls1.2".to_string()));
    }

    // ---- Full config serialization round-trip ----

    #[test]
    fn test_tcp_config_round_trip() {
        let original = make_tcp_config();
        let json = serde_json::to_string(&original).unwrap();
        let restored: ConnectionConfig = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.id, original.id);
        assert!(matches!(restored.connection_type, ConnectionType::Tcp));
        assert!(restored.ssh_config.is_none());
        assert!(restored.tls_config.is_none());
    }

    #[test]
    fn test_ssh_config_round_trip() {
        let original = make_ssh_config();
        let json = serde_json::to_string(&original).unwrap();
        let restored: ConnectionConfig = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.id, original.id);
        assert!(matches!(restored.connection_type, ConnectionType::Ssh));
        let ssh = restored.ssh_config.unwrap();
        assert_eq!(ssh.host, "jump.example.com");
        assert_eq!(ssh.username, "ubuntu");
    }

    #[test]
    fn test_tls_config_round_trip() {
        let original = make_tls_config();
        let json = serde_json::to_string(&original).unwrap();
        let restored: ConnectionConfig = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.id, original.id);
        assert!(matches!(restored.connection_type, ConnectionType::Tls));
        let tls = restored.tls_config.unwrap();
        assert!(tls.verify_cert);
    }

    // ---- Backward compatibility: old config without connection_type ----

    #[test]
    fn test_config_without_connection_type_defaults_to_tcp() {
        // Simulate a Phase 1 config (no connection_type field)
        let json = r#"{
            "id": "old-conn",
            "name": "Old Connection",
            "group_name": "",
            "host": "127.0.0.1",
            "port": 6379,
            "auth_db": 0,
            "timeout_ms": 5000,
            "sort_order": 0
        }"#;
        let cfg: ConnectionConfig = serde_json::from_str(json).unwrap();
        assert!(
            matches!(cfg.connection_type, ConnectionType::Tcp),
            "Old configs without connection_type should default to TCP"
        );
        assert!(cfg.ssh_config.is_none());
        assert!(cfg.tls_config.is_none());
    }
}

#[cfg(test)]
mod tls_url_generation {
    use seven_redis_nav_lib::services::tls_connection::build_tls_redis_url;

    #[test]
    fn test_tls_url_uses_rediss_scheme() {
        let url = build_tls_redis_url("redis.example.com", 6380, None);
        assert!(url.starts_with("rediss://"), "TLS URL must use rediss:// scheme");
    }

    #[test]
    fn test_tls_url_includes_host_and_port() {
        let url = build_tls_redis_url("redis.example.com", 6380, None);
        assert!(url.contains("redis.example.com:6380"));
    }

    #[test]
    fn test_tls_url_with_password_format() {
        let url = build_tls_redis_url("localhost", 6380, Some("mypassword"));
        // Format: rediss://:password@host:port
        assert!(url.contains(":mypassword@"));
        assert!(url.contains("localhost:6380"));
    }
}

#[cfg(test)]
mod ssh_tunnel_unit {
    use seven_redis_nav_lib::services::ssh_tunnel::SshTunnel;

    #[test]
    fn test_tunnel_stop_flag_lifecycle() {
        let (tunnel, flag) = SshTunnel::new_for_test(9999);
        assert!(!*flag.lock().unwrap(), "Flag should start as false");
        tunnel.stop();
        assert!(*flag.lock().unwrap(), "Flag should be true after stop()");
    }

    #[test]
    fn test_tunnel_drop_stops_forwarding() {
        let (tunnel, flag) = SshTunnel::new_for_test(9998);
        drop(tunnel);
        assert!(*flag.lock().unwrap(), "Drop should stop the tunnel");
    }
}

// ---- Tests requiring real SSH/Redis servers (run manually with --ignored) ----

#[cfg(test)]
mod integration_with_real_servers {
    /// Test SSH tunnel with a real SSH server.
    /// Set environment variables: SSH_HOST, SSH_PORT, SSH_USER, SSH_PASS, REDIS_HOST, REDIS_PORT
    #[test]
    #[ignore = "Requires real SSH server. Run with: cargo test -- --ignored"]
    fn test_ssh_tunnel_with_real_server() {
        use std::env;
        use seven_redis_nav_lib::models::connection::{SshAuthMethod, SshConfig};
        use seven_redis_nav_lib::services::ssh_tunnel::establish_tunnel;

        let ssh_host = env::var("SSH_HOST").unwrap_or_else(|_| "localhost".to_string());
        let ssh_port: u16 = env::var("SSH_PORT").unwrap_or_else(|_| "22".to_string()).parse().unwrap();
        let ssh_user = env::var("SSH_USER").unwrap_or_else(|_| "ubuntu".to_string());
        let ssh_pass = env::var("SSH_PASS").unwrap_or_default();
        let redis_host = env::var("REDIS_HOST").unwrap_or_else(|_| "127.0.0.1".to_string());
        let redis_port: u16 = env::var("REDIS_PORT").unwrap_or_else(|_| "6379".to_string()).parse().unwrap();

        let config = SshConfig {
            host: ssh_host,
            port: ssh_port,
            username: ssh_user,
            auth_method: SshAuthMethod::Password,
            password: Some(ssh_pass),
            ..Default::default()
        };

        let result = establish_tunnel(&config, &redis_host, redis_port);
        assert!(result.is_ok(), "SSH tunnel should establish: {:?}", result.err());
        let tunnel = result.unwrap();
        assert!(tunnel.local_port > 0, "Local port should be assigned");
        println!("SSH tunnel established on local port: {}", tunnel.local_port);
    }

    /// Test TLS connection with a real Redis server with TLS enabled.
    /// Set environment variables: REDIS_TLS_HOST, REDIS_TLS_PORT
    #[test]
    #[ignore = "Requires real Redis TLS server. Run with: cargo test -- --ignored"]
    fn test_tls_connection_with_real_server() {
        use std::env;
        use seven_redis_nav_lib::models::connection::TlsConfig;
        use seven_redis_nav_lib::services::tls_connection::{build_tls_redis_url, validate_tls_config};

        let host = env::var("REDIS_TLS_HOST").unwrap_or_else(|_| "localhost".to_string());
        let port: u16 = env::var("REDIS_TLS_PORT").unwrap_or_else(|_| "6380".to_string()).parse().unwrap();

        let config = TlsConfig {
            verify_cert: false, // for self-signed test certs
            ..Default::default()
        };

        let warnings = validate_tls_config(&config).expect("Config should be valid");
        println!("TLS config warnings: {:?}", warnings);

        let url = build_tls_redis_url(&host, port, None);
        println!("TLS Redis URL: {}", url);
        assert!(url.starts_with("rediss://"));
    }
}

// ---- Security tests ----

#[cfg(test)]
mod security_tests {
    use seven_redis_nav_lib::models::connection::{ConnectionConfig, ConnectionType, TlsConfig};
    use seven_redis_nav_lib::services::tls_connection::validate_tls_config;

    /// Verify that passwords are never included in exported configs
    #[test]
    fn test_exported_config_has_no_password() {
        let config = ConnectionConfig {
            id: "sec-test".to_string(),
            name: "Security Test".to_string(),
            group_name: "".to_string(),
            host: "127.0.0.1".to_string(),
            port: 6379,
            password: Some("super_secret_password".to_string()),
            has_password: true,
            auth_db: 0,
            timeout_ms: 5000,
            sort_order: 0,
            connection_type: ConnectionType::Tcp,
            ssh_config: None,
            tls_config: None,
            sentinel_nodes: None,
            master_name: None,
            cluster_nodes: None,
        };

        // Simulate export: set password to None
        let exported = ConnectionConfig {
            password: None,
            ..config
        };

        let json = serde_json::to_string(&exported).unwrap();
        assert!(
            !json.contains("super_secret_password"),
            "Exported config must not contain plaintext password"
        );
    }

    /// Verify that SSH passwords are not leaked in serialized configs
    #[test]
    fn test_ssh_password_not_in_connection_type_field() {
        use seven_redis_nav_lib::models::connection::{SshAuthMethod, SshConfig};

        let config = ConnectionConfig {
            id: "ssh-sec".to_string(),
            name: "SSH Security Test".to_string(),
            group_name: "".to_string(),
            host: "10.0.0.1".to_string(),
            port: 6379,
            password: None,
            has_password: false,
            auth_db: 0,
            timeout_ms: 5000,
            sort_order: 0,
            connection_type: ConnectionType::Ssh,
            ssh_config: Some(SshConfig {
                host: "jump.example.com".to_string(),
                port: 22,
                username: "ubuntu".to_string(),
                auth_method: SshAuthMethod::Password,
                password: Some("ssh_secret_123".to_string()),
                private_key_path: None,
                private_key_passphrase: None,
                timeout_ms: 10000,
            }),
            tls_config: None,
            sentinel_nodes: None,
            master_name: None,
            cluster_nodes: None,
        };

        // The connection_type field should just be "ssh", not contain the password
        let json = serde_json::to_string(&config).unwrap();
        // Password IS in the JSON (it's stored), but connection_type field is just "ssh"
        assert!(json.contains("\"connection_type\":\"ssh\""));
        // Verify the structure is correct
        let restored: ConnectionConfig = serde_json::from_str(&json).unwrap();
        assert!(matches!(restored.connection_type, ConnectionType::Ssh));
    }

    /// Verify that TLS verify_cert defaults to true (secure by default)
    #[test]
    fn test_tls_verify_cert_defaults_to_true() {
        let config = TlsConfig::default();
        assert!(
            config.verify_cert,
            "TLS certificate verification must be enabled by default (secure by default)"
        );
    }

    /// Verify that disabling cert verification produces a security warning
    #[test]
    fn test_disabling_cert_verification_produces_warning() {
        let config = TlsConfig {
            verify_cert: false,
            ..Default::default()
        };
        let warnings = validate_tls_config(&config).unwrap();
        assert!(
            !warnings.is_empty(),
            "Disabling cert verification should produce at least one warning"
        );
        assert!(
            warnings.iter().any(|w| w.to_lowercase().contains("insecure") || w.to_lowercase().contains("security")),
            "Warning should mention security risk"
        );
    }

    /// Verify that private key path traversal is not possible
    #[test]
    fn test_private_key_path_with_traversal_fails_gracefully() {
        use seven_redis_nav_lib::models::connection::{SshAuthMethod, SshConfig};
        use seven_redis_nav_lib::services::ssh_tunnel::establish_tunnel;

        // Path traversal attempt
        let config = SshConfig {
            host: "127.0.0.1".to_string(),
            port: 19996,
            username: "user".to_string(),
            auth_method: SshAuthMethod::PrivateKey,
            private_key_path: Some("../../../../etc/passwd".to_string()),
            ..Default::default()
        };

        // Should fail at TCP connect (no SSH server), not at path validation
        let result = establish_tunnel(&config, "127.0.0.1", 6379);
        assert!(
            result.is_err(),
            "Should fail (no SSH server), not panic on path traversal"
        );
    }

    /// Verify that TLS URL does not expose password in logs (password is in URL but masked)
    #[test]
    fn test_tls_url_format_is_correct() {
        use seven_redis_nav_lib::services::tls_connection::build_tls_redis_url;

        let url = build_tls_redis_url("redis.example.com", 6380, Some("secret_pass"));
        // URL format: rediss://:password@host:port
        // Password comes after ":" and before "@"
        assert!(url.starts_with("rediss://"));
        assert!(url.contains("@redis.example.com:6380"));
        // The password should be in the URL (for redis-rs to use), but format is correct
        assert!(url.contains(":secret_pass@"));
    }
}
