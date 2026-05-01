use native_tls::{TlsConnector, Certificate, Identity};
use std::fs;

use crate::models::connection::TlsConfig;
use crate::error::{IpcError, IpcResult};

/// Build a native-tls TlsConnector from TlsConfig
pub fn build_tls_connector(tls_config: &TlsConfig) -> IpcResult<TlsConnector> {
    let mut builder = TlsConnector::builder();

    // Disable certificate verification if requested (e.g. self-signed)
    if !tls_config.verify_cert {
        builder.danger_accept_invalid_certs(true);
        builder.danger_accept_invalid_hostnames(true);
    }

    // Load custom CA certificate
    if let Some(ref ca_path) = tls_config.ca_cert_path {
        let ca_pem = fs::read(ca_path).map_err(|e| IpcError::Internal {
            message: format!("Failed to read CA cert '{}': {}", ca_path, e),
        })?;
        let cert = Certificate::from_pem(&ca_pem).map_err(|e| IpcError::Internal {
            message: format!("Invalid CA cert: {}", e),
        })?;
        builder.add_root_certificate(cert);
    }

    // Load client certificate + key (mutual TLS)
    if let (Some(ref cert_path), Some(ref key_path)) =
        (&tls_config.client_cert_path, &tls_config.client_key_path)
    {
        let cert_pem = fs::read(cert_path).map_err(|e| IpcError::Internal {
            message: format!("Failed to read client cert '{}': {}", cert_path, e),
        })?;
        let key_pem = fs::read(key_path).map_err(|e| IpcError::Internal {
            message: format!("Failed to read client key '{}': {}", key_path, e),
        })?;

        // Combine cert + key into PKCS#12 identity
        // native-tls accepts PEM via Identity::from_pkcs8
        let identity = Identity::from_pkcs8(&cert_pem, &key_pem).map_err(|e| IpcError::Internal {
            message: format!("Invalid client cert/key: {}", e),
        })?;
        builder.identity(identity);
    }

    // Minimum TLS version
    if let Some(ref version) = tls_config.min_tls_version {
        match version.as_str() {
            "tls1.2" => {
                builder.min_protocol_version(Some(native_tls::Protocol::Tlsv12));
            }
            "tls1.3" => {
                // native-tls doesn't expose TLS 1.3 min version directly on all platforms
                // Set TLS 1.2 as minimum (TLS 1.3 will be used if available)
                builder.min_protocol_version(Some(native_tls::Protocol::Tlsv12));
            }
            _ => {}
        }
    }

    builder.build().map_err(|e| IpcError::Internal {
        message: format!("Failed to build TLS connector: {}", e),
    })
}

/// Build a Redis URL with TLS for use with redis-rs
pub fn build_tls_redis_url(host: &str, port: u16, password: Option<&str>) -> String {
    if let Some(pw) = password {
        format!("rediss://:{}@{}:{}", pw, host, port)
    } else {
        format!("rediss://{}:{}", host, port)
    }
}

