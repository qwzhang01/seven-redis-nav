<script setup lang="ts">
import { ref, computed } from 'vue';
import { useConnectionStore } from '@/stores/connection';
import ConnectionForm from '@/components/dialogs/ConnectionForm.vue';
import type { ConnectionConfig } from '@/types/connection';

const connStore = useConnectionStore();

const statusText = computed(() => {
  if (!connStore.isConnected || !connStore.activeConnId) return null;
  if (connStore.isTempConnection && connStore.tempConnectionConfig) {
    const c = connStore.tempConnectionConfig;
    return `${c.host}:${c.port}`;
  }
  const c = connStore.activeConnection;
  if (!c) return null;
  return `${c.host}:${c.port}`;
});

// Save temp connection dialog
const showSaveForm = ref(false);
const savePrefill = ref<ConnectionConfig | null>(null);

function handleSaveTemp() {
  if (!connStore.tempConnectionConfig) return;
  const cfg = connStore.tempConnectionConfig;
  savePrefill.value = {
    id: '',
    name: `${cfg.host}:${cfg.port}`,
    group_name: '',
    host: cfg.host,
    port: cfg.port,
    password: cfg.password ?? null,
    auth_db: 0,
    timeout_ms: cfg.timeout_ms ?? 5000,
    sort_order: 0,
  };
  showSaveForm.value = true;
}

function handleSaved() {
  showSaveForm.value = false;
  savePrefill.value = null;
}
</script>

<template>
  <div class="statusbar">
    <div class="statusbar-left">
      <template v-if="statusText">
        <span>
          <i class="ri-server-line" style="color: var(--srn-color-success);" />
          {{ statusText }}
        </span>
        <span class="sep">·</span>
        <span>DB {{ connStore.currentDb }}</span>
        <template v-if="connStore.isTempConnection">
          <span class="sep">·</span>
          <span class="temp-badge">临时连接</span>
        </template>
      </template>
      <template v-else>
        <span style="color: var(--srn-color-text-3);">
          <i class="ri-server-line" /> 未连接
        </span>
      </template>
    </div>
    <div class="statusbar-right">
      <!-- Save temp connection prompt -->
      <button
        v-if="connStore.isTempConnection"
        class="save-temp-btn"
        @click="handleSaveTemp"
      >
        <i class="ri-save-line" />
        保存连接
      </button>
      <span v-else-if="connStore.isConnected">
        <i class="ri-checkbox-circle-line" style="color: var(--srn-color-success);" /> 已连接
      </span>
    </div>
  </div>

  <!-- Save temp connection form -->
  <ConnectionForm
    :visible="showSaveForm"
    :edit-config="savePrefill"
    @close="showSaveForm = false"
    @saved="handleSaved"
  />
</template>

<style scoped>
.statusbar {
  height: var(--srn-statusbar-h);
  background: var(--srn-color-statusbar);
  border-top: 1px solid #d5d5d9;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  font-size: 11px;
  color: var(--srn-color-text-2);
}
.statusbar-left, .statusbar-right { display: flex; align-items: center; gap: 12px; }
.sep { color: #ccc; }
.statusbar i { margin-right: 2px; }

.temp-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(255, 149, 0, 0.1);
  color: var(--srn-color-warning);
  border: 1px solid rgba(255, 149, 0, 0.2);
}

.save-temp-btn {
  height: 22px;
  padding: 0 10px;
  border: 1px solid var(--srn-color-primary);
  border-radius: var(--srn-radius-xs);
  background: rgba(220, 56, 45, 0.06);
  color: var(--srn-color-primary);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all var(--srn-motion-fast);
  animation: gentle-pulse 2s ease-in-out infinite;
}
.save-temp-btn:hover {
  background: rgba(220, 56, 45, 0.12);
}

@keyframes gentle-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
</style>
