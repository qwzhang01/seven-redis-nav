import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useSlowlogStore } from './slowlog';
import { useConnectionStore } from './connection';
import { slowlogGet, slowlogReset } from '@/ipc/phase2';

vi.mock('@/ipc/phase2', () => ({
  slowlogGet: vi.fn(),
  slowlogReset: vi.fn(),
}));

vi.mock('./connection', () => ({
  useConnectionStore: vi.fn(),
}));

describe('Slowlog Store', () => {
  let store: ReturnType<typeof useSlowlogStore>;
  let connMock: any;

  const mockEntries = [
    { id: 0, timestamp: 1000, duration_us: 500, command: ['GET', 'key1'], client_addr: '127.0.0.1', client_name: '' },
    { id: 1, timestamp: 2000, duration_us: 1000, command: ['SET', 'key2', 'val'], client_addr: '127.0.0.1', client_name: '' },
    { id: 2, timestamp: 3000, duration_us: 200, command: ['HGETALL', 'hash1'], client_addr: '10.0.0.1', client_name: 'app' },
  ];

  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.useFakeTimers();
    connMock = { activeConnId: 'conn-1' };
    (useConnectionStore as any).mockReturnValue(connMock);
    store = useSlowlogStore();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('初始状态', () => {
    it('应该具有正确的默认值', () => {
      expect(store.entries).toEqual([]);
      expect(store.loading).toBe(false);
      expect(store.sortField).toBe('duration_us');
      expect(store.sortOrder).toBe('desc');
      expect(store.autoRefresh).toBe(false);
      expect(store.autoRefreshInterval).toBe(5);
      expect(store.entryCount).toBe(128);
    });
  });

  describe('fetchEntries', () => {
    it('应该从 IPC 加载慢查询日志', async () => {
      (slowlogGet as any).mockResolvedValue(mockEntries);

      await store.fetchEntries();

      expect(slowlogGet).toHaveBeenCalledWith('conn-1', 128);
      expect(store.entries).toEqual(mockEntries);
      expect(store.loading).toBe(false);
    });

    it('没有活动连接时应该不执行', async () => {
      connMock.activeConnId = null;
      await store.fetchEntries();
      expect(slowlogGet).not.toHaveBeenCalled();
    });

    it('IPC 抛错应该重置 loading', async () => {
      (slowlogGet as any).mockRejectedValue(new Error('fail'));
      await store.fetchEntries();
      expect(store.loading).toBe(false);
    });
  });

  describe('resetSlowlog', () => {
    it('应该清空慢查询日志', async () => {
      (slowlogReset as any).mockResolvedValue(undefined);
      (slowlogGet as any).mockResolvedValue(mockEntries);
      await store.fetchEntries();
      expect(store.entries).toHaveLength(3);

      await store.resetSlowlog();
      expect(slowlogReset).toHaveBeenCalledWith('conn-1');
      expect(store.entries).toEqual([]);
    });

    it('没有活动连接时不执行', async () => {
      connMock.activeConnId = null;
      await store.resetSlowlog();
      expect(slowlogReset).not.toHaveBeenCalled();
    });
  });

  describe('setSort', () => {
    it('同一字段应切换排序方向', () => {
      // 初始 sortField='duration_us', sortOrder='desc'
      store.setSort('duration_us');  // 同一字段 → toggle to asc
      expect(store.sortField).toBe('duration_us');
      expect(store.sortOrder).toBe('asc');

      store.setSort('duration_us');  // 再次 toggle → desc
      expect(store.sortOrder).toBe('desc');
    });

    it('不同字段应设置降序', () => {
      store.setSort('duration_us');
      store.setSort('timestamp');
      expect(store.sortField).toBe('timestamp');
      expect(store.sortOrder).toBe('desc');
    });

    it('支持 id, timestamp, duration_us', () => {
      store.setSort('id');
      expect(store.sortField).toBe('id');
      store.setSort('timestamp');
      expect(store.sortField).toBe('timestamp');
    });
  });

  describe('sortedEntries', () => {
    beforeEach(async () => {
      (slowlogGet as any).mockResolvedValue(mockEntries);
      await store.fetchEntries();
    });

    it('默认按 duration_us 降序', () => {
      const sorted = store.sortedEntries;
      expect(sorted[0].duration_us).toBe(1000);
      expect(sorted[1].duration_us).toBe(500);
    });

    it('切换为升序后正确排序', () => {
      store.setSort('duration_us'); // toggle: desc → asc
      const sorted = store.sortedEntries;
      expect(sorted[0].duration_us).toBe(200);  // 最小值排第一
    });
    it('按 timestamp 排序', () => {
      store.setSort('timestamp');
      const sorted = store.sortedEntries;
      // desc: 最新(3000)排第一
      expect(sorted[0].timestamp).toBe(3000);
      expect(sorted[2].timestamp).toBe(1000);
    });
  });

  describe('自动刷新', () => {
    it('toggleAutoRefresh 应切换状态', () => {
      store.toggleAutoRefresh();
      expect(store.autoRefresh).toBe(true);

      store.toggleAutoRefresh();
      expect(store.autoRefresh).toBe(false);
    });

    it('startAutoRefresh 应启动定时器', () => {
      (slowlogGet as any).mockResolvedValue(mockEntries);
      store.startAutoRefresh();
      expect(store.autoRefresh).toBe(true);

      // startAutoRefresh 只设置 setInterval，不立即调用 fetchEntries
      vi.advanceTimersByTime(5000);
      expect(slowlogGet).toHaveBeenCalledTimes(1);  // 定时器触发 1 次
    });

    it('stopAutoRefresh 应停止定时器', () => {
      (slowlogGet as any).mockResolvedValue(mockEntries);
      store.startAutoRefresh();
      store.stopAutoRefresh();
      expect(store.autoRefresh).toBe(false);

      vi.advanceTimersByTime(10000);
      // stop 后定时器已清除，不应该有任何调用
      expect(slowlogGet).toHaveBeenCalledTimes(0);
    });
  });
});
