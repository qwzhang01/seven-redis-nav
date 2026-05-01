use crate::error::IpcResult;
use crate::models::phase3::BitmapChunk;
use crate::services::connection_manager::SharedConnectionManager;
use tauri::State;

/// GETRANGE — read a chunk of raw bytes from a bitmap key (Base64 encoded)
#[tauri::command]
pub async fn bitmap_chunk(
    conn_id: String,
    key: String,
    start_byte: u64,
    end_byte: u64,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<BitmapChunk> {
    tracing::info!(
        command = "bitmap_chunk",
        conn_id = %conn_id,
        key = %key,
        start_byte,
        end_byte,
        "IPC call"
    );
    crate::services::bitmap::bitmap_chunk(mgr.inner(), &conn_id, &key, start_byte, end_byte).await
}

/// BITCOUNT — count set bits in a range
#[tauri::command]
pub async fn bitmap_count(
    conn_id: String,
    key: String,
    start: i64,
    end: i64,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<u64> {
    tracing::info!(
        command = "bitmap_count",
        conn_id = %conn_id,
        key = %key,
        start,
        end,
        "IPC call"
    );
    crate::services::bitmap::bitmap_count(mgr.inner(), &conn_id, &key, start, end).await
}

/// BITPOS — find the first set/unset bit
#[tauri::command]
pub async fn bitmap_pos(
    conn_id: String,
    key: String,
    bit: u8,
    start: Option<i64>,
    end: Option<i64>,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<i64> {
    tracing::info!(
        command = "bitmap_pos",
        conn_id = %conn_id,
        key = %key,
        bit,
        start = ?start,
        end = ?end,
        "IPC call"
    );
    crate::services::bitmap::bitmap_pos(mgr.inner(), &conn_id, &key, bit, start, end).await
}

/// SETBIT — set a single bit
#[tauri::command]
pub async fn bitmap_set_bit(
    conn_id: String,
    key: String,
    offset: u64,
    value: u8,
    mgr: State<'_, SharedConnectionManager>,
) -> IpcResult<u8> {
    tracing::info!(
        command = "bitmap_set_bit",
        conn_id = %conn_id,
        key = %key,
        offset,
        value,
        "IPC call"
    );
    crate::services::bitmap::bitmap_set_bit(mgr.inner(), &conn_id, &key, offset, value).await
}
