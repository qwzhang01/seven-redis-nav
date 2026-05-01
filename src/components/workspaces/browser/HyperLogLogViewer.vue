<script setup lang="ts">
import { ref, watch } from 'vue';
import { hllCount, hllAdd, hllMerge } from '@/ipc/phase3';
import { useDataStore } from '@/stores/data';
import { useConnectionStore } from '@/stores/connection';
import type { HllStats } from '@/types/phase3';

const dataStore = useDataStore();
const connStore = useConnectionStore();

const stats = ref<HllStats | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

// PFADD form
const addElements = ref('');
const addLoading = ref(false);

// PFMERGE form
const mergeDestKey = ref('');
const mergeSourceKeys = ref('');
const mergeLoading = ref(false);

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

async function loadStats() {
  loading.value = true;
  error.value = null;
  try {
    stats.value = await hllCount(getConnId(), getKey());
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
}

async function handlePfadd() {
  const elements = addElements.value
    .split(',')
    .map(s => s.trim())
    .filter(s => s.length > 0);
  if (elements.length === 0) return;
  addLoading.value = true;
  try {
    await hllAdd(getConnId(), getKey(), elements);
    showToast(`PFADD 成功：添加 ${elements.length} 个元素`);
    addElements.value = '';
    await loadStats();
  } catch (e: any) {
    showToast(`PFADD 失败：${e?.message ?? '未知错误'}`, 'error');
  } finally {
    addLoading.value = false;
  }
}

async function handlePfmerge() {
  const dest = mergeDestKey.value.trim();
  const sources = mergeSourceKeys.value
    .split(',')
    .map(s => s.trim())
    .filter(s => s.length > 0);
  if (!dest || sources.length === 0) return;
  mergeLoading.value = true;
  try {
    await hllMerge(getConnId(), dest, sources);
    showToast(`PFMERGE 成功：合并 ${sources.length} 个 Key → ${dest}`);
    mergeDestKey.value = '';
    mergeSourceKeys.value = '';
  } catch (e: any) {
    showToast(`PFMERGE 失败：${e?.message ?? '未知错误'}`, 'error');
  } finally {
    mergeLoading.value = false;
  }
}

watch(() => dataStore.currentKey, (newKey) => {
  if (newKey) {
    loadStats();
  }
}, { immediate: true });
</script>

<template>
  <div class="hll-viewer">
    <!-- Meta bar -->
    <div class="hll-meta">
      <span><i class="ri-pie-chart-line" /> HyperLogLog</span>
      <span class="sep">·</span>
      <span><i class="ri-bar-chart-line" /> 估算基数: {{ stats?.estimated_cardinality ?? '-' }}</span>
      <span class="sep">·</span>
      <span><i class="ri-code-line" /> 编码: {{ stats?.encoding ?? '-' }}</span>
    </div>

    <!-- Stats card -->
    <div class="hll-content">
      <div v-if="loading" class="hll-loading">加载中...</div>
      <div v-else-if="error" class="hll-error">{{ error }}</div>
      <template v-else>
        <div class="hll-stats-card">
          <div class="hll-card-icon"><i class="ri-bar-chart-grouped-line" /></div>
          <div class="hll-card-value">{{ stats?.estimated_cardinality ?? 0 }}</div>
          <div class="hll-card-label">估算基数 (PFCOUNT)</div>
        </div>

        <div class="hll-sections">
          <!-- PFADD section -->
          <div class="hll-section">
            <h4>PFADD — 添加元素</h4>
            <div class="hll-input-row">
              <input
                v-model="addElements"
                type="text"
                class="hll-input"
                placeholder="逗号分隔多个元素，如：user1, user2, user3"
                @keyup.enter="handlePfadd"
              />
              <button class="hll-btn primary" :disabled="addLoading || !addElements.trim()" @click="handlePfadd">
                {{ addLoading ? '提交中...' : 'PFADD' }}
              </button>
            </div>
          </div>

          <!-- PFMERGE section -->
          <div class="hll-section">
            <h4>PFMERGE — 合并多个 Key</h4>
            <div class="hll-input-row">
              <input
                v-model="mergeDestKey"
                type="text"
                class="hll-input"
                placeholder="目标 Key"
                style="width: 140px;"
              />
              <span class="hll-arrow">←</span>
              <input
                v-model="mergeSourceKeys"
                type="text"
                class="hll-input"
                placeholder="源 Key（逗号分隔）"
                @keyup.enter="handlePfmerge"
              />
              <button class="hll-btn primary" :disabled="mergeLoading || !mergeDestKey.trim() || !mergeSourceKeys.trim()" @click="handlePfmerge">
                {{ mergeLoading ? '合并中...' : 'PFMERGE' }}
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>

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
.hll-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.hll-meta {
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

.hll-content { flex: 1; overflow: auto; padding: 16px; }
.hll-loading, .hll-error {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--srn-color-text-3);
  font-size: 13px;
}
.hll-error { color: var(--srn-color-primary); }

.hll-stats-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
  background: var(--srn-color-surface-2);
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-md);
  margin-bottom: 20px;
}
.hll-card-icon { font-size: 32px; color: var(--srn-color-primary); margin-bottom: 8px; }
.hll-card-value {
  font-size: 36px;
  font-weight: 700;
  font-family: var(--srn-font-mono);
  color: var(--srn-color-text-1);
}
.hll-card-label { font-size: 12px; color: var(--srn-color-text-3); margin-top: 4px; }

.hll-sections { display: flex; flex-direction: column; gap: 16px; }
.hll-section {
  background: var(--srn-color-surface-2);
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-md);
  padding: 14px;
}
.hll-section h4 {
  font-size: 12px;
  font-weight: 600;
  color: var(--srn-color-text-2);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.hll-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.hll-input {
  flex: 1;
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
.hll-input:focus { border-color: var(--srn-color-info); }
.hll-arrow { color: var(--srn-color-text-3); font-size: 16px; }

.hll-btn {
  height: 32px;
  padding: 0 14px;
  border-radius: var(--srn-radius-sm);
  font-size: 12px;
  font-family: var(--srn-font-mono);
  cursor: pointer;
  transition: all var(--srn-motion-fast);
  border: 1px solid var(--srn-color-border);
  background: transparent;
  color: var(--srn-color-text-2);
}
.hll-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.hll-btn.primary { background: var(--srn-color-primary); color: #fff; border-color: var(--srn-color-primary); }
.hll-btn.primary:not(:disabled):hover { opacity: 0.9; }

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
</style>
