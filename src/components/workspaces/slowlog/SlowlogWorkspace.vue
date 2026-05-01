<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { useSlowlogStore } from '@/stores/slowlog';

const store = useSlowlogStore();

onMounted(() => {
  store.fetchEntries();
});

onUnmounted(() => {
  store.stopAutoRefresh();
});

function formatTimestamp(ts: number): string {
  if (!ts) return '--';
  const d = new Date(ts * 1000);
  return d.toLocaleString('zh-CN', { hour12: false });
}

function formatDuration(us: number): string {
  if (us >= 1_000_000) return (us / 1_000_000).toFixed(2) + 's';
  if (us >= 1_000) return (us / 1_000).toFixed(2) + 'ms';
  return us + 'μs';
}

function durationClass(us: number): string {
  if (us >= 100_000) return 'dur-danger';   // > 100ms
  if (us >= 10_000) return 'dur-warning';   // > 10ms
  return 'dur-normal';
}

function sortIcon(field: string): string {
  if (store.sortField !== field) return 'ri-arrow-up-down-line';
  return store.sortOrder === 'asc' ? 'ri-arrow-up-line' : 'ri-arrow-down-line';
}
</script>

<template>
  <div class="slowlog-workspace">
    <!-- Toolbar -->
    <div class="slowlog-toolbar">
      <div class="toolbar-left">
        <button class="btn-action" :disabled="store.loading" @click="store.fetchEntries">
          <i class="ri-refresh-line" :class="{ spin: store.loading }" /> Refresh
        </button>
        <button class="btn-action danger" @click="store.resetSlowlog">
          <i class="ri-delete-bin-line" /> Reset
        </button>
        <label class="auto-refresh-toggle">
          <input type="checkbox" :checked="store.autoRefresh" @change="store.toggleAutoRefresh" />
          <span>Auto ({{ store.autoRefreshInterval }}s)</span>
        </label>
      </div>
      <div class="toolbar-right">
        <span class="stat">Entries: <strong>{{ store.entries.length }}</strong></span>
        <label class="count-input">
          Count:
          <input v-model.number="store.entryCount" type="number" min="1" max="500" />
        </label>
      </div>
    </div>

    <!-- Table -->
    <div class="table-container">
      <table class="slowlog-table">
        <thead>
          <tr>
            <th class="col-id" @click="store.setSort('id')">
              ID <i :class="sortIcon('id')" />
            </th>
            <th class="col-time" @click="store.setSort('timestamp')">
              Time <i :class="sortIcon('timestamp')" />
            </th>
            <th class="col-dur" @click="store.setSort('duration_us')">
              Duration <i :class="sortIcon('duration_us')" />
            </th>
            <th class="col-cmd">Command</th>
            <th class="col-client">Client</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="store.sortedEntries.length === 0">
            <td colspan="5" class="empty-cell">
              <div class="empty-state">
                <i class="ri-time-line" />
                <p>No slowlog entries</p>
              </div>
            </td>
          </tr>
          <tr v-for="entry in store.sortedEntries" :key="entry.id">
            <td class="col-id">{{ entry.id }}</td>
            <td class="col-time">{{ formatTimestamp(entry.timestamp) }}</td>
            <td class="col-dur" :class="durationClass(entry.duration_us)">
              {{ formatDuration(entry.duration_us) }}
            </td>
            <td class="col-cmd">
              <code>{{ entry.command.join(' ') }}</code>
            </td>
            <td class="col-client">{{ entry.client_addr }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.slowlog-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--srn-color-surface-1);
}

.slowlog-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid var(--srn-color-border);
  gap: 12px;
}

.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-action {
  height: 30px;
  padding: 0 12px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  background: transparent;
  color: var(--srn-color-text-2);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}
.btn-action:hover { background: var(--srn-color-surface-2); }
.btn-action:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-action.danger:hover { background: rgba(239, 68, 68, 0.1); color: #ef4444; }

.auto-refresh-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--srn-color-text-2);
  cursor: pointer;
}
.auto-refresh-toggle input { margin: 0; }

.stat { font-size: 11px; color: var(--srn-color-text-3); }
.stat strong { color: var(--srn-color-text-1); }

.count-input {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--srn-color-text-3);
}
.count-input input {
  width: 50px;
  height: 22px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 0 4px;
  font-size: 11px;
  background: var(--srn-color-surface-2);
  color: var(--srn-color-text-1);
  outline: none;
  text-align: center;
}

.table-container {
  flex: 1;
  overflow: auto;
}

.slowlog-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.slowlog-table thead {
  position: sticky;
  top: 0;
  z-index: 1;
}

.slowlog-table th {
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  color: var(--srn-color-text-2);
  background: var(--srn-color-surface-2);
  border-bottom: 1px solid var(--srn-color-border);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}
.slowlog-table th:hover { color: var(--srn-color-text-1); }
.slowlog-table th i { font-size: 11px; margin-left: 4px; }

.slowlog-table td {
  padding: 6px 12px;
  border-bottom: 1px solid var(--srn-color-border);
  color: var(--srn-color-text-1);
}
.slowlog-table tr:hover td { background: var(--srn-color-surface-2); }

.col-id { width: 60px; color: var(--srn-color-text-3); }
.col-time { width: 160px; }
.col-dur { width: 100px; font-family: var(--srn-font-mono); font-weight: 600; }
.col-cmd { font-family: var(--srn-font-mono); }
.col-cmd code { font-size: 11px; word-break: break-all; }
.col-client { width: 140px; color: var(--srn-color-text-3); font-family: var(--srn-font-mono); font-size: 11px; }

.dur-danger { color: #ef4444; }
.dur-warning { color: #f97316; }
.dur-normal { color: var(--srn-color-text-1); }

.empty-cell { text-align: center; }
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  color: var(--srn-color-text-3);
  gap: 8px;
}
.empty-state i { font-size: 48px; }

@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }
</style>
