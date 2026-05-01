use base64::Engine;
use crate::error::{IpcError, IpcResult};
use crate::models::phase3::BitmapChunk;
use crate::services::connection_manager::SharedConnectionManager;

/// GETRANGE — read a chunk of raw bytes from a bitmap key
pub async fn bitmap_chunk(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    key: &str,
    start_byte: u64,
    end_byte: u64,
) -> IpcResult<BitmapChunk> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let result: Vec<u8> = redis::cmd("GETRANGE")
        .arg(key)
        .arg(start_byte)
        .arg(end_byte)
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    let byte_length = result.len() as u64;
    let data_base64 = base64::engine::general_purpose::STANDARD.encode(&result);

    Ok(BitmapChunk {
        data_base64,
        start_byte,
        byte_length,
    })
}

/// BITCOUNT — count set bits in a range
pub async fn bitmap_count(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    key: &str,
    start: i64,
    end: i64,
) -> IpcResult<u64> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let count: u64 = redis::cmd("BITCOUNT")
        .arg(key)
        .arg(start)
        .arg(end)
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(count)
}

/// BITPOS — find the first set/unset bit
pub async fn bitmap_pos(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    key: &str,
    bit: u8,
    start: Option<i64>,
    end: Option<i64>,
) -> IpcResult<i64> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let mut cmd = redis::cmd("BITPOS");
    cmd.arg(key).arg(bit);
    if let Some(s) = start {
        cmd.arg(s);
    }
    if let Some(e) = end {
        cmd.arg(e);
    }

    let pos: i64 = cmd
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(pos)
}

/// SETBIT — set a single bit
pub async fn bitmap_set_bit(
    mgr: &SharedConnectionManager,
    conn_id: &str,
    key: &str,
    offset: u64,
    value: u8,
) -> IpcResult<u8> {
    let session = {
        let mgr_lock = mgr.lock().await;
        mgr_lock.get_session(conn_id)?
    };
    let mut guard = session.lock().await;

    let old_value: u8 = redis::cmd("SETBIT")
        .arg(key)
        .arg(offset)
        .arg(value)
        .query_async(&mut guard.conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    Ok(old_value)
}
