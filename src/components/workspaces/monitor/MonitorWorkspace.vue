<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { useMonitorStore, classifyCommand } from '@/stores/monitor';
import { useConnectionStore } from '@/stores/connection';
import { monitorStart, monitorStop } from '@/ipc/phase2';
import { listenMonitorCommand } from '@/ipc/event';
import MetricsDashboard from './MetricsDashboard.vue';

type TabKey = 'commands' | 'dashboard';

const store = useMonitorStore();
const connStore = useConnectionStore();

const activeTab = ref<TabKey>('commands');
const streamRef = ref<HTMLDivElement | null>(null);
const autoScroll = ref(true);
const loading = ref(false);

let unlistenCmd: (() => void) | null = null;

onMounted(async () => {
  unlistenCmd = await listenMonitorCommand((cmd) => {
    store.addCommand(cmd);
  });
});

onUnmounted(() => {
  unlistenCmd?.();
});

// Auto-scroll logic
watch(() => store.commands.length, () => {
  if (autoScroll.value && !store.paused && streamRef.value) {
    requestAnimationFrame(() => {
      if (streamRef.value) {
        streamRef.value.scrollTop = streamRef.value.scrollHeight;
      }
    });
  }
});

function handleScroll() {
  if (!streamRef.value) return;
  const { scrollTop, scrollHeight, clientHeight } = streamRef.value;
  autoScroll.value = scrollHeight - scrollTop - clientHeight < 50;
}

function scrollToBottom() {
  autoScroll.value = true;
  nextTick(() => {
    if (streamRef.value) {
      streamRef.value.scrollTop = streamRef.value.scrollHeight;
    }
  });
}

async function handleStart() {
  if (!connStore.activeConnId) return;
  loading.value = true;
  try {
    await monitorStart(connStore.activeConnId);
    store.setActive(true);
  } catch (e) {
    console.error('Monitor start failed:', e);
  } finally {
    loading.value = false;
  }
}

async function handleStop() {
  loading.value = true;
  try {
    await monitorStop(connStore.activeConnId!);
    store.setActive(false);
  } catch (e) {
    console.error('Monitor stop failed:', e);
  } finally {
    loading.value = false;
  }
}

function getCmdClass(cmd: string): string {
  return 'cmd-' + classifyCommand(cmd);
}

function formatTimestamp(ts: number): string {
  if (ts === 0) return '--';
  try {
    const d = new Date(ts * 1000);
    const time = d.toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const ms = String(d.getMilliseconds()).padStart(3, '0');
    return `${time}.${ms}`;
  } catch {
    return String(ts);
  }
}
</script>

<template>
  <div class="monitor-workspace">
    <!-- Toolbar -->
    <div class="monitor-toolbar">
      <div class="toolbar-left">
        <div class="tab-group">
          <button class="tab-btn" :class="{ active: activeTab === 'commands' }" @click="activeTab = 'commands'">
            <i class="ri-terminal-box-line" /> Command Trace
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'dashboard' }" @click="activeTab = 'dashboard'">
            <i class="ri-dashboard-3-line" /> Metrics Dashboard
          </button>
        </div>
      </div>
      <div class="toolbar-right">
        <template v-if="activeTab === 'commands'">
          <button v-if="!store.active" class="btn-start" :disabled="loading" @click="handleStart">
            <i class="ri-play-fill" /> Start
          </button>
          <button v-else class="btn-stop" :disabled="loading" @click="handleStop">
            <i class="ri-stop-fill" /> Stop
          </button>
          <button class="btn-icon" :class="{ active: store.paused }" :title="store.paused ? 'Resume' : 'Pause'" @click="store.paused ? store.resume() : store.pause()">
            <i :class="store.paused ? 'ri-play-line' : 'ri-pause-line'" />
          </button>
          <button class="btn-icon" title="Clear" @click="store.clearCommands">
            <i class="ri-delete-bin-line" />
          </button>
          <span class="stat">Total: <strong>{{ store.totalReceived }}</strong></span>
          <span v-if="store.paused" class="paused-badge">
            <i class="ri-pause-circle-line" /> {{ store.pauseBuffer.length }} buffered
          </span>
          <div class="filter-box">
            <i class="ri-search-line" />
            <input v-model="store.filterKeyword" type="text" placeholder="Filter commands..." />
          </div>
        </template>
      </div>
    </div>

    <!-- Command Trace Tab -->
    <template v-if="activeTab === 'commands'">
      <!-- Legend -->
      <div class="legend-bar">
        <span class="legend-item"><span class="dot read" /> Read</span>
        <span class="legend-item"><span class="dot write" /> Write</span>
        <span class="legend-item"><span class="dot admin" /> Admin</span>
      </div>

      <!-- Command stream -->
      <div ref="streamRef" class="command-stream" @scroll="handleScroll">
        <div v-if="store.filteredCommands.length === 0" class="empty-state">
          <i class="ri-terminal-box-line" />
          <p v-if="!store.active">Click "Start" to begin monitoring Redis commands</p>
          <p v-else>Waiting for commands...</p>
        </div>
        <div
          v-for="(cmd, idx) in store.filteredCommands"
          :key="idx"
          class="cmd-row"
        >
          <span class="cmd-time">{{ formatTimestamp(cmd.timestamp) }}</span>
          <span class="cmd-db">db{{ cmd.db }}</span>
          <span class="cmd-client">{{ cmd.client }}</span>
          <span class="cmd-name" :class="getCmdClass(cmd.command)">{{ cmd.command }}</span>
          <span class="cmd-args">{{ cmd.args.join(' ') }}</span>
        </div>
      </div>

      <!-- Scroll to bottom button -->
      <Transition name="fade">
        <button v-if="!autoScroll" class="scroll-bottom-btn" @click="scrollToBottom">
          <i class="ri-arrow-down-line" /> Scroll to bottom
        </button>
      </Transition>
    </template>

    <!-- Metrics Dashboard Tab -->
    <MetricsDashboard v-else />
  </div>