/// Validate TLS configuration (check files exist, etc.)
pub fn validate_tls_config(tls_config: &TlsConfig) -> IpcResult<Vec<String>> {
    let mut warnings = Vec::new();

    if let Some(ref ca_path) = tls_config.ca_cert_path {
        if !std::path::Path::new(ca_path).exists() {
            return Err(IpcError::Internal {
                message: format!("CA cert file not found: {}", ca_path),
            });
        }
        // Check expiry
        if let Ok(pem) = fs::read(ca_path) {
            if let Ok(_cert) = native_tls::Certificate::from_pem(&pem) {
                // Note: native-tls doesn't expose expiry directly; warn generically
                warnings.push("CA certificate loaded successfully".to_string());
            }
        }
    }

    if let Some(ref cert_path) = tls_config.client_cert_path {
        if !std::path::Path::new(cert_path).exists() {
            return Err(IpcError::Internal {
                message: format!("Client cert file not found: {}", cert_path),
            });
        }
    }

    if let Some(ref key_path) = tls_config.client_key_path {
        if !std::path::Path::new(key_path).exists() {
            return Err(IpcError::Internal {
                message: format!("Client key file not found: {}", key_path),
            });
        }
    }

    if !tls_config.verify_cert {
        warnings.push(
            "Certificate verification is disabled. This is insecure in production.".to_string(),
        );
    }

    Ok(warnings)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::connection::TlsConfig;

    // ---- URL builder ----

    #[test]
    fn test_build_tls_redis_url_no_password() {
        let url = build_tls_redis_url("localhost", 6380, None);
        assert_eq!(url, "rediss://localhost:6380");
    }

    #[test]
    fn test_build_tls_redis_url_with_password() {
        let url = build_tls_redis_url("redis.example.com", 6380, Some("secret"));
        assert_eq!(url, "rediss://:secret@redis.example.com:6380");
    }

    #[test]
    fn test_build_tls_redis_url_with_special_chars_in_password() {
        let url = build_tls_redis_url("127.0.0.1", 6379, Some("p@ss!word"));
        assert!(url.starts_with("rediss://"));
        assert!(url.contains("127.0.0.1:6379"));
    }

    #[test]
    fn test_build_tls_redis_url_default_port() {
        let url = build_tls_redis_url("redis.prod.internal", 6379, None);
        assert_eq!(url, "rediss://redis.prod.internal:6379");
    }

    // ---- Config validation: empty config ----

    #[test]
    fn test_validate_tls_config_empty_is_ok() {
        let config = TlsConfig::default();
        let result = validate_tls_config(&config);
        assert!(result.is_ok(), "Empty TLS config should be valid");
        let warnings = result.unwrap();
        assert!(warnings.is_empty(), "No warnings for default config");
    }

    // ---- Config validation: verify_cert = false ----

    #[test]
    fn test_validate_tls_config_no_verify_warns() {
        let config = TlsConfig {
            verify_cert: false,
            ..Default::default()
        };
        let result = validate_tls_config(&config);
        assert!(result.is_ok());
        let warnings = result.unwrap();
        assert!(
            warnings.iter().any(|w| w.contains("insecure")),
            "Should warn about disabled cert verification"
        );
    }

    // ---- Config validation: missing CA cert file ----

    #[test]
    fn test_validate_tls_config_missing_ca_cert_returns_error() {
        let config = TlsConfig {
            ca_cert_path: Some("/nonexistent/path/ca.pem".to_string()),
            ..Default::default()
        };
        let result = validate_tls_config(&config);
        assert!(result.is_err(), "Should fail when CA cert file doesn't exist");
        let err = result.unwrap_err().to_string();
        assert!(err.contains("CA cert") || err.contains("not found") || err.contains("ca.pem"));
    }

    // ---- Config validation: missing client cert file ----

    #[test]
    fn test_validate_tls_config_missing_client_cert_returns_error() {
        let config = TlsConfig {
            client_cert_path: Some("/nonexistent/client.crt".to_string()),
            ..Default::default()
        };
        let result = validate_tls_config(&config);
        assert!(result.is_err(), "Should fail when client cert file doesn't exist");
    }

    // ---- Config validation: missing client key file ----

    #[test]
    fn test_validate_tls_config_missing_client_key_returns_error() {
        let config = TlsConfig {
            client_key_path: Some("/nonexistent/client.key".to_string()),
            ..Default::default()
        };
        let result = validate_tls_config(&config);
        assert!(result.is_err(), "Should fail when client key file doesn't exist");
    }

    // ---- TlsConfig default values ----

    #[test]
    fn test_tls_config_default_verify_cert_is_true() {
        let config = TlsConfig::default();
        assert!(config.verify_cert, "verify_cert should default to true");
    }

    #[test]
    fn test_tls_config_default_optional_fields_are_none() {
        let config = TlsConfig::default();
        assert!(config.ca_cert_path.is_none());
        assert!(config.client_cert_path.is_none());
        assert!(config.client_key_path.is_none());
        assert!(config.min_tls_version.is_none());
        assert!(config.server_name.is_none());
    }

    // ---- TlsConfig serialization ----

    #[test]
    fn test_tls_config_serializes_correctly() {
        let config = TlsConfig {
            verify_cert: true,
            ca_cert_path: Some("/etc/ssl/ca.pem".to_string()),
            client_cert_path: None,
            client_key_path: None,
            min_tls_version: Some("tls1.2".to_string()),
            server_name: Some("redis.internal".to_string()),
        };
        let json = serde_json::to_string(&config).expect("Should serialize");
        assert!(json.contains("ca.pem"));
        assert!(json.contains("tls1.2"));
        assert!(json.contains("redis.internal"));
        assert!(json.contains("\"verify_cert\":true"));
    }

    #[test]
    fn test_tls_config_deserializes_with_defaults() {
        // Only verify_cert provided — others should default
        let json = r#"{"verify_cert":false}"#;
        let config: TlsConfig = serde_json::from_str(json).expect("Should deserialize");
        assert!(!config.verify_cert);
        assert!(config.ca_cert_path.is_none());
        assert!(config.min_tls_version.is_none());
    }

    #[test]
    fn test_tls_config_full_round_trip() {
        let original = TlsConfig {
            verify_cert: false,
            ca_cert_path: Some("/tmp/ca.pem".to_string()),
            client_cert_path: Some("/tmp/client.crt".to_string()),
            client_key_path: Some("/tmp/client.key".to_string()),
            min_tls_version: Some("tls1.3".to_string()),
            server_name: Some("myredis.example.com".to_string()),
        };
        let json = serde_json::to_string(&original).unwrap();
        let restored: TlsConfig = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.verify_cert, original.verify_cert);
        assert_eq!(restored.ca_cert_path, original.ca_cert_path);
        assert_eq!(restored.client_cert_path, original.client_cert_path);
        assert_eq!(restored.client_key_path, original.client_key_path);
        assert_eq!(restored.min_tls_version, original.min_tls_version);
        assert_eq!(restored.server_name, original.server_name);
    }

    // ---- TLS connector builder (no real certs) ----

    #[test]
    fn test_build_tls_connector_default_config_succeeds() {
        // Default config (no custom certs) should build successfully
        let config = TlsConfig::default();
        let result = build_tls_connector(&config);
        assert!(result.is_ok(), "Should build TLS connector with default config");
    }

    #[test]
    fn test_build_tls_connector_no_verify_succeeds() {
        let config = TlsConfig {
            verify_cert: false,
            ..Default::default()
        };
        let result = build_tls_connector(&config);
        assert!(result.is_ok(), "Should build TLS connector with verify_cert=false");
    }

    #[test]
    fn test_build_tls_connector_with_tls12_min_version() {
        let config = TlsConfig {
            min_tls_version: Some("tls1.2".to_string()),
            ..Default::default()
        };
        let result = build_tls_connector(&config);
        assert!(result.is_ok(), "Should build TLS connector with TLS 1.2 minimum");
    }

    #[test]
    fn test_build_tls_connector_with_tls13_min_version() {
        let config = TlsConfig {
            min_tls_version: Some("tls1.3".to_string()),
            ..Default::default()
        };
        let result = build_tls_connector(&config);
        assert!(result.is_ok(), "Should build TLS connector with TLS 1.3 minimum");
    }

    #[test]
    fn test_build_tls_connector_with_invalid_ca_cert_fails() {
        // Create a temp file with invalid PEM content
        use std::io::Write;
        let mut tmp = tempfile::NamedTempFile::new().expect("Should create temp file");
        tmp.write_all(b"NOT A VALID PEM CERTIFICATE").unwrap();
        let path = tmp.path().to_str().unwrap().to_string();

        let config = TlsConfig {
            ca_cert_path: Some(path),
            ..Default::default()
        };
        let result = build_tls_connector(&config);
        assert!(result.is_err(), "Should fail with invalid CA cert content");
    }
}
