<script setup lang="ts">
import { computed, onMounted, onUnmounted, onActivated, onDeactivated } from 'vue';
import { useMonitorStore } from '@/stores/monitor';
import { useConnectionStore } from '@/stores/connection';
import MetricCard from './MetricCard.vue';
import TrendChart from './TrendChart.vue';
import ServerInfoCard from './ServerInfoCard.vue';
import KeyspaceCard from './KeyspaceCard.vue';
import ClientListCard from './ClientListCard.vue';

const store = useMonitorStore();
const connStore = useConnectionStore();

function formatBytes(bytes: number): string {
  if (bytes >= 1_073_741_824) return (bytes / 1_073_741_824).toFixed(2);
  if (bytes >= 1_048_576) return (bytes / 1_048_576).toFixed(1);
  if (bytes >= 1024) return (bytes / 1024).toFixed(1);
  return String(bytes);
}

function bytesUnit(bytes: number): string {
  if (bytes >= 1_073_741_824) return 'GB';
  if (bytes >= 1_048_576) return 'MB';
  if (bytes >= 1024) return 'KB';
  return 'B';
}

const memoryDisplay = computed(() => {
  const b = store.latestMetrics?.used_memory_bytes ?? 0;
  return formatBytes(b);
});

const memoryUnit = computed(() => {
  const b = store.latestMetrics?.used_memory_bytes ?? 0;
  return bytesUnit(b);
});

const hitRate = computed(() => {
  if (!store.latestMetrics) return '0';
  const total = store.latestMetrics.keyspace_hits + store.latestMetrics.keyspace_misses;
  if (total === 0) return '0';
  return ((store.latestMetrics.keyspace_hits / total) * 100).toFixed(1);
});

const serverInfo = computed(() => store.latestMetrics?.server_info);
const keyspace = computed(() => store.latestMetrics?.keyspace ?? []);
const clients = computed(() => store.latestMetrics?.clients ?? []);

onMounted(() => {
  startDashboard();
});

onUnmounted(() => {
  stopDashboard();
});

onActivated(() => {
  startDashboard();
});

onDeactivated(() => {
  stopDashboard();
});

async function startDashboard() {
  const connId = connStore.activeConnId;
  if (!connId) return;
  try {
    await store.startMetrics(connId, 5000);
  } catch (e) {
    console.error('Failed to start metrics:', e);
  }
}

async function stopDashboard() {
  try {
    await store.stopMetrics();
  } catch (e) {
    console.error('Failed to stop metrics:', e);
  }
}
</script>

<template>
  <div class="metrics-dashboard">
    <!-- Top: Metric Cards + Trend Charts (2x2 grid) -->
    <div class="metrics-grid">
      <div class="metric-cell">
        <MetricCard label="OPS" :value="store.latestMetrics?.ops_per_sec ?? 0" unit="ops/s" color="#6366f1" />
        <TrendChart :data="store.metricsOpsHistory" color="#6366f1" />
      </div>
      <div class="metric-cell">
        <MetricCard label="Memory" :value="memoryDisplay" :unit="memoryUnit" color="#22c55e" />
        <TrendChart :data="store.metricsMemoryHistory" color="#22c55e" />
      </div>
      <div class="metric-cell">
        <MetricCard label="Clients" :value="store.latestMetrics?.connected_clients ?? 0" color="#f97316" />
        <TrendChart :data="store.metricsClientsHistory" color="#f97316" />
      </div>
      <div class="metric-cell">
        <MetricCard label="Hit Rate" :value="hitRate" unit="%" color="#eab308" />
        <TrendChart :data="store.metricsHitRateHistory" color="#eab308" />
      </div>
    </div>

    <!-- Bottom: Info Cards -->
    <div class="info-grid">
      <ServerInfoCard v-if="serverInfo" :info="serverInfo" />
      <KeyspaceCard :keyspace="keyspace" />
      <ClientListCard :clients="clients" />
    </div>
  </div>
</template>

<style scoped>
.metrics-dashboard {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  overflow-y: auto;
  padding: 12px 16px;
  background: var(--srn-color-surface-1);
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.metric-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.info-grid > *:last-child:nth-child(odd) {
  grid-column: 1 / -1;
}
</style>
