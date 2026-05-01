<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useServerConfigStore as useStore } from '@/stores/serverConfig';
import { DANGEROUS_PARAMS } from '@/stores/serverConfig';
import { useConnectionStore } from '@/stores/connection';
import { configRewrite, configResetstat, configGetNotifyKeyspaceEvents, configSet } from '@/ipc/phase2';

const store = useStore();
const connStore = useConnectionStore();

type ConfigTab = 'config' | 'diff';

const activeTab = ref<ConfigTab>('config');
const editingKey = ref<string | null>(null);
const editValue = ref('');
const showConfirmDialog = ref(false);
const confirmKey = ref('');
const confirmOldValue = ref('');
const confirmNewValue = ref('');
const saving = ref(false);

// Dangerous param confirmation
const showDangerDialog = ref(false);
const dangerAcknowledge = ref(false);
const pendingDangerKey = ref('');
const pendingDangerOldValue = ref('');
const pendingDangerNewValue = ref('');

// Enhanced features
const notifyEvents = ref('');
const notifyLoading = ref(false);
const notifyEditValue = ref('');
const showNotifyDialog = ref(false);
const rewriteLoading = ref(false);
const resetstatLoading = ref(false);
const actionToast = ref<{ msg: string; type: 'success' | 'error' } | null>(null);
let actionToastTimer: ReturnType<typeof setTimeout>;

function showActionToast(msg: string, type: 'success' | 'error' = 'success') {
  clearTimeout(actionToastTimer);
  actionToast.value = { msg, type };
  actionToastTimer = setTimeout(() => { actionToast.value = null; }, 3000);
}

function isDangerous(key: string): boolean {
  return DANGEROUS_PARAMS.has(key);
}

async function loadNotifyKeyspaceEvents() {
  notifyLoading.value = true;
  try {
    notifyEvents.value = await configGetNotifyKeyspaceEvents(connStore.activeConnId ?? '');
    notifyEditValue.value = notifyEvents.value;
  } catch (e: any) {
    console.error('Failed to load notify-keyspace-events:', e);
    notifyEvents.value = '';
  } finally {
    notifyLoading.value = false;
  }
}

function openNotifyDialog() {
  notifyEditValue.value = notifyEvents.value;
  showNotifyDialog.value = true;
}

async function saveNotifyEvents() {
  try {
    await configSet(connStore.activeConnId ?? '', 'notify-keyspace-events', notifyEditValue.value);
    notifyEvents.value = notifyEditValue.value;
    showNotifyDialog.value = false;
    showActionToast('notify-keyspace-events 已更新');
  } catch (e: any) {
    showActionToast(`更新失败：${e?.message ?? '未知错误'}`, 'error');
  }
}

async function handleRewrite() {
  rewriteLoading.value = true;
  try {
    await configRewrite(connStore.activeConnId ?? '');
    showActionToast('CONFIG REWRITE 成功');
  } catch (e: any) {
    showActionToast(`REWRITE 失败：${e?.message ?? '未知错误'}`, 'error');
  } finally {
    rewriteLoading.value = false;
  }
}

async function handleResetstat() {
  resetstatLoading.value = true;
  try {
    await configResetstat(connStore.activeConnId ?? '');
    showActionToast('CONFIG RESETSTAT 成功，统计已重置');
    await store.fetchInfo();
  } catch (e: any) {
    showActionToast(`RESETSTAT 失败：${e?.message ?? '未知错误'}`, 'error');
  } finally {
    resetstatLoading.value = false;
  }
}

onMounted(() => {
  store.fetchConfigs();
  store.fetchInfo();
  loadNotifyKeyspaceEvents();
});

function startEdit(key: string, currentValue: string) {
  editingKey.value = key;
  editValue.value = currentValue;
}

function cancelEdit() {
  editingKey.value = null;
  editValue.value = '';
}

function requestSave(key: string, oldValue: string) {
  // Check for dangerous parameters
  if (isDangerous(key)) {
    pendingDangerKey.value = key;
    pendingDangerOldValue.value = oldValue;
    pendingDangerNewValue.value = editValue.value;
    dangerAcknowledge.value = false;
    showDangerDialog.value = true;
    return;
  }
  confirmKey.value = key;
  confirmOldValue.value = oldValue;
  confirmNewValue.value = editValue.value;
  showConfirmDialog.value = true;
}

