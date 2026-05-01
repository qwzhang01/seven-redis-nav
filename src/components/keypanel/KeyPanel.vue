<script setup lang="ts">
import { ref, watch, computed, onMounted, onBeforeUnmount } from 'vue';
import { useVirtualizer } from '@tanstack/vue-virtual';
import { useKeyBrowserStore } from '@/stores/keyBrowser';
import { useDataStore } from '@/stores/data';
import { useConnectionStore } from '@/stores/connection';
import type { KeyType } from '@/types/data';
import BulkActionBar from './BulkActionBar.vue';
import { exportDbJson, exportKeysJson } from '@/ipc/phase4';
import { saveAs } from 'file-saver';

const keyBrowserStore = useKeyBrowserStore();
const dataStore = useDataStore();
const connStore = useConnectionStore();

// Export functions
const isExporting = ref(false);

async function exportSelectedKeys() {
  if (!connStore.activeConnId || keyBrowserStore.selectedKeys.size === 0) return;
  isExporting.value = true;
  try {
    const keys = Array.from(keyBrowserStore.selectedKeys);
    const data = await exportKeysJson(connStore.activeConnId, keys);
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json;charset=utf-8;' });
    saveAs(blob, `redis-keys-${Date.now()}.json`);
  } finally {
    isExporting.value = false;
  }
}

async function exportAllKeys() {
  if (!connStore.activeConnId) return;
  isExporting.value = true;
  try {
    const data = await exportDbJson(connStore.activeConnId);
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json;charset=utf-8;' });
    const host = connStore.activeConnection?.host ?? 'redis';
    saveAs(blob, `redis-export-${host}-${Date.now()}.json`);
  } finally {
    isExporting.value = false;
  }
}

const isClusterMode = computed(() =>
  connStore.activeConnection?.connection_type === 'cluster',
);

const searchInput = ref('');
const typeFilterValue = ref<KeyType | ''>('');
const showNewKeyForm = ref(false);
const newKeyName = ref('');
const newKeyType = ref<KeyType>('string');
const newKeyValue = ref('');

// Virtual scroll setup
const parentRef = ref<HTMLElement | null>(null);
const ROW_HEIGHT = 34;

const virtualizer = useVirtualizer(
  computed(() => ({
    count: keyBrowserStore.filteredKeys.length,
    getScrollElement: () => parentRef.value,
    estimateSize: () => ROW_HEIGHT,
    overscan: 10,
  })),
);

const virtualRows = computed(() => virtualizer.value.getVirtualItems());
const totalSize = computed(() => virtualizer.value.getTotalSize());

// Watch connection state to auto-load keys
watch(() => connStore.isConnected, async (connected) => {
  if (connected) {
    await keyBrowserStore.refresh();
  } else {
    keyBrowserStore.reset();
  }
});

// Debounced search
let searchTimer: ReturnType<typeof setTimeout>;
function handleSearchInput() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(async () => {
    keyBrowserStore.setPattern(searchInput.value ? `*${searchInput.value}*` : '');
    await keyBrowserStore.refresh();
  }, 400);
}

function handleTypeFilter() {
  keyBrowserStore.setTypeFilter(typeFilterValue.value);
}

async function handleKeyClick(key: string, event: MouseEvent) {
  // ⌘/Ctrl + click: toggle multi-select
  if (event.metaKey || event.ctrlKey) {
    event.preventDefault();
    keyBrowserStore.toggleSelect(key);
    return;
  }
  // Shift + click: range select
  if (event.shiftKey) {
    event.preventDefault();
    keyBrowserStore.rangeSelect(key);
    return;
  }
  // Plain click: clear multi-selection and open key detail
  keyBrowserStore.clearSelection();
  keyBrowserStore.selectKey(key);
  await dataStore.loadKey(key);
}

