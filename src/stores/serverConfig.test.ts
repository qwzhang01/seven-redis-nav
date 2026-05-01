import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useServerConfigStore } from './serverConfig';
import { useConnectionStore } from './connection';
import { configGetAll, configSet, serverInfo } from '@/ipc/phase2';

vi.mock('@/ipc/phase2', () => ({
  configGetAll: vi.fn(),
  configSet: vi.fn(),
  serverInfo: vi.fn(),
}));

vi.mock('./connection', () => ({
  useConnectionStore: vi.fn(),
}));

describe('ServerConfig Store', () => {
  let store: ReturnType<typeof useServerConfigStore>;
  let connMock: any;

  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    connMock = { activeConnId: 'conn-1' };
    (useConnectionStore as any).mockReturnValue(connMock);
    store = useServerConfigStore();
  });

  describe('初始状态', () => {
    it('应该具有正确的默认值', () => {
      expect(store.configs).toEqual([]);
      expect(store.info).toBe(null);
      expect(store.loading).toBe(false);
      expect(store.infoLoading).toBe(false);
      expect(store.searchKeyword).toBe('');
      expect(store.selectedGroup).toBe('');
    });
  });

  describe('fetchConfigs', () => {
    it('应该从 IPC 加载配置', async () => {
      const mockConfigs = [
        { key: 'maxmemory', value: '100mb' },
        { key: 'port', value: '6379' },
      ];
      (configGetAll as any).mockResolvedValue(mockConfigs);

      await store.fetchConfigs();

      expect(configGetAll).toHaveBeenCalledWith('conn-1');
      expect(store.configs).toEqual(mockConfigs);
      expect(store.loading).toBe(false);
    });

    it('没有活动连接时应该不执行', async () => {
      connMock.activeConnId = null;
      await store.fetchConfigs();
      expect(configGetAll).not.toHaveBeenCalled();
    });

    it('IPC 抛错应该重置 loading', async () => {
      (configGetAll as any).mockRejectedValue(new Error('IPC error'));
      await store.fetchConfigs();
      expect(store.loading).toBe(false);
    });
  });

  describe('fetchInfo', () => {
    it('应该从 IPC 加载服务器信息', async () => {
      const mockInfo = {
        redis_version: '7.0.0',
        uptime_secs: 100,
        connected_clients: 5,
        used_memory: 1024,
        max_memory: 2048,
        hit_rate: 0.9,
        total_keys: 1000,
        ops_per_sec: 500,
      };
      (serverInfo as any).mockResolvedValue(mockInfo);

      await store.fetchInfo();

      expect(serverInfo).toHaveBeenCalledWith('conn-1');
      expect(store.info).toEqual(mockInfo);
      expect(store.infoLoading).toBe(false);
    });

    it('没有活动连接时应该不执行', async () => {
      connMock.activeConnId = null;
      await store.fetchInfo();
      expect(serverInfo).not.toHaveBeenCalled();
    });
  });

  describe('updateConfig', () => {
    it('应该调用 IPC 并更新本地状态', async () => {
      (configGetAll as any).mockResolvedValue([
        { key: 'maxmemory', value: '100mb' },
      ]);
      await store.fetchConfigs();

      (configSet as any).mockResolvedValue(undefined);
      const result = await store.updateConfig('maxmemory', '200mb');

      expect(configSet).toHaveBeenCalledWith('conn-1', 'maxmemory', '200mb');
      expect(result).toBe(true);
      expect(store.configs.find(c => c.key === 'maxmemory')?.value).toBe('200mb');
    });

    it('IPC 抛错应该返回 false', async () => {
      (configSet as any).mockRejectedValue(new Error('fail'));
      const result = await store.updateConfig('maxmemory', '200mb');
      expect(result).toBe(false);
    });

    it('没有活动连接时应该返回 false', async () => {
      connMock.activeConnId = null;
      const result = await store.updateConfig('maxmemory', '200mb');
      expect(result).toBe(false);
    });
  });

  describe('isReadOnly', () => {
    it('只读参数返回 true', () => {
      expect(store.isReadOnly('port')).toBe(true);
      expect(store.isReadOnly('bind')).toBe(true);
      expect(store.isReadOnly('cluster-enabled')).toBe(true);
    });

    it('可写参数返回 false', () => {
      expect(store.isReadOnly('maxmemory')).toBe(false);
      expect(store.isReadOnly('requirepass')).toBe(false);
      expect(store.isReadOnly('save')).toBe(false);
    });
  });

  describe('分组与过滤', () => {
    beforeEach(async () => {
      (configGetAll as any).mockResolvedValue([
        { key: 'port', value: '6379' },
        { key: 'maxmemory', value: '100mb' },
        { key: 'requirepass', value: 'secret' },
        { key: 'save', value: '900 1' },
      ]);
      await store.fetchConfigs();
    });

    it('groups 应按预定义分组归类', () => {
      const groups = store.groups;
      expect(groups.has('Network')).toBe(true);
      expect(groups.has('Memory')).toBe(true);
      expect(groups.has('Security')).toBe(true);
      expect(groups.has('Persistence')).toBe(true);
    });

    it('filteredConfigs 按 searchKeyword 过滤', () => {
      expect(store.filteredConfigs).toHaveLength(4);
      store.searchKeyword = 'max';
      expect(store.filteredConfigs).toHaveLength(1);
      expect(store.filteredConfigs[0].key).toBe('maxmemory');
    });

    it('filteredConfigs 按 selectedGroup 过滤', () => {
      store.selectedGroup = 'Memory';
      const filtered = store.filteredConfigs;
      expect(filtered.every(c => ['maxmemory'].includes(c.key))).toBe(true);
    });

    it('groupNames 返回排序后分组名', () => {
      const names = store.groupNames;
      expect(names).toContain('Memory');
      expect(names).toContain('Network');
      expect(names).toContain('Security');
      expect(names).toContain('Persistence');
    });
  });
});
