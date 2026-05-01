<script setup lang="ts">
import { ref, watch } from 'vue';
import { useStreamBrowserStore } from '@/stores/streamBrowser';
import { useDataStore } from '@/stores/data';
import { useConnectionStore } from '@/stores/connection';

type StreamTab = 'entries' | 'groups';

const streamStore = useStreamBrowserStore();
const dataStore = useDataStore();
const connStore = useConnectionStore();

const activeTab = ref<StreamTab>('entries');
const expandedGroup = ref<string | null>(null);

// Add entry form
const showAddForm = ref(false);
const addIdMode = ref<'auto' | 'manual'>('auto');
const addManualId = ref('');
const addFields = ref<[string, string][]>([['', '']]);
const addMaxlen = ref<number | null>(null);

// Delete dialog
const showDeleteDialog = ref(false);
const deleteIds = ref<string[]>([]);

// Toast
const toast = ref<{ msg: string; type: 'success' | 'error' } | null>(null);
let toastTimer: ReturnType<typeof setTimeout>;
function showToast(msg: string, type: 'success' | 'error' = 'success') {
  clearTimeout(toastTimer);
  toast.value = { msg, type };
  toastTimer = setTimeout(() => { toast.value = null; }, 3000);
}

function getConnId(): string {
  return connStore.activeConnId ?? '';
}

function getKey(): string {
  return dataStore.currentKey?.key ?? '';
}

async function refresh() {
  const connId = getConnId();
  const key = getKey();
  if (!connId || !key) return;
  await Promise.all([
    streamStore.loadEntries(connId, key),
    streamStore.loadGroups(connId, key),
    streamStore.loadInfo(connId, key),
  ]);
}

async function toggleReverse() {
  streamStore.reverse = !streamStore.reverse;
  await streamStore.loadEntries(getConnId(), getKey());
}

async function toggleGroupExpand(groupName: string) {
  if (expandedGroup.value === groupName) {
    expandedGroup.value = null;
  } else {
    expandedGroup.value = groupName;
    await streamStore.loadPending(getConnId(), getKey(), groupName);
  }
}

function addFieldRow() {
  addFields.value.push(['', '']);
}

function removeFieldRow(index: number) {
  addFields.value.splice(index, 1);
}

async function handleAddEntry() {
  const filtered = addFields.value.filter(([k, v]) => k.trim() && v.trim());
  if (filtered.length === 0) return;
  try {
    const id = addIdMode.value === 'manual' ? addManualId.value : undefined;
    await streamStore.addEntry(
      getConnId(),
      getKey(),
      filtered,
      id,
      addMaxlen.value ?? undefined,
    );
    showAddForm.value = false;
    addFields.value = [['', '']];
    addManualId.value = '';
    addMaxlen.value = null;
    showToast('条目已添加');
  } catch (e: any) {
    showToast(`添加失败：${e?.message ?? '未知错误'}`, 'error');
  }
}

function confirmDelete(ids: string[]) {
  deleteIds.value = ids;
  showDeleteDialog.value = true;
}

async function handleDelete() {
  try {
    await streamStore.deleteEntries(getConnId(), getKey(), deleteIds.value);
    showDeleteDialog.value = false;
    deleteIds.value = [];
    showToast('条目已删除');
  } catch (e: any) {
    showToast(`删除失败：${e?.message ?? '未知错误'}`, 'error');
  }
}

function formatTimestamp(ms: number) {
  return new Date(ms).toLocaleString('zh-CN');
}

watch(() => dataStore.currentKey, (newKey) => {
  if (newKey && newKey.key_type === 'stream') {
    streamStore.streamLength = newKey.length;
    streamStore.reset();
    refresh();
  }
}, { immediate: true });
</script>