// ⌘A / Ctrl+A: select all (only when the panel is focused)
function handleKeydown(e: KeyboardEvent) {
  if (!(e.metaKey || e.ctrlKey) || e.key.toLowerCase() !== 'a') return;
  const target = e.target as HTMLElement | null;
  // Don't hijack ⌘A in input/select fields
  if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT')) {
    return;
  }
  // Only trigger when focus is inside the key panel
  const panel = parentRef.value?.closest('.key-panel') as HTMLElement | null;
  if (!panel || !panel.contains(document.activeElement as Node) && document.activeElement !== document.body) {
    return;
  }
  e.preventDefault();
  keyBrowserStore.selectAll();
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown);
});
onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown);
});

async function handleRefresh() {
  await keyBrowserStore.refresh();
}

// Infinite scroll: load more when near bottom
function handleScroll() {
  if (!parentRef.value) return;
  const { scrollTop, scrollHeight, clientHeight } = parentRef.value;
  const remaining = scrollHeight - scrollTop - clientHeight;
  // Trigger load more when within ~20 items of the bottom
  if (remaining < ROW_HEIGHT * 20 && keyBrowserStore.hasNext && !keyBrowserStore.loading) {
    keyBrowserStore.loadMore();
  }
}

// Scroll to a specific key by name
function scrollToKey(keyName: string) {
  const idx = keyBrowserStore.getKeyIndex(keyName);
  if (idx >= 0) {
    virtualizer.value.scrollToIndex(idx, { align: 'center' });
  }
}

// Expose scrollToKey for parent components
defineExpose({ scrollToKey });

async function handleCreateKey() {
  if (!newKeyName.value) return;
  let value: unknown = newKeyValue.value;
  if (newKeyType.value === 'hash') value = { field1: newKeyValue.value };
  if (newKeyType.value === 'list') value = [newKeyValue.value];
  if (newKeyType.value === 'set') value = [newKeyValue.value];
  if (newKeyType.value === 'zset') value = [{ score: 0, member: newKeyValue.value }];

  await dataStore.createKey(newKeyName.value, value, newKeyType.value);
  await keyBrowserStore.refresh();
  showNewKeyForm.value = false;
  newKeyName.value = '';
  newKeyValue.value = '';
}

const typeColors: Record<string, { bg: string; text: string }> = {
  string: { bg: 'var(--srn-type-string-bg)', text: 'var(--srn-type-string-text)' },
  hash: { bg: 'var(--srn-type-hash-bg)', text: 'var(--srn-type-hash-text)' },
  list: { bg: 'var(--srn-type-list-bg)', text: 'var(--srn-type-list-text)' },
  set: { bg: 'var(--srn-type-set-bg)', text: 'var(--srn-type-set-text)' },
  zset: { bg: 'var(--srn-type-zset-bg)', text: 'var(--srn-type-zset-text)' },
  stream: { bg: 'var(--srn-type-stream-bg)', text: 'var(--srn-type-stream-text)' },
};

function formatTTL(ttl: number) {
  if (ttl < 0) return '永久';
  if (ttl > 86400) return `${Math.floor(ttl / 86400)}d`;
  if (ttl > 3600) return `${Math.floor(ttl / 3600)}h`;
  if (ttl > 60) return `${Math.floor(ttl / 60)}m`;
  return `${ttl}s`;
}

