use redis::aio::MultiplexedConnection;
use redis::Value as RedisValue;
use sqlx::SqlitePool;
use std::collections::HashMap;
use std::sync::LazyLock;
use std::sync::Mutex;
use chrono::Utc;

use crate::error::{IpcError, IpcResult};
use crate::models::terminal::{CliHistoryEntry, CliReply, DANGEROUS_COMMANDS};
use crate::utils::redis_utils::bytes_to_display_string;

/// In-memory store for pending dangerous-command confirm tokens.
///
/// Key = token (random UUID), Value = the command name that the token
/// authorises. Tokens are one-shot: once consumed they are removed.
/// This prevents an attacker from replaying a predictable token (fix 3.5).
static PENDING_TOKENS: LazyLock<Mutex<HashMap<String, String>>> =
    LazyLock::new(|| Mutex::new(HashMap::new()));

/// Generate a random UUID token for a dangerous command and store it.
fn issue_token(command: &str) -> String {
    let token = uuid::Uuid::new_v4().to_string();
    PENDING_TOKENS
        .lock()
        .unwrap()
        .insert(token.clone(), command.to_uppercase());
    token
}

/// Verify and consume a one-shot token for a dangerous command.
fn verify_token(token: &str, command: &str) -> bool {
    let mut map = PENDING_TOKENS.lock().unwrap();
    if let Some(cmd) = map.remove(token) {
        cmd == command.to_uppercase()
    } else {
        false
    }
}
/// Format a Redis Value into a human-readable string
pub(crate) fn format_redis_value(val: &RedisValue, indent: usize) -> String {
    let pad = "  ".repeat(indent);
    match val {
        RedisValue::Nil => "(nil)".to_string(),
        RedisValue::Int(n) => format!("(integer) {n}"),
        RedisValue::BulkString(bytes) => {
            bytes_to_display_string(&bytes)
        }
        RedisValue::SimpleString(s) => s.clone(),
        RedisValue::Array(items) => {
            if items.is_empty() {
                return "(empty array)".to_string();
            }
            items
                .iter()
                .enumerate()
                .map(|(i, v)| format!("{pad}{}) {}", i + 1, format_redis_value(v, indent + 1)))
                .collect::<Vec<_>>()
                .join("\n")
        }
        RedisValue::Map(pairs) => {
            pairs
                .iter()
                .enumerate()
                .map(|(i, (k, v))| {
                    format!(
                        "{pad}{}) {}\n{pad}   {}",
                        i + 1,
                        format_redis_value(k, indent + 1),
                        format_redis_value(v, indent + 1)
                    )
                })
                .collect::<Vec<_>>()
                .join("\n")
        }
        RedisValue::Boolean(b) => format!("{b}"),
        RedisValue::Double(f) => format!("{f}"),
        RedisValue::BigNumber(n) => format!("{n}"),
        RedisValue::VerbatimString { format: _, text } => text.clone(),
        RedisValue::Set(items) => {
            items
                .iter()
                .enumerate()
                .map(|(i, v)| format!("{pad}{}) {}", i + 1, format_redis_value(v, indent + 1)))
                .collect::<Vec<_>>()
                .join("\n")
        }
        RedisValue::Push { kind: _, data } => {
            data
                .iter()
                .enumerate()
                .map(|(i, v)| format!("{pad}{}) {}", i + 1, format_redis_value(v, indent + 1)))
                .collect::<Vec<_>>()
                .join("\n")
        }
        RedisValue::Okay => "OK".to_string(),
        _ => "(unknown)".to_string(),
    }
}

/// Check if a command is dangerous
pub(crate) fn is_dangerous(cmd_upper: &str, args: &[&str]) -> bool {
    if DANGEROUS_COMMANDS.contains(&cmd_upper) {
        // Special case: CONFIG is only dangerous for SET requirepass
        if cmd_upper == "CONFIG" {
            if let Some(sub) = args.first() {
                if sub.to_uppercase() == "SET" {
                    if let Some(param) = args.get(1) {
                        return param.to_lowercase() == "requirepass";
                    }
                }
            }
            return false;
        }
        return true;
    }
    false
}

/// Execute a CLI command
pub async fn cli_exec(
    conn: &mut MultiplexedConnection,
    db: &SqlitePool,
    raw_command: &str,
    confirm_token: Option<&str>,
) -> IpcResult<CliReply> {
    let parts: Vec<&str> = raw_command.split_whitespace().collect();
    if parts.is_empty() {
        return Ok(CliReply { output: "".to_string(), is_error: false });
    }

    let cmd_upper = parts[0].to_uppercase();
    let args = &parts[1..];

    // Check dangerous commands
    if is_dangerous(&cmd_upper, args) {
        match confirm_token {
            Some(token) if verify_token(token, &cmd_upper) => {
                // Token valid & consumed — proceed with execution
            }
            _ => {
                let token = issue_token(&cmd_upper);
                return Err(IpcError::DangerousCommand {
                    command: cmd_upper,
                    confirm_token: token,
                });
            }
        }
    }

    // Build and execute redis command
    let mut redis_cmd = redis::cmd(&cmd_upper);
    for arg in args {
        redis_cmd.arg(arg);
    }

    let result: Result<RedisValue, _> = redis_cmd.query_async(conn).await;

    let reply = match result {
        Ok(val) => CliReply {
            output: format_redis_value(&val, 0),
            is_error: false,
        },
        Err(e) => CliReply {
            output: format!("(error) {e}"),
            is_error: true,
        },
    };

    // Persist to history
    let now = Utc::now().to_rfc3339();
    let _ = sqlx::query("INSERT INTO cli_history (command, created_at) VALUES (?, ?)")
        .bind(raw_command)
        .bind(&now)
        .execute(db)
        .await;

    // Trim history to 200 entries
    let _ = sqlx::query(
        "DELETE FROM cli_history WHERE id NOT IN (SELECT id FROM cli_history ORDER BY id DESC LIMIT 200)"
    )
    .execute(db)
    .await;

    Ok(reply)
}

