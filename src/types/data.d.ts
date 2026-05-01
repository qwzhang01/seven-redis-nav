export type KeyType = 'string' | 'hash' | 'list' | 'set' | 'zset' | 'stream' | 'unknown';

export interface KeyMeta {
  key: string;
  key_type: KeyType;
  ttl: number;       // -1 = no expiry, -2 = not exists
  size: number;      // bytes
  encoding: string;
}

export interface ScanPage {
  keys: KeyMeta[];
  cursor: number;    // 0 = scan complete
  total_scanned: number;
}

export type RedisValue =
  | { type: 'string'; value: string }
  | { type: 'hash'; fields: [string, string][] }
  | { type: 'list'; items: string[] }
  | { type: 'set'; members: string[] }
  | { type: 'zset'; members: [number, string][] }
  | { type: 'stream'; entries: unknown[] };

export interface KeyDetail {
  key: string;
  key_type: KeyType;
  ttl: number;
  size: number;
  encoding: string;
  length: number;
  db: number;
  value: RedisValue;
}

export interface BulkResult {
  success: number;
  failed: string[];
}
