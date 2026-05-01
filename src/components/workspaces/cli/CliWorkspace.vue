<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useTerminalStore } from '@/stores/terminal';
import { useConnectionStore } from '@/stores/connection';
import { listen } from '@tauri-apps/api/event';
import { getFriendlyMessage } from '@/ipc/index';
import type { IpcError } from '@/types/ipc';
import CliTabBar from './CliTabBar.vue';
import CliTabPanel from './CliTabPanel.vue';

const termStore = useTerminalStore();
const connStore = useConnectionStore();

const initError = ref<string | null>(null);

// Create the first CLI tab for the current connection
async function initTab() {
  if (!connStore.activeConnId) return;
  if (termStore.tabList.length > 0) return;
  initError.value = null;
  try {
    await termStore.createTab(connStore.activeConnId);
  } catch (e: unknown) {
    const ipcErr = e as IpcError;
    if (ipcErr?.kind) {
      initError.value = getFriendlyMessage(ipcErr);
    } else {
      initError.value = String(e) || '终端初始化失败';
    }
  }
}

onMounted(initTab);

// When connection changes (e.g. user connects after CLI tab is already mounted),
// automatically create a new tab so the panel doesn't stay in the "no connection" state.
watch(
  () => connStore.activeConnId,
  (newId) => {
    if (newId && termStore.tabList.length === 0) {
      initTab();
    }
  },
);

// Listen for tab disconnected events
let unlisten: (() => void) | null = null;
onMounted(async () => {
  unlisten = await listen<{ tab_id: string }>('cli:tab_disconnected', (e) => {
    termStore.onTabDisconnected(e.payload.tab_id);
  });
});
onUnmounted(() => unlisten?.());

// Keyboard shortcuts: ⌘T new tab, ⌘W close tab
function handleKeydown(e: KeyboardEvent) {
  if (!e.metaKey && !e.ctrlKey) return;
  if (e.key === 't') {
    e.preventDefault();
    if (connStore.activeConnId && termStore.canAddTab) {
      termStore.createTab(connStore.activeConnId);
    }
  } else if (e.key === 'w') {
    e.preventDefault();
    if (termStore.activeTabId) {
      termStore.closeTab(termStore.activeTabId);
    }
  }
}
</script>

<template>
  <div class="cli-workspace" @keydown="handleKeydown" tabindex="-1">
    <!-- Multi-tab mode -->
    <template v-if="termStore.tabList.length > 0">
      <CliTabBar />
      <CliTabPanel
        v-if="termStore.activeTab"
        :key="termStore.activeTabId!"
        :tab="termStore.activeTab"
      />
    </template>

    <!-- Connected but tab init failed -->
    <template v-else-if="connStore.activeConnId && initError">
      <div class="cli-legacy-notice">
        <i class="ri-error-warning-line" style="color: var(--srn-color-warning);" />
        <span>终端初始化失败：{{ initError }}</span>
        <button class="retry-btn" @click="initTab">重试</button>
      </div>
    </template>

    <!-- Not connected -->
    <template v-else>
      <div class="cli-legacy-notice">
        <i class="ri-wifi-off-line" />
        <span>请先连接到 Redis 服务器</span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.cli-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  outline: none;
}
.cli-legacy-notice {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 100%;
  color: var(--srn-color-text-3);
  font-size: 13px;
  background: #1a1a2e;
}
.retry-btn {
  padding: 4px 12px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  background: transparent;
  color: var(--srn-color-text-2);
  font-size: 12px;
  cursor: pointer;
}
.retry-btn:hover {
  background: var(--srn-color-surface-2);
}
</style>
