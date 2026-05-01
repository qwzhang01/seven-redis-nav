<script setup lang="ts">
import { ref, computed } from 'vue';
import { useKeyBrowserStore } from '@/stores/keyBrowser';
import { useConnectionStore } from '@/stores/connection';
import { keysBulkDelete, keysBulkTtl } from '@/ipc/data';
import type { BulkResult } from '@/types/data';

const keyBrowserStore = useKeyBrowserStore();
const connStore = useConnectionStore();

// Dialog state
const showDeleteDialog = ref(false);
const deleteConfirmText = ref('');
const showTtlDialog = ref(false);
const ttlInput = ref<number>(3600);

// Progress state
const busy = ref(false);
const progressLabel = ref('');
const progressCurrent = ref(0);
const progressTotal = ref(0);

// Toast feedback (lightweight inline toast; app-level toast system can replace later)
const toast = ref<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);
let toastTimer: ReturnType<typeof setTimeout> | null = null;

function showToast(type: 'success' | 'error' | 'info', text: string) {
  toast.value = { type, text };
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.value = null;
  }, 4000);
}

const selectedCount = computed(() => keyBrowserStore.selectedKeys.size);
const selectedList = computed(() => Array.from(keyBrowserStore.selectedKeys));

const requiresTypedConfirm = computed(() => selectedCount.value >= 100);

function openDelete() {
  deleteConfirmText.value = '';
  showDeleteDialog.value = true;
}

function openSetTtl() {
  ttlInput.value = 3600;
  showTtlDialog.value = true;
}

async function confirmDelete() {
  if (requiresTypedConfirm.value && deleteConfirmText.value !== 'DELETE') {
    return;
  }
  showDeleteDialog.value = false;

  const connId = connStore.activeConnId;
  if (!connId) return;

  const keys = selectedList.value;
  busy.value = true;
  progressLabel.value = '批量删除中';
  progressCurrent.value = 0;
  progressTotal.value = keys.length;

  const BATCH_SIZE = 100;
  let totalSuccess = 0;
  const totalFailed: string[] = [];

  try {
    for (let i = 0; i < keys.length; i += BATCH_SIZE) {
      const chunk = keys.slice(i, i + BATCH_SIZE);
      const res: BulkResult = await keysBulkDelete(connId, chunk);
      totalSuccess += res.success;
      totalFailed.push(...res.failed);
      progressCurrent.value = Math.min(i + chunk.length, keys.length);
    }
    if (totalFailed.length === 0) {
      showToast('success', `已删除 ${totalSuccess} 个键`);
    } else {
      showToast(
        'error',
        `删除完成：成功 ${totalSuccess} 个，失败 ${totalFailed.length} 个`,
      );
    }
    keyBrowserStore.clearSelection();
    await keyBrowserStore.refresh();
  } catch (e) {
    showToast('error', `批量删除失败：${String(e)}`);
  } finally {
    busy.value = false;
  }
}

async function confirmSetTtl() {
  showTtlDialog.value = false;
  const connId = connStore.activeConnId;
  if (!connId) return;

  const keys = selectedList.value;
  busy.value = true;
  progressLabel.value = '批量设置 TTL';
  progressCurrent.value = 0;
  progressTotal.value = keys.length;

  try {
    const res: BulkResult = await keysBulkTtl(connId, keys, ttlInput.value);
    progressCurrent.value = keys.length;
    if (res.failed.length === 0) {
      showToast('success', `已为 ${res.success} 个键设置 TTL=${ttlInput.value}s`);
    } else {
      showToast(
        'error',
        `设置 TTL 完成：成功 ${res.success} 个，失败 ${res.failed.length} 个`,
      );
    }
    keyBrowserStore.clearSelection();
    await keyBrowserStore.refresh();
  } catch (e) {
    showToast('error', `批量设置 TTL 失败：${String(e)}`);
  } finally {
    busy.value = false;
  }
}

