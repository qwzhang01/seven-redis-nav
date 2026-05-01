<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useDataStore } from '@/stores/data';
import StringViewer from './StringViewer.vue';
import HashViewer from './HashViewer.vue';
import ListViewer from './ListViewer.vue';
import SetViewer from './SetViewer.vue';
import ZSetViewer from './ZSetViewer.vue';
import StreamViewer from './StreamViewer.vue';
import BitmapViewer from './BitmapViewer.vue';
import HyperLogLogViewer from './HyperLogLogViewer.vue';

const dataStore = useDataStore();

type SubTab = 'data' | 'raw' | 'commands';
const activeSubTab = ref<SubTab>('data');

// Manual viewer type override (for string keys that could be Bitmap/HyperLogLog)
const manualViewerType = ref<string | null>(null);

// Effective viewer type: combines Redis key_type with detection logic and manual override
const effectiveViewerType = computed(() => {
  const key = dataStore.currentKey;
  if (!key) return null;

  // If user manually selected a viewer type, use that
  if (manualViewerType.value) return manualViewerType.value;

  const kt = key.key_type;

  // Stream is a native Redis type — always use StreamViewer
  if (kt === 'stream') return 'stream';

  // For string type, try to detect Bitmap or HyperLogLog
  if (kt === 'string') {
    // Bitmap detection: key name convention (bitmap:* or bs:*) or large byte size
    const keyName = key.key.toLowerCase();
    if (keyName.startsWith('bitmap:') || keyName.startsWith('bs:')) {
      return 'bitmap';
    }
    // HyperLogLog detection: key name convention (hll:* or hyperloglog:*)
    if (keyName.startsWith('hll:') || keyName.startsWith('hyperloglog:')) {
      return 'hyperloglog';
    }
    // Default: string
    return 'string';
  }

  return kt;
});

// Whether to show the manual type switcher (only for string keys)
const showTypeSwitcher = computed(() => {
  return dataStore.currentKey?.key_type === 'string';
});

// Available viewer options for string keys
const stringViewerOptions = [
  { value: 'string', label: 'String' },
  { value: 'bitmap', label: 'Bitmap' },
  { value: 'hyperloglog', label: 'HyperLogLog' },
];

function setManualViewerType(type: string) {
  manualViewerType.value = type;
}

// Reset manual override when key changes
watch(
  () => dataStore.currentKey?.key,
  () => { manualViewerType.value = null; },
);

// Delete dialog
const showDeleteDialog = ref(false);
const deleteConfirmInput = ref('');

// Rename dialog
const showRenameDialog = ref(false);
const newKeyName = ref('');

// TTL dialog
const showTtlDialog = ref(false);
const ttlValue = ref(0);
const ttlUnit = ref<'s' | 'm' | 'h' | 'd'>('s');

const ttlInSeconds = computed(() => {
  const multipliers = { s: 1, m: 60, h: 3600, d: 86400 };
  return ttlValue.value * multipliers[ttlUnit.value];
});

// Toast
const toast = ref<{ msg: string; type: 'success' | 'error' } | null>(null);
let toastTimer: ReturnType<typeof setTimeout>;

function showToast(msg: string, type: 'success' | 'error' = 'success') {
  clearTimeout(toastTimer);
  toast.value = { msg, type };
  toastTimer = setTimeout(() => { toast.value = null; }, 3000);
}

function formatTTL(ttl: number) {
  if (ttl === -1) return '永久';
  if (ttl === -2) return '已过期';
  if (ttl >= 86400) return `${Math.floor(ttl / 86400)}d ${Math.floor((ttl % 86400) / 3600)}h`;
  if (ttl >= 3600) return `${Math.floor(ttl / 3600)}h ${Math.floor((ttl % 3600) / 60)}m`;
  if (ttl > 60) return `${Math.floor(ttl / 60)}m ${ttl % 60}s`;
  return `${ttl}s`;
}

