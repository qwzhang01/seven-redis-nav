import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { ConnectionConfig, ConnId, DbStat, ConnectionState, QuickConnectReq } from '@/types/connection';
import {
  connectionList,
  connectionSave,
  connectionDelete,
  connectionOpen,
  connectionClose,
  connectionOpenTemp,
  dbSelect,
} from '@/ipc/connection';
import { listenConnectionState } from '@/ipc/event';
import { serverInfo } from '@/ipc/phase2';

export const useConnectionStore = defineStore('connection', () => {
  // State
  const connections = ref<ConnectionConfig[]>([]);
  const activeConnId = ref<ConnId | null>(null);
  const sessionStates = ref<Record<ConnId, ConnectionState>>({});
  const dbStats = ref<DbStat[]>([]);
  const currentDb = ref<number>(0);
  const serverVersion = ref<string | null>(null);
  const unlistenFn = ref<(() => void) | null>(null);
  const tempConnectionConfig = ref<QuickConnectReq | null>(null);

  // Computed
  const activeConnection = computed(() =>
    connections.value.find(c => c.id === activeConnId.value) ?? null,
  );

  const isConnected = computed(() =>
    activeConnId.value !== null &&
    sessionStates.value[activeConnId.value] === 'connected',
  );

  const isTempConnection = computed(() =>
    activeConnId.value !== null && activeConnId.value.startsWith('temp-'),
  );

  // Actions
  async function loadConnections() {
    connections.value = await connectionList();
  }

  async function saveConnection(config: ConnectionConfig): Promise<ConnId> {
    const id = await connectionSave(config);
    await loadConnections();
    return id;
  }

  async function deleteConnection(connId: ConnId) {
    await connectionDelete(connId);
    if (activeConnId.value === connId) {
      activeConnId.value = null;
    }
    await loadConnections();
  }

  async function openConnection(connId: ConnId) {
    await connectionOpen(connId);
    activeConnId.value = connId;
    sessionStates.value[connId] = 'connected';
    tempConnectionConfig.value = null;

    // Load DB stats
    const stats = await dbSelect(connId, currentDb.value);
    dbStats.value = stats;

    // Fetch Redis server version via INFO server
    try {
      const info = await serverInfo(connId, 'server');
      serverVersion.value = info.redis_version ?? null;
    } catch {
      serverVersion.value = null;
    }
  }

  async function openTempConnection(config: QuickConnectReq) {
    const connId = await connectionOpenTemp(config);
    activeConnId.value = connId;
    sessionStates.value[connId] = 'connected';
    tempConnectionConfig.value = config;

    // Load DB stats
    const stats = await dbSelect(connId, 0);
    dbStats.value = stats;
    currentDb.value = 0;

    // Fetch Redis server version via INFO server
    try {
      const info = await serverInfo(connId, 'server');
      serverVersion.value = info.redis_version ?? null;
    } catch {
      serverVersion.value = null;
    }
  }

  async function saveTempConnection(name: string, groupName: string = ''): Promise<ConnId> {
    if (!tempConnectionConfig.value || !activeConnId.value) {
      throw new Error('No temporary connection to save');
    }

    const config: ConnectionConfig = {
      id: '',
      name,
      group_name: groupName,
      host: tempConnectionConfig.value.host,
      port: tempConnectionConfig.value.port,
      password: tempConnectionConfig.value.password ?? null,
      auth_db: 0,
      timeout_ms: tempConnectionConfig.value.timeout_ms ?? 5000,
      sort_order: 0,
    };

    // Save to SQLite + Keychain
    const newId = await connectionSave(config);
    await loadConnections();

    // Close temp session and open persistent one
    const oldTempId = activeConnId.value;
    await connectionClose(oldTempId);
    delete sessionStates.value[oldTempId];

    await connectionOpen(newId);
    activeConnId.value = newId;
    sessionStates.value[newId] = 'connected';
    tempConnectionConfig.value = null;

    return newId;
  }

  async function closeConnection(connId: ConnId) {
    await connectionClose(connId);
    sessionStates.value[connId] = 'disconnected';
    if (activeConnId.value === connId) {
      activeConnId.value = null;
      dbStats.value = [];
      tempConnectionConfig.value = null;
      serverVersion.value = null;
    }
  }

  async function selectDb(dbIndex: number) {
    if (!activeConnId.value) return;
    const stats = await dbSelect(activeConnId.value, dbIndex);
    dbStats.value = stats;
    currentDb.value = dbIndex;
  }

  async function startListening() {
    if (unlistenFn.value) return;
    unlistenFn.value = await listenConnectionState((event) => {
      sessionStates.value[event.conn_id] = event.state;
      if (event.state === 'disconnected' && event.conn_id === activeConnId.value) {
        dbStats.value = [];
      }
    });
  }

  function stopListening() {
    unlistenFn.value?.();
    unlistenFn.value = null;
  }

  return {
    connections,
    activeConnId,
    sessionStates,
    dbStats,
    currentDb,
    serverVersion,
    unlistenFn,
    tempConnectionConfig,
    activeConnection,
    isConnected,
    isTempConnection,
    loadConnections,
    saveConnection,
    deleteConnection,
    openConnection,
    openTempConnection,
    saveTempConnection,
    closeConnection,
    selectDb,
    startListening,
    stopListening,
  };
});
