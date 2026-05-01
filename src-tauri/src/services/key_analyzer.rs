use redis::aio::MultiplexedConnection;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use tokio::sync::oneshot;

use crate::error::{IpcError, IpcResult};
use crate::models::key_analyzer::{KeyMemoryStat, ScanProgress, TtlBucket, TtlDistribution};

/// Active scan task handle.
pub struct ScanTask {
    pub cancel_tx: oneshot::Sender<()>,
}

/// Completed scan results keyed by task_id.
pub type SharedScanResults = Arc<Mutex<HashMap<String, Vec<KeyMemoryStat>>>>;

/// Global registry of active scan tasks.
pub type SharedScanRegistry = Arc<Mutex<HashMap<String, ScanTask>>>;

pub fn new_scan_registry() -> SharedScanRegistry {
    Arc::new(Mutex::new(HashMap::new()))
}

pub fn new_scan_results() -> SharedScanResults {
    Arc::new(Mutex::new(HashMap::new()))
}

/// Run a key memory scan in the background, emitting progress events.
pub async fn run_key_scan(
    mut conn: MultiplexedConnection,
    task_id: String,
    low_impact: bool,
    app: tauri::AppHandle,
    registry: SharedScanRegistry,
    results: SharedScanResults,
    mut cancel_rx: oneshot::Receiver<()>,
) {
    use tauri::Emitter;

    let mut cursor: u64 = 0;
    let mut scanned: u64 = 0;
    let mut top_keys: Vec<KeyMemoryStat> = Vec::new();

    // Estimate total keys via DBSIZE
    let total_estimate: u64 = redis::cmd("DBSIZE")
        .query_async(&mut conn)
        .await
        .unwrap_or(0);

    loop {
        // Check for cancellation
        if cancel_rx.try_recv().is_ok() {
            break;
        }

        let result: Result<(u64, Vec<String>), _> = redis::cmd("SCAN")
            .arg(cursor)
            .arg("COUNT")
            .arg(100)
            .query_async(&mut conn)
            .await;

        let (next_cursor, keys) = match result {
            Ok(r) => r,
            Err(_) => break,
        };
        cursor = next_cursor;

        // Pipeline phase 1: MEMORY USAGE + TYPE + OBJECT ENCODING for all keys in batch
        let mut pipe1 = redis::pipe();
        for key in &keys {
            pipe1
                .cmd("MEMORY").arg("USAGE").arg(key).arg("SAMPLES").arg(0).ignore()
                .cmd("TYPE").arg(key).ignore()
                .cmd("OBJECT").arg("ENCODING").arg(key).ignore();
        }
        // Execute pipeline; collect raw results as Vec<redis::Value>
        let pipe1_results: Vec<redis::Value> = pipe1
            .query_async(&mut conn)
            .await
            .unwrap_or_default();

        // Parse phase-1 results (3 values per key: mem, type, encoding)
        let mut key_metas: Vec<(u64, String, String)> = Vec::with_capacity(keys.len());
        let mut idx = 0;
        for _ in &keys {
            let mem: u64 = pipe1_results.get(idx)
                .and_then(|v| redis::from_redis_value(v).ok())
                .unwrap_or(0);
            let key_type: String = pipe1_results.get(idx + 1)
                .and_then(|v| redis::from_redis_value(v).ok())
                .unwrap_or_else(|| "unknown".to_string());
            let encoding: String = pipe1_results.get(idx + 2)
                .and_then(|v| redis::from_redis_value(v).ok())
                .unwrap_or_else(|| "unknown".to_string());
            key_metas.push((mem, key_type, encoding));
            idx += 3;
        }

        // Pipeline phase 2: element count command per key (depends on type)
        let mut pipe2 = redis::pipe();
        for (i, key) in keys.iter().enumerate() {
            match key_metas[i].1.as_str() {
                "hash"   => { pipe2.cmd("HLEN").arg(key).ignore(); }
                "list"   => { pipe2.cmd("LLEN").arg(key).ignore(); }
                "set"    => { pipe2.cmd("SCARD").arg(key).ignore(); }
                "zset"   => { pipe2.cmd("ZCARD").arg(key).ignore(); }
                "stream" => { pipe2.cmd("XLEN").arg(key).ignore(); }
                _        => { pipe2.cmd("STRLEN").arg(key).ignore(); }
            }
        }
        let pipe2_results: Vec<redis::Value> = pipe2
            .query_async(&mut conn)
            .await
            .unwrap_or_default();

        for (i, key) in keys.iter().enumerate() {
            let (mem, key_type, encoding) = key_metas[i].clone();
            let element_count: u64 = pipe2_results.get(i)
                .and_then(|v| redis::from_redis_value(v).ok())
                .unwrap_or(if key_type == "string" { 1 } else { 0 });

            let stat = KeyMemoryStat {
                key: key.clone(),
                key_type,
                memory_bytes: mem,
                encoding,
                element_count,
            };

            // Maintain top 100 by memory
            top_keys.push(stat);
            top_keys.sort_by(|a, b| b.memory_bytes.cmp(&a.memory_bytes));
            top_keys.truncate(100);

            scanned += 1;
        }

        // Emit progress every 1000 keys
        if scanned % 1000 < 100 {
            let progress = ScanProgress {
                scanned,
                total_estimate,
                top_keys: top_keys.clone(),
                is_done: false,
            };
            let _ = app.emit(&format!("key_analyzer:progress:{task_id}"), &progress);
        }

        // Low-impact mode: sleep between batches
        if low_impact {
            tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;
        }

        if cursor == 0 { break; }
    }

    // Final progress event
    let final_progress = ScanProgress {
        scanned,
        total_estimate,
        top_keys: top_keys.clone(),
        is_done: true,
    };
    let _ = app.emit(&format!("key_analyzer:progress:{task_id}"), &final_progress);

    // Store final results for CSV export
    if let Ok(mut res) = results.lock() {
        res.insert(task_id.clone(), top_keys.clone());
    }

    // Remove from registry
    if let Ok(mut reg) = registry.lock() {
        reg.remove(&task_id);
    }
}

