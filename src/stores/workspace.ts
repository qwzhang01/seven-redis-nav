import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useConnectionStore } from './connection';

export type WorkspaceTab = 'browser' | 'cli' | 'monitor' | 'slowlog' | 'pubsub' | 'config' | 'lua' | 'tools';

export const useWorkspaceStore = defineStore('workspace', () => {
  const activeTab = ref<WorkspaceTab>('browser');

  // connected state is now driven by connection store
  const connected = computed(() => {
    const connStore = useConnectionStore();
    return connStore.isConnected;
  });

  function setActiveTab(tab: WorkspaceTab) {
    activeTab.value = tab;
  }

  // Keep setConnected for backward compatibility (no-op now)
  function setConnected(_val: boolean) {
    // noop: driven by connection store
  }

  return { activeTab, connected, setActiveTab, setConnected };
});
