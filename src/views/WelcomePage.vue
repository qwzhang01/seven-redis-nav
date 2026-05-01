<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { connectionTest } from '@/ipc/connection';
import { useConnectionStore } from '@/stores/connection';
import { useKeyBrowserStore } from '@/stores/keyBrowser';
import ConnectionForm from '@/components/dialogs/ConnectionForm.vue';
import SavedConnectionList from '@/components/welcome/SavedConnectionList.vue';
import QuickConnectForm from '@/components/welcome/QuickConnectForm.vue';
import EmptyState from '@/components/welcome/EmptyState.vue';
import type { IpcError } from '@/types/ipc';
import { getFriendlyMessage } from '@/ipc';
import type { ConnectionConfig, ConnId, QuickConnectReq } from '@/types/connection';

const connStore = useConnectionStore();
const keyBrowserStore = useKeyBrowserStore();

// Connection form dialog state
const showForm = ref(false);
const editConfig = ref<ConnectionConfig | null>(null);

// Connecting state for saved connections
const connectingId = ref<ConnId | null>(null);
const errorId = ref<ConnId | null>(null);

// Quick connect form ref
const quickFormRef = ref<InstanceType<typeof QuickConnectForm> | null>(null);

// Delete confirmation
const showDeleteConfirm = ref(false);
const deleteTargetId = ref<ConnId | null>(null);

const hasSavedConnections = computed(() => connStore.connections.length > 0);

onMounted(async () => {
  await connStore.loadConnections();
});

// ---- Quick connect handlers ----

async function handleQuickConnect(config: QuickConnectReq) {
  try {
    await connStore.openTempConnection(config);
    await keyBrowserStore.refresh();
  } catch (e) {
    const err = e as IpcError;
    quickFormRef.value?.setError(getFriendlyMessage(err));
  }
}

async function handleQuickTest(config: QuickConnectReq) {
  try {
    const res = await connectionTest({
      host: config.host,
      port: config.port,
      password: config.password,
      timeout_ms: config.timeout_ms,
    });
    const msg = `🎉 PONG! 延迟 ${res.latency_ms}ms` +
      (res.server_version ? ` · Redis ${res.server_version}` : '');
    quickFormRef.value?.setTestResult(msg);
  } catch (e) {
    const err = e as IpcError;
    quickFormRef.value?.setError(getFriendlyMessage(err));
  }
}

// ---- Saved connection handlers ----

async function handleConnectSaved(connId: ConnId) {
  connectingId.value = connId;
  errorId.value = null;
  try {
    await connStore.openConnection(connId);
    await keyBrowserStore.refresh();
  } catch (e) {
    console.error('Failed to connect:', e);
    errorId.value = connId;
    setTimeout(() => { errorId.value = null; }, 2000);
  } finally {
    connectingId.value = null;
  }
}

function handleEditConnection(config: ConnectionConfig) {
  editConfig.value = config;
  showForm.value = true;
}

function handleDeleteConnection(connId: ConnId) {
  deleteTargetId.value = connId;
  showDeleteConfirm.value = true;
}

async function confirmDelete() {
  if (deleteTargetId.value) {
    await connStore.deleteConnection(deleteTargetId.value);
  }
  showDeleteConfirm.value = false;
  deleteTargetId.value = null;
}

function cancelDelete() {
  showDeleteConfirm.value = false;
  deleteTargetId.value = null;
}

// ---- New connection ----

function handleNewConnection() {
  editConfig.value = null;
  showForm.value = true;
}

async function handleFormSaved(id: string) {
  showForm.value = false;
  editConfig.value = null;
  // Auto-connect after saving new connection
  await handleConnectSaved(id);
}
</script>