function formatSize(bytes: number) {
  if (bytes === 0) return '-';
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`;
}
</script>

<template>
  <section class="key-panel">
    <!-- 搜索与筛选 -->
    <div class="kp-header">
      <div class="kp-search-wrap">
        <i class="ri-search-line" />
        <input
          v-model="searchInput"
          type="text"
          placeholder="键匹配模式 (例: user:*)"
          @input="handleSearchInput"
        />
      </div>
      <select v-model="typeFilterValue" class="kp-type-select" @change="handleTypeFilter">
        <option value="">全部类型</option>
        <option value="string">String</option>
        <option value="hash">Hash</option>
        <option value="list">List</option>
        <option value="set">Set</option>
        <option value="zset">ZSet</option>
        <option value="stream">Stream</option>
      </select>
      <button class="kp-icon-btn" title="新建键" @click="showNewKeyForm = !showNewKeyForm">
        <i class="ri-add-line" />
      </button>
      <button
        v-if="keyBrowserStore.selectedKeys.size > 0"
        class="kp-icon-btn export-btn"
        :title="`导出选中 ${keyBrowserStore.selectedKeys.size} 个键`"
        :disabled="isExporting"
        @click="exportSelectedKeys"
      >
        <i class="ri-upload-2-line" />
      </button>
      <button
        class="kp-icon-btn"
        title="导出全部键"
        :disabled="isExporting"
        @click="exportAllKeys"
      >
        <i class="ri-database-2-line" />
      </button>
      <button class="kp-icon-btn" title="刷新" :class="{ spinning: keyBrowserStore.loading }" @click="handleRefresh">
        <i class="ri-refresh-line" />
      </button>
    </div>

    <!-- 新建键表单 -->
    <Transition name="slide">
      <div v-if="showNewKeyForm" class="new-key-form">
        <input v-model="newKeyName" type="text" placeholder="键名" class="new-key-input" />
        <select v-model="newKeyType" class="kp-type-select">
          <option value="string">String</option>
          <option value="hash">Hash</option>
          <option value="list">List</option>
          <option value="set">Set</option>
          <option value="zset">ZSet</option>
        </select>
        <input v-model="newKeyValue" type="text" placeholder="初始值" class="new-key-input" />
        <button class="kp-create-btn" @click="handleCreateKey">创建</button>
      </div>
    </Transition>

    <!-- 统计 -->
    <div class="kp-stats">
      <span>
        <i class="ri-key-2-line" />
        <b>{{ keyBrowserStore.filteredKeys.length }}</b> 个键
      </span>
      <span v-if="keyBrowserStore.allKeysLoaded" class="sep">·</span>
      <span v-if="keyBrowserStore.allKeysLoaded" style="color: var(--srn-color-text-3); font-size: 10px;">All loaded</span>
      <span v-if="keyBrowserStore.loading" class="sep">·</span>
      <span v-if="keyBrowserStore.loading" style="color: var(--srn-color-info);">
        <i class="ri-loader-4-line spin" /> 加载中...
      </span>
    </div>

    <!-- Cluster mode banner -->
    <div v-if="isClusterMode" class="kp-cluster-banner">
      <i class="ri-grid-line" />
      Cluster 模式：键浏览仅显示当前节点数据，跨节点 SCAN 将在后续版本支持
    </div>

    <!-- 键列表 (virtual scroll) -->
    <div ref="parentRef" class="kp-list" @scroll="handleScroll">
      <template v-if="!connStore.isConnected">
        <div class="kp-empty">
          <i class="ri-plug-line" />
          <p>请先连接 Redis</p>
        </div>
      </template>
      <template v-else-if="keyBrowserStore.filteredKeys.length === 0 && !keyBrowserStore.loading">
        <div class="kp-empty">
          <i class="ri-inbox-line" />
          <p>没有匹配的键</p>
        </div>
      </template>
      <template v-else>
        <div :style="{ height: `${totalSize}px`, width: '100%', position: 'relative' }">
          <div
            v-for="virtualRow in virtualRows"
            :key="virtualRow.index"
            class="key-item"
            :class="{
              active: keyBrowserStore.filteredKeys[virtualRow.index]?.key === keyBrowserStore.selectedKey,
              'multi-selected': keyBrowserStore.selectedKeys.has(keyBrowserStore.filteredKeys[virtualRow.index]?.key ?? ''),
            }"
            :style="{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualRow.size}px`,
              transform: `translateY(${virtualRow.start}px)`,
            }"
            @click="handleKeyClick(keyBrowserStore.filteredKeys[virtualRow.index]?.key, $event)"
          >
            <span
              class="key-type-badge"
              :style="{ background: typeColors[keyBrowserStore.filteredKeys[virtualRow.index]?.key_type]?.bg, color: typeColors[keyBrowserStore.filteredKeys[virtualRow.index]?.key_type]?.text }"
            >{{ keyBrowserStore.filteredKeys[virtualRow.index]?.key_type }}</span>
            <span class="key-name">{{ keyBrowserStore.filteredKeys[virtualRow.index]?.key }}</span>
            <span class="key-ttl">{{ formatTTL(keyBrowserStore.filteredKeys[virtualRow.index]?.ttl ?? -1) }}</span>
            <span class="key-size">{{ formatSize(keyBrowserStore.filteredKeys[virtualRow.index]?.size ?? 0) }}</span>
          </div>
        </div>
      </template>
    </div>

    <!-- 批量操作栏 (当有多选项时显示) -->
    <BulkActionBar />
  </section>