/// Get CLI history (latest 200)
pub async fn cli_history_get(db: &SqlitePool) -> IpcResult<Vec<CliHistoryEntry>> {
    sqlx::query_as::<_, CliHistoryEntry>(
        "SELECT id, command, created_at FROM cli_history ORDER BY id DESC LIMIT 200",
    )
    .fetch_all(db)
    .await
    .map_err(|e| IpcError::Internal { message: e.to_string() })
}

#[cfg(test)]
mod tests {
    use super::*;

    // ===== format_redis_value tests =====

    #[test]
    fn test_format_nil() {
        let val = RedisValue::Nil;
        assert_eq!(format_redis_value(&val, 0), "(nil)");
    }

    #[test]
    fn test_format_integer() {
        let val = RedisValue::Int(42);
        assert_eq!(format_redis_value(&val, 0), "(integer) 42");
    }

    #[test]
    fn test_format_negative_integer() {
        let val = RedisValue::Int(-1);
        assert_eq!(format_redis_value(&val, 0), "(integer) -1");
    }

    #[test]
    fn test_format_bulk_string() {
        let val = RedisValue::BulkString(b"hello world".to_vec());
        assert_eq!(format_redis_value(&val, 0), "hello world");
    }

    #[test]
    fn test_format_simple_string() {
        let val = RedisValue::SimpleString("PONG".to_string());
        assert_eq!(format_redis_value(&val, 0), "PONG");
    }

    #[test]
    fn test_format_okay() {
        let val = RedisValue::Okay;
        assert_eq!(format_redis_value(&val, 0), "OK");
    }

    #[test]
    fn test_format_boolean_true() {
        let val = RedisValue::Boolean(true);
        assert_eq!(format_redis_value(&val, 0), "true");
    }

    #[test]
    fn test_format_boolean_false() {
        let val = RedisValue::Boolean(false);
        assert_eq!(format_redis_value(&val, 0), "false");
    }

    #[test]
    fn test_format_double() {
        let val = RedisValue::Double(3.14);
        assert_eq!(format_redis_value(&val, 0), "3.14");
    }

    #[test]
    fn test_format_empty_array() {
        let val = RedisValue::Array(vec![]);
        assert_eq!(format_redis_value(&val, 0), "(empty array)");
    }

    #[test]
    fn test_format_array_with_items() {
        let val = RedisValue::Array(vec![
            RedisValue::BulkString(b"foo".to_vec()),
            RedisValue::BulkString(b"bar".to_vec()),
        ]);
        let result = format_redis_value(&val, 0);
        assert!(result.contains("1) foo"));
        assert!(result.contains("2) bar"));
    }

    #[test]
    fn test_format_nested_array() {
        let val = RedisValue::Array(vec![
            RedisValue::Array(vec![
                RedisValue::Int(1),
                RedisValue::Int(2),
            ]),
        ]);
        let result = format_redis_value(&val, 0);
        assert!(result.contains("1)"));
    }

    #[test]
    fn test_format_verbatim_string() {
        let val = RedisValue::VerbatimString {
            format: redis::VerbatimFormat::Text,
            text: "some text".to_string(),
        };
        assert_eq!(format_redis_value(&val, 0), "some text");
    }

    // ===== is_dangerous tests =====

    #[test]
    fn test_flushdb_is_dangerous() {
        assert!(is_dangerous("FLUSHDB", &[]));
    }

    #[test]
    fn test_flushall_is_dangerous() {
        assert!(is_dangerous("FLUSHALL", &[]));
    }

    #[test]
    fn test_shutdown_is_dangerous() {
        assert!(is_dangerous("SHUTDOWN", &[]));
    }

    #[test]
    fn test_debug_is_dangerous() {
        assert!(is_dangerous("DEBUG", &[]));
    }

    #[test]
    fn test_config_set_requirepass_is_dangerous() {
        assert!(is_dangerous("CONFIG", &["SET", "requirepass"]));
    }

    #[test]
    fn test_config_get_is_not_dangerous() {
        assert!(!is_dangerous("CONFIG", &["GET", "maxmemory"]));
    }

    #[test]
    fn test_config_set_other_is_not_dangerous() {
        assert!(!is_dangerous("CONFIG", &["SET", "maxmemory"]));
    }

    #[test]
    fn test_config_no_args_is_not_dangerous() {
        assert!(!is_dangerous("CONFIG", &[]));
    }

    #[test]
    fn test_get_is_not_dangerous() {
        assert!(!is_dangerous("GET", &["mykey"]));
    }

    #[test]
    fn test_set_is_not_dangerous() {
        assert!(!is_dangerous("SET", &["mykey", "myvalue"]));
    }

    #[test]
    fn test_ping_is_not_dangerous() {
        assert!(!is_dangerous("PING", &[]));
    }

    #[test]
    fn test_del_is_not_dangerous() {
        // DEL is not in the dangerous list (only FLUSHDB/FLUSHALL are)
        assert!(!is_dangerous("DEL", &["key1"]));
    }
}
