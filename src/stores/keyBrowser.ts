import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { KeyMeta, KeyType } from '@/types/data';
import { keysScan } from '@/ipc/data';
import { useConnectionStore } from './connection';

export const useKeyBrowserStore = defineStore('keyBrowser', () => {
  // State
  const keys = ref<KeyMeta[]>([]);
  const cursorStack = ref<number[]>([0]); // stack of cursors for back navigation
  const currentCursor = ref<number>(0);
  const nextCursor = ref<number>(0);
  const pattern = ref<string>('');
  const typeFilter = ref<KeyType | ''>('');
  const selectedKey = ref<string | null>(null);
  const loading = ref<boolean>(false);
  const totalScanned = ref<number>(0);
  const allKeysLoaded = ref<boolean>(false);
  // Multi-select state for bulk operations
  const selectedKeys = ref<Set<string>>(new Set());
  const lastSelectedKey = ref<string | null>(null);

  // Computed
  const filteredKeys = computed(() => {
    if (!typeFilter.value) return keys.value;
    return keys.value.filter(k => k.key_type === typeFilter.value);
  });

  const hasPrev = computed(() => cursorStack.value.length > 1);
  const hasNext = computed(() => nextCursor.value !== 0);
  const currentPage = computed(() => cursorStack.value.length);

  // Actions
  async function scan(cursor = 0) {
    const connStore = useConnectionStore();
    if (!connStore.activeConnId) return;

    loading.value = true;
    try {
      const page = await keysScan(connStore.activeConnId, cursor, pattern.value);
      keys.value = page.keys;
      nextCursor.value = page.cursor;
      totalScanned.value = page.total_scanned;
      currentCursor.value = cursor;
      allKeysLoaded.value = page.cursor === 0;
    } finally {
      loading.value = false;
    }
  }

  /// Append next batch of keys (for infinite scroll / virtual scroll)
  async function loadMore() {
    if (!hasNext.value || loading.value) return;
    const connStore = useConnectionStore();
    if (!connStore.activeConnId) return;

    loading.value = true;
    try {
      const page = await keysScan(connStore.activeConnId, nextCursor.value, pattern.value);
      // Append new keys, dedup by key name
      const existingKeys = new Set(keys.value.map(k => k.key));
      const newKeys = page.keys.filter(k => !existingKeys.has(k.key));
      keys.value = [...keys.value, ...newKeys];
      nextCursor.value = page.cursor;
      totalScanned.value += page.total_scanned;
      cursorStack.value.push(page.cursor);
      allKeysLoaded.value = page.cursor === 0;
    } finally {
      loading.value = false;
    }
  }

  async function nextPage() {
    if (!hasNext.value) return;
    cursorStack.value.push(nextCursor.value);
    await scan(nextCursor.value);
  }

  async function prevPage() {
    if (!hasPrev.value) return;
    cursorStack.value.pop();
    const cursor = cursorStack.value[cursorStack.value.length - 1];
    await scan(cursor);
  }

  async function refresh() {
    cursorStack.value = [0];
    allKeysLoaded.value = false;
    await scan(0);
  }

  function setPattern(p: string) {
    pattern.value = p;
  }

  function setTypeFilter(t: KeyType | '') {
    typeFilter.value = t;
  }

  function selectKey(key: string | null) {
    selectedKey.value = key;
  }

  /// Toggle a key's selection (⌘+click). Also updates lastSelectedKey anchor.
  function toggleSelect(key: string) {
    const next = new Set(selectedKeys.value);
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
    }
    selectedKeys.value = next;
    lastSelectedKey.value = key;
  }

  /// Range-select between the last selected key and the given key (Shift+click).
  /// If no anchor exists yet, behaves like toggleSelect.
  function rangeSelect(key: string) {
    const list = filteredKeys.value;
    const anchor = lastSelectedKey.value;
    const targetIdx = list.findIndex((k) => k.key === key);
    if (targetIdx < 0) return;
    if (!anchor) {
      toggleSelect(key);
      return;
    }
    const anchorIdx = list.findIndex((k) => k.key === anchor);
    if (anchorIdx < 0) {
      toggleSelect(key);
      return;
    }
    const [from, to] = anchorIdx < targetIdx ? [anchorIdx, targetIdx] : [targetIdx, anchorIdx];
    const next = new Set(selectedKeys.value);
    for (let i = from; i <= to; i++) {
      next.add(list[i].key);
    }
    selectedKeys.value = next;
    lastSelectedKey.value = key;
  }

  /// Select all currently loaded (filtered) keys.
  function selectAll() {
    const next = new Set<string>();
    for (const k of filteredKeys.value) {
      next.add(k.key);
    }
    selectedKeys.value = next;
    if (filteredKeys.value.length > 0) {
      lastSelectedKey.value = filteredKeys.value[filteredKeys.value.length - 1].key;
    }
  }

  /// Clear all multi-selection state.
  function clearSelection() {
    selectedKeys.value = new Set();
    lastSelectedKey.value = null;
  }

  /// Scroll to a specific key by name (for search result navigation)
  function getKeyIndex(keyName: string): number {
    return filteredKeys.value.findIndex(k => k.key === keyName);
  }

  function reset() {
    keys.value = [];
    cursorStack.value = [0];
    currentCursor.value = 0;
    nextCursor.value = 0;
    pattern.value = '';
    typeFilter.value = '';
    selectedKey.value = null;
    totalScanned.value = 0;
    allKeysLoaded.value = false;
    selectedKeys.value = new Set();
    lastSelectedKey.value = null;
  }

  return {
    keys,
    cursorStack,
    currentCursor,
    nextCursor,
    pattern,
    typeFilter,
    selectedKey,
    loading,
    totalScanned,
    allKeysLoaded,
    selectedKeys,
    lastSelectedKey,
    filteredKeys,
    hasPrev,
    hasNext,
    currentPage,
    scan,
    loadMore,
    nextPage,
    prevPage,
    refresh,
    setPattern,
    setTypeFilter,
    selectKey,
    toggleSelect,
    rangeSelect,
    selectAll,
    clearSelection,
    getKeyIndex,
    reset,
  };
});
