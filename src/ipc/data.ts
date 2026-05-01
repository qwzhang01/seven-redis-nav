import { invoke } from './index';
import type { ConnId } from '@/types/connection';
import type { ScanPage, KeyDetail, BulkResult } from '@/types/data';

export async function keysScan(
  connId: ConnId,
  cursor: number,
  pattern: string,
): Promise<ScanPage> {
  return invoke<ScanPage>('keys_scan', { connId, cursor, pattern });
}

export async function keyGet(connId: ConnId, key: string): Promise<KeyDetail> {
  return invoke<KeyDetail>('key_get', { connId, key });
}

export async function keySet(
  connId: ConnId,
  key: string,
  value: unknown,
  keyType: string,
): Promise<void> {
  return invoke<void>('key_set', { connId, key, value, keyType });
}

export async function keyDelete(connId: ConnId, key: string): Promise<void> {
  return invoke<void>('key_delete', { connId, key });
}

export async function keyRename(connId: ConnId, oldKey: string, newKey: string): Promise<void> {
  return invoke<void>('key_rename', { connId, oldKey, newKey });
}

export async function keyTtlSet(connId: ConnId, key: string, ttlSeconds: number): Promise<void> {
  return invoke<void>('key_ttl_set', { connId, key, ttlSeconds });
}

export async function keysBulkDelete(connId: ConnId, keys: string[]): Promise<BulkResult> {
  return invoke<BulkResult>('keys_bulk_delete', { connId, keys });
}

export async function keysBulkTtl(
  connId: ConnId,
  keys: string[],
  ttlSeconds: number | null,
): Promise<BulkResult> {
  return invoke<BulkResult>('keys_bulk_ttl', { connId, keys, ttlSeconds });
}
