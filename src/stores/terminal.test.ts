import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useTerminalStore } from './terminal';
import { useConnectionStore } from './connection';
import { cliExec, cliHistoryGet } from '@/ipc/terminal';

vi.mock('@/ipc/terminal', () => ({
  cliExec: vi.fn(),
  cliHistoryGet: vi.fn(),
}));

vi.mock('./connection', () => ({
  useConnectionStore: vi.fn(),
}));

describe('Terminal Store', () => {
  let store: ReturnType<typeof useTerminalStore>;
  let connMock: any;

  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    connMock = {
      activeConnId: 'conn-1',
      activeConnection: { host: 'localhost', port: 6379 },
      currentDb: 0,
    };
    (useConnectionStore as any).mockReturnValue(connMock);
    store = useTerminalStore();
  });

  describe('初始状态', () => {
    it('应该具有正确的默认值', () => {
      expect(store.outputLines).toEqual([]);
      expect(store.history).toEqual([]);
      expect(store.historyIndex).toBe(-1);
      expect(store.currentInput).toBe('');
      expect(store.loading).toBe(false);
    });
  });

  describe('execute', () => {
    it('应该执行命令并追加输出行', async () => {
      (cliExec as any).mockResolvedValue({ output: 'OK', is_error: false });

      await store.execute('SET key val');

      expect(cliExec).toHaveBeenCalledWith('conn-1', 'SET key val', undefined);
      expect(store.outputLines).toHaveLength(1);
      expect(store.outputLines[0].command).toBe('SET key val');
      expect(store.outputLines[0].output).toBe('OK');
      expect(store.outputLines[0].isError).toBe(false);
    });

    it('应该正确格式化提示符', async () => {
      (cliExec as any).mockResolvedValue({ output: 'OK', is_error: false });
      await store.execute('PING');
      expect(store.outputLines[0].prompt).toContain('localhost');
      expect(store.outputLines[0].prompt).toContain('6379');
    });

    it('应该处理错误输出', async () => {
      (cliExec as any).mockResolvedValue({ output: 'ERR unknown command', is_error: true });
      await store.execute('FOO');
      expect(store.outputLines[0].isError).toBe(true);
      expect(store.outputLines[0].output).toBe('ERR unknown command');
    });

    it('应该处理 CLEAR 命令', async () => {
      await store.execute('CLEAR');
      expect(cliExec).not.toHaveBeenCalled();
      expect(store.outputLines).toEqual([]);
    });

    it('应该忽略空命令', async () => {
      await store.execute('   ');
      expect(cliExec).not.toHaveBeenCalled();
    });

    it('没有活动连接时应该不执行', async () => {
      connMock.activeConnId = null;
      await store.execute('PING');
      expect(cliExec).not.toHaveBeenCalled();
    });

    it('应该传递 confirmToken', async () => {
      (cliExec as any).mockResolvedValue({ output: 'OK', is_error: false });
      await store.execute('FLUSHDB', 'sync');
      expect(cliExec).toHaveBeenCalledWith('conn-1', 'FLUSHDB', 'sync');
    });

    it('应该在 finally 块中重置 loading', async () => {
      (cliExec as any).mockRejectedValue(new Error('fail'));
      await expect(store.execute('CMD')).rejects.toThrow('fail');
      expect(store.loading).toBe(false);
    });
  });

  describe('navigateHistory', () => {
    it('向上导航应浏览更早的历史', async () => {
      (cliHistoryGet as any).mockResolvedValue([
        { id: 1, command: 'SET a 1', created_at: '1' },
        { id: 2, command: 'GET a', created_at: '2' },
      ]);
      await store.loadHistory();

      store.navigateHistory('up');
      expect(store.currentInput).toBe('SET a 1');
      expect(store.historyIndex).toBe(0);

      store.navigateHistory('up');
      expect(store.currentInput).toBe('GET a');
      expect(store.historyIndex).toBe(1);
    });

    it('向上导航不应超过历史上限', async () => {
      (cliHistoryGet as any).mockResolvedValue([
        { id: 1, command: 'GET a', created_at: '1' },
      ]);
      await store.loadHistory();

      store.navigateHistory('up');
      store.navigateHistory('up');
      expect(store.historyIndex).toBe(0);
    });

    it('向下导航应浏览更近的历史', async () => {
      (cliHistoryGet as any).mockResolvedValue([
        { id: 1, command: 'SET a 1', created_at: '1' },
        { id: 2, command: 'GET a', created_at: '2' },
      ]);
      await store.loadHistory();
      store.navigateHistory('up');
      store.navigateHistory('up');

      store.navigateHistory('down');
      expect(store.historyIndex).toBe(0);
      expect(store.currentInput).toBe('SET a 1');
    });

    it('向下导航到 -1 时应清空输入', async () => {
      (cliHistoryGet as any).mockResolvedValue([
        { id: 1, command: 'SET a 1', created_at: '1' },
      ]);
      await store.loadHistory();
      store.navigateHistory('up');

      store.navigateHistory('down');
      expect(store.historyIndex).toBe(-1);
      expect(store.currentInput).toBe('');
    });

    it('无历史记录时不做操作', () => {
      (cliHistoryGet as any).mockResolvedValue([]);
      store.navigateHistory('up');
      expect(store.historyIndex).toBe(-1);
    });
  });

  describe('clearOutput', () => {
    it('应清空输出行', async () => {
      (cliExec as any).mockResolvedValue({ output: 'OK', is_error: false });
      await store.execute('PING');
      expect(store.outputLines).toHaveLength(1);

      store.clearOutput();
      expect(store.outputLines).toEqual([]);
    });
  });

  describe('setInput', () => {
    it('应设置输入并重置历史索引', () => {
      store.setInput('GET key');
      expect(store.currentInput).toBe('GET key');
      expect(store.historyIndex).toBe(-1);
    });
  });

  describe('loadHistory', () => {
    it('应该从 IPC 加载历史', async () => {
      const mockHistory = [
        { id: 1, command: 'SET a 1', created_at: '1' },
      ];
      (cliHistoryGet as any).mockResolvedValue(mockHistory);

      await store.loadHistory();
      expect(store.history).toEqual(mockHistory);
      expect(store.historyIndex).toBe(-1);
    });
  });
});
