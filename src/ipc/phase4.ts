/**
 * Phase 4 IPC — Advanced Tools
 * Lua script editor, import/export, key analyzer, health check,
 * multi-tab CLI, data masking, shortcut customization.
 */
import { invoke } from './index';

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

export interface LuaScript {
  id: string;
  name: string;
  script: string;
  created_at: string;
  last_used_at: string;
}

export interface LuaEvalResult {
  output: string;
  is_error: boolean;
  sha1?: string;
  value_type?: string;
  elapsed_ms?: number;
  value?: unknown;
}

export interface RedisExportKey {
  key: string;
  type: string;
  ttl: number;
  value: unknown;
  truncated?: boolean;
  size_bytes?: number;
  preview?: string;
}

export interface RedisExport {
  version: string;
  connection: { host: string; port: number; db: number };
  exported_at: string;
  keys: RedisExportKey[];
}

export interface ImportResult {
  success: number;
  skipped: number;
  failed: number;
  errors: string[];
}

export interface KeyMemoryStat {
  key: string;
  key_type: string;
  memory_bytes: number;
  encoding: string;
  element_count: number;
}

export interface ScanProgress {
  scanned: number;
  total_estimate: number;
  top_keys: KeyMemoryStat[];
  is_done: boolean;
}

export interface TtlBucket {
  label: string;
  count: number;
  percentage: number;
}

export interface TtlDistribution {
  total_sampled: number;
  buckets: TtlBucket[];
  expiring_soon_count: number;
  expiring_soon_warning: boolean;
}

export type HealthLevel = 'normal' | 'warning' | 'danger';

export interface HealthIndicator {
  name: string;
  value: string;
  level: HealthLevel;
  score: number;
  suggestion?: string;
}

export interface HealthReport {
  id: string;
  connection_id: string;
  score: number;
  indicators: HealthIndicator[];
  created_at: string;
}

export interface CliTabInfo {
  tab_id: string;
  name: string;
  db: number;
  is_connected: boolean;
}

export interface MaskingRule {
  id: string;
  pattern: string;
  mask_char: string;
  enabled: boolean;
  sort_order: number;
}

export interface ShortcutBinding {
  action: string;
  binding: string;
  updated_at: string;
}

// ─────────────────────────────────────────────
// Lua Script Editor
// ─────────────────────────────────────────────

export function luaEval(connId: string, script: string, keys: string[], argv: string[]): Promise<LuaEvalResult> {
  return invoke('lua_eval', { connId, script, keys, argv });
}

export function luaEvalsha(connId: string, sha1: string, keys: string[], argv: string[]): Promise<LuaEvalResult> {
  return invoke('lua_evalsha', { connId, sha1, keys, argv });
}

export function luaScriptLoad(connId: string, script: string): Promise<string> {
  return invoke('lua_script_load', { connId, script });
}

export function luaScriptExists(connId: string, sha1: string): Promise<boolean> {
  return invoke('lua_script_exists', { connId, sha1 });
}

export function luaHistorySave(script: string, name: string): Promise<LuaScript> {
  return invoke('lua_history_save', { script, name });
}

export function luaHistoryList(): Promise<LuaScript[]> {
  return invoke('lua_history_list', {});
}

export function luaHistoryDelete(id: string): Promise<void> {
  return invoke('lua_history_delete', { id });
}

export function luaHistoryRename(id: string, name: string): Promise<void> {
  return invoke('lua_history_rename', { id, name });
}

// ─────────────────────────────────────────────
// Import / Export
// ─────────────────────────────────────────────

export function exportKeysJson(connId: string, keys: string[]): Promise<RedisExport> {
  return invoke('export_keys_json', { connId, keys });
}

export function exportDbJson(connId: string): Promise<RedisExport> {
  return invoke('export_db_json', { connId });
}

export function importKeysJson(connId: string, data: RedisExport, overwrite: boolean): Promise<ImportResult> {
  return invoke('import_keys_json', { connId, data, overwrite });
}

export function rdbParseFile(filePath: string): Promise<RedisExport> {
  return invoke('rdb_parse_file', { filePath });
}

// ─────────────────────────────────────────────
// Key Analyzer
// ─────────────────────────────────────────────

export function keyScanMemoryStart(connId: string, lowImpact: boolean): Promise<string> {
  return invoke('key_scan_memory_start', { connId, lowImpact });
}

export function keyScanMemoryStop(taskId: string): Promise<void> {
  return invoke('key_scan_memory_stop', { taskId });
}

export function keyTtlDistribution(connId: string): Promise<TtlDistribution> {
  return invoke('key_ttl_distribution', { connId });
}

export function keyScanMemoryExportCsv(taskId: string): Promise<string> {
  return invoke('key_scan_memory_export_csv', { taskId });
}

// ─────────────────────────────────────────────
// Health Check
// ─────────────────────────────────────────────

export function healthCheckGenerate(connId: string): Promise<HealthReport> {
  return invoke('health_check_generate', { connId });
}

export function healthCheckHistoryList(): Promise<HealthReport[]> {
  return invoke('health_check_history_list', {});
}

export function healthCheckHistoryGet(id: string): Promise<HealthReport> {
  return invoke('health_check_history_get', { id });
}

export function healthCheckExportMarkdown(connId: string, report: HealthReport): Promise<string> {
  return invoke('health_check_export_markdown', { connId, report });
}

// ─────────────────────────────────────────────
// Multi-Tab CLI
// ─────────────────────────────────────────────

export function cliTabCreate(connId: string): Promise<CliTabInfo> {
  return invoke('cli_tab_create', { connId });
}

export function cliTabClose(tabId: string): Promise<void> {
  return invoke('cli_tab_close', { tabId });
}

export function cliExecTab(tabId: string, rawCommand: string, confirmToken?: string): Promise<{ output: string; is_error: boolean }> {
  return invoke('cli_exec_tab', { tabId, rawCommand, confirmToken });
}

export function cliHistoryGetTab(tabId: string): Promise<string[]> {
  return invoke('cli_history_get_tab', { tabId });
}

// ─────────────────────────────────────────────
// Data Masking
// ─────────────────────────────────────────────

export function maskingRuleList(): Promise<MaskingRule[]> {
  return invoke('masking_rule_list', {});
}

export function maskingRuleSave(rule: MaskingRule): Promise<void> {
  return invoke('masking_rule_save', { rule });
}

export function maskingRuleDelete(id: string): Promise<void> {
  return invoke('masking_rule_delete', { id });
}

export function maskingRuleReorder(ids: string[]): Promise<void> {
  return invoke('masking_rule_reorder', { ids });
}

// ─────────────────────────────────────────────
// Shortcut Customization
// ─────────────────────────────────────────────

export function shortcutBindingList(): Promise<ShortcutBinding[]> {
  return invoke('shortcut_binding_list', {});
}

export function shortcutBindingSave(action: string, binding: string): Promise<void> {
  return invoke('shortcut_binding_save', { action, binding });
}

export function shortcutBindingDelete(action: string): Promise<void> {
  return invoke('shortcut_binding_delete', { action });
}

export function shortcutBindingResetAll(): Promise<void> {
  return invoke('shortcut_binding_reset_all', {});
}
