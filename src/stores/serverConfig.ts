import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useConnectionStore } from './connection';
import { configGetAll, configSet, serverInfo } from '@/ipc/phase2';
import type { ServerConfigItem, ServerInfo } from '@/types/phase2';

// Config parameter group mapping (9 built-in categories)
const GROUP_MAP: Record<string, string[]> = {
  'Memory': ['maxmemory', 'maxmemory-policy', 'maxmemory-samples', 'lazyfree-lazy-eviction', 'lazyfree-lazy-expire', 'lazyfree-lazy-server-del', 'activedefrag', 'active-defrag-threshold-lower', 'active-defrag-threshold-upper', 'active-defrag-cycle-min', 'active-defrag-cycle-max', 'hash-max-ziplist-entries', 'hash-max-ziplist-value', 'list-max-ziplist-size', 'list-compress-depth', 'set-max-intset-entries', 'zset-max-ziplist-entries', 'zset-max-ziplist-value', 'hll-sparse-max-bytes', 'stream-node-max-bytes', 'stream-node-max-entries'],
  'Persistence': ['save', 'stop-writes-on-bgsave-error', 'rdbcompression', 'rdbchecksum', 'dbfilename', 'dir', 'appendonly', 'appendfilename', 'appendfsync', 'no-appendfsync-on-rewrite', 'auto-aof-rewrite-percentage', 'auto-aof-rewrite-min-size', 'aof-load-truncated', 'aof-use-rdb-preamble'],
  'Replication': ['slaveof', 'replicaof', 'masterauth', 'slave-serve-stale-data', 'replica-serve-stale-data', 'slave-read-only', 'replica-read-only', 'repl-diskless-sync', 'repl-diskless-sync-delay', 'repl-ping-slave-period', 'repl-timeout', 'repl-backlog-size', 'repl-backlog-ttl', 'slave-priority', 'replica-priority', 'min-slaves-to-write', 'min-replicas-to-write', 'min-slaves-max-lag', 'min-replicas-max-lag'],
  'Security': ['requirepass', 'rename-command', 'protected-mode'],
  'Network': ['bind', 'port', 'tcp-backlog', 'unixsocket', 'timeout', 'tcp-keepalive', 'notify-keyspace-events'],
  'Clients': ['maxclients'],
  'Slowlog': ['slowlog-log-slower-than', 'slowlog-max-len'],
  'Advanced': ['lua-time-limit', 'loglevel', 'logfile', 'databases', 'always-show-logo', 'daemonize', 'pidfile', 'syslog-enabled', 'syslog-ident', 'syslog-facility'],
  'Cluster': ['cluster-enabled', 'cluster-config-file', 'cluster-node-timeout', 'cluster-migration-barrier', 'cluster-require-full-coverage', 'cluster-announce-ip'],
};

// Known read-only parameters
const READ_ONLY_PARAMS = new Set([
  'bind', 'port', 'unixsocket', 'daemonize', 'pidfile', 'logfile',
  'databases', 'always-show-logo', 'cluster-enabled', 'cluster-config-file',
]);

// Dangerous parameters that require extra confirmation
export const DANGEROUS_PARAMS = new Set([
  'bind', 'protected-mode', 'requirepass', 'masterauth',
  'cluster-announce-ip', 'rename-command',
]);

export interface ConfigDiff {
  key: string;
  oldValue: string;
  newValue: string;
}

function getGroup(key: string): string {
  for (const [group, keys] of Object.entries(GROUP_MAP)) {
    if (keys.includes(key)) return group;
  }
  return 'Other';
}

export const useServerConfigStore = defineStore('serverConfig', () => {
  const configs = ref<ServerConfigItem[]>([]);
  const info = ref<ServerInfo | null>(null);
  const loading = ref(false);
  const infoLoading = ref(false);
  const searchKeyword = ref('');
  const selectedGroup = ref('');

  // Diff tracking: store original values when configs are first loaded
  const originalValues = ref<Map<string, string>>(new Map());

  async function fetchConfigs() {
    const connStore = useConnectionStore();
    if (!connStore.activeConnId) return;

    loading.value = true;
    try {
      configs.value = await configGetAll(connStore.activeConnId);
      // Snapshot original values on first load (or refresh = reset snapshot)
      originalValues.value.clear();
      for (const item of configs.value) {
        originalValues.value.set(item.key, item.value);
      }
    } catch (e) {
      console.error('Failed to fetch configs:', e);
    } finally {
      loading.value = false;
    }
  }

  async function fetchInfo() {
    const connStore = useConnectionStore();
    if (!connStore.activeConnId) return;

    infoLoading.value = true;
    try {
      info.value = await serverInfo(connStore.activeConnId);
    } catch (e) {
      console.error('Failed to fetch server info:', e);
    } finally {
      infoLoading.value = false;
    }
  }

  async function updateConfig(key: string, value: string): Promise<boolean> {
    const connStore = useConnectionStore();
    if (!connStore.activeConnId) return false;

    try {
      await configSet(connStore.activeConnId, key, value);
      // Update local state
      const item = configs.value.find((c) => c.key === key);
      if (item) item.value = value;
      return true;
    } catch (e) {
      console.error('Failed to set config:', e);
      return false;
    }
  }

  function isReadOnly(key: string): boolean {
    return READ_ONLY_PARAMS.has(key);
  }

  function isDangerous(key: string): boolean {
    return DANGEROUS_PARAMS.has(key);
  }

  function revertDiff(key: string) {
    const original = originalValues.value.get(key);
    if (original !== undefined) {
      const item = configs.value.find((c) => c.key === key);
      if (item) item.value = original;
    }
  }

  const diffs = computed<ConfigDiff[]>(() => {
    const result: ConfigDiff[] = [];
    for (const item of configs.value) {
      const original = originalValues.value.get(item.key);
      if (original !== undefined && original !== item.value) {
        result.push({ key: item.key, oldValue: original, newValue: item.value });
      }
    }
    return result;
  });

  const diffCount = computed(() => diffs.value.length);

  const groups = computed(() => {
    const groupMap = new Map<string, ServerConfigItem[]>();
    for (const item of configs.value) {
      const group = getGroup(item.key);
      if (!groupMap.has(group)) groupMap.set(group, []);
      groupMap.get(group)!.push(item);
    }
    return groupMap;
  });

  const filteredConfigs = computed(() => {
    let items = configs.value;

    if (selectedGroup.value) {
      items = items.filter((item) => getGroup(item.key) === selectedGroup.value);
    }

    if (searchKeyword.value) {
      const kw = searchKeyword.value.toLowerCase();
      items = items.filter(
        (item) =>
          item.key.toLowerCase().includes(kw) ||
          item.value.toLowerCase().includes(kw),
      );
    }

    return items;
  });

  const groupNames = computed(() => {
    const names = new Set<string>();
    for (const item of configs.value) {
      names.add(getGroup(item.key));
    }
    return Array.from(names).sort();
  });

  return {
    configs,
    info,
    loading,
    infoLoading,
    searchKeyword,
    selectedGroup,
    groups,
    filteredConfigs,
    groupNames,
    originalValues,
    diffs,
    diffCount,
    fetchConfigs,
    fetchInfo,
    updateConfig,
    isReadOnly,
    isDangerous,
    revertDiff,
  };
});
