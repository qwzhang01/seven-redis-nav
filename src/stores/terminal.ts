import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { CliHistoryEntry } from '@/types/terminal';
import { cliExec, cliHistoryGet } from '@/ipc/terminal';
import { cliHistoryGetTab } from '@/ipc/phase4';
import { useConnectionStore } from './connection';
import * as ipc from '@/ipc/phase4';

export interface OutputLine {
  id: number;
  prompt: string;
  command: string;
  output: string;
  isError: boolean;
}

export interface CliTabState {
  tabId: string;
  name: string;
  db: number;
  isConnected: boolean;
  outputLines: OutputLine[];
  history: CliHistoryEntry[];
  historyIndex: number;
  currentInput: string;
  loading: boolean;
}

let lineIdCounter = 0;

export const useTerminalStore = defineStore('terminal', () => {
  // ─── Legacy single-tab state (backward compatible) ───────────────────
  const outputLines = ref<OutputLine[]>([]);
  const history = ref<CliHistoryEntry[]>([]);
  const historyIndex = ref<number>(-1);
  const currentInput = ref<string>('');
  const loading = ref<boolean>(false);

  // ─── Multi-tab state ─────────────────────────────────────────────────
  const tabs = ref<Map<string, CliTabState>>(new Map());
  const activeTabId = ref<string | null>(null);
  const MAX_TABS = 8;

  const tabList = computed(() => Array.from(tabs.value.values()));
  const activeTab = computed(() => activeTabId.value ? tabs.value.get(activeTabId.value) ?? null : null);
  const canAddTab = computed(() => tabs.value.size < MAX_TABS);

  // ─── Multi-tab actions ───────────────────────────────────────────────
  async function createTab(connId: string): Promise<string> {
    if (!canAddTab.value) throw new Error(`最多支持 ${MAX_TABS} 个终端标签页`);
    const info = await ipc.cliTabCreate(connId);

    // Load persistent history from SQLite for this tab
    let persistedHistory: CliHistoryEntry[] = [];
    try {
      const cmds = await cliHistoryGetTab(info.tab_id);
      persistedHistory = cmds.map((cmd, i) => ({
        id: Date.now() + i,
        command: cmd,
        created_at: new Date().toISOString(),
      }));
    } catch { /* ignore if history not available */ }

    const state: CliTabState = {
      tabId: info.tab_id,
      name: info.name,
      db: info.db,
      isConnected: info.is_connected,
      outputLines: [],
      history: persistedHistory,
      historyIndex: -1,
      currentInput: '',
      loading: false,
    };
    tabs.value.set(info.tab_id, state);
    activeTabId.value = info.tab_id;
    return info.tab_id;
  }

  async function closeTab(tabId: string) {
    if (tabs.value.size <= 1) return; // Cannot close last tab
    await ipc.cliTabClose(tabId);
    tabs.value.delete(tabId);
    if (activeTabId.value === tabId) {
      activeTabId.value = tabList.value[0]?.tabId ?? null;
    }
  }

  function switchTab(tabId: string) {
    if (tabs.value.has(tabId)) activeTabId.value = tabId;
  }

  function renameTab(tabId: string, name: string) {
    const tab = tabs.value.get(tabId);
    if (tab) tab.name = name;
  }

  async function executeInTab(tabId: string, command: string, confirmToken?: string) {
    const tab = tabs.value.get(tabId);
    if (!tab) return;
    const connStore = useConnectionStore();
    const trimmed = command.trim();
    if (!trimmed) return;

    if (trimmed.toUpperCase() === 'CLEAR') {
      tab.outputLines = [];
      return;
    }

    tab.loading = true;
    const prompt = `${connStore.activeConnection?.host ?? ''}:${connStore.activeConnection?.port ?? 6379}[${tab.db}]>`;

    try {
      const reply = await ipc.cliExecTab(tabId, trimmed, confirmToken);
      tab.outputLines.push({
        id: lineIdCounter++,
        prompt,
        command: trimmed,
        output: reply.output,
        isError: reply.is_error,
      });
      // History is persisted to SQLite by the backend; update in-memory list too
      tab.history.unshift({ id: Date.now(), command: trimmed, created_at: new Date().toISOString() });
      tab.historyIndex = -1;
    } finally {
      tab.loading = false;
    }
  }

  function onTabDisconnected(tabId: string) {
    const tab = tabs.value.get(tabId);
    if (tab) {
      tab.isConnected = false;
      tab.name = tab.name.replace(' (已断开)', '') + ' (已断开)';
    }
  }

  // ─── Legacy single-tab actions (backward compatible) ─────────────────
  async function loadHistory() {
    history.value = await cliHistoryGet();
    historyIndex.value = -1;
  }

  async function execute(command: string, confirmToken?: string) {
    const connStore = useConnectionStore();
    if (!connStore.activeConnId) return;

    const trimmed = command.trim();
    if (!trimmed) return;

    if (trimmed.toUpperCase() === 'CLEAR') {
      outputLines.value = [];
      return;
    }

    loading.value = true;
    const prompt = `${connStore.activeConnection?.host ?? ''}:${connStore.activeConnection?.port ?? 6379}[${connStore.currentDb}]>`;

    try {
      const reply = await cliExec(connStore.activeConnId, trimmed, confirmToken);
      outputLines.value.push({
        id: lineIdCounter++,
        prompt,
        command: trimmed,
        output: reply.output,
        isError: reply.is_error,
      });
      history.value.unshift({
        id: Date.now(),
        command: trimmed,
        created_at: new Date().toISOString(),
      });
      historyIndex.value = -1;
    } finally {
      loading.value = false;
    }
  }

  function navigateHistory(direction: 'up' | 'down') {
    if (history.value.length === 0) return;

    if (direction === 'up') {
      historyIndex.value = Math.min(historyIndex.value + 1, history.value.length - 1);
    } else {
      historyIndex.value = Math.max(historyIndex.value - 1, -1);
    }

    if (historyIndex.value === -1) {
      currentInput.value = '';
    } else {
      currentInput.value = history.value[historyIndex.value]?.command ?? '';
    }
  }

  function clearOutput() {
    outputLines.value = [];
  }

  function setInput(val: string) {
    currentInput.value = val;
    historyIndex.value = -1;
  }

  return {
    // Legacy
    outputLines, history, historyIndex, currentInput, loading,
    loadHistory, execute, navigateHistory, clearOutput, setInput,
    // Multi-tab
    tabs, activeTabId, tabList, activeTab, canAddTab,
    createTab, closeTab, switchTab, renameTab, executeInTab, onTabDisconnected,
  };
});
