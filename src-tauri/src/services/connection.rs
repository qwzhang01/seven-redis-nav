use std::time::Instant;
use tokio::time::{timeout, Duration};

use crate::error::{IpcError, IpcResult};
use crate::models::connection::{ConnectionTestReq, PingResult};

pub async fn ping(req: &ConnectionTestReq) -> IpcResult<PingResult> {
    let timeout_ms = req.timeout_ms.unwrap_or(5000);
    let addr = format!("redis://{}:{}", req.host, req.port);

    let client = redis::Client::open(addr.as_str()).map_err(|_e| IpcError::ConnectionRefused {
        target: format!("{}:{}", req.host, req.port),
    })?;

    let fut = async {
        let mut conn = client
            .get_multiplexed_async_connection()
            .await
            .map_err(|e| IpcError::ConnectionRefused {
                target: format!("{}:{} ({})", req.host, req.port, e),
            })?;

        // AUTH if password provided
        if let Some(ref pw) = req.password {
            redis::cmd("AUTH")
                .arg(pw.as_str())
                .query_async::<()>(&mut conn)
                .await
                .map_err(|e| IpcError::Redis {
                    message: e.to_string(),
                })?;
        }

        // PING with latency measurement
        let start = Instant::now();
        redis::cmd("PING")
            .query_async::<String>(&mut conn)
            .await
            .map_err(|e| IpcError::Redis {
                message: e.to_string(),
            })?;
        let latency_ms = start.elapsed().as_millis() as u32;

        // Extract server version from INFO server
        let info: String = redis::cmd("INFO")
            .arg("server")
            .query_async(&mut conn)
            .await
            .unwrap_or_default();

        let server_version = info
            .lines()
            .find(|l| l.starts_with("redis_version:"))
            .map(|l| l.trim_start_matches("redis_version:").trim().to_string());

        Ok(PingResult {
            latency_ms,
            server_version,
        })
    };

    timeout(Duration::from_millis(timeout_ms), fut)
        .await
        .map_err(|_| IpcError::Timeout { ms: timeout_ms })?
}
