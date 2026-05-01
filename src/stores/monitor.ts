import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { MonitorCommand, MetricsSnapshot } from '@/types/phase2';
import { monitorMetricsStart, monitorMetricsStop } from '@/ipc/phase2';
import { listenMetricsSnapshot } from '@/ipc/event';

const MAX_COMMANDS = 10000;

// Command classification for coloring
const READ_COMMANDS = new Set([
  'GET', 'MGET', 'HGET', 'HGETALL', 'HMGET', 'HVALS', 'HKEYS', 'HLEN',
  'LRANGE', 'LLEN', 'LINDEX', 'SMEMBERS', 'SCARD', 'SISMEMBER',
  'ZRANGE', 'ZRANGEBYSCORE', 'ZCARD', 'ZSCORE', 'ZRANK',
  'TTL', 'PTTL', 'TYPE', 'EXISTS', 'KEYS', 'SCAN', 'DBSIZE',
  'STRLEN', 'GETRANGE', 'SRANDMEMBER', 'RANDOMKEY',
]);

const ADMIN_COMMANDS = new Set([
  'CONFIG', 'FLUSHDB', 'FLUSHALL', 'DEBUG', 'SHUTDOWN', 'BGSAVE',
  'BGREWRITEAOF', 'SLAVEOF', 'REPLICAOF', 'CLUSTER', 'CLIENT',
  'SLOWLOG', 'MONITOR', 'INFO', 'SAVE', 'LASTSAVE',
]);

export type CommandCategory = 'read' | 'write' | 'admin';

export function classifyCommand(cmd: string): CommandCategory {
  const upper = cmd.toUpperCase();
  if (READ_COMMANDS.has(upper)) return 'read';
  if (ADMIN_COMMANDS.has(upper)) return 'admin';
  return 'write';
}

export const useMonitorStore = defineStore('monitor', () => {
  const commands = ref<MonitorCommand[]>([]);
  const active = ref(false);
  const paused = ref(false);
  const pauseBuffer = ref<MonitorCommand[]>([]);
  const filterKeyword = ref('');
  const totalReceived = ref(0);

  function addCommand(cmd: MonitorCommand) {
    totalReceived.value++;

    if (paused.value) {
      pauseBuffer.value.push(cmd);
      return;
    }

    pushToRingBuffer(cmd);
  }

  function pushToRingBuffer(cmd: MonitorCommand) {
    commands.value.push(cmd);
    if (commands.value.length > MAX_COMMANDS) {
      commands.value.shift();
    }
  }

  function pause() { paused.value = true; }

  function resume() {
    paused.value = false;
    for (const cmd of pauseBuffer.value) {
      pushToRingBuffer(cmd);
    }
    pauseBuffer.value = [];
  }

  function clearCommands() {
    commands.value = [];
    pauseBuffer.value = [];
    totalReceived.value = 0;
  }

  function setActive(val: boolean) { active.value = val; }

  function reset() {
    clearCommands();
    active.value = false;
    paused.value = false;
  }

  // ---- Metrics Dashboard State ----
  const MAX_METRICS_POINTS = 40;

  const metricsTaskId = ref<string | null>(null);
  const latestMetrics = ref<MetricsSnapshot | null>(null);
  const metricsOpsHistory = ref<number[]>([]);
  const metricsMemoryHistory = ref<number[]>([]);
  const metricsClientsHistory = ref<number[]>([]);
  const metricsHitRateHistory = ref<number[]>([]);
  const metricsUnlisten = ref<(() => void) | null>(null);

  async function startMetrics(connId: string, intervalMs: number = 5000) {
    // Stop any existing metrics task
    await stopMetrics();

    // Listen for metrics events
    const unlisten = await listenMetricsSnapshot((snapshot) => {
      latestMetrics.value = snapshot;

      // Push to sliding window histories
      metricsOpsHistory.value.push(snapshot.ops_per_sec);
      if (metricsOpsHistory.value.length > MAX_METRICS_POINTS) {
        metricsOpsHistory.value.shift();
      }

      metricsMemoryHistory.value.push(snapshot.used_memory_bytes);
      if (metricsMemoryHistory.value.length > MAX_METRICS_POINTS) {
        metricsMemoryHistory.value.shift();
      }

      metricsClientsHistory.value.push(snapshot.connected_clients);
      if (metricsClientsHistory.value.length > MAX_METRICS_POINTS) {
        metricsClientsHistory.value.shift();
      }

      const total = snapshot.keyspace_hits + snapshot.keyspace_misses;
      const hitRate = total > 0 ? (snapshot.keyspace_hits / total) * 100 : 0;
      metricsHitRateHistory.value.push(hitRate);
      if (metricsHitRateHistory.value.length > MAX_METRICS_POINTS) {
        metricsHitRateHistory.value.shift();
      }
    });

    metricsUnlisten.value = unlisten;

    // Start the backend sampling task
    const taskId = await monitorMetricsStart(connId, intervalMs);
    metricsTaskId.value = taskId;
  }

  async function stopMetrics() {
    // Stop the backend sampling task
    try {
      await monitorMetricsStop();
    } catch {
      // Ignore errors if already stopped
    }

    // Unlisten from events
    if (metricsUnlisten.value) {
      metricsUnlisten.value();
      metricsUnlisten.value = null;
    }

    metricsTaskId.value = null;
  }

  function clearMetrics() {
    latestMetrics.value = null;
    metricsOpsHistory.value = [];
    metricsMemoryHistory.value = [];
    metricsClientsHistory.value = [];
    metricsHitRateHistory.value = [];
  }

  const filteredCommands = computed(() => {
    if (!filterKeyword.value) return commands.value;
    const kw = filterKeyword.value.toLowerCase();
    return commands.value.filter(
      (c) =>
        c.command.toLowerCase().includes(kw) ||
        c.args.some((a) => a.toLowerCase().includes(kw)),
    );
  });

  return {
    commands,
    active,
    paused,
    pauseBuffer,
    filterKeyword,
    totalReceived,
    filteredCommands,
    addCommand,
    pause,
    resume,
    clearCommands,
    setActive,
    reset,
    // Metrics Dashboard
    metricsTaskId,
    latestMetrics,
    metricsOpsHistory,
    metricsMemoryHistory,
    metricsClientsHistory,
    metricsHitRateHistory,
    startMetrics,
    stopMetrics,
    clearMetrics,
  };
});
