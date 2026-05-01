use serde::Serialize;

#[derive(Debug, thiserror::Error, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum IpcError {
    #[error("redis error: {message}")]
    Redis { message: String },

    #[error("connection refused: {target}")]
    ConnectionRefused { target: String },

    #[error("timeout after {ms}ms")]
    Timeout { ms: u64 },

    #[error("invalid argument: {field}")]
    InvalidArgument { field: String, reason: String },

    #[error("internal error: {message}")]
    Internal { message: String },

    #[error("authentication failed")]
    AuthFailed,

    /// User cancelled a biometric / passcode prompt (e.g. clicked "Cancel"
    /// on the Touch ID sheet). Fix 1.3 — this is distinct from AuthFailed
    /// so the frontend can avoid showing an alarming error toast.
    #[error("authentication cancelled by user")]
    AuthCancelled,

    #[error("not found: {key}")]
    NotFound { key: String },

    #[error("dangerous command: {command}")]
    DangerousCommand { command: String, confirm_token: String },
}

pub type IpcResult<T> = Result<T, IpcError>;

// Fix 3.7: blanket From impl for sqlx::Error → IpcError, so we can use `?`
// directly instead of `.map_err(|e| IpcError::Internal { message: e.to_string() })?`
// at every call-site.
impl From<sqlx::Error> for IpcError {
    fn from(e: sqlx::Error) -> Self {
        IpcError::Internal { message: e.to_string() }
    }
}

// io::Error → IpcError (used in TLS / SSH modules)
impl From<std::io::Error> for IpcError {
    fn from(e: std::io::Error) -> Self {
        IpcError::Internal { message: e.to_string() }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ipc_error_serializes_with_kind_tag() {
        let err = IpcError::Redis { message: "connection lost".to_string() };
        let json = serde_json::to_string(&err).unwrap();
        assert!(json.contains("\"kind\":\"redis\""));
        assert!(json.contains("\"message\":\"connection lost\""));
    }

    #[test]
    fn test_connection_refused_serialization() {
        let err = IpcError::ConnectionRefused { target: "127.0.0.1:6379".to_string() };
        let json = serde_json::to_string(&err).unwrap();
        assert!(json.contains("\"kind\":\"connection_refused\""));
        assert!(json.contains("\"target\":\"127.0.0.1:6379\""));
    }

    #[test]
    fn test_timeout_serialization() {
        let err = IpcError::Timeout { ms: 5000 };
        let json = serde_json::to_string(&err).unwrap();
        assert!(json.contains("\"kind\":\"timeout\""));
        assert!(json.contains("\"ms\":5000"));
    }

    #[test]
    fn test_invalid_argument_serialization() {
        let err = IpcError::InvalidArgument {
            field: "port".to_string(),
            reason: "must be > 0".to_string(),
        };
        let json = serde_json::to_string(&err).unwrap();
        assert!(json.contains("\"kind\":\"invalid_argument\""));
        assert!(json.contains("\"field\":\"port\""));
        assert!(json.contains("\"reason\":\"must be > 0\""));
    }

    #[test]
    fn test_auth_failed_serialization() {
        let err = IpcError::AuthFailed;
        let json = serde_json::to_string(&err).unwrap();
        assert!(json.contains("\"kind\":\"auth_failed\""));
    }

    #[test]
    fn test_not_found_serialization() {
        let err = IpcError::NotFound { key: "conn-123".to_string() };
        let json = serde_json::to_string(&err).unwrap();
        assert!(json.contains("\"kind\":\"not_found\""));
        assert!(json.contains("\"key\":\"conn-123\""));
    }

    #[test]
    fn test_dangerous_command_serialization() {
        let err = IpcError::DangerousCommand {
            command: "FLUSHDB".to_string(),
            confirm_token: "confirm-flushdb".to_string(),
        };
        let json = serde_json::to_string(&err).unwrap();
        assert!(json.contains("\"kind\":\"dangerous_command\""));
        assert!(json.contains("\"command\":\"FLUSHDB\""));
        assert!(json.contains("\"confirm_token\":\"confirm-flushdb\""));
    }

    #[test]
    fn test_error_display_messages() {
        assert_eq!(
            IpcError::Redis { message: "oops".to_string() }.to_string(),
            "redis error: oops"
        );
        assert_eq!(
            IpcError::Timeout { ms: 3000 }.to_string(),
            "timeout after 3000ms"
        );
        assert_eq!(
            IpcError::AuthFailed.to_string(),
            "authentication failed"
        );
    }
}
