<script setup lang="ts">
import type { ClientEntry } from '@/types/phase2';

defineProps<{
  clients: ClientEntry[];
}>();

function formatAge(secs: number): string {
  if (secs >= 86400) return `${Math.floor(secs / 86400)}d ${Math.floor((secs % 86400) / 3600)}h`;
  if (secs >= 3600) return `${Math.floor(secs / 3600)}h ${Math.floor((secs % 3600) / 60)}m`;
  if (secs >= 60) return `${Math.floor(secs / 60)}m ${secs % 60}s`;
  return `${secs}s`;
}
</script>

<template>
  <div class="client-list-card">
    <div class="card-title">
      <i class="ri-user-line" /> Clients
    </div>
    <div v-if="clients.length === 0" class="empty-state">No client data</div>
    <div v-else class="client-list">
      <div class="client-header">
        <span class="col-addr">Address</span>
        <span class="col-cmd">Command</span>
        <span class="col-age">Age</span>
        <span class="col-db">DB</span>
      </div>
      <div v-for="client in clients.slice(0, 6)" :key="client.id" class="client-row">
        <span class="col-addr" :title="client.name || client.addr">
          {{ client.name || client.addr }}
        </span>
        <span class="col-cmd">{{ client.cmd }}</span>
        <span class="col-age">{{ formatAge(client.age_secs) }}</span>
        <span class="col-db">{{ client.db }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.client-list-card {
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

.empty-state {
  font-size: 11px;
  color: var(--srn-color-text-3);
  text-align: center;
  padding: 16px 0;
}

.client-list {
  font-size: 11px;
}

.client-header {
  display: flex;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid var(--srn-color-border);
  color: var(--srn-color-text-3);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 10px;
  letter-spacing: 0.5px;
}

.client-row {
  display: flex;
  gap: 8px;
  padding: 4px 0;
  color: var(--srn-color-text-2);
}
.client-row:hover { background: var(--srn-color-surface-1); }

.col-addr { flex: 2; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.col-cmd { flex: 1; color: #6366f1; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.col-age { flex: 1; color: var(--srn-color-text-3); font-variant-numeric: tabular-nums; }
.col-db { flex: 0 0 30px; color: #a78bfa; }
</style>
