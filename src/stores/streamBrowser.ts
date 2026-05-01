import { defineStore } from 'pinia';
import { ref } from 'vue';
import {
  streamRange,
  streamRevRange,
  streamAdd,
  streamDel,
  streamGroups,
  streamPending,
  streamInfo,
} from '@/ipc/phase3';
import type { StreamEntry, StreamGroup, PendingEntry } from '@/types/phase3';

export const useStreamBrowserStore = defineStore('streamBrowser', () => {
  // Entries
  const entries = ref<StreamEntry[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Pagination
  const startId = ref('-');
  const endId = ref('+');
  const count = ref(50);
  const reverse = ref(false);

  // Consumer Groups
  const groups = ref<StreamGroup[]>([]);
  const groupsLoading = ref(false);

  // Pending entries per group
  const pendingMap = ref<Record<string, PendingEntry[]>>({});
  const pendingLoading = ref<Record<string, boolean>>({});

  // Stream meta
  const streamLength = ref(0);
  const lastId = ref('');
  const radixNodes = ref(0);
  const radixLevels = ref(0);
  const maxLength = ref(0);
  const firstEntryId = ref('');
  const groupsCount = ref(0);

  // Info loading state
  const infoLoading = ref(false);

  async function loadEntries(connId: string, key: string) {
    loading.value = true;
    error.value = null;
    try {
      const fn = reverse.value ? streamRevRange : streamRange;
      entries.value = await fn(connId, key, startId.value, endId.value, count.value);
    } catch (e: any) {
      error.value = e?.message ?? String(e);
    } finally {
      loading.value = false;
    }
  }

  async function loadInfo(connId: string, key: string) {
    infoLoading.value = true;
    try {
      const info = await streamInfo(connId, key);
      streamLength.value = info.length;
      radixNodes.value = info.radix_nodes;
      radixLevels.value = info.radix_levels;
      lastId.value = info.last_id;
      maxLength.value = info.max_length;
      groupsCount.value = info.groups;
      firstEntryId.value = info.first_entry_id;
    } catch (e: any) {
      console.error('Failed to load stream info:', e);
    } finally {
      infoLoading.value = false;
    }
  }

  async function loadGroups(connId: string, key: string) {
    groupsLoading.value = true;
    try {
      groups.value = await streamGroups(connId, key);
      groupsCount.value = groups.value.length;
    } catch (e: any) {
      console.error('Failed to load groups:', e);
    } finally {
      groupsLoading.value = false;
    }
  }

  async function loadPending(connId: string, key: string, group: string) {
    pendingLoading.value[group] = true;
    try {
      const result = await streamPending(connId, key, group);
      pendingMap.value[group] = result;
    } catch (e: any) {
      console.error('Failed to load pending:', e);
    } finally {
      pendingLoading.value[group] = false;
    }
  }

  async function addEntry(connId: string, key: string, fields: [string, string][], id?: string, maxlen?: number) {
    const resultId = await streamAdd(connId, key, fields, id, maxlen);
    await loadEntries(connId, key);
    return resultId;
  }

  async function deleteEntries(connId: string, key: string, ids: string[]) {
    await streamDel(connId, key, ids);
    await loadEntries(connId, key);
  }

  function reset() {
    entries.value = [];
    groups.value = [];
    pendingMap.value = {};
    streamLength.value = 0;
    lastId.value = '';
    radixNodes.value = 0;
    radixLevels.value = 0;
    maxLength.value = 0;
    firstEntryId.value = '';
    groupsCount.value = 0;
    infoLoading.value = false;
    error.value = null;
  }

  return {
    entries,
    loading,
    error,
    startId,
    endId,
    count,
    reverse,
    groups,
    groupsLoading,
    pendingMap,
    pendingLoading,
    streamLength,
    lastId,
    radixNodes,
    radixLevels,
    maxLength,
    firstEntryId,
    groupsCount,
    infoLoading,
    loadEntries,
    loadGroups,
    loadPending,
    loadInfo,
    addEntry,
    deleteEntries,
    reset,
  };
});
