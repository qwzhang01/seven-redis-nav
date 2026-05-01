import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useWorkspaceStore } from './workspace';
import { useConnectionStore } from './connection';

describe('Workspace Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  describe('初始状态', () => {
    it('activeTab 默认应为 browser', () => {
      const s = useWorkspaceStore();
      expect(s.activeTab).toBe('browser');
    });

    it('connected 应随 connectionStore 联动', () => {
      const conn = useConnectionStore();
      const s = useWorkspaceStore();
      expect(s.connected).toBe(false);

      // 设置连接状态为已连接
      (conn as any).activeConnId = 'conn-1';
      (conn as any).sessionStates = { 'conn-1': 'connected' };
      expect(s.connected).toBe(true);
    });
  });

  describe('setActiveTab', () => {
    it('应该切换 activeTab', () => {
      const s = useWorkspaceStore();
      s.setActiveTab('cli');
      expect(s.activeTab).toBe('cli');
      s.setActiveTab('monitor');
      expect(s.activeTab).toBe('monitor');
    });

    it('应该支持所有合法标签', () => {
      const s = useWorkspaceStore();
      const tabs = ['browser', 'cli', 'monitor', 'slowlog', 'pubsub', 'config'] as const;
      for (const t of tabs) {
        s.setActiveTab(t);
        expect(s.activeTab).toBe(t);
      }
    });
  });

  describe('setConnected（向后兼容 noop）', () => {
    it('不应影响 connected 计算属性', () => {
      const s = useWorkspaceStore();
      s.setConnected(true);
      // connected 驱动源仍是 connectionStore，因此保持 false
      expect(s.connected).toBe(false);
    });
  });
});
