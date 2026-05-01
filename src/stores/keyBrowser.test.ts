import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useKeyBrowserStore } from './keyBrowser';
import { useConnectionStore } from './connection';
import { keysScan } from '@/ipc/data';

vi.mock('@/ipc/data', () => ({
  keysScan: vi.fn(),
}));

vi.mock('./connection', () => ({
  useConnectionStore: vi.fn(),
}));

function mkKey(k: string, type: any = 'string') {
  return { key: k, key_type: type, ttl: -1, size: 0 };
}

describe('KeyBrowser Store', () => {
  let store: ReturnType<typeof useKeyBrowserStore>;
  let connMock: any;

  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    connMock = { activeConnId: 'conn-1' };
    (useConnectionStore as any).mockReturnValue(connMock);
    store = useKeyBrowserStore();
  });

  describe('初始状态', () => {
    it('应该具有正确的默认值', () => {
      expect(store.keys).toEqual([]);
      expect(store.cursorStack).toEqual([0]);
      expect(store.currentCursor).toBe(0);
      expect(store.nextCursor).toBe(0);
      expect(store.pattern).toBe('');
      expect(store.typeFilter).toBe('');
      expect(store.selectedKey).toBe(null);
      expect(store.loading).toBe(false);
      expect(store.allKeysLoaded).toBe(false);
      expect(store.selectedKeys.size).toBe(0);
      expect(store.hasPrev).toBe(false);
      expect(store.hasNext).toBe(false);
      expect(store.currentPage).toBe(1);
    });
  });

  describe('scan', () => {
    it('应该从 IPC 拉取一页并写入状态', async () => {
      (keysScan as any).mockResolvedValue({
        keys: [mkKey('a'), mkKey('b')],
        cursor: 10,
        total_scanned: 2,
      });

      await store.scan(0);

      expect(keysScan).toHaveBeenCalledWith('conn-1', 0, '');
      expect(store.keys).toHaveLength(2);
      expect(store.nextCursor).toBe(10);
      expect(store.totalScanned).toBe(2);
      expect(store.allKeysLoaded).toBe(false);
      expect(store.loading).toBe(false);
    });

    it('cursor=0 表示所有键已加载', async () => {
      (keysScan as any).mockResolvedValue({
        keys: [mkKey('a')],
        cursor: 0,
        total_scanned: 1,
      });

      await store.scan(0);
      expect(store.allKeysLoaded).toBe(true);
    });

    it('没有活动连接时应该不执行', async () => {
      connMock.activeConnId = null;
      await store.scan(0);
      expect(keysScan).not.toHaveBeenCalled();
    });

    it('IPC 抛错应该重置 loading', async () => {
      (keysScan as any).mockRejectedValue(new Error('boom'));
      await expect(store.scan(0)).rejects.toThrow('boom');
      expect(store.loading).toBe(false);
    });
  });

  describe('filteredKeys', () => {
    beforeEach(async () => {
      (keysScan as any).mockResolvedValue({
        keys: [mkKey('a', 'string'), mkKey('b', 'hash'), mkKey('c', 'string')],
        cursor: 0,
        total_scanned: 3,
      });
      await store.scan(0);
    });

    it('未设置 typeFilter 时返回全部', () => {
      expect(store.filteredKeys).toHaveLength(3);
    });

    it('设置 typeFilter 后仅返回匹配键', () => {
      store.setTypeFilter('string');
      expect(store.filteredKeys).toHaveLength(2);
      expect(store.filteredKeys.every(k => k.key_type === 'string')).toBe(true);
    });
  });

  describe('loadMore', () => {
    it('应该追加新键并去重', async () => {
      (keysScan as any).mockResolvedValueOnce({
        keys: [mkKey('a'), mkKey('b')],
        cursor: 10,
        total_scanned: 2,
      });
      await store.scan(0);

      (keysScan as any).mockResolvedValueOnce({
        keys: [mkKey('b'), mkKey('c')],
        cursor: 0,
        total_scanned: 2,
      });
      await store.loadMore();

      expect(store.keys.map(k => k.key)).toEqual(['a', 'b', 'c']);
      expect(store.allKeysLoaded).toBe(true);
    });

    it('hasNext 为 false 时应跳过', async () => {
      await store.loadMore();
      expect(keysScan).not.toHaveBeenCalled();
    });
  });

  describe('分页 nextPage / prevPage', () => {
    it('nextPage 应该推入游标栈', async () => {
      (keysScan as any).mockResolvedValue({ keys: [], cursor: 50, total_scanned: 0 });
      await store.scan(0);
      expect(store.hasNext).toBe(true);

      (keysScan as any).mockResolvedValue({ keys: [], cursor: 0, total_scanned: 0 });
      await store.nextPage();
      expect(store.cursorStack).toEqual([0, 50]);
      expect(store.currentPage).toBe(2);
      expect(store.hasPrev).toBe(true);
    });

    it('prevPage 应该弹出游标栈', async () => {
      (keysScan as any).mockResolvedValue({ keys: [], cursor: 50, total_scanned: 0 });
      await store.scan(0);
      await store.nextPage();

      (keysScan as any).mockResolvedValue({ keys: [], cursor: 50, total_scanned: 0 });
      await store.prevPage();
      expect(store.cursorStack).toEqual([0]);
    });

    it('无前页时 prevPage 不做任何事', async () => {
      await store.prevPage();
      expect(keysScan).not.toHaveBeenCalled();
    });
  });

  describe('refresh', () => {
    it('应该重置游标栈并重新扫描', async () => {
      store.cursorStack = [0, 10, 20];
      store.allKeysLoaded = true;
      (keysScan as any).mockResolvedValue({ keys: [], cursor: 0, total_scanned: 0 });
      await store.refresh();
      expect(store.cursorStack).toEqual([0]);
      expect(keysScan).toHaveBeenCalledWith('conn-1', 0, '');
    });
  });

  describe('多选', () => {
    beforeEach(async () => {
      (keysScan as any).mockResolvedValue({
        keys: [mkKey('k1'), mkKey('k2'), mkKey('k3'), mkKey('k4')],
        cursor: 0,
        total_scanned: 4,
      });
      await store.scan(0);
    });

    it('toggleSelect 应该切换状态并更新 anchor', () => {
      store.toggleSelect('k1');
      expect(store.selectedKeys.has('k1')).toBe(true);
      expect(store.lastSelectedKey).toBe('k1');

      store.toggleSelect('k1');
      expect(store.selectedKeys.has('k1')).toBe(false);
    });

    it('rangeSelect 无 anchor 时等价于 toggleSelect', () => {
      store.rangeSelect('k2');
      expect(store.selectedKeys.has('k2')).toBe(true);
    });

    it('rangeSelect 应选择 anchor 到目标之间全部键', () => {
      store.toggleSelect('k1');
      store.rangeSelect('k3');
      expect([...store.selectedKeys].sort()).toEqual(['k1', 'k2', 'k3']);
    });

    it('rangeSelect 反向范围也正确', () => {
      store.toggleSelect('k4');
      store.rangeSelect('k2');
      expect([...store.selectedKeys].sort()).toEqual(['k2', 'k3', 'k4']);
    });

    it('rangeSelect 对未知键应直接返回', () => {
      store.toggleSelect('k1');
      store.rangeSelect('unknown');
      expect(store.selectedKeys.size).toBe(1);
    });

    it('selectAll 选中全部过滤后的键', () => {
      store.selectAll();
      expect(store.selectedKeys.size).toBe(4);
      expect(store.lastSelectedKey).toBe('k4');
    });

    it('clearSelection 清空多选', () => {
      store.selectAll();
      store.clearSelection();
      expect(store.selectedKeys.size).toBe(0);
      expect(store.lastSelectedKey).toBe(null);
    });
  });

  describe('其他动作', () => {
    it('setPattern / setTypeFilter / selectKey 应该更新状态', () => {
      store.setPattern('foo*');
      store.setTypeFilter('hash');
      store.selectKey('x');
      expect(store.pattern).toBe('foo*');
      expect(store.typeFilter).toBe('hash');
      expect(store.selectedKey).toBe('x');
    });

    it('getKeyIndex 返回正确索引', async () => {
      (keysScan as any).mockResolvedValue({
        keys: [mkKey('a'), mkKey('b')],
        cursor: 0,
        total_scanned: 2,
      });
      await store.scan(0);
      expect(store.getKeyIndex('b')).toBe(1);
      expect(store.getKeyIndex('zz')).toBe(-1);
    });

    it('reset 应该恢复所有状态', async () => {
      (keysScan as any).mockResolvedValue({
        keys: [mkKey('a')],
        cursor: 10,
        total_scanned: 1,
      });
      await store.scan(0);
      store.setPattern('p');
      store.toggleSelect('a');

      store.reset();
      expect(store.keys).toEqual([]);
      expect(store.pattern).toBe('');
      expect(store.selectedKeys.size).toBe(0);
      expect(store.cursorStack).toEqual([0]);
    });
  });
});