/// Analyze TTL distribution by sampling up to 10000 keys.
pub async fn analyze_ttl_distribution(
    conn: &mut MultiplexedConnection,
) -> IpcResult<TtlDistribution> {
    let mut cursor: u64 = 0;
    let mut sampled: u64 = 0;
    let mut permanent: u64 = 0;
    let mut lt_1h: u64 = 0;
    let mut lt_24h: u64 = 0;
    let mut lt_7d: u64 = 0;
    let mut gt_7d: u64 = 0;

    loop {
        let result: (u64, Vec<String>) = redis::cmd("SCAN")
            .arg(cursor)
            .arg("COUNT")
            .arg(100)
            .query_async(conn)
            .await
            .map_err(|e| IpcError::Redis { message: e.to_string() })?;

        cursor = result.0;
        for key in &result.1 {
            let ttl: i64 = redis::cmd("TTL")
                .arg(key)
                .query_async(conn)
                .await
                .unwrap_or(-1);

            match ttl {
                -1 => permanent += 1,
                t if t <= 3600 => lt_1h += 1,
                t if t <= 86400 => lt_24h += 1,
                t if t <= 604800 => lt_7d += 1,
                _ => gt_7d += 1,
            }
            sampled += 1;
        }

        if cursor == 0 || sampled >= 10000 { break; }
    }

    let total = sampled as f64;
    let pct = |n: u64| if total > 0.0 { (n as f64 / total * 100.0 * 10.0).round() / 10.0 } else { 0.0 };

    let buckets = vec![
        TtlBucket { label: "永久".to_string(),    count: permanent, percentage: pct(permanent) },
        TtlBucket { label: "< 1小时".to_string(), count: lt_1h,     percentage: pct(lt_1h) },
        TtlBucket { label: "1h-24h".to_string(),  count: lt_24h,    percentage: pct(lt_24h) },
        TtlBucket { label: "1d-7d".to_string(),   count: lt_7d,     percentage: pct(lt_7d) },
        TtlBucket { label: "> 7天".to_string(),   count: gt_7d,     percentage: pct(gt_7d) },
    ];

    let expiring_soon_warning = total > 0.0 && (lt_1h as f64 / total) > 0.1;

    Ok(TtlDistribution {
        total_sampled: sampled,
        buckets,
        expiring_soon_count: lt_1h,
        expiring_soon_warning,
    })
}
