import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { KeyDetail } from '@/types/data';
import { keyGet, keySet, keyDelete, keyRename, keyTtlSet } from '@/ipc/data';
import { useConnectionStore } from './connection';

export const useDataStore = defineStore('data', () => {
  // State
  const currentKey = ref<KeyDetail | null>(null);
  const loading = ref<boolean>(false);
  const editingField = ref<string | null>(null); // for hash/list/set/zset inline edit

  // Actions
  async function loadKey(key: string) {
    const connStore = useConnectionStore();
    if (!connStore.activeConnId) return;

    loading.value = true;
    try {
      currentKey.value = await keyGet(connStore.activeConnId, key);
    } finally {
      loading.value = false;
    }
  }

  async function createKey(key: string, value: unknown, keyType: string) {
    const connStore = useConnectionStore();
    if (!connStore.activeConnId) return;
    await keySet(connStore.activeConnId, key, value, keyType);
  }

  async function updateKey(key: string, value: unknown, keyType: string) {
    const connStore = useConnectionStore();
    if (!connStore.activeConnId) return;
    await keySet(connStore.activeConnId, key, value, keyType);
    // Reload
    await loadKey(key);
  }

  async function deleteKey(key: string) {
    const connStore = useConnectionStore();
    if (!connStore.activeConnId) return;
    await keyDelete(connStore.activeConnId, key);
    if (currentKey.value?.key === key) {
      currentKey.value = null;
    }
  }

  async function renameKey(oldKey: string, newKey: string) {
    const connStore = useConnectionStore();
    if (!connStore.activeConnId) return;
    await keyRename(connStore.activeConnId, oldKey, newKey);
    await loadKey(newKey);
  }

  async function setTtl(key: string, ttlSeconds: number) {
    const connStore = useConnectionStore();
    if (!connStore.activeConnId) return;
    await keyTtlSet(connStore.activeConnId, key, ttlSeconds);
    await loadKey(key);
  }

  function setEditingField(field: string | null) {
    editingField.value = field;
  }

  function clearCurrentKey() {
    currentKey.value = null;
  }

  return {
    currentKey,
    loading,
    editingField,
    loadKey,
    createKey,
    updateKey,
    deleteKey,
    renameKey,
    setTtl,
    setEditingField,
    clearCurrentKey,
  };
});