function formatSize(bytes: number) {
  if (bytes === 0) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

const rawJson = computed(() => {
  if (!dataStore.currentKey) return '';
  return JSON.stringify(dataStore.currentKey.value, null, 2);
});

const relatedCommands = computed(() => {
  const t = effectiveViewerType.value ?? dataStore.currentKey?.key_type;
  const cmds: Record<string, string[]> = {
    string: ['GET', 'SET', 'GETSET', 'STRLEN', 'APPEND', 'INCR', 'DECR'],
    hash: ['HGET', 'HSET', 'HDEL', 'HGETALL', 'HKEYS', 'HVALS', 'HLEN'],
    list: ['LRANGE', 'LPUSH', 'RPUSH', 'LPOP', 'RPOP', 'LLEN', 'LINDEX'],
    set: ['SMEMBERS', 'SADD', 'SREM', 'SCARD', 'SISMEMBER', 'SUNION'],
    zset: ['ZRANGE', 'ZADD', 'ZREM', 'ZSCORE', 'ZCARD', 'ZRANK', 'ZRANGEBYSCORE'],
    stream: ['XRANGE', 'XREVRANGE', 'XADD', 'XDEL', 'XGROUP', 'XPENDING', 'XLEN', 'XINFO'],
    bitmap: ['GETBIT', 'SETBIT', 'BITCOUNT', 'BITPOS', 'BITFIELD', 'BITOP'],
    hyperloglog: ['PFADD', 'PFCOUNT', 'PFMERGE'],
  };
  return cmds[t ?? ''] ?? [];
});

// Delete
async function confirmDelete() {
  if (!dataStore.currentKey) return;
  if (deleteConfirmInput.value !== dataStore.currentKey.key) return;
  try {
    await dataStore.deleteKey(dataStore.currentKey.key);
    showDeleteDialog.value = false;
    deleteConfirmInput.value = '';
    showToast('键已删除');
  } catch (e: any) {
    showToast(`删除失败：${e?.message ?? e?.kind ?? '未知错误'}`, 'error');
  }
}

// Rename
async function confirmRename() {
  if (!dataStore.currentKey || !newKeyName.value) return;
  try {
    await dataStore.renameKey(dataStore.currentKey.key, newKeyName.value);
    showRenameDialog.value = false;
    showToast('重命名成功');
  } catch (e: any) {
    showToast(`重命名失败：${e?.message ?? e?.kind ?? '未知错误'}`, 'error');
  }
}

// TTL
async function confirmTtl() {
  if (!dataStore.currentKey) return;
  try {
    await dataStore.setTtl(dataStore.currentKey.key, ttlInSeconds.value);
    showTtlDialog.value = false;
    showToast('TTL 已更新');
  } catch (e: any) {
    showToast(`TTL 设置失败：${e?.message ?? e?.kind ?? '未知错误'}`, 'error');
  }
}

async function handleRefresh() {
  if (!dataStore.currentKey) return;
  try {
    await dataStore.loadKey(dataStore.currentKey.key);
    showToast('已刷新');
  } catch (e: any) {
    showToast(`刷新失败：${e?.message ?? e?.kind ?? '未知错误'}`, 'error');
  }
}
</script>

<template>
  <div class="browser-workspace">
    <!-- Empty state -->
    <template v-if="!dataStore.currentKey">
      <div class="bw-empty">
        <i class="ri-key-2-line" />
        <p>从左侧选择一个键查看详情</p>
      </div>
    </template>

    <template v-else>
      <!-- Header -->
      <div class="bw-header">
        <div class="bw-key-name">
          <span
            class="bw-type-badge"
            :class="`type-${effectiveViewerType ?? dataStore.currentKey.key_type}`"
          >{{ effectiveViewerType ?? dataStore.currentKey.key_type }}</span>
          <span class="bw-key-text">{{ dataStore.currentKey.key }}</span>
          <!-- Type switcher for string keys (can be Bitmap/HyperLogLog) -->
          <div v-if="showTypeSwitcher" class="bw-type-switcher">
            <button
              v-for="opt in stringViewerOptions"
              :key="opt.value"
              class="bw-type-opt"
              :class="{ active: effectiveViewerType === opt.value }"
              @click="setManualViewerType(opt.value)"
            >{{ opt.label }}</button>
          </div>
        </div>
        <div class="bw-actions">
          <button class="bw-btn" title="刷新" @click="handleRefresh">
            <i class="ri-refresh-line" />
          </button>
          <button class="bw-btn" title="重命名" @click="showRenameDialog = true; newKeyName = dataStore.currentKey!.key">
            <i class="ri-edit-line" />
          </button>
          <button class="bw-btn" title="设置 TTL" @click="showTtlDialog = true">
            <i class="ri-time-line" />
          </button>
          <button class="bw-btn danger" title="删除键" @click="showDeleteDialog = true">
            <i class="ri-delete-bin-line" />
          </button>
        </div>
      </div>

      <!-- Metadata bar -->
      <div class="bw-meta">
        <span><i class="ri-database-line" /> DB {{ dataStore.currentKey.db }}</span>
        <span class="sep">·</span>
        <span><i class="ri-time-line" /> TTL: {{ formatTTL(dataStore.currentKey.ttl) }}</span>
        <span class="sep">·</span>
        <span><i class="ri-hard-drive-line" /> {{ formatSize(dataStore.currentKey.size) }}</span>
        <span class="sep">·</span>
        <span><i class="ri-code-line" /> {{ dataStore.currentKey.encoding }}</span>
        <span class="sep">·</span>
        <span><i class="ri-list-check" /> {{ dataStore.currentKey.length }} 个元素</span>
      </div>

      <!-- Sub tabs -->
      <div class="bw-tabs">
        <button
          v-for="tab in (['data', 'raw', 'commands'] as const)"
          :key="tab"
          class="bw-tab"
          :class="{ active: activeSubTab === tab }"
          @click="activeSubTab = tab"
        >
          {{ tab === 'data' ? '数据' : tab === 'raw' ? '原始 (JSON)' : '相关命令' }}
        </button>
      </div>

      <!-- Tab content -->
      <div class="bw-content">
        <template v-if="activeSubTab === 'data'">
          <StringViewer v-if="effectiveViewerType === 'string'" :detail="dataStore.currentKey" />
          <HashViewer v-else-if="effectiveViewerType === 'hash'" :detail="dataStore.currentKey" />
          <ListViewer v-else-if="effectiveViewerType === 'list'" :detail="dataStore.currentKey" />
          <SetViewer v-else-if="effectiveViewerType === 'set'" :detail="dataStore.currentKey" />
          <ZSetViewer v-else-if="effectiveViewerType === 'zset'" :detail="dataStore.currentKey" />
          <StreamViewer v-else-if="effectiveViewerType === 'stream'" :detail="dataStore.currentKey" />
          <BitmapViewer v-else-if="effectiveViewerType === 'bitmap'" :detail="dataStore.currentKey" />
          <HyperLogLogViewer v-else-if="effectiveViewerType === 'hyperloglog'" :detail="dataStore.currentKey" />
          <div v-else class="bw-unsupported">
            <i class="ri-question-line" />
            <p>暂不支持 {{ dataStore.currentKey.key_type }} 类型的查看器</p>
          </div>
        </template>

        <template v-else-if="activeSubTab === 'raw'">
          <pre class="bw-raw">{{ rawJson }}</pre>
        </template>

        <template v-else>
          <div class="bw-commands">
            <div v-for="cmd in relatedCommands" :key="cmd" class="bw-cmd-item">
              <code>{{ cmd }}</code>
            </div>
          </div>
        </template>
      </div>
    </template>

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toast" class="bw-toast" :class="toast.type">
        <i :class="toast.type === 'success' ? 'ri-checkbox-circle-fill' : 'ri-close-circle-fill'" />
        {{ toast.msg }}
      </div>
    </Transition>

    <!-- Delete Dialog -->
    <Transition name="modal">
      <div v-if="showDeleteDialog" class="modal-overlay" @click.self="showDeleteDialog = false">
        <div class="modal-card">
          <div class="modal-header">
            <h3><i class="ri-delete-bin-line" style="color: var(--srn-color-primary);" /> 删除键</h3>
          </div>
          <div class="modal-body">
            <p>此操作不可撤销。请输入键名确认删除：</p>
            <code class="key-confirm-name">{{ dataStore.currentKey?.key }}</code>
            <input
              v-model="deleteConfirmInput"
              type="text"
              class="confirm-input"
              placeholder="输入键名确认"
            />
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showDeleteDialog = false; deleteConfirmInput = ''">取消</button>
            <button
              class="btn-danger"
              :disabled="deleteConfirmInput !== dataStore.currentKey?.key"
              @click="confirmDelete"
            >确认删除</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Rename Dialog -->
    <Transition name="modal">
      <div v-if="showRenameDialog" class="modal-overlay" @click.self="showRenameDialog = false">
        <div class="modal-card">
          <div class="modal-header">
            <h3><i class="ri-edit-line" /> 重命名键</h3>
          </div>
          <div class="modal-body">
            <label>新键名</label>
            <input v-model="newKeyName" type="text" class="confirm-input" placeholder="输入新键名" />
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showRenameDialog = false">取消</button>
            <button class="btn-save" :disabled="!newKeyName || newKeyName === dataStore.currentKey?.key" @click="confirmRename">确认</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- TTL Dialog -->
    <Transition name="modal">
      <div v-if="showTtlDialog" class="modal-overlay" @click.self="showTtlDialog = false">
        <div class="modal-card">
          <div class="modal-header">
            <h3><i class="ri-time-line" /> 设置 TTL</h3>
          </div>
          <div class="modal-body">
            <div class="ttl-row">
              <input v-model.number="ttlValue" type="number" min="-1" class="confirm-input" style="width: 100px;" />
              <select v-model="ttlUnit" class="ttl-unit">
                <option value="s">秒</option>
                <option value="m">分钟</option>
                <option value="h">小时</option>
                <option value="d">天</option>
              </select>
              <span class="ttl-hint">(-1 = 永久)</span>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showTtlDialog = false">取消</button>
            <button class="btn-save" @click="confirmTtl">确认</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.browser-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.bw-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--srn-color-text-3);
  gap: 12px;
}
.bw-empty i { font-size: 48px; }
.bw-empty p { font-size: 13px; }

