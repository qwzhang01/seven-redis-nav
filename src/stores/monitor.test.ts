import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useMonitorStore, classifyCommand } from './monitor';

describe('classifyCommand', () => {
  it('GET 应归类为 read', () => {
    expect(classifyCommand('GET')).toBe('read');
  });

  it('HGETALL 应归类为 read', () => {
    expect(classifyCommand('HGETALL')).toBe('read');
  });

  it('SET 应归类为 write', () => {
    expect(classifyCommand('SET')).toBe('write');
  });

  it('CONFIG 应归类为 admin', () => {
    expect(classifyCommand('CONFIG')).toBe('admin');
  });

  it('FLUSHDB 应归类为 admin', () => {
    expect(classifyCommand('FLUSHDB')).toBe('admin');
  });

  it('INFO 应归类为 admin', () => {
    expect(classifyCommand('INFO')).toBe('admin');
  });

  it('未知命令应归类为 write', () => {
    expect(classifyCommand('UNKNOWN')).toBe('write');
  });

  it('大小写不敏感', () => {
    expect(classifyCommand('get')).toBe('read');
    expect(classifyCommand('Set')).toBe('write');
  });
});

describe('Monitor Store', () => {
  let store: ReturnType<typeof useMonitorStore>;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useMonitorStore();
  });

  describe('初始状态', () => {
    it('应该具有正确的默认值', () => {
      expect(store.commands).toEqual([]);
      expect(store.active).toBe(false);
      expect(store.paused).toBe(false);
      expect(store.pauseBuffer).toEqual([]);
      expect(store.filterKeyword).toBe('');
      expect(store.totalReceived).toBe(0);
    });
  });

  describe('addCommand', () => {
    it('应该向命令列表添加命令', () => {
      const cmd = { timestamp: 1, client: 'c1', db: 0, command: 'GET', args: ['key'] };
      store.addCommand(cmd);
      expect(store.commands).toHaveLength(1);
      expect(store.commands[0]).toEqual(cmd);
    });

    it('应该递增 totalReceived', () => {
      store.addCommand({ timestamp: 1, client: 'c1', db: 0, command: 'GET', args: [] });
      store.addCommand({ timestamp: 2, client: 'c2', db: 0, command: 'SET', args: [] });
      expect(store.totalReceived).toBe(2);
    });

    it('暂停时命令应进入缓冲区', () => {
      store.pause();
      const cmd = { timestamp: 1, client: 'c1', db: 0, command: 'GET', args: [] };
      store.addCommand(cmd);
      expect(store.commands).toHaveLength(0);
      expect(store.pauseBuffer).toHaveLength(1);
    });

    it('环形缓冲区超过 MAX_COMMANDS 时应淘汰最旧命令', () => {
      for (let i = 0; i < 10001; i++) {
        store.addCommand({ timestamp: i, client: 'c', db: 0, command: 'CMD', args: [] });
      }
      expect(store.commands).toHaveLength(10000);
      // 最新命令应保留
      expect(store.commands[9999].timestamp).toBe(10000);
    });
  });

  describe('暂停与恢复', () => {
    it('pause 应设置 paused=true', () => {
      store.pause();
      expect(store.paused).toBe(true);
    });

    it('resume 应设置 paused=false 并刷入缓冲区', () => {
      store.pause();
      store.addCommand({ timestamp: 1, client: 'c1', db: 0, command: 'GET', args: [] });
      expect(store.pauseBuffer).toHaveLength(1);

      store.resume();
      expect(store.paused).toBe(false);
      expect(store.pauseBuffer).toEqual([]);
      expect(store.commands).toHaveLength(1);
    });
  });

  describe('clearCommands', () => {
    it('应清空命令和缓冲区', () => {
      store.addCommand({ timestamp: 1, client: 'c1', db: 0, command: 'GET', args: [] });
      store.pause();
      store.addCommand({ timestamp: 2, client: 'c2', db: 0, command: 'SET', args: [] });
      store.clearCommands();
      expect(store.commands).toEqual([]);
      expect(store.pauseBuffer).toEqual([]);
      expect(store.totalReceived).toBe(0);
    });
  });

  describe('reset', () => {
    it('应重置全部状态', () => {
      store.addCommand({ timestamp: 1, client: 'c1', db: 0, command: 'GET', args: [] });
      store.setActive(true);
      store.pause();
      store.reset();
      expect(store.commands).toEqual([]);
      expect(store.active).toBe(false);
      expect(store.paused).toBe(false);
      expect(store.totalReceived).toBe(0);
    });
  });

  describe('setActive', () => {
    it('应设置 active 状态', () => {
      store.setActive(true);
      expect(store.active).toBe(true);
      store.setActive(false);
      expect(store.active).toBe(false);
    });
  });

  describe('filteredCommands', () => {
    beforeEach(() => {
      store.addCommand({ timestamp: 1, client: 'c1', db: 0, command: 'GET', args: ['key1'] });
      store.addCommand({ timestamp: 2, client: 'c2', db: 0, command: 'SET', args: ['key2', 'val'] });
      store.addCommand({ timestamp: 3, client: 'c3', db: 0, command: 'CONFIG', args: ['GET', 'maxmemory'] });
    });

    it('无关键字时返回全部', () => {
      expect(store.filteredCommands).toHaveLength(3);
    });

    it('按命令名过滤', () => {
      store.filterKeyword = 'get';
      // 'get' 匹配了 GET 命令本身和 CONFIG 命令的参数 'GET'
      expect(store.filteredCommands).toHaveLength(2);
      expect(store.filteredCommands[0].command).toBe('GET');
      expect(store.filteredCommands[1].command).toBe('CONFIG');
    });

    it('按参数过滤', () => {
      store.filterKeyword = 'key2';
      expect(store.filteredCommands).toHaveLength(1);
      expect(store.filteredCommands[0].command).toBe('SET');
    });

    it('大小写不敏感过滤', () => {
      store.filterKeyword = 'CONFIG';
      // 'config' 匹配了 CONFIG 命令本身
      expect(store.filteredCommands).toHaveLength(1);
      expect(store.filteredCommands[0].command).toBe('CONFIG');
    });
  });
});