<template>
  <div class="stream-viewer">
    <!-- Meta bar -->
    <div class="sv-meta">
      <span><i class="ri-database-line" /> Stream</span>
      <span class="sep">·</span>
      <span><i class="ri-list-check" /> XLEN: {{ streamStore.streamLength }}</span>
      <span class="sep">·</span>
      <span><i class="ri-node-tree" /> Radix: {{ streamStore.radixNodes }}</span>
      <span class="sep">·</span>
      <span><i class="ri-price-tag-3-line" /> Last ID: {{ streamStore.lastId || '—' }}</span>
      <span v-if="streamStore.maxLength > 0" class="sep">·</span>
      <span v-if="streamStore.maxLength > 0"><i class="ri-database-2-line" /> MaxLen: {{ streamStore.maxLength }}</span>
      <span class="sep">·</span>
      <span><i class="ri-group-line" /> Groups: {{ streamStore.groupsCount }}</span>
    </div>

    <!-- Tabs -->
    <div class="sv-tabs">
      <button
        class="sv-tab"
        :class="{ active: activeTab === 'entries' }"
        @click="activeTab = 'entries'"
      >条目</button>
      <button
        class="sv-tab"
        :class="{ active: activeTab === 'groups' }"
        @click="activeTab = 'groups'"
      >Consumer Groups</button>
      <div class="sv-tab-actions">
        <button class="sv-action-btn" title="倒序" :class="{ active: streamStore.reverse }" @click="toggleReverse">
          <i class="ri-sort-desc" />
        </button>
        <button class="sv-action-btn" title="刷新" @click="refresh">
          <i class="ri-refresh-line" />
        </button>
        <button class="sv-action-btn primary" title="添加条目" @click="showAddForm = true">
          <i class="ri-add-line" />
        </button>
      </div>
    </div>

    <!-- Entries tab -->
    <div v-if="activeTab === 'entries'" class="sv-content">
      <div v-if="streamStore.loading" class="sv-loading">加载中...</div>
      <div v-else-if="streamStore.error" class="sv-error">{{ streamStore.error }}</div>
      <div v-else-if="streamStore.entries.length === 0" class="sv-empty">暂无条目</div>
      <table v-else class="sv-table">
        <thead>
          <tr>
            <th style="width: 200px;">ID</th>
            <th>字段 / 值</th>
            <th style="width: 160px;">时间戳</th>
            <th style="width: 40px;"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in streamStore.entries" :key="entry.id">
            <td class="sv-id-cell">{{ entry.id }}</td>
            <td class="sv-fields-cell">
              <div v-for="(fv, idx) in entry.fields" :key="idx" class="sv-field-row">
                <span class="sv-field-key">{{ fv.field }}</span>
                <span class="sv-field-sep">→</span>
                <span class="sv-field-val">{{ fv.value }}</span>
              </div>
            </td>
            <td class="sv-ts-cell">{{ formatTimestamp(entry.timestamp_ms) }}</td>
            <td>
              <button class="sv-del-btn" title="删除" @click="confirmDelete([entry.id])">
                <i class="ri-delete-bin-line" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Groups tab -->
    <div v-if="activeTab === 'groups'" class="sv-content">
      <div v-if="streamStore.groupsLoading" class="sv-loading">加载中...</div>
      <div v-else-if="streamStore.groups.length === 0" class="sv-empty">暂无 Consumer Group</div>
      <table v-else class="sv-table">
        <thead>
          <tr>
            <th>Group Name</th>
            <th style="width: 90px;">Consumers</th>
            <th style="width: 80px;">Pending</th>
            <th>Last Delivered ID</th>
            <th style="width: 40px;"></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="group in streamStore.groups" :key="group.name">
            <tr
              class="sv-group-row"
              :class="{ expanded: expandedGroup === group.name }"
              @click="toggleGroupExpand(group.name)"
            >
              <td class="sv-group-name">
                <i :class="expandedGroup === group.name ? 'ri-arrow-down-s-line' : 'ri-arrow-right-s-line'" />
                {{ group.name }}
              </td>
              <td>{{ group.consumers }}</td>
              <td>{{ group.pending }}</td>
              <td class="sv-id-cell">{{ group.last_delivered_id }}</td>
              <td></td>
            </tr>
            <!-- Pending entries -->
            <tr v-if="expandedGroup === group.name" class="sv-pending-row">
              <td colspan="5">
                <div v-if="streamStore.pendingLoading[group.name]" class="sv-loading-sm">加载 Pending...</div>
                <div v-else-if="(streamStore.pendingMap[group.name] ?? []).length === 0" class="sv-empty-sm">无 Pending 条目</div>
                <table v-else class="sv-pending-table">
                  <thead>
                    <tr>
                      <th>Consumer</th>
                      <th>Pending Count</th>
                      <th>Idle (ms)</th>
                      <th>Last Delivered ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="pe in streamStore.pendingMap[group.name]" :key="pe.consumer_name">
                      <td>{{ pe.consumer_name }}</td>
                      <td>{{ pe.pending_count }}</td>
                      <td>{{ pe.idle_ms }}</td>
                      <td class="sv-id-cell">{{ pe.last_delivered_id }}</td>
                    </tr>
                  </tbody>
                </table>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Add entry form -->
    <Transition name="modal">
      <div v-if="showAddForm" class="modal-overlay" @click.self="showAddForm = false">
        <div class="modal-card">
          <div class="modal-header">
            <h3><i class="ri-add-line" /> 添加 Stream 条目</h3>
          </div>
          <div class="modal-body">
            <div class="add-id-row">
              <label>ID 模式</label>
              <select v-model="addIdMode" class="add-select">
                <option value="auto">自动 (*)</option>
                <option value="manual">手动指定</option>
              </select>
              <input
                v-if="addIdMode === 'manual'"
                v-model="addManualId"
                type="text"
                class="confirm-input"
                placeholder="如：1680000000000-0"
              />
            </div>
            <div class="add-fields">
              <label>字段-值对</label>
              <div v-for="([_k, _v], idx) in addFields" :key="idx" class="add-field-row">
                <input v-model="addFields[idx][0]" type="text" class="confirm-input field-key" placeholder="字段名" />
                <input v-model="addFields[idx][1]" type="text" class="confirm-input field-val" placeholder="值" />
                <button v-if="addFields.length > 1" class="add-rm-btn" @click="removeFieldRow(idx)">
                  <i class="ri-close-line" />
                </button>
              </div>
              <button class="add-more-btn" @click="addFieldRow">
                <i class="ri-add-line" /> 添加字段
              </button>
            </div>
            <div class="add-maxlen-row">
              <label>MAXLEN（可选）</label>
              <input v-model.number="addMaxlen" type="number" class="confirm-input" style="width: 120px;" placeholder="留空不限" />
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showAddForm = false">取消</button>
            <button class="btn-save" @click="handleAddEntry">XADD</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Delete dialog -->
    <Transition name="modal">
      <div v-if="showDeleteDialog" class="modal-overlay" @click.self="showDeleteDialog = false">
        <div class="modal-card">
          <div class="modal-header">
            <h3><i class="ri-delete-bin-line" style="color: var(--srn-color-primary);" /> 删除条目</h3>
          </div>
          <div class="modal-body">
            <p>确认删除以下 {{ deleteIds.length }} 个条目？</p>
            <div v-for="id in deleteIds" :key="id" class="key-confirm-name">{{ id }}</div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showDeleteDialog = false">取消</button>
            <button class="btn-danger" @click="handleDelete">确认删除</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toast" class="bw-toast" :class="toast.type">
        <i :class="toast.type === 'success' ? 'ri-checkbox-circle-fill' : 'ri-close-circle-fill'" />
        {{ toast.msg }}
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.stream-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.sv-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  font-size: 11px;
  color: var(--srn-color-text-3);
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-1);
}
.sep { color: #ddd; }

.sv-tabs {
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
}
.sv-tab {
  padding: 8px 16px;
  border: none;
  background: transparent;
  font-size: 12px;
  color: var(--srn-color-text-3);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all var(--srn-motion-fast);
}
.sv-tab:hover { color: var(--srn-color-text-1); }
.sv-tab.active { color: var(--srn-color-primary); border-bottom-color: var(--srn-color-primary); }
.sv-tab-actions { margin-left: auto; display: flex; gap: 4px; padding-right: 8px; }
.sv-action-btn {
  border: 1px solid var(--srn-color-border);
  background: transparent;
  color: var(--srn-color-text-2);
  cursor: pointer;
  font-size: 14px;
  padding: 4px 7px;
  border-radius: var(--srn-radius-xs);
  transition: all var(--srn-motion-fast);
}
.sv-action-btn:hover { background: rgba(0,0,0,0.05); }
.sv-action-btn.active { background: var(--srn-color-primary); color: #fff; border-color: var(--srn-color-primary); }
.sv-action-btn.primary { background: var(--srn-color-primary); color: #fff; border-color: var(--srn-color-primary); }

.sv-content { flex: 1; overflow: auto; }

.sv-loading, .sv-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--srn-color-text-3);
  font-size: 13px;
}
.sv-error { padding: 20px; color: var(--srn-color-primary); font-size: 13px; }

.sv-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.sv-table th {
  padding: 6px 12px;
  text-align: left;
  font-size: 10px;
  font-weight: 600;
  color: var(--srn-color-text-3);
  text-transform: uppercase;
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
  position: sticky;
  top: 0;
  z-index: 1;
}
.sv-table td { padding: 7px 12px; border-bottom: 1px solid rgba(0,0,0,0.04); }
.sv-table tr:hover td { background: rgba(0,0,0,0.02); }

.sv-id-cell { font-family: var(--srn-font-mono); color: var(--srn-color-info); font-weight: 500; font-size: 11px; }
.sv-ts-cell { font-size: 11px; color: var(--srn-color-text-3); }

.sv-fields-cell { max-width: 400px; }
.sv-field-row { display: flex; align-items: center; gap: 4px; margin-bottom: 2px; }
.sv-field-key {
  font-family: var(--srn-font-mono);
  font-weight: 500;
  color: var(--srn-color-text-1);
  font-size: 12px;
}
.sv-field-sep { color: var(--srn-color-text-3); font-size: 10px; }
.sv-field-val {
  font-family: var(--srn-font-mono);
  color: var(--srn-color-text-2);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sv-del-btn {
  border: none;
  background: transparent;
  color: var(--srn-color-text-3);
  cursor: pointer;
  font-size: 12px;
  padding: 2px 4px;
  border-radius: var(--srn-radius-xs);
  opacity: 0;
  transition: all var(--srn-motion-fast);
}
.sv-table tr:hover .sv-del-btn { opacity: 1; }
.sv-del-btn:hover { color: var(--srn-color-primary); }

.sv-group-row { cursor: pointer; }
.sv-group-name { display: flex; align-items: center; gap: 4px; font-weight: 500; }
.sv-group-row.expanded td { background: rgba(0,0,0,0.03); }
.sv-pending-row td { padding: 0 !important; }

.sv-pending-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
  background: var(--srn-color-surface-1);
}
.sv-pending-table th {
  padding: 4px 12px;
  font-size: 10px;
  font-weight: 600;
  color: var(--srn-color-text-3);
  border-bottom: 1px solid var(--srn-color-border);
}
.sv-pending-table td { padding: 4px 12px; border-bottom: 1px solid rgba(0,0,0,0.03); }

.sv-loading-sm, .sv-empty-sm {
  padding: 12px;
  text-align: center;
  font-size: 12px;
  color: var(--srn-color-text-3);
}

/* Add entry form */
.add-id-row { display: flex; align-items: center; gap: 8px; }
.add-select {
  height: 32px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 0 8px;
  font-size: 13px;
  background: var(--srn-color-surface-1);
  outline: none;
}
.add-fields { display: flex; flex-direction: column; gap: 6px; }
.add-field-row { display: flex; gap: 6px; align-items: center; }
.field-key { width: 140px; }
.field-val { flex: 1; }
.add-rm-btn {
  border: none;
  background: transparent;
  color: var(--srn-color-text-3);
  cursor: pointer;
  font-size: 14px;
  padding: 2px;
}
.add-rm-btn:hover { color: var(--srn-color-primary); }
.add-more-btn {
  border: 1px dashed var(--srn-color-border);
  background: transparent;
  color: var(--srn-color-text-3);
  cursor: pointer;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: var(--srn-radius-xs);
  display: flex;
  align-items: center;
  gap: 4px;
  width: fit-content;
}
.add-more-btn:hover { border-color: var(--srn-color-info); color: var(--srn-color-info); }
.add-maxlen-row { display: flex; align-items: center; gap: 8px; }

/* Reuse modal styles from BrowserWorkspace */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-card {
  width: 480px;
  max-height: 80vh;
  background: var(--srn-color-surface-2);
  border-radius: var(--srn-radius-lg);
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  border: 1px solid var(--srn-color-border);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.modal-header { padding: 14px 20px; border-bottom: 1px solid var(--srn-color-border); }
.modal-header h3 { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.modal-body {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  font-size: 13px;
  color: var(--srn-color-text-2);
  overflow-y: auto;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-1);
}
.confirm-input {
  height: 32px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 0 10px;
  font-size: 13px;
  font-family: var(--srn-font-mono);
  background: var(--srn-color-surface-1);
  outline: none;
  box-sizing: border-box;
}
.confirm-input:focus { border-color: var(--srn-color-info); }
.key-confirm-name {
  padding: 4px 10px;
  background: var(--srn-color-surface-1);
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-xs);
  font-family: var(--srn-font-mono);
  font-size: 11px;
  color: var(--srn-color-text-1);
}
.btn-cancel, .btn-save, .btn-danger {
  height: 30px;
  padding: 0 14px;
  border-radius: var(--srn-radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--srn-motion-fast);
}
.btn-cancel { border: 1px solid var(--srn-color-border); background: transparent; color: var(--srn-color-text-2); }
.btn-cancel:hover { background: rgba(0,0,0,0.04); }
.btn-save { border: none; background: var(--srn-color-primary); color: #fff; }
.btn-danger { border: none; background: var(--srn-color-primary); color: #fff; }

.bw-toast {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 16px;
  border-radius: var(--srn-radius-sm);
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.bw-toast.success { background: #166534; color: #fff; }
.bw-toast.error { background: var(--srn-color-primary); color: #fff; }

.toast-enter-active, .toast-leave-active { transition: all 0.3s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(10px); }

.modal-enter-active, .modal-leave-active { transition: all 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