.bw-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
}

.bw-key-name { display: flex; align-items: center; gap: 10px; min-width: 0; }
.bw-type-badge {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}
.type-string { background: var(--srn-type-string-bg); color: var(--srn-type-string-text); }
.type-hash { background: var(--srn-type-hash-bg); color: var(--srn-type-hash-text); }
.type-list { background: var(--srn-type-list-bg); color: var(--srn-type-list-text); }
.type-set { background: var(--srn-type-set-bg); color: var(--srn-type-set-text); }
.type-zset { background: var(--srn-type-zset-bg); color: var(--srn-type-zset-text); }
.type-stream { background: #dbeafe; color: #1d4ed8; }
.type-bitmap { background: #fef3c7; color: #92400e; }
.type-hyperloglog { background: #ede9fe; color: #6d28d9; }

.bw-type-switcher {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-left: 4px;
  background: var(--srn-color-surface-1);
  border-radius: 4px;
  padding: 1px;
  border: 1px solid var(--srn-color-border);
}
.bw-type-opt {
  font-size: 10px;
  padding: 2px 8px;
  border: none;
  border-radius: 3px;
  background: transparent;
  color: var(--srn-color-text-3);
  cursor: pointer;
  transition: all var(--srn-motion-fast);
  white-space: nowrap;
}
.bw-type-opt:hover { color: var(--srn-color-text-1); background: var(--srn-color-surface-2); }
.bw-type-opt.active {
  background: var(--srn-color-info);
  color: #fff;
  font-weight: 600;
}

.bw-key-text {
  font-size: 14px;
  font-family: var(--srn-font-mono);
  font-weight: 500;
  color: var(--srn-color-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bw-actions { display: flex; gap: 4px; flex-shrink: 0; }
.bw-btn {
  border: 1px solid var(--srn-color-border);
  background: transparent;
  color: var(--srn-color-text-2);
  cursor: pointer;
  font-size: 14px;
  padding: 5px 8px;
  border-radius: var(--srn-radius-xs);
  transition: all var(--srn-motion-fast);
}
.bw-btn:hover { background: rgba(0,0,0,0.05); }
.bw-btn.danger:hover { color: var(--srn-color-primary); border-color: var(--srn-color-primary); }

.bw-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  font-size: 11px;
  color: var(--srn-color-text-3);
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-1);
  flex-wrap: wrap;
}
.sep { color: #ddd; }

.bw-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
}
.bw-tab {
  padding: 8px 16px;
  border: none;
  background: transparent;
  font-size: 12px;
  color: var(--srn-color-text-3);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all var(--srn-motion-fast);
}
.bw-tab:hover { color: var(--srn-color-text-1); }
.bw-tab.active { color: var(--srn-color-primary); border-bottom-color: var(--srn-color-primary); }

.bw-content { flex: 1; overflow: auto; padding: 12px; }

.bw-raw {
  font-family: var(--srn-font-mono);
  font-size: 12px;
  color: var(--srn-color-text-1);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

.bw-commands { display: flex; flex-wrap: wrap; gap: 8px; }
.bw-cmd-item {
  padding: 4px 10px;
  background: var(--srn-color-surface-2);
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-xs);
}
.bw-cmd-item code { font-size: 12px; font-family: var(--srn-font-mono); color: var(--srn-color-info); }

.bw-unsupported {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--srn-color-text-3);
  gap: 8px;
}

/* Toast */
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

/* Modal */
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
  width: 400px;
  background: var(--srn-color-surface-2);
  border-radius: var(--srn-radius-lg);
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  border: 1px solid var(--srn-color-border);
  overflow: hidden;
}
.modal-header {
  padding: 14px 20px;
  border-bottom: 1px solid var(--srn-color-border);
}
.modal-header h3 { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.modal-body {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 13px;
  color: var(--srn-color-text-2);
}
.key-confirm-name {
  display: block;
  padding: 6px 10px;
  background: var(--srn-color-surface-1);
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-xs);
  font-family: var(--srn-font-mono);
  font-size: 12px;
  color: var(--srn-color-text-1);
  word-break: break-all;
}
.confirm-input {
  width: 100%;
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
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-1);
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
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger { border: none; background: var(--srn-color-primary); color: #fff; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }

.ttl-row { display: flex; align-items: center; gap: 8px; }
.ttl-unit {
  height: 32px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 0 8px;
  font-size: 13px;
  background: var(--srn-color-surface-1);
  outline: none;
}
.ttl-hint { font-size: 11px; color: var(--srn-color-text-3); }

.modal-enter-active, .modal-leave-active { transition: all 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
