// ---- Phase 0 types ----
export interface ConnectionTestReq {
  host: string;
  port: number;
  password?: string;
  timeout_ms?: number;
}

export interface PingResult {
  latency_ms: number;
  server_version: string | null;
}

// ---- Phase 1 types ----

export type ConnId = string;
export type SessionId = string;

// ---- Phase 2: SSH/TLS types ----

export type ConnectionType = 'tcp' | 'ssh' | 'tls' | 'sentinel' | 'cluster';
export type SshAuthMethod = 'password' | 'private_key';

export interface SshConfig {
  host: string;
  port: number;
  username: string;
  auth_method: SshAuthMethod;
  password?: string | null;
  private_key_path?: string | null;
  private_key_passphrase?: string | null;
  timeout_ms: number;
}

export interface TlsConfig {
  verify_cert: boolean;
  ca_cert_path?: string | null;
  client_cert_path?: string | null;
  client_key_path?: string | null;
  min_tls_version?: string | null;
  server_name?: string | null;
}

export interface AdvancedConnectionTestResult {
  success: boolean;
  ssh_ok?: boolean | null;
  redis_ok?: boolean | null;
  tls_ok?: boolean | null;
  latency_ms?: number | null;
  error?: string | null;
  details: string[];
}

export interface ConnectionConfig {
  id: ConnId;
  name: string;
  group_name: string;
  host: string;
  port: number;
  /** Password plaintext. Only present when explicitly provided (e.g. during save).
   *  Will be `null`/`undefined` in list responses — check `hasPassword` instead. */
  password?: string | null;
  /** Whether a password is stored in Keychain for this connection.
   *  Set by the backend in list responses; `password` will be null in that case. */
  has_password?: boolean;
  auth_db: number;
  timeout_ms: number;
  sort_order: number;
  // Phase 2 fields
  connection_type?: ConnectionType;
  ssh_config?: SshConfig | null;
  tls_config?: TlsConfig | null;
  // Sentinel/Cluster fields
  sentinel_nodes?: string[] | null;
  master_name?: string | null;
  cluster_nodes?: string[] | null;
}

export interface DbStat {
  index: number;
  key_count: number;
}

export type ConnectionState = 'connected' | 'disconnected' | 'reconnecting';

export interface ConnectionStateEvent {
  conn_id: ConnId;
  state: ConnectionState;
}

// ---- Welcome page redesign types ----

export interface QuickConnectReq {
  host: string;
  port: number;
  password?: string;
  timeout_ms?: number;
}