async function confirmSave() {
  saving.value = true;
  const success = await store.updateConfig(confirmKey.value, confirmNewValue.value);
  saving.value = false;
  if (success) {
    editingKey.value = null;
    editValue.value = '';
  }
  showConfirmDialog.value = false;
}

async function confirmDangerSave() {
  if (!dangerAcknowledge.value) return;
  saving.value = true;
  const success = await store.updateConfig(pendingDangerKey.value, pendingDangerNewValue.value);
  saving.value = false;
  if (success) {
    editingKey.value = null;
    editValue.value = '';
    showActionToast(`危险参数 ${pendingDangerKey.value} 已修改`);
  }
  showDangerDialog.value = false;
}

function handleRevertDiff(key: string) {
  store.revertDiff(key);
}

function formatMemory(bytes: number): string {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i];
}

function formatUptime(secs: number): string {
  const days = Math.floor(secs / 86400);
  const hours = Math.floor((secs % 86400) / 3600);
  const mins = Math.floor((secs % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h ${mins}m`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}
</script>

<template>
  <div class="config-workspace">
    <!-- Info overview panel -->
    <div v-if="store.info" class="info-panel">
      <div class="info-card">
        <span class="info-label">Version</span>
        <span class="info-value">{{ store.info.redis_version }}</span>
      </div>
      <div class="info-card">
        <span class="info-label">Uptime</span>
        <span class="info-value">{{ formatUptime(store.info.uptime_secs) }}</span>
      </div>
      <div class="info-card">
        <span class="info-label">Clients</span>
        <span class="info-value">{{ store.info.connected_clients }}</span>
      </div>
      <div class="info-card">
        <span class="info-label">Memory</span>
        <span class="info-value">{{ formatMemory(store.info.used_memory) }} / {{ store.info.max_memory ? formatMemory(store.info.max_memory) : '∞' }}</span>
      </div>
      <div class="info-card">
        <span class="info-label">Hit Rate</span>
        <span class="info-value">{{ (store.info.hit_rate * 100).toFixed(1) }}%</span>
      </div>
      <div class="info-card">
        <span class="info-label">Keys</span>
        <span class="info-value">{{ store.info.total_keys.toLocaleString() }}</span>
      </div>
      <div class="info-card">
        <span class="info-label">Ops/sec</span>
        <span class="info-value">{{ store.info.ops_per_sec.toLocaleString() }}</span>
      </div>
      <button class="info-refresh" @click="store.fetchInfo" :disabled="store.infoLoading">
        <i class="ri-refresh-line" :class="{ spin: store.infoLoading }" />
      </button>
    </div>

    <!-- Config toolbar -->
    <div class="config-toolbar">
      <div class="toolbar-left">
        <button class="btn-action" :disabled="store.loading" @click="store.fetchConfigs">
          <i class="ri-refresh-line" :class="{ spin: store.loading }" /> Refresh
        </button>
        <select v-model="store.selectedGroup" class="group-select">
          <option value="">All Groups</option>
          <option v-for="g in store.groupNames" :key="g" :value="g">{{ g }}</option>
        </select>
      </div>
      <div class="toolbar-right">
        <span class="stat">{{ store.filteredConfigs.length }} / {{ store.configs.length }} params</span>
        <div class="search-box">
          <i class="ri-search-line" />
          <input v-model="store.searchKeyword" type="text" placeholder="Search config..." />
        </div>
        <button class="btn-action" :disabled="rewriteLoading" @click="handleRewrite" title="CONFIG REWRITE — 将当前配置写入磁盘">
          <i class="ri-save-line" :class="{ spin: rewriteLoading }" /> Rewrite
        </button>
        <button class="btn-action" :disabled="resetstatLoading" @click="handleResetstat" title="CONFIG RESETSTAT — 重置统计信息">
          <i class="ri-refresh-line" :class="{ spin: resetstatLoading }" /> ResetStat
        </button>
        <button class="btn-action notify-btn" @click="openNotifyDialog" title="配置 Keyspace Notifications">
          <i class="ri-notification-3-line" /> Notify <code v-if="notifyEvents">{{ notifyEvents }}</code>
        </button>
      </div>
    </div>

    <!-- Tab bar: Config / Diff -->
    <div class="config-tab-bar">
      <button
        class="config-tab"
        :class="{ active: activeTab === 'config' }"
        @click="activeTab = 'config'"
      >
        <i class="ri-settings-3-line" /> 配置参数
      </button>
      <button
        class="config-tab"
        :class="{ active: activeTab === 'diff' }"
        @click="activeTab = 'diff'"
      >
        <i class="ri-file-list-3-line" /> 差异
        <span v-if="store.diffCount > 0" class="diff-badge">{{ store.diffCount }}</span>
      </button>
    </div>

    <!-- Config list -->
    <div v-if="activeTab === 'config'" class="config-list">
      <div v-if="store.filteredConfigs.length === 0" class="empty-state">
        <i class="ri-settings-3-line" />
        <p>No configuration parameters found</p>
      </div>
      <div
        v-for="item in store.filteredConfigs"
        :key="item.key"
        class="config-row"
        :class="{ 'danger-row': isDangerous(item.key), 'diff-row': store.diffs.some(d => d.key === item.key) }"
      >
        <div class="config-key">
          <i v-if="store.isReadOnly(item.key)" class="ri-lock-line readonly-icon" title="Read-only" />
          <i v-if="isDangerous(item.key)" class="ri-shield-keyhole-line danger-icon" title="危险参数" />
          {{ item.key }}
        </div>
        <div class="config-value">
          <template v-if="editingKey === item.key">
            <input
              v-model="editValue"
              type="text"
              class="edit-input"
              @keydown.enter="requestSave(item.key, item.value)"
              @keydown.escape="cancelEdit"
            />
            <button class="btn-sm save" @click="requestSave(item.key, item.value)">
              <i class="ri-check-line" />
            </button>
            <button class="btn-sm cancel" @click="cancelEdit">
              <i class="ri-close-line" />
            </button>
          </template>
          <template v-else>
            <span class="value-text">{{ item.value || '(empty)' }}</span>
            <button
              v-if="!store.isReadOnly(item.key)"
              class="btn-edit"
              @click="startEdit(item.key, item.value)"
            >
              <i class="ri-pencil-line" />
            </button>
          </template>
        </div>
      </div>
    </div>

    <!-- Diff panel -->
    <div v-if="activeTab === 'diff'" class="config-list">
      <div v-if="store.diffs.length === 0" class="empty-state">
        <i class="ri-file-list-3-line" />
        <p>暂无配置变更</p>
        <p class="hint">修改配置参数后，变更将在此处显示</p>
      </div>
      <div v-for="diff in store.diffs" :key="diff.key" class="config-row diff-row">
        <div class="config-key">
          <i v-if="isDangerous(diff.key)" class="ri-shield-keyhole-line danger-icon" title="危险参数" />
          {{ diff.key }}
        </div>
        <div class="config-value diff-values">
          <code class="old-value">{{ diff.oldValue || '(empty)' }}</code>
          <i class="ri-arrow-right-line diff-arrow" />
          <code class="new-value">{{ diff.newValue }}</code>
        </div>
        <div class="diff-actions">
          <button class="btn-sm revert" title="撤销" @click="handleRevertDiff(diff.key)">
            <i class="ri-arrow-go-back-line" /> 撤销
          </button>
        </div>
      </div>
    </div>

    <!-- Confirm dialog -->
    <Transition name="modal">
      <div v-if="showConfirmDialog" class="modal-overlay" @click.self="showConfirmDialog = false">
        <div class="modal-card">
          <div class="modal-header">
            <h3><i class="ri-settings-3-line" /> Confirm Config Change</h3>
          </div>
          <div class="modal-body">
            <div class="confirm-detail">
              <span class="confirm-label">Parameter:</span>
              <code>{{ confirmKey }}</code>
            </div>
            <div class="confirm-detail">
              <span class="confirm-label">Current:</span>
              <code class="old-value">{{ confirmOldValue || '(empty)' }}</code>
            </div>
            <div class="confirm-detail">
              <span class="confirm-label">New:</span>
              <code class="new-value">{{ confirmNewValue }}</code>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showConfirmDialog = false">Cancel</button>
            <button class="btn-confirm" :disabled="saving" @click="confirmSave">
              <i v-if="saving" class="ri-loader-4-line spin" />
              Apply
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Dangerous param confirmation dialog -->
    <Transition name="modal">
      <div v-if="showDangerDialog" class="modal-overlay" @click.self="showDangerDialog = false">
        <div class="modal-card danger-modal">
          <div class="modal-header danger-header">
            <h3><i class="ri-shield-keyhole-line" /> 危险参数修改确认</h3>
          </div>
          <div class="modal-body">
            <div class="danger-warning">
              <i class="ri-error-warning-fill" />
              <p>您正在修改危险参数 <code>{{ pendingDangerKey }}</code>，此操作可能导致 Redis 服务不可用或安全风险。</p>
            </div>
            <div class="confirm-detail">
              <span class="confirm-label">当前值：</span>
              <code class="old-value">{{ pendingDangerOldValue || '(empty)' }}</code>
            </div>
            <div class="confirm-detail">
              <span class="confirm-label">新值：</span>
              <code class="new-value">{{ pendingDangerNewValue }}</code>
            </div>
            <label class="danger-ack">
              <input v-model="dangerAcknowledge" type="checkbox" />
              <span>我了解此操作的风险，确认修改</span>
            </label>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showDangerDialog = false">取消</button>
            <button class="btn-danger" :disabled="!dangerAcknowledge || saving" @click="confirmDangerSave">
              <i v-if="saving" class="ri-loader-4-line spin" />
              确认修改
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Keyspace Notify dialog -->
    <Transition name="modal">
      <div v-if="showNotifyDialog" class="modal-overlay" @click.self="showNotifyDialog = false">
        <div class="modal-card">
          <div class="modal-header">
            <h3><i class="ri-notification-3-line" /> Keyspace Notifications</h3>
          </div>
          <div class="modal-body">
            <p class="notify-hint">配置 <code>notify-keyspace-events</code>，控制 Redis 向 Pub/Sub 客户端发送哪些事件通知。</p>
            <div class="notify-flags">
              <label v-for="flag in [
                { val: 'K', desc: 'Keyspace 通知' },
                { val: 'E', desc: 'Keyevent 通知' },
                { val: 'g', desc: '通用命令 (DEL, EXPIRE...)' },
                { val: '$', desc: 'String 命令' },
                { val: 'l', desc: 'List 命令' },
                { val: 's', desc: 'Set 命令' },
                { val: 'h', desc: 'Hash 命令' },
                { val: 'z', desc: 'ZSet 命令' },
                { val: 'x', desc: '过期事件' },
                { val: 'e', desc: '驱逐事件' },
                { val: 'A', desc: '全部 (g$lshzxe)' },
              ]" :key="flag.val" class="notify-flag">
                <input
                  type="checkbox"
                  :checked="notifyEditValue.includes(flag.val)"
                  @change="(e: Event) => {
                    const checked = (e.target as HTMLInputElement).checked;
                    if (checked) {
                      notifyEditValue += flag.val;
                    } else {
                      notifyEditValue = notifyEditValue.replace(flag.val, '');
                    }
                  }"
                />
                <code>{{ flag.val }}</code> {{ flag.desc }}
              </label>
            </div>
            <div class="notify-preview">
              <span class="confirm-label">当前值：</span>
              <code>{{ notifyEditValue || '(空)' }}</code>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showNotifyDialog = false">取消</button>
            <button class="btn-confirm" @click="saveNotifyEvents">保存</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Action toast -->
    <Transition name="toast">
      <div v-if="actionToast" class="action-toast" :class="actionToast.type">
        <i :class="actionToast.type === 'success' ? 'ri-checkbox-circle-fill' : 'ri-close-circle-fill'" />
        {{ actionToast.msg }}
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.config-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--srn-color-surface-1);
}

/* Info panel */
.info-panel {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
  flex-wrap: wrap;
}

.info-card {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.info-label { font-size: 10px; color: var(--srn-color-text-3); text-transform: uppercase; letter-spacing: 0.5px; }
.info-value { font-size: 13px; font-weight: 600; color: var(--srn-color-text-1); font-family: var(--srn-font-mono); }

.info-refresh {
  margin-left: auto;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--srn-color-text-3);
  cursor: pointer;
  border-radius: var(--srn-radius-sm);
}
.info-refresh:hover { background: var(--srn-color-surface-1); }

/* Toolbar */
.config-toolbar {
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
.btn-action:disabled { opacity: 0.5; }

.group-select {
  height: 30px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 0 8px;
  font-size: 12px;
  background: var(--srn-color-surface-2);
  color: var(--srn-color-text-1);
  outline: none;
}

.stat { font-size: 11px; color: var(--srn-color-text-3); }

.search-box {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--srn-color-text-3);
}
.search-box input {
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

/* Config list */
.config-list {
  flex: 1;
  overflow-y: auto;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  color: var(--srn-color-text-3);
  gap: 8px;
}
.empty-state i { font-size: 36px; }

.config-row {
  display: flex;
  align-items: center;
  padding: 6px 16px;
  border-bottom: 1px solid var(--srn-color-border);
  gap: 16px;
}
.config-row:hover { background: var(--srn-color-surface-2); }

.config-key {
  width: 280px;
  flex-shrink: 0;
  font-family: var(--srn-font-mono);
  font-size: 12px;
  color: var(--srn-color-info);
  display: flex;
  align-items: center;
  gap: 6px;
}

.readonly-icon { color: var(--srn-color-text-3); font-size: 11px; }

.config-value {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.value-text {
  font-family: var(--srn-font-mono);
  font-size: 12px;
  color: var(--srn-color-text-1);
  word-break: break-all;
}

.edit-input {
  flex: 1;
  height: 26px;
  border: 1px solid var(--srn-color-info);
  border-radius: var(--srn-radius-sm);
  padding: 0 8px;
  font-size: 12px;
  font-family: var(--srn-font-mono);
  background: var(--srn-color-surface-2);
  color: var(--srn-color-text-1);
  outline: none;
}

.btn-edit {
  width: 22px;
  height: 22px;
  border: none;
  background: transparent;
  color: var(--srn-color-text-3);
  cursor: pointer;
  border-radius: var(--srn-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  opacity: 0;
}
.config-row:hover .btn-edit { opacity: 1; }
.btn-edit:hover { background: var(--srn-color-surface-2); color: var(--srn-color-info); }

.btn-sm {
  width: 22px;
  height: 22px;
  border: none;
  border-radius: var(--srn-radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
}
.btn-sm.save { background: #22c55e; color: #fff; }
.btn-sm.cancel { background: transparent; color: var(--srn-color-text-3); }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-card {
  width: 420px;
  background: var(--srn-color-surface-2);
  border-radius: var(--srn-radius-lg);
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  border: 1px solid var(--srn-color-border);
  overflow: hidden;
}
.modal-header { padding: 14px 20px; border-bottom: 1px solid var(--srn-color-border); }
.modal-header h3 { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; color: var(--srn-color-text-1); }
.modal-body { padding: 16px 20px; display: flex; flex-direction: column; gap: 10px; }
.confirm-detail { display: flex; gap: 8px; font-size: 13px; align-items: baseline; }
.confirm-label { color: var(--srn-color-text-3); min-width: 70px; }
.confirm-detail code { font-family: var(--srn-font-mono); font-size: 12px; color: var(--srn-color-text-1); word-break: break-all; }
.old-value { color: var(--srn-color-text-3); text-decoration: line-through; }
.new-value { color: #22c55e; }
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-1);
}
.btn-cancel, .btn-confirm {
  height: 30px;
  padding: 0 14px;
  border-radius: var(--srn-radius-sm);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}
.btn-cancel { border: 1px solid var(--srn-color-border); background: transparent; color: var(--srn-color-text-2); }
.btn-confirm { border: none; background: var(--srn-color-info); color: #fff; }
.btn-confirm:disabled { opacity: 0.5; }

.modal-enter-active, .modal-leave-active { transition: all 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }

.notify-btn code {
  font-family: var(--srn-font-mono);
  font-size: 10px;
  background: rgba(59,130,246,0.12);
  padding: 1px 5px;
  border-radius: 3px;
  color: var(--srn-color-info);
}

.notify-hint {
  font-size: 13px;
  color: var(--srn-color-text-2);
  line-height: 1.5;
  margin: 0 0 12px;
}
.notify-hint code {
  font-family: var(--srn-font-mono);
  font-size: 12px;
  background: rgba(0,0,0,0.06);
  padding: 1px 5px;
  border-radius: 3px;
}
.notify-flags {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-bottom: 12px;
}
.notify-flag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--srn-color-text-2);
  cursor: pointer;
}
.notify-flag input { margin: 0; }
.notify-flag code {
  font-family: var(--srn-font-mono);
  font-weight: 600;
  color: var(--srn-color-info);
}
.notify-preview {
  display: flex;
  gap: 8px;
  align-items: baseline;
  padding: 8px 12px;
  background: var(--srn-color-surface-1);
  border-radius: var(--srn-radius-sm);
  border: 1px solid var(--srn-color-border);
}
.notify-preview code {
  font-family: var(--srn-font-mono);
  font-size: 13px;
  color: var(--srn-color-text-1);
}

/* Tab bar */
.config-tab-bar {
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
}
.config-tab {
  padding: 8px 16px;
  border: none;
  background: transparent;
  font-size: 12px;
  color: var(--srn-color-text-3);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all var(--srn-motion-fast);
}
.config-tab:hover { color: var(--srn-color-text-1); }
.config-tab.active { color: var(--srn-color-primary); border-bottom-color: var(--srn-color-primary); }

.diff-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 10px;
  background: var(--srn-color-primary);
  color: #fff;
  min-width: 16px;
  text-align: center;
}

/* Danger row */
.config-row.danger-row { border-left: 3px solid var(--srn-color-primary); }
.danger-icon { color: var(--srn-color-primary) !important; font-size: 12px; }

/* Diff row */
.config-row.diff-row { background: rgba(59, 130, 246, 0.04); }

.diff-values {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}
.diff-arrow { color: var(--srn-color-text-3); font-size: 12px; flex-shrink: 0; }
.diff-actions { flex-shrink: 0; }
.btn-sm.revert {
  display: flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--srn-color-border);
  background: transparent;
  color: var(--srn-color-text-2);
  cursor: pointer;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--srn-radius-xs);
  transition: all var(--srn-motion-fast);
}
.btn-sm.revert:hover { background: rgba(0,0,0,0.05); }

.empty-state .hint { font-size: 12px; color: var(--srn-color-text-3); }

/* Danger modal */
.danger-modal { border: 2px solid var(--srn-color-primary); }
.danger-header { background: rgba(220, 38, 38, 0.06); }
.danger-header h3 { color: var(--srn-color-primary); }

.danger-warning {
  display: flex;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(220, 38, 38, 0.06);
  border: 1px solid rgba(220, 38, 38, 0.15);
  border-radius: var(--srn-radius-sm);
  font-size: 13px;
  color: var(--srn-color-text-1);
  line-height: 1.5;
}
.danger-warning i { color: var(--srn-color-primary); font-size: 18px; flex-shrink: 0; margin-top: 2px; }
.danger-warning p { margin: 0; }

.danger-ack {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--srn-color-text-1);
  cursor: pointer;
  margin-top: 4px;
}
.danger-ack input { margin: 0; }

.btn-danger {
  height: 30px;
  padding: 0 14px;
  border-radius: var(--srn-radius-sm);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: var(--srn-color-primary);
  color: #fff;
}
.btn-danger:disabled { opacity: 0.5; }

.action-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 10px 18px;
  border-radius: var(--srn-radius-md);
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 2000;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}
.action-toast.success { background: #166534; color: #fff; }
.action-toast.error { background: #991b1b; color: #fff; }

.toast-enter-active, .toast-leave-active { transition: all 0.3s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(10px); }

@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }
</style>
