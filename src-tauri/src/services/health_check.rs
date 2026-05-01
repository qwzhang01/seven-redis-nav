use redis::aio::MultiplexedConnection;
use std::collections::HashMap;

use crate::error::{IpcError, IpcResult};
use crate::models::health_check::{HealthIndicator, HealthLevel, HealthReport};

/// Parse INFO all output into a key-value map.
fn parse_info(info: &str) -> HashMap<String, String> {
    let mut map = HashMap::new();
    for line in info.lines() {
        if line.starts_with('#') || line.is_empty() { continue; }
        if let Some((k, v)) = line.split_once(':') {
            map.insert(k.trim().to_string(), v.trim().to_string());
        }
    }
    map
}

fn parse_f64(map: &HashMap<String, String>, key: &str) -> f64 {
    map.get(key).and_then(|v| v.parse().ok()).unwrap_or(0.0)
}

fn parse_i64(map: &HashMap<String, String>, key: &str) -> i64 {
    map.get(key).and_then(|v| v.parse().ok()).unwrap_or(0)
}

fn parse_str<'a>(map: &'a HashMap<String, String>, key: &str) -> &'a str {
    map.get(key).map(|s| s.as_str()).unwrap_or("")
}

/// Generate a full health check report for the current connection.
pub async fn generate_health_report(
    conn: &mut MultiplexedConnection,
    connection_id: &str,
) -> IpcResult<HealthReport> {
    // Collect INFO all
    let info_str: String = redis::cmd("INFO")
        .arg("all")
        .query_async(conn)
        .await
        .map_err(|e| IpcError::Redis { message: e.to_string() })?;

    let info = parse_info(&info_str);

    // Collect SLOWLOG LEN
    let slowlog_len: i64 = redis::cmd("SLOWLOG")
        .arg("LEN")
        .query_async(conn)
        .await
        .unwrap_or(0);

    // Collect CONFIG GET maxmemory, maxclients, appendonly
    let maxmemory_cfg: Vec<String> = redis::cmd("CONFIG")
        .arg("GET")
        .arg("maxmemory")
        .query_async(conn)
        .await
        .unwrap_or_default();
    let maxmemory: u64 = maxmemory_cfg.get(1).and_then(|v| v.parse().ok()).unwrap_or(0);

    let maxclients_cfg: Vec<String> = redis::cmd("CONFIG")
        .arg("GET")
        .arg("maxclients")
        .query_async(conn)
        .await
        .unwrap_or_default();
    let maxclients: u64 = maxclients_cfg.get(1).and_then(|v| v.parse().ok()).unwrap_or(10000);

    let appendonly_cfg: Vec<String> = redis::cmd("CONFIG")
        .arg("GET")
        .arg("appendonly")
        .query_async(conn)
        .await
        .unwrap_or_default();
    let aof_enabled = appendonly_cfg.get(1).map(|v| v == "yes").unwrap_or(false);

    // ─── Compute indicators ───────────────────────────────────────────────

    let mut indicators = Vec::new();

    // 1. Memory usage rate
    let used_memory = parse_i64(&info, "used_memory") as u64;
    let mem_usage_pct = if maxmemory > 0 {
        (used_memory as f64 / maxmemory as f64) * 100.0
    } else {
        0.0
    };
    let mem_level = if maxmemory == 0 {
        HealthLevel::Normal
    } else if mem_usage_pct < 70.0 {
        HealthLevel::Normal
    } else if mem_usage_pct < 90.0 {
        HealthLevel::Warning
    } else {
        HealthLevel::Danger
    };
    indicators.push(HealthIndicator {
        name: "内存使用率".to_string(),
        value: if maxmemory == 0 { "未设置 maxmemory".to_string() } else { format!("{:.1}%", mem_usage_pct) },
        score: mem_level.score(),
        suggestion: if mem_level == HealthLevel::Danger {
            Some("内存使用率过高，建议配置 maxmemory 并设置合适的淘汰策略".to_string())
        } else { None },
        level: mem_level,
    });

    // 2. Memory fragmentation ratio
    let frag_ratio = parse_f64(&info, "mem_fragmentation_ratio");
    let frag_level = if frag_ratio >= 1.0 && frag_ratio <= 1.5 {
        HealthLevel::Normal
    } else if frag_ratio <= 2.0 {
        HealthLevel::Warning
    } else {
        HealthLevel::Danger
    };
    indicators.push(HealthIndicator {
        name: "内存碎片率".to_string(),
        value: format!("{:.2}", frag_ratio),
        score: frag_level.score(),
        suggestion: if frag_level == HealthLevel::Danger {
            Some("内存碎片率过高，建议执行 MEMORY PURGE 或重启 Redis".to_string())
        } else { None },
        level: frag_level,
    });

    // 3. maxmemory policy
    let eviction_policy = parse_str(&info, "maxmemory_policy");
    let policy_level = if eviction_policy == "noeviction" || eviction_policy.is_empty() {
        HealthLevel::Warning
    } else {
        HealthLevel::Normal
    };
    indicators.push(HealthIndicator {
        name: "maxmemory 策略".to_string(),
        value: if eviction_policy.is_empty() { "未配置".to_string() } else { eviction_policy.to_string() },
        score: policy_level.score(),
        suggestion: if policy_level == HealthLevel::Warning {
            Some("建议配置合适的 maxmemory-policy（如 allkeys-lru）避免 OOM".to_string())
        } else { None },
        level: policy_level,
    });

    // 4. Cache hit rate
    let hits = parse_i64(&info, "keyspace_hits") as f64;
    let misses = parse_i64(&info, "keyspace_misses") as f64;
    let hit_rate = if hits + misses > 0.0 { hits / (hits + misses) * 100.0 } else { 100.0 };
    let hit_level = if hit_rate >= 90.0 { HealthLevel::Normal }
        else if hit_rate >= 70.0 { HealthLevel::Warning }
        else { HealthLevel::Danger };
    indicators.push(HealthIndicator {
        name: "缓存命中率".to_string(),
        value: format!("{:.1}%", hit_rate),
        score: hit_level.score(),
        suggestion: if hit_level == HealthLevel::Danger {
            Some("命中率过低，检查 key 设计和 TTL 策略".to_string())
        } else { None },
        level: hit_level,
    });

    // 5. Slow query count
    let slow_level = if slowlog_len == 0 { HealthLevel::Normal }
        else if slowlog_len <= 10 { HealthLevel::Warning }
        else { HealthLevel::Danger };
    indicators.push(HealthIndicator {
        name: "慢查询数量".to_string(),
        value: slowlog_len.to_string(),
        score: slow_level.score(),
        suggestion: if slow_level != HealthLevel::Normal {
            Some("存在慢查询，建议使用 SLOWLOG GET 查看详情并优化".to_string())
        } else { None },
        level: slow_level,
    });

    // 6. OPS (instantaneous_ops_per_sec)
    let ops = parse_i64(&info, "instantaneous_ops_per_sec");
    let ops_level = if ops < 10000 { HealthLevel::Normal }
        else if ops < 50000 { HealthLevel::Warning }
        else { HealthLevel::Danger };
    indicators.push(HealthIndicator {
        name: "OPS 峰值".to_string(),
        value: format!("{} ops/s", ops),
        score: ops_level.score(),
        suggestion: if ops_level == HealthLevel::Danger {
            Some("OPS 过高，考虑读写分离或集群扩容".to_string())
        } else { None },
        level: ops_level,
    });

    // 7. Connected clients ratio
    let connected_clients = parse_i64(&info, "connected_clients") as u64;
    let client_ratio = (connected_clients as f64 / maxclients as f64) * 100.0;
    let client_level = if client_ratio < 60.0 { HealthLevel::Normal }
        else if client_ratio < 80.0 { HealthLevel::Warning }
        else { HealthLevel::Danger };
    indicators.push(HealthIndicator {
        name: "连接数/maxclients".to_string(),
        value: format!("{}/{} ({:.1}%)", connected_clients, maxclients, client_ratio),
        score: client_level.score(),
        suggestion: if client_level == HealthLevel::Danger {
            Some("连接数接近上限，考虑增大 maxclients 或使用连接池".to_string())
        } else { None },
        level: client_level,
    });

    // 8. Rejected connections
    let rejected = parse_i64(&info, "rejected_connections");
    let reject_level = if rejected == 0 { HealthLevel::Normal }
        else if rejected <= 10 { HealthLevel::Warning }
        else { HealthLevel::Danger };
    indicators.push(HealthIndicator {
        name: "被拒绝连接数".to_string(),
        value: rejected.to_string(),
        score: reject_level.score(),
        suggestion: if reject_level != HealthLevel::Normal {
            Some("存在被拒绝的连接，检查 maxclients 配置".to_string())
        } else { None },
        level: reject_level,
    });

    // 9. RDB last save time
    let rdb_last_save = parse_i64(&info, "rdb_last_bgsave_time_sec");
    let rdb_changes = parse_i64(&info, "rdb_changes_since_last_save");
    let now_ts = chrono::Utc::now().timestamp();
    let rdb_age_secs = now_ts - rdb_last_save;
    let rdb_level = if rdb_last_save == 0 { HealthLevel::Danger }
        else if rdb_age_secs < 3600 { HealthLevel::Normal }
        else if rdb_age_secs < 86400 { HealthLevel::Warning }
        else { HealthLevel::Danger };
    indicators.push(HealthIndicator {
        name: "RDB 最近保存时间".to_string(),
        value: if rdb_last_save == 0 { "从未保存".to_string() }
               else { format!("{} 秒前（{} 个变更未保存）", rdb_age_secs, rdb_changes) },
        score: rdb_level.score(),
        suggestion: if rdb_level == HealthLevel::Danger {
            Some("RDB 长时间未保存，检查 save 配置或手动执行 BGSAVE".to_string())
        } else { None },
        level: rdb_level,
    });

    // 10. AOF status
    let aof_level = if aof_enabled { HealthLevel::Normal } else { HealthLevel::Warning };
    indicators.push(HealthIndicator {
        name: "AOF 状态".to_string(),
        value: if aof_enabled { "已启用".to_string() } else { "未启用".to_string() },
        score: aof_level.score(),
        suggestion: if !aof_enabled {
            Some("生产环境建议启用 AOF 持久化以防止数据丢失".to_string())
        } else { None },
        level: aof_level,
    });

    Ok(HealthReport::new(connection_id, indicators))
}

/// Generate Markdown text from a health report.
pub fn export_to_markdown(report: &HealthReport, host: &str) -> String {
    let mut md = String::new();
    md.push_str(&format!("# Redis 健康检查报告\n\n"));
    md.push_str(&format!("- **连接**: {}\n", host));
    md.push_str(&format!("- **生成时间**: {}\n", report.created_at));
    md.push_str(&format!("- **总体健康分**: {}/100\n\n", report.score));

    md.push_str("## 指标详情\n\n");
    md.push_str("| 指标 | 当前值 | 评级 | 建议 |\n");
    md.push_str("|------|--------|------|------|\n");

    for ind in &report.indicators {
        let level_str = match ind.level {
            HealthLevel::Normal  => "✅ 正常",
            HealthLevel::Warning => "⚠️ 警告",
            HealthLevel::Danger  => "🔴 危险",
        };
        let suggestion = ind.suggestion.as_deref().unwrap_or("-");
        md.push_str(&format!("| {} | {} | {} | {} |\n",
            ind.name, ind.value, level_str, suggestion));
    }

    md
}
