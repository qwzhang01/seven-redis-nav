<script setup lang="ts">
import type { DbKeyspace } from '@/types/phase2';

defineProps<{
  keyspace: DbKeyspace[];
}>();

function formatTTL(secs: number): string {
  if (secs <= 0) return '--';
  if (secs >= 86400) return `${(secs / 86400).toFixed(1)}d`;
  if (secs >= 3600) return `${(secs / 3600).toFixed(1)}h`;
  return `${secs.toFixed(0)}s`;
}
</script>

<template>
  <div class="keyspace-card">
    <div class="card-title">
      <i class="ri-database-2-line" /> Keyspace
    </div>
    <div v-if="keyspace.length === 0" class="empty-state">No keyspace data</div>
    <div v-else class="keyspace-list">
      <div v-for="db in keyspace" :key="db.db" class="db-row">
        <span class="db-name">db{{ db.db }}</span>
        <div class="db-stats">
          <span class="stat total">
            <span class="stat-num">{{ db.keys }}</span>
            <span class="stat-label">keys</span>
          </span>
          <span class="stat expires">
            <span class="stat-num">{{ db.expires }}</span>
            <span class="stat-label">TTL</span>
          </span>
          <span class="stat permanent">
            <span class="stat-num">{{ db.keys - db.expires }}</span>
            <span class="stat-label">persist</span>
          </span>
          <span v-if="db.avg_ttl_secs > 0" class="stat avg-ttl">
            <span class="stat-num">{{ formatTTL(db.avg_ttl_secs) }}</span>
            <span class="stat-label">avg TTL</span>
          </span>
        </div>
        <div class="db-bar">
          <div
            class="bar-expires"
            :style="{ width: db.keys > 0 ? (db.expires / db.keys * 100) + '%' : '0%' }"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.keyspace-card {
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

.keyspace-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.db-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.db-name {
  font-size: 12px;
  font-weight: 600;
  color: #a78bfa;
}

.db-stats {
  display: flex;
  gap: 12px;
}

.stat {
  display: flex;
  align-items: baseline;
  gap: 3px;
  font-size: 11px;
}

.stat-num {
  font-weight: 600;
  color: var(--srn-color-text-1);
  font-variant-numeric: tabular-nums;
}

.stat-label {
  color: var(--srn-color-text-3);
}

.stat.total .stat-num { color: #6366f1; }
.stat.expires .stat-num { color: #f97316; }
.stat.permanent .stat-num { color: #22c55e; }
.stat.avg-ttl .stat-num { color: #eab308; }

.db-bar {
  height: 3px;
  background: var(--srn-color-surface-1);
  border-radius: 2px;
  overflow: hidden;
}

.bar-expires {
  height: 100%;
  background: #f97316;
  border-radius: 2px;
  transition: width 0.3s;
}
</style>
