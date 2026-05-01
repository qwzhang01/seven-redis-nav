<script setup lang="ts">
import type { MetricsServerInfo } from '@/types/phase2';

defineProps<{
  info: MetricsServerInfo;
}>();

function formatUptime(secs: number): string {
  const d = Math.floor(secs / 86400);
  const h = Math.floor((secs % 86400) / 3600);
  const m = Math.floor((secs % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function formatTimestamp(ts: number): string {
  if (ts === 0) return 'Never';
  return new Date(ts * 1000).toLocaleString('zh-CN', { hour12: false });
}
</script>

<template>
  <div class="server-info-card">
    <div class="card-title">
      <i class="ri-server-line" /> Server Info
    </div>
    <div class="info-grid">
      <div class="info-item">
        <span class="info-label">Version</span>
        <span class="info-value">{{ info.redis_version }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">OS</span>
        <span class="info-value">{{ info.os }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">PID</span>
        <span class="info-value">{{ info.process_id }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">Port</span>
        <span class="info-value">{{ info.tcp_port }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">Uptime</span>
        <span class="info-value">{{ formatUptime(info.uptime_secs) }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">Role</span>
        <span class="role-badge" :class="info.role">{{ info.role }}</span>
      </div>
      <div v-if="info.role === 'master'" class="info-item">
        <span class="info-label">Slaves</span>
        <span class="info-value">{{ info.connected_slaves }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">AOF</span>
        <span class="info-value">
          <span class="status-indicator" :class="info.aof_enabled ? 'on' : 'off'" />
          {{ info.aof_enabled ? 'ON' : 'OFF' }}
        </span>
      </div>
      <div class="info-item">
        <span class="info-label">Last RDB</span>
        <span class="info-value">{{ formatTimestamp(info.last_rdb_save_ts) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.server-info-card {
  background: var(--srn-color-surface-2);
  border-radius: var(--srn-radius-md, 8px);
  padding: 12px 16px;
  border: 1px solid var(--srn-color-border);
}

.card-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--srn-color-text-2);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-label {
  font-size: 11px;
  color: var(--srn-color-text-3);
  flex-shrink: 0;
  min-width: 56px;
}

.info-value {
  font-size: 12px;
  color: var(--srn-color-text-1);
  font-variant-numeric: tabular-nums;
}

.role-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 10px;
  text-transform: uppercase;
}
.role-badge.master {
  background: #22c55e20;
  color: #22c55e;
}
.role-badge.slave {
  background: #f9731620;
  color: #f97316;
}

.status-indicator {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.status-indicator.on { background: #22c55e; }
.status-indicator.off { background: #ef4444; }
</style>
