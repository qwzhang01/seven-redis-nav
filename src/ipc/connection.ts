import { invoke } from './index';
import type {
  ConnectionTestReq, PingResult, ConnectionConfig, ConnId, DbStat,
  QuickConnectReq, AdvancedConnectionTestResult
} from '@/types/connection';

// ---- Phase 0 ----
export async function connectionTest(req: ConnectionTestReq): Promise<PingResult> {
  return invoke<PingResult>('connection_test', { req });
}

// ---- Phase 1 ----
export async function connectionList(): Promise<ConnectionConfig[]> {
  return invoke<ConnectionConfig[]>('connection_list');
}

export async function connectionSave(config: ConnectionConfig): Promise<ConnId> {
  return invoke<ConnId>('connection_save', { config });
}

export async function connectionDelete(connId: ConnId): Promise<void> {
  return invoke<void>('connection_delete', { connId });
}

export async function connectionOpen(connId: ConnId): Promise<void> {
  return invoke<void>('connection_open', { connId });
}

export async function connectionClose(connId: ConnId): Promise<void> {
  return invoke<void>('connection_close', { connId });
}

export async function dbSelect(connId: ConnId, dbIndex: number): Promise<DbStat[]> {
  return invoke<DbStat[]>('db_select', { connId, dbIndex });
}

// ---- Temporary connection (welcome page redesign) ----
export async function connectionOpenTemp(config: QuickConnectReq): Promise<ConnId> {
  return invoke<ConnId>('connection_open_temp', {
    host: config.host,
    port: config.port,
    password: config.password ?? null,
    timeoutMs: config.timeout_ms ?? null,
  });
}

// ---- Phase 2: SSH/TLS connection tests ----

/** Test an SSH tunnel connection (layered: SSH + Redis) */
export async function connectionTestSsh(config: ConnectionConfig): Promise<AdvancedConnectionTestResult> {
  return invoke<AdvancedConnectionTestResult>('connection_test_ssh', { config });
}

/** Test a TLS-encrypted Redis connection */
export async function connectionTestTls(config: ConnectionConfig): Promise<AdvancedConnectionTestResult> {
  return invoke<AdvancedConnectionTestResult>('connection_test_tls', { config });
}

/** Test a Sentinel-mode connection */
export async function connectionTestSentinel(config: ConnectionConfig): Promise<AdvancedConnectionTestResult> {
  return invoke<AdvancedConnectionTestResult>('connection_test_sentinel', { config });
}

/** Test a Cluster-mode connection */
export async function connectionTestCluster(config: ConnectionConfig): Promise<AdvancedConnectionTestResult> {
  return invoke<AdvancedConnectionTestResult>('connection_test_cluster', { config });
}