</template>

<style scoped>
.monitor-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--srn-color-surface-1);
  position: relative;
}

.monitor-toolbar {
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

.tab-group {
  display: flex;
  gap: 2px;
  background: var(--srn-color-surface-2);
  border-radius: var(--srn-radius-sm);
  padding: 2px;
}

.tab-btn {
  height: 28px;
  padding: 0 12px;
  border: none;
  border-radius: var(--srn-radius-sm);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  background: transparent;
  color: var(--srn-color-text-3);
  transition: all 0.15s;
}
.tab-btn:hover { color: var(--srn-color-text-2); }
.tab-btn.active {
  background: var(--srn-color-surface-1);
  color: var(--srn-color-text-1);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.btn-start, .btn-stop {
  height: 30px;
  padding: 0 12px;
  border: none;
  border-radius: var(--srn-radius-sm);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #fff;
}
.btn-start { background: #22c55e; }
.btn-stop { background: #ef4444; }
.btn-start:disabled, .btn-stop:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-icon {
  width: 28px;
  height: 28px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  background: transparent;
  color: var(--srn-color-text-2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}
.btn-icon:hover { background: var(--srn-color-surface-2); }
.btn-icon.active { background: var(--srn-color-warning); color: #fff; border-color: var(--srn-color-warning); }

.stat { font-size: 11px; color: var(--srn-color-text-3); }
.stat strong { color: var(--srn-color-text-1); }

.paused-badge {
  font-size: 11px;
  color: var(--srn-color-warning);
  display: flex;
  align-items: center;
  gap: 4px;
}

.filter-box {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--srn-color-text-3);
}
.filter-box input {
  width: 160px;
  height: 24px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 0 6px;
  font-size: 11px;
  background: var(--srn-color-surface-2);
  color: var(--srn-color-text-1);
  outline: none;
}

.legend-bar {
  display: flex;
  gap: 16px;
  padding: 4px 16px;
  border-bottom: 1px solid var(--srn-color-border);
  font-size: 11px;
  color: var(--srn-color-text-3);
}
.legend-item { display: flex; align-items: center; gap: 4px; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.read { background: #22c55e; }
.dot.write { background: #f97316; }
.dot.admin { background: #ef4444; }

.command-stream {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
  font-family: var(--srn-font-mono);
  font-size: 12px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--srn-color-text-3);
  gap: 8px;
}
.empty-state i { font-size: 48px; }

.cmd-row {
  display: flex;
  gap: 10px;
  padding: 2px 16px;
  line-height: 1.6;
}
.cmd-row:hover { background: var(--srn-color-surface-2); }

.cmd-time { color: var(--srn-color-text-3); flex-shrink: 0; }
.cmd-db { color: #a78bfa; flex-shrink: 0; min-width: 30px; }
.cmd-client { color: var(--srn-color-text-3); flex-shrink: 0; min-width: 100px; font-size: 11px; }
.cmd-name { font-weight: 600; flex-shrink: 0; min-width: 60px; }
.cmd-args { color: var(--srn-color-text-2); word-break: break-all; }

.cmd-read { color: #22c55e; }
.cmd-write { color: #f97316; }
.cmd-admin { color: #ef4444; }

.scroll-bottom-btn {
  position: absolute;
  bottom: 16px;
  right: 16px;
  height: 28px;
  padding: 0 12px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  background: var(--srn-color-surface-2);
  color: var(--srn-color-text-2);
  font-size: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.scroll-bottom-btn:hover { background: var(--srn-color-surface-3, var(--srn-color-surface-2)); }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
