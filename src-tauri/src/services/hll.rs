use crate::error::{IpcError, IpcResult};
use crate::models::phase3::HllStats;
use crate::services::connection_manager::SharedConnectionManager;

/// PFADD — add elements to a HyperLogLog
pub async fn hll_add(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    key: &str,
    elements: &[String],
) -> IpcResult<bool> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let mut cmd = redis::cmd("PFADD");
    cmd.arg(key);
    for elem in elements {
        cmd.arg(elem);
    }

    let result: i64 = cmd
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(result == 1)
}

/// PFCOUNT — get estimated cardinality of a HyperLogLog
pub async fn hll_count(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    key: &str,
) -> IpcResult<HllStats> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let cardinality: u64 = redis::cmd("PFCOUNT")
        .arg(key)
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    // Determine encoding via DEBUG OBJECT
    let encoding = get_hll_encoding(&mut guard.conn).await;

    Ok(HllStats {
        estimated_cardinality: cardinality,
        encoding,
    })
}

/// PFMERGE — merge multiple HyperLogLog keys
pub async fn hll_merge(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    dest_key: &str,
    source_keys: &[String],
) -> IpcResult<()> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let mut cmd = redis::cmd("PFMERGE");
    cmd.arg(dest_key);
    for key in source_keys {
        cmd.arg(key);
    }

    cmd.query_async::<()>(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(())
}

/// Get HLL encoding via DEBUG OBJECT (best-effort)
async fn get_hll_encoding(conn: &mut redis::aio::MultiplexedConnection) -> String {
    let result: Result<String, _> = redis::cmd("DEBUG")
        .arg("OBJECT")
        .arg("___hll_encoding_probe___") // Non-existent key probe
        .query_async(conn)
        .await;

    match result {
        Ok(s) => {
            if s.contains("dense") {
                "dense".to_string()
            } else if s.contains("sparse") {
                "sparse".to_string()
            } else {
                "unknown".to_string()
            }
        }
        Err(_) => "unknown".to_string(),
    }
}
