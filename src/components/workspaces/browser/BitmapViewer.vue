<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import { bitmapChunk, bitmapCount, bitmapPos, bitmapSetBit } from '@/ipc/phase3';
import { useDataStore } from '@/stores/data';
import { useConnectionStore } from '@/stores/connection';
import type { BitmapChunk } from '@/types/phase3';

const dataStore = useDataStore();
const connStore = useConnectionStore();

const viewMode = ref<'bits' | 'bytes'>('bits');
const loading = ref(false);
const error = ref<string | null>(null);

// Bitmap data
const chunkData = ref<BitmapChunk | null>(null);
const startByte = ref(0);
const chunkSize = ref(512); // bytes per chunk
const totalBitCount = ref(0);
const setBitCount = ref(0);

// Virtual scrolling for bit grid
const ROW_BYTES = 4; // 4 bytes = 32 bits per row
const ROW_HEIGHT = 12; // 10px cell + 2px gap
const scrollContainer = ref<HTMLElement | null>(null);
const scrollTop = ref(0);
const containerHeight = ref(0);

const visibleRowRange = computed(() => {
  if (!chunkData.value) return { start: 0, end: 0 };
  const bytes = decodeBase64(chunkData.value.data_base64);
  const totalRows = Math.ceil(bytes.length / ROW_BYTES);
  const startRow = Math.floor(scrollTop.value / ROW_HEIGHT);
  const visibleCount = Math.ceil(containerHeight.value / ROW_HEIGHT) + 2; // +2 for buffer
  const endRow = Math.min(startRow + visibleCount, totalRows);
  return { start: startRow, end: endRow };
});

const bitGrid = computed(() => {
  if (!chunkData.value) return [];
  const bytes = decodeBase64(chunkData.value.data_base64);
  const grid: number[][] = [];
  const { start, end } = visibleRowRange.value;
  for (let ri = start; ri < end; ri++) {
    const row: number[] = [];
    for (let j = 0; j < ROW_BYTES && (ri * ROW_BYTES + j) < bytes.length; j++) {
      const byte = bytes[ri * ROW_BYTES + j];
      for (let bit = 7; bit >= 0; bit--) {
        row.push((byte >> bit) & 1);
      }
    }
    grid.push(row);
  }
  return grid;
});

const bitGridStartRow = computed(() => visibleRowRange.value.start);

// Estimated total scroll height for the bit grid
const bitGridTotalHeight = computed(() => {
  if (!chunkData.value) return 0;
  const bytes = decodeBase64(chunkData.value.data_base64);
  const totalRows = Math.ceil(bytes.length / ROW_BYTES);
  return totalRows * ROW_HEIGHT;
});

// Operation results
const opResult = ref<string | null>(null);

// Set bit dialog
const showSetBitDialog = ref(false);
const setBitOffset = ref(0);
const setBitValue = ref(0);

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