</template>

<style scoped>
.key-panel {
  width: var(--srn-keypanel-w);
  background: var(--srn-color-surface-2);
  border-right: 1px solid var(--srn-color-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.kp-header { display: flex; align-items: center; gap: 6px; padding: 8px 10px; border-bottom: 1px solid var(--srn-color-border); }
.kp-search-wrap {
  flex: 1; display: flex; align-items: center; gap: 4px;
  background: var(--srn-color-surface-1); border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-xs); padding: 0 8px; height: 28px;
}
.kp-search-wrap i { color: var(--srn-color-text-3); font-size: 12px; }
.kp-search-wrap input { border: none; outline: none; flex: 1; font-size: 11px; font-family: var(--srn-font-mono); background: transparent; }
.kp-type-select { border: 1px solid var(--srn-color-border); border-radius: var(--srn-radius-xs); font-size: 11px; padding: 4px 6px; background: #fff; color: var(--srn-color-text-2); }
.kp-icon-btn { border: none; background: transparent; color: var(--srn-color-text-3); cursor: pointer; font-size: 14px; padding: 4px; border-radius: var(--srn-radius-xs); }
.kp-icon-btn:hover { background: var(--srn-color-surface-1); }
.kp-icon-btn.spinning i { animation: spin 1s linear infinite; }

.kp-cluster-banner {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: rgba(0, 122, 255, 0.06);
  border-bottom: 1px solid rgba(0, 122, 255, 0.15);
  font-size: 11px;
  color: var(--srn-color-info);
}

.new-key-form {
  display: flex;
  gap: 6px;
  padding: 8px 10px;
  border-bottom: 1px solid var(--srn-color-border);
  background: rgba(0,122,255,0.04);
}
.new-key-input {
  flex: 1;
  height: 26px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-xs);
  padding: 0 8px;
  font-size: 11px;
  font-family: var(--srn-font-mono);
  background: var(--srn-color-surface-1);
  outline: none;
}
.kp-create-btn {
  height: 26px;
  padding: 0 10px;
  border: none;
  background: var(--srn-color-primary);
  color: #fff;
  border-radius: var(--srn-radius-xs);
  font-size: 11px;
  cursor: pointer;
}

.kp-stats { padding: 4px 12px; font-size: 11px; color: var(--srn-color-text-3); display: flex; gap: 6px; align-items: center; border-bottom: 1px solid var(--srn-color-border); }
.sep { color: #ddd; }

.kp-list { flex: 1; overflow-y: auto; }
.key-item {
  display: flex; align-items: center; gap: 8px; padding: 7px 12px;
  cursor: pointer; transition: background var(--srn-motion-fast);
  border-left: 3px solid transparent;
}
.key-item:hover { background: rgba(0,0,0,0.02); }
.key-item.active { background: rgba(220,56,45,0.06); border-left-color: var(--srn-color-primary); }
.key-item.multi-selected { background: rgba(0,122,255,0.08); border-left-color: #007aff; }
.key-item.multi-selected.active { background: rgba(0,122,255,0.14); }
.key-type-badge {
  font-size: 9px; font-weight: 700; text-transform: uppercase; font-family: var(--srn-font-mono);
  padding: 2px 6px; border-radius: 3px; flex-shrink: 0; letter-spacing: 0.3px;
}
.key-name { flex: 1; font-size: 12px; font-family: var(--srn-font-mono); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.key-ttl { font-size: 11px; color: var(--srn-color-text-3); flex-shrink: 0; }
.key-size { font-size: 11px; color: var(--srn-color-text-3); font-family: var(--srn-font-mono); flex-shrink: 0; }

.kp-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 0; color: var(--srn-color-text-3); }
.kp-empty i { font-size: 40px; margin-bottom: 8px; }
.kp-empty p { font-size: 12px; }

@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }

.slide-enter-active, .slide-leave-active { transition: all 0.2s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
