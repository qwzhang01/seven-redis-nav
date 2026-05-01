// Phase 3 types for Stream, Bitmap, HyperLogLog viewers

// ===== Stream =====

export interface FieldValuePair {
  field: string;
  value: string;
}

export interface StreamEntry {
  id: string;
  fields: FieldValuePair[];
  timestamp_ms: number;
}

export interface StreamGroup {
  name: string;
  consumers: number;
  pending: number;
  last_delivered_id: string;
}

export interface PendingEntry {
  consumer_name: string;
  pending_count: number;
  idle_ms: number;
  last_delivered_id: string;
}

// ===== Stream Info =====

export interface StreamInfo {
  length: number;
  radix_nodes: number;
  radix_levels: number;
  last_id: string;
  max_length: number;
  groups: number;
  first_entry_id: string;
}

// ===== Bitmap =====

export interface BitmapChunk {
  data_base64: string;
  start_byte: number;
  byte_length: number;
}

// ===== HyperLogLog =====

export interface HllStats {
  estimated_cardinality: number;
  encoding: string;
}