function decodeBase64(b64: string): Uint8Array {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

const byteRows = computed(() => {
  if (!chunkData.value) return [];
  const bytes = decodeBase64(chunkData.value.data_base64);
  const rows: { offset: number; bytes: number[]; ascii: string }[] = [];
  for (let i = 0; i < bytes.length; i += 16) {
    const slice = Array.from(bytes.slice(i, Math.min(i + 16, bytes.length)));
    const ascii = slice.map(b => (b >= 32 && b <= 126) ? String.fromCharCode(b) : '.').join('');
    rows.push({ offset: startByte.value + i, bytes: slice, ascii });
  }
  return rows;
});

async function loadChunk() {
  loading.value = true;
  error.value = null;
  try {
    chunkData.value = await bitmapChunk(
      getConnId(),
      getKey(),
      startByte.value,
      startByte.value + chunkSize.value - 1,
    );
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
}

async function loadBitCount() {
  try {
    setBitCount.value = await bitmapCount(getConnId(), getKey(), 0, -1);
  } catch (e: any) {
    console.error('BITCOUNT failed:', e);
  }
}

async function handleBitcount() {
  try {
    const count = await bitmapCount(getConnId(), getKey(), 0, -1);
    opResult.value = `BITCOUNT: ${count}`;
    showToast(`BITCOUNT = ${count}`);
  } catch (e: any) {
    showToast(`BITCOUNT 失败：${e?.message ?? '未知错误'}`, 'error');
  }
}

async function handleBitpos() {
  try {
    const pos = await bitmapPos(getConnId(), getKey(), 1);
    opResult.value = `BITPOS (bit=1): ${pos}`;
    showToast(`BITPOS = ${pos}`);
  } catch (e: any) {
    showToast(`BITPOS 失败：${e?.message ?? '未知错误'}`, 'error');
  }
}

async function handleSetBit() {
  try {
    const prev = await bitmapSetBit(getConnId(), getKey(), setBitOffset.value, setBitValue.value);
    showSetBitDialog.value = false;
    showToast(`SETBIT 成功，原值 = ${prev}`);
    await loadChunk();
    await loadBitCount();
  } catch (e: any) {
    showToast(`SETBIT 失败：${e?.message ?? '未知错误'}`, 'error');
  }
}

async function prevChunk() {
  if (startByte.value > 0) {
    startByte.value = Math.max(0, startByte.value - chunkSize.value);
    await loadChunk();
  }
}

async function nextChunk() {
  startByte.value += chunkSize.value;
  await loadChunk();
}

function formatSize(bytes: number) {
  if (bytes === 0) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function onBitGridScroll(e: Event) {
  const el = e.target as HTMLElement;
  scrollTop.value = el.scrollTop;
}

function onBitGridResize(e: ResizeObserverEntry[]) {
  if (e.length > 0) {
    containerHeight.value = e[0].contentRect.height;
  }
}

watch(() => dataStore.currentKey, (newKey) => {
  if (newKey && newKey.key_type === 'string') {
    totalBitCount.value = newKey.size * 8;
    startByte.value = 0;
    loadChunk();
    loadBitCount();
  }
}, { immediate: true });

onMounted(() => {
  nextTick(() => {
    if (scrollContainer.value) {
      const ro = new ResizeObserver((entries) => onBitGridResize(entries));
      ro.observe(scrollContainer.value);
    }
  });
});
</script>

<template>
  <div class="bitmap-viewer">
    <!-- Meta bar -->
    <div class="bv-meta">
      <span><i class="ri-grid-line" /> Bitmap</span>
      <span class="sep">·</span>
      <span><i class="ri-ruler-line" /> {{ formatSize(dataStore.currentKey?.size ?? 0) }}</span>
      <span class="sep">·</span>
      <span><i class="ri-checkbox-circle-line" /> Set bits: {{ setBitCount }}</span>
      <span class="sep">·</span>
      <span><i class="ri-list-check" /> Total: {{ totalBitCount }} bits</span>
    </div>

    <!-- View toggle & actions -->
    <div class="bv-toolbar">
      <div class="bv-tabs">
        <button class="bv-tab" :class="{ active: viewMode === 'bits' }" @click="viewMode = 'bits'">位网格</button>
        <button class="bv-tab" :class="{ active: viewMode === 'bytes' }" @click="viewMode = 'bytes'">字节预览</button>
      </div>
      <div class="bv-actions">
        <button class="bv-action-btn" @click="handleBitcount">BITCOUNT</button>
        <button class="bv-action-btn" @click="handleBitpos">BITPOS</button>
        <button class="bv-action-btn primary" @click="showSetBitDialog = true">SETBIT</button>
      </div>
    </div>

    <!-- Op result -->
    <div v-if="opResult" class="bv-op-result">{{ opResult }}</div>

    <!-- Content -->
    <div class="bv-content">
      <div v-if="loading" class="bv-loading">加载中...</div>
      <div v-else-if="error" class="bv-error">{{ error }}</div>

      <!-- Bit grid view with virtual scrolling -->
      <template v-else-if="viewMode === 'bits'">
        <div
          ref="scrollContainer"
          class="bv-bit-grid-scroll"
          @scroll="onBitGridScroll"
        >
          <div class="bv-bit-grid" :style="{ height: bitGridTotalHeight + 'px' }">
            <div
              v-for="(row, ri) in bitGrid"
              :key="bitGridStartRow + ri"
              class="bv-bit-row"
              :style="{ transform: `translateY(${(bitGridStartRow + ri) * ROW_HEIGHT}px)` }"
            >
              <span class="bv-row-offset">{{ ((startByte + (bitGridStartRow + ri) * ROW_BYTES) * 8).toString(16).padStart(4, '0') }}</span>
              <div
                v-for="(bit, bi) in row"
                :key="bi"
                class="bv-bit-cell"
                :class="{ set: bit === 1 }"
                :title="`Offset: ${(bitGridStartRow + ri) * 32 + bi}`"
              />
            </div>
          </div>
        </div>
      </template>

      <!-- Byte view -->
      <template v-else-if="viewMode === 'bytes'">
        <table class="bv-byte-table">
          <thead>
            <tr>
              <th>Offset</th>
              <th colspan="16">Hex</th>
              <th>ASCII</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in byteRows" :key="row.offset">
              <td class="bv-offset-cell">{{ row.offset.toString(16).padStart(8, '0') }}</td>
              <td v-for="(b, idx) in row.bytes" :key="idx" class="bv-hex-cell">{{ b.toString(16).padStart(2, '0') }}</td>
              <td v-for="idx in 16 - row.bytes.length" :key="'pad-' + idx" class="bv-hex-cell empty" />
              <td class="bv-ascii-cell">{{ row.ascii }}</td>
            </tr>
          </tbody>
        </table>
      </template>

      <!-- Pagination -->
      <div class="bv-pagination">
        <button class="bv-page-btn" :disabled="startByte === 0" @click="prevChunk">← 上一段</button>
        <span class="bv-page-info">起始字节: {{ startByte }}</span>
        <button class="bv-page-btn" @click="nextChunk">下一段 →</button>
      </div>
    </div>

    <!-- SetBit dialog -->
    <Transition name="modal">
      <div v-if="showSetBitDialog" class="modal-overlay" @click.self="showSetBitDialog = false">
        <div class="modal-card">
          <div class="modal-header">
            <h3><i class="ri-edit-line" /> SETBIT</h3>
          </div>
          <div class="modal-body">
            <div class="setbit-row">
              <label>Offset</label>
              <input v-model.number="setBitOffset" type="number" min="0" class="confirm-input" />
            </div>
            <div class="setbit-row">
              <label>Value (0 或 1)</label>
              <select v-model.number="setBitValue" class="add-select">
                <option :value="0">0</option>
                <option :value="1">1</option>
              </select>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showSetBitDialog = false">取消</button>
            <button class="btn-save" @click="handleSetBit">SETBIT</button>
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
.bitmap-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.bv-meta {
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

.bv-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
  padding: 0 8px;
}
.bv-tabs { display: flex; }
.bv-tab {
  padding: 8px 14px;
  border: none;
  background: transparent;
  font-size: 12px;
  color: var(--srn-color-text-3);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all var(--srn-motion-fast);
}
.bv-tab:hover { color: var(--srn-color-text-1); }
.bv-tab.active { color: var(--srn-color-primary); border-bottom-color: var(--srn-color-primary); }
.bv-actions { display: flex; gap: 4px; }
.bv-action-btn {
  border: 1px solid var(--srn-color-border);
  background: transparent;
  color: var(--srn-color-text-2);
  cursor: pointer;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: var(--srn-radius-xs);
  font-family: var(--srn-font-mono);
  transition: all var(--srn-motion-fast);
}
.bv-action-btn:hover { background: rgba(0,0,0,0.05); }
.bv-action-btn.primary { background: var(--srn-color-primary); color: #fff; border-color: var(--srn-color-primary); }

.bv-op-result {
  padding: 4px 16px;
  font-size: 12px;
  font-family: var(--srn-font-mono);
  color: var(--srn-color-info);
  background: var(--srn-color-surface-2);
  border-bottom: 1px solid var(--srn-color-border);
}

.bv-content { flex: 1; overflow: auto; padding: 12px; }
.bv-loading, .bv-error {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--srn-color-text-3);
  font-size: 13px;
}
.bv-error { color: var(--srn-color-primary); }

/* Bit grid */
.bv-bit-grid-scroll {
  flex: 1;
  overflow-y: auto;
  position: relative;
}
.bv-bit-grid {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.bv-bit-row { display: flex; align-items: center; gap: 1px; position: absolute; left: 0; right: 0; }
.bv-row-offset {
  font-family: var(--srn-font-mono);
  font-size: 9px;
  color: var(--srn-color-text-3);
  width: 40px;
  text-align: right;
  margin-right: 6px;
}
.bv-bit-cell {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  background: var(--srn-color-surface-2);
  border: 1px solid rgba(0,0,0,0.06);
  transition: all var(--srn-motion-fast);
}
.bv-bit-cell.set { background: var(--srn-color-primary); border-color: var(--srn-color-primary); }
.bv-bit-cell:hover { outline: 2px solid var(--srn-color-info); }

/* Byte table */
.bv-byte-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  font-family: var(--srn-font-mono);
}
.bv-byte-table th {
  padding: 4px 8px;
  font-size: 10px;
  font-weight: 600;
  color: var(--srn-color-text-3);
  text-transform: uppercase;
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
  position: sticky;
  top: 0;
}
.bv-offset-cell { color: var(--srn-color-text-3); font-size: 11px; }
.bv-hex-cell { color: var(--srn-color-text-1); padding: 2px 4px; font-size: 11px; }
.bv-hex-cell.empty { color: transparent; }
.bv-ascii-cell { color: var(--srn-color-text-2); padding-left: 8px; font-size: 11px; }

/* Pagination */
.bv-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 8px;
  border-top: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
}
.bv-page-btn {
  border: 1px solid var(--srn-color-border);
  background: transparent;
  color: var(--srn-color-text-2);
  cursor: pointer;
  font-size: 12px;
  padding: 4px 12px;
  border-radius: var(--srn-radius-xs);
}
.bv-page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.bv-page-btn:not(:disabled):hover { background: rgba(0,0,0,0.05); }
.bv-page-info { font-size: 11px; color: var(--srn-color-text-3); font-family: var(--srn-font-mono); }

/* Modal & dialog styles */
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
  width: 380px;
  background: var(--srn-color-surface-2);
  border-radius: var(--srn-radius-lg);
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  border: 1px solid var(--srn-color-border);
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
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-1);
}
.setbit-row { display: flex; align-items: center; gap: 8px; }
.add-select {
  height: 32px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 0 8px;
  font-size: 13px;
  background: var(--srn-color-surface-1);
  outline: none;
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
.btn-cancel, .btn-save {
  height: 30px;
  padding: 0 14px;
  border-radius: var(--srn-radius-sm);
  font-size: 13px;
  cursor: pointer;
}
.btn-cancel { border: 1px solid var(--srn-color-border); background: transparent; color: var(--srn-color-text-2); }
.btn-save { border: none; background: var(--srn-color-primary); color: #fff; }

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