async function removeTtl() {
  const connId = connStore.activeConnId;
  if (!connId) return;

  const keys = selectedList.value;
  busy.value = true;
  progressLabel.value = '批量移除 TTL';
  progressCurrent.value = 0;
  progressTotal.value = keys.length;

  try {
    const res: BulkResult = await keysBulkTtl(connId, keys, null);
    progressCurrent.value = keys.length;
    if (res.failed.length === 0) {
      showToast('success', `已为 ${res.success} 个键移除 TTL`);
    } else {
      showToast(
        'error',
        `移除 TTL 完成：成功 ${res.success} 个，失败 ${res.failed.length} 个`,
      );
    }
    keyBrowserStore.clearSelection();
    await keyBrowserStore.refresh();
  } catch (e) {
    showToast('error', `批量移除 TTL 失败：${String(e)}`);
  } finally {
    busy.value = false;
  }
}

async function copyNames() {
  const keys = selectedList.value;
  if (keys.length === 0) return;
  try {
    await navigator.clipboard.writeText(keys.join('\n'));
    showToast('success', `已复制 ${keys.length} 个键名`);
  } catch (e) {
    showToast('error', `复制失败：${String(e)}`);
  }
}

function clear() {
  keyBrowserStore.clearSelection();
}
</script>

<template>
  <div v-if="selectedCount > 0 || busy" class="bulk-bar">
    <div class="bulk-bar-main">
      <span class="bulk-count">
        <i class="ri-checkbox-multiple-line" />
        已选 <b>{{ selectedCount }}</b> 个键
      </span>
      <div class="bulk-actions">
        <button class="bulk-btn danger" :disabled="busy" @click="openDelete">
          <i class="ri-delete-bin-line" /> 删除
        </button>
        <button class="bulk-btn" :disabled="busy" @click="openSetTtl">
          <i class="ri-timer-line" /> 设置 TTL
        </button>
        <button class="bulk-btn" :disabled="busy" @click="removeTtl">
          <i class="ri-timer-2-line" /> 移除 TTL
        </button>
        <button class="bulk-btn" :disabled="busy" @click="copyNames">
          <i class="ri-file-copy-line" /> 复制键名
        </button>
        <button class="bulk-btn ghost" :disabled="busy" @click="clear">
          <i class="ri-close-line" /> 取消
        </button>
      </div>
    </div>

    <!-- Progress bar while busy -->
    <div v-if="busy" class="bulk-progress">
      <div class="bulk-progress-label">
        {{ progressLabel }} · {{ progressCurrent }} / {{ progressTotal }}
      </div>
      <div class="bulk-progress-track">
        <div
          class="bulk-progress-fill"
          :style="{ width: progressTotal > 0 ? `${(progressCurrent / progressTotal) * 100}%` : '0%' }"
        />
      </div>
    </div>

    <!-- Toast -->
    <div v-if="toast" class="bulk-toast" :class="toast.type">
      {{ toast.text }}
    </div>
  </div>

  <!-- Delete confirmation -->
  <div v-if="showDeleteDialog" class="modal-mask" @click.self="showDeleteDialog = false">
    <div class="modal">
      <h3>删除 {{ selectedCount }} 个键？</h3>
      <p class="modal-desc">
        此操作不可撤销。将逐批（每批 100 个）对 Redis 执行 <code>DEL</code>。
        <span v-if="requiresTypedConfirm" class="warn">
          选中数量较多，请在下方输入 <b>DELETE</b> 以确认。
        </span>
      </p>
      <input
        v-if="requiresTypedConfirm"
        v-model="deleteConfirmText"
        class="modal-input"
        placeholder="输入 DELETE 以确认"
      />
      <div class="modal-actions">
        <button class="bulk-btn ghost" @click="showDeleteDialog = false">取消</button>
        <button
          class="bulk-btn danger"
          :disabled="requiresTypedConfirm && deleteConfirmText !== 'DELETE'"
          @click="confirmDelete"
        >
          确认删除
        </button>
      </div>
    </div>
  </div>

  <!-- Set TTL dialog -->
  <div v-if="showTtlDialog" class="modal-mask" @click.self="showTtlDialog = false">
    <div class="modal">
      <h3>为 {{ selectedCount }} 个键设置 TTL</h3>
      <p class="modal-desc">请输入 TTL 秒数（>0）。</p>
      <input v-model.number="ttlInput" type="number" min="1" class="modal-input" />
      <div class="modal-actions">
        <button class="bulk-btn ghost" @click="showTtlDialog = false">取消</button>
        <button class="bulk-btn" :disabled="!ttlInput || ttlInput <= 0" @click="confirmSetTtl">
          确认
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bulk-bar {
  border-top: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-1);
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
}
.bulk-bar-main { display: flex; align-items: center; gap: 10px; justify-content: space-between; }
.bulk-count { font-size: 12px; color: var(--srn-color-text-2); display: flex; align-items: center; gap: 4px; }
.bulk-count i { font-size: 14px; color: var(--srn-color-primary); }
.bulk-count b { color: var(--srn-color-primary); font-weight: 600; }
.bulk-actions { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.bulk-btn {
  height: 26px; padding: 0 10px; border-radius: var(--srn-radius-xs);
  border: 1px solid var(--srn-color-border); background: #fff;
  color: var(--srn-color-text-2); font-size: 11px; display: inline-flex;
  align-items: center; gap: 4px; cursor: pointer;
  transition: background var(--srn-motion-fast), border-color var(--srn-motion-fast);
}
.bulk-btn:hover:not(:disabled) { background: var(--srn-color-surface-2); border-color: var(--srn-color-text-3); }
.bulk-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.bulk-btn.danger { background: #dc382d; color: #fff; border-color: #dc382d; }
.bulk-btn.danger:hover:not(:disabled) { background: #c02e24; }
.bulk-btn.ghost { background: transparent; border-color: transparent; color: var(--srn-color-text-3); }
.bulk-btn.ghost:hover:not(:disabled) { background: rgba(0,0,0,0.04); }

.bulk-progress { display: flex; flex-direction: column; gap: 4px; }
.bulk-progress-label { font-size: 11px; color: var(--srn-color-text-3); font-family: var(--srn-font-mono); }
.bulk-progress-track { height: 4px; background: #eee; border-radius: 2px; overflow: hidden; }
.bulk-progress-fill { height: 100%; background: var(--srn-color-primary); transition: width 0.2s ease; }

.bulk-toast {
  position: absolute; top: -36px; left: 50%; transform: translateX(-50%);
  padding: 6px 12px; border-radius: var(--srn-radius-xs); font-size: 11px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.12); white-space: nowrap;
}
.bulk-toast.success { background: #1a7f37; color: #fff; }
.bulk-toast.error { background: #dc382d; color: #fff; }
.bulk-toast.info { background: #007aff; color: #fff; }

.modal-mask {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; z-index: 9999;
}
.modal {
  width: 360px; background: #fff; border-radius: var(--srn-radius-md);
  padding: 18px 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.modal h3 { margin: 0 0 8px; font-size: 14px; font-weight: 600; color: var(--srn-color-text-1); }
.modal-desc { font-size: 12px; color: var(--srn-color-text-2); margin: 0 0 12px; line-height: 1.5; }
.modal-desc .warn { color: #c02e24; display: block; margin-top: 4px; }
.modal-desc code { background: #f5f5f5; padding: 1px 4px; border-radius: 2px; font-family: var(--srn-font-mono); }
.modal-input {
  width: 100%; height: 30px; padding: 0 10px; font-size: 12px;
  border: 1px solid var(--srn-color-border); border-radius: var(--srn-radius-xs);
  font-family: var(--srn-font-mono); outline: none; margin-bottom: 12px;
}
.modal-input:focus { border-color: var(--srn-color-primary); }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; }
</style>
