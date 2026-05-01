import { invoke } from './index';
import type { StreamEntry, StreamGroup, PendingEntry, BitmapChunk, HllStats, StreamInfo } from '@/types/phase3';

// ---- Stream ----

export async function streamRange(
  connId: string,
  key: string,
  start: string,
  end: string,
  count?: number,
): Promise<StreamEntry[]> {
  return invoke<StreamEntry[]>('stream_range', { connId, key, start, end, count: count ?? null });
}

export async function streamRevRange(
  connId: string,
  key: string,
  start: string,
  end: string,
  count?: number,
): Promise<StreamEntry[]> {
  return invoke<StreamEntry[]>('stream_rev_range', { connId, key, start, end, count: count ?? null });
}

export async function streamAdd(
  connId: string,
  key: string,
  fields: [string, string][],
  id?: string,
  maxlen?: number,
  approx?: boolean,
): Promise<string> {
  return invoke<string>('stream_add', { connId, key, fields, id: id ?? null, maxlen: maxlen ?? null, approx: approx ?? null });
}

export async function streamDel(
  connId: string,
  key: string,
  ids: string[],
): Promise<number> {
  return invoke<number>('stream_del', { connId, key, ids });
}

export async function streamGroups(
  connId: string,
  key: string,
): Promise<StreamGroup[]> {
  return invoke<StreamGroup[]>('stream_groups', { connId, key });
}

export async function streamPending(
  connId: string,
  key: string,
  group: string,
): Promise<PendingEntry[]> {
  return invoke<PendingEntry[]>('stream_pending', { connId, key, group });
}

export async function streamInfo(
  connId: string,
  key: string,
): Promise<StreamInfo> {
  return invoke<StreamInfo>('stream_info', { connId, key });
}

// ---- Bitmap ----

export async function bitmapChunk(
  connId: string,
  key: string,
  startByte: number,
  endByte: number,
): Promise<BitmapChunk> {
  return invoke<BitmapChunk>('bitmap_chunk', { connId, key, startByte, endByte });
}

export async function bitmapCount(
  connId: string,
  key: string,
  start: number,
  end: number,
): Promise<number> {
  return invoke<number>('bitmap_count', { connId, key, start, end });
}

export async function bitmapPos(
  connId: string,
  key: string,
  bit: number,
  start?: number,
  end?: number,
): Promise<number> {
  return invoke<number>('bitmap_pos', { connId, key, bit, start: start ?? null, end: end ?? null });
}

export async function bitmapSetBit(
  connId: string,
  key: string,
  offset: number,
  value: number,
): Promise<number> {
  return invoke<number>('bitmap_set_bit', { connId, key, offset, value });
}

// ---- HyperLogLog ----

export async function hllAdd(
  connId: string,
  key: string,
  elements: string[],
): Promise<boolean> {
  return invoke<boolean>('hll_add', { connId, key, elements });
}

export async function hllCount(
  connId: string,
  key: string,
): Promise<HllStats> {
  return invoke<HllStats>('hll_count', { connId, key });
}

export async function hllMerge(
  connId: string,
  destKey: string,
  sourceKeys: string[],
): Promise<void> {
  return invoke<void>('hll_merge', { connId, destKey, sourceKeys });
}
