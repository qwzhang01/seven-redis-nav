// Phase 2 types for Pub/Sub, Monitor, Slowlog, and Server Config

export interface PubSubMessage {
  channel: string;
  pattern: string | null;
  message: string;
  timestamp: string;
}

export interface MonitorCommand {
  timestamp: number;
  client: string;
  db: number;
  command: string;
  args: string[];
}

export interface SlowlogEntry {
  id: number;
  timestamp: number;
  duration_us: number;
  command: string[];
  client_addr: string;
  client_name: string;
}

export interface ServerConfigItem {
  key: string;
  value: string;
}

export interface ServerInfo {
  redis_version: string;
  uptime_secs: number;
  connected_clients: number;
  used_memory: number;
  max_memory: number;
  hit_rate: number;
  total_keys: number;
  ops_per_sec: number;
}

export interface MetricsServerInfo {
  redis_version: string;
  os: string;
  process_id: number;
  tcp_port: number;
  uptime_secs: number;
  role: string;
  connected_slaves: number;
  aof_enabled: boolean;
  last_rdb_save_ts: number;
}

export interface DbKeyspace {
  db: number;
  keys: number;
  expires: number;
  avg_ttl_secs: number;
}

export interface ClientEntry {
  id: number;
  addr: string;
  name: string;
  cmd: string;
  age_secs: number;
  db: number;
}

export interface MetricsSnapshot {
  ops_per_sec: number;
  used_memory_bytes: number;
  connected_clients: number;
  keyspace_hits: number;
  keyspace_misses: number;
  server_info: MetricsServerInfo;
  keyspace: DbKeyspace[];
  clients: ClientEntry[];
  timestamp: string;
}
