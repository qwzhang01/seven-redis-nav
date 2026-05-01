import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useConnectionStore } from './connection';
import { slowlogGet, slowlogReset } from '@/ipc/phase2';
import type { SlowlogEntry } from '@/types/phase2';

export type SortField = 'id' | 'timestamp' | 'duration_us';
export type SortOrder = 'asc' | 'desc';

export const useSlowlogStore = defineStore('slowlog', () => {
  const entries = ref<SlowlogEntry[]>([]);
  const loading = ref(false);
  const sortField = ref<SortField>('duration_us');
  const sortOrder = ref<SortOrder>('desc');
  const autoRefresh = ref(false);
  const autoRefreshInterval = ref(5);
  const entryCount = ref(128);

  let refreshTimer: ReturnType<typeof setInterval> | null = null;

  async function fetchEntries() {
    const connStore = useConnectionStore();
    if (!connStore.activeConnId) return;

    loading.value = true;
    try {
      entries.value = await slowlogGet(connStore.activeConnId, entryCount.value);
    } catch (e) {
      console.error('Failed to fetch slowlog:', e);
    } finally {
      loading.value = false;
    }
  }

  async function resetSlowlog() {
    const connStore = useConnectionStore();
    if (!connStore.activeConnId) return;

    try {
      await slowlogReset(connStore.activeConnId);
      entries.value = [];
    } catch (e) {
      console.error('Failed to reset slowlog:', e);
    }
  }

  function setSort(field: SortField) {
    if (sortField.value === field) {
      sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
    } else {
      sortField.value = field;
      sortOrder.value = 'desc';
    }
  }

  function startAutoRefresh() {
    stopAutoRefresh();
    autoRefresh.value = true;
    refreshTimer = setInterval(() => {
      fetchEntries();
    }, autoRefreshInterval.value * 1000);
  }

  function stopAutoRefresh() {
    autoRefresh.value = false;
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  }

  function toggleAutoRefresh() {
    if (autoRefresh.value) {
      stopAutoRefresh();
    } else {
      startAutoRefresh();
    }
  }

  const sortedEntries = computed(() => {
    const sorted = [...entries.value];
    sorted.sort((a, b) => {
      const aVal = a[sortField.value];
      const bVal = b[sortField.value];
      const diff = Number(aVal) - Number(bVal);
      return sortOrder.value === 'asc' ? diff : -diff;
    });
    return sorted;
  });

  return {
    entries,
    loading,
    sortField,
    sortOrder,
    autoRefresh,
    autoRefreshInterval,
    entryCount,
    sortedEntries,
    fetchEntries,
    resetSlowlog,
    setSort,
    toggleAutoRefresh,
    startAutoRefresh,
    stopAutoRefresh,
  };
});