<template>
  <div class="welcome-page">
    <!-- Logo & Branding -->
    <div class="welcome-header">
      <div class="welcome-logo">
        <i class="ri-database-2-fill" />
      </div>
      <h1>Seven Redis Nav</h1>
      <p class="welcome-subtitle">macOS 原生 Redis 管理工具</p>
    </div>

    <!-- Main content area -->
    <div class="welcome-content" :class="{ 'has-saved': hasSavedConnections }">
      <!-- Left: Saved connections list -->
      <div v-if="hasSavedConnections" class="panel panel-left">
        <SavedConnectionList
          :connections="connStore.connections"
          :connecting-id="connectingId"
          :error-id="errorId"
          @connect="handleConnectSaved"
          @edit="handleEditConnection"
          @delete="handleDeleteConnection"
        />
      </div>

      <!-- Right: Quick connect + New connection -->
      <div class="panel panel-right">
        <!-- Empty state (shown in left panel area when no saved connections) -->
        <EmptyState
          v-if="!hasSavedConnections"
          @new-connection="handleNewConnection"
        />

        <QuickConnectForm
          ref="quickFormRef"
          @connect="handleQuickConnect"
          @test="handleQuickTest"
        />

        <!-- Divider + New connection button -->
        <div class="new-conn-section">
          <div class="divider">
            <span>或</span>
          </div>
          <button class="new-conn-btn" @click="handleNewConnection">
            <i class="ri-add-circle-line" />
            新建连接
          </button>
        </div>
      </div>
    </div>

    <!-- Tips -->
    <div class="welcome-tips">
      <p><i class="ri-information-line" /> 确保 Redis 服务已启动，默认端口 6379</p>
    </div>
  </div>

  <!-- Connection Form Dialog -->
  <ConnectionForm
    :visible="showForm"
    :edit-config="editConfig"
    @close="showForm = false"
    @saved="handleFormSaved"
  />

  <!-- Delete Confirmation Dialog -->
  <Transition name="modal">
    <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="cancelDelete">
      <div class="confirm-card">
        <div class="confirm-icon">
          <i class="ri-error-warning-line" />
        </div>
        <h3>确认删除</h3>
        <p>删除后将无法恢复，确定要删除此连接吗？</p>
        <div class="confirm-actions">
          <button class="btn-cancel" @click="cancelDelete">取消</button>
          <button class="btn-danger" @click="confirmDelete">删除</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.welcome-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 24px;
  background: var(--srn-color-surface-1);
  overflow-y: auto;
  gap: 20px;
}

/* Header */
.welcome-header { text-align: center; }
.welcome-logo {
  width: 56px; height: 56px; margin: 0 auto 12px;
  background: linear-gradient(135deg, var(--srn-color-primary), var(--srn-color-primary-light));
  border-radius: 14px; display: flex; align-items: center; justify-content: center;
  font-size: 28px; color: #fff; box-shadow: 0 4px 12px rgba(220, 56, 45, 0.25);
}
.welcome-header h1 { font-size: 20px; font-weight: 600; color: var(--srn-color-text-1); margin-bottom: 4px; }
.welcome-subtitle { font-size: 13px; color: var(--srn-color-text-3); }

/* Main content */
.welcome-content {
  width: 100%;
  max-width: 440px;
  background: var(--srn-color-surface-2);
  border-radius: var(--srn-radius-lg);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--srn-color-border);
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.welcome-content.has-saved {
  max-width: 720px;
  flex-direction: row;
  gap: 24px;
}

.panel { flex: 1; min-width: 0; }

.panel-left {
  border-right: 1px solid var(--srn-color-border);
  padding-right: 24px;
  max-height: 360px;
  overflow-y: auto;
}

.panel-right {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* New connection section */
.new-conn-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--srn-color-text-3);
  font-size: 11px;
}
.divider::before, .divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--srn-color-border);
}

.new-conn-btn {
  width: 100%;
  height: 36px;
  border: 1px dashed var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  background: transparent;
  color: var(--srn-color-text-2);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all var(--srn-motion-fast);
}
.new-conn-btn:hover {
  border-color: var(--srn-color-primary);
  color: var(--srn-color-primary);
  background: rgba(220, 56, 45, 0.04);
}

/* Tips */
.welcome-tips { text-align: center; }
.welcome-tips p {
  font-size: 11px;
  color: var(--srn-color-text-3);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

/* Delete confirmation modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.confirm-card {
  width: 320px;
  background: var(--srn-color-surface-2);
  border-radius: var(--srn-radius-lg);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  border: 1px solid var(--srn-color-border);
  padding: 24px;
  text-align: center;
}

.confirm-icon {
  font-size: 36px;
  color: var(--srn-color-warning);
  margin-bottom: 12px;
}

.confirm-card h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--srn-color-text-1);
  margin-bottom: 8px;
}

.confirm-card p {
  font-size: 13px;
  color: var(--srn-color-text-2);
  margin-bottom: 20px;
}

.confirm-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.btn-cancel, .btn-danger {
  height: 32px;
  padding: 0 16px;
  border-radius: var(--srn-radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--srn-motion-fast);
}

.btn-cancel {
  border: 1px solid var(--srn-color-border);
  background: transparent;
  color: var(--srn-color-text-2);
}
.btn-cancel:hover { background: rgba(0, 0, 0, 0.04); }

.btn-danger {
  border: none;
  background: var(--srn-color-error);
  color: #fff;
}
.btn-danger:hover { opacity: 0.9; }

.modal-enter-active, .modal-leave-active { transition: all 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
