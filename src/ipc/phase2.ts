import { invoke } from './index';
import type { SlowlogEntry, ServerConfigItem, ServerInfo } from '@/types/phase2';

// ---- Pub/Sub ----
export async function pubsubSubscribe(connId: string, channels: string[], pattern: boolean = false): Promise<void> {
  return invoke<void>('pubsub_subscribe', { connId, channels, pattern });
}

export async function pubsubUnsubscribe(connId: string, channels: string[], pattern: boolean = false): Promise<void> {
  return invoke<void>('pubsub_unsubscribe', { connId, channels, pattern });
}

export async function pubsubPublish(connId: string, channel: string, message: string): Promise<number> {
  return invoke<number>('pubsub_publish', { connId, channel, message });
}

// ---- Monitor ----
export async function monitorStart(connId: string): Promise<void> {
  return invoke<void>('monitor_start', { connId });
}

export async function monitorStop(connId: string): Promise<void> {
  return invoke<void>('monitor_stop', { connId });
}

// ---- Slowlog ----
export async function slowlogGet(connId: string, count?: number): Promise<SlowlogEntry[]> {
  return invoke<SlowlogEntry[]>('slowlog_get', { connId, count: count ?? null });
}

export async function slowlogReset(connId: string): Promise<void> {
  return invoke<void>('slowlog_reset', { connId });
}

// ---- Server Config ----
export async function configGetAll(connId: string): Promise<ServerConfigItem[]> {
  return invoke<ServerConfigItem[]>('config_get_all', { connId });
}

export async function configSet(connId: string, key: string, value: string): Promise<void> {
  return invoke<void>('config_set', { connId, key, value });
}

export async function serverInfo(connId: string, section?: string): Promise<ServerInfo> {
  return invoke<ServerInfo>('server_info', { connId, section: section ?? null });
}

export async function configRewrite(connId: string): Promise<void> {
  return invoke<void>('config_rewrite', { connId });
}

export async function configResetstat(connId: string): Promise<void> {
  return invoke<void>('config_resetstat', { connId });
}

export async function configGetNotifyKeyspaceEvents(connId: string): Promise<string> {
  return invoke<string>('config_get_notify_keyspace_events', { connId });
}

// ---- Metrics Dashboard ----
export async function monitorMetricsStart(connId: string, intervalMs: number = 5000): Promise<string> {
  return invoke<string>('monitor_metrics_start', { connId, intervalMs });
}

export async function monitorMetricsStop(): Promise<void> {
  return invoke<void>('monitor_metrics_stop');
}
