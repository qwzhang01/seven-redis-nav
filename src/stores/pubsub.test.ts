import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { usePubSubStore } from './pubsub';

describe('PubSub Store', () => {
  let store: ReturnType<typeof usePubSubStore>;

  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    store = usePubSubStore();
  });

  describe('初始状态', () => {
    it('应该具有正确的默认值', () => {
      expect(store.messages).toEqual([]);
      expect(store.subscriptions).toEqual([]);
      expect(store.patternSubscriptions).toEqual([]);
      expect(store.paused).toBe(false);
      expect(store.pauseBuffer).toEqual([]);
      expect(store.filterKeyword).toBe('');
      expect(store.totalReceived).toBe(0);
      expect(store.ratePerSec).toBe(0);
      expect(store.channelCounts).toEqual({});
    });
  });

  describe('addMessage', () => {
    it('应该向消息列表添加消息', () => {
      const msg = { channel: 'ch1', pattern: null, message: 'hello', timestamp: '2026-01-01' };
      store.addMessage(msg);
      expect(store.messages).toHaveLength(1);
      expect(store.messages[0]).toEqual(msg);
    });

    it('应该递增 totalReceived', () => {
      store.addMessage({ channel: 'ch1', pattern: null, message: 'a', timestamp: '1' });
      store.addMessage({ channel: 'ch2', pattern: null, message: 'b', timestamp: '2' });
      expect(store.totalReceived).toBe(2);
    });

    it('应该更新 channelCounts', () => {
      store.addMessage({ channel: 'ch1', pattern: null, message: 'a', timestamp: '1' });
      store.addMessage({ channel: 'ch1', pattern: null, message: 'b', timestamp: '2' });
      expect(store.channelCounts['ch1']).toBe(2);
    });

    it('暂停时消息应进入缓冲区', () => {
      store.pause();
      store.addMessage({ channel: 'ch1', pattern: null, message: 'hi', timestamp: '1' });
      expect(store.messages).toHaveLength(0);
      expect(store.pauseBuffer).toHaveLength(1);
    });

    it('环形缓冲区超过 MAX_MESSAGES 时应淘汰最旧消息', () => {
      for (let i = 0; i < 5001; i++) {
        store.addMessage({ channel: 'ch', pattern: null, message: `msg-${i}`, timestamp: String(i) });
      }
      expect(store.messages).toHaveLength(5000);
    });
  });

  describe('pause / resume', () => {
    it('pause 应设置 paused=true', () => {
      store.pause();
      expect(store.paused).toBe(true);
    });

    it('resume 应设置 paused=false 并刷入缓冲区', () => {
      store.pause();
      store.addMessage({ channel: 'ch', pattern: null, message: 'buffered', timestamp: '1' });
      store.resume();
      expect(store.paused).toBe(false);
      expect(store.pauseBuffer).toEqual([]);
      expect(store.messages).toHaveLength(1);
    });
  });

  describe('clearMessages', () => {
    it('应清空消息和计数', () => {
      store.addMessage({ channel: 'ch', pattern: null, message: 'hi', timestamp: '1' });
      store.clearMessages();
      expect(store.messages).toEqual([]);
      expect(store.pauseBuffer).toEqual([]);
      expect(store.totalReceived).toBe(0);
      expect(store.channelCounts).toEqual({});
      expect(store.ratePerSec).toBe(0);
    });
  });

  describe('订阅管理', () => {
    it('addSubscription 应添加不存在的频道', () => {
      store.addSubscription(['ch1', 'ch2'], false);
      expect(store.subscriptions).toEqual(['ch1', 'ch2']);
    });

    it('addSubscription 不应添加已存在的频道', () => {
      store.addSubscription(['ch1'], false);
      store.addSubscription(['ch1', 'ch2'], false);
      expect(store.subscriptions).toEqual(['ch1', 'ch2']);
    });

    it('addSubscription pattern=true 应添加到 patternSubscriptions', () => {
      store.addSubscription(['ch*'], true);
      expect(store.patternSubscriptions).toEqual(['ch*']);
    });

    it('removeSubscription 应移除普通频道', () => {
      store.addSubscription(['ch1', 'ch2'], false);
      store.removeSubscription(['ch1'], false);
      expect(store.subscriptions).toEqual(['ch2']);
    });

    it('removeSubscription 应移除 pattern 频道', () => {
      store.addSubscription(['ch*'], true);
      store.removeSubscription(['ch*'], true);
      expect(store.patternSubscriptions).toEqual([]);
    });

    it('hasSubscriptions 有订阅时为 true', () => {
      store.addSubscription(['ch1'], false);
      expect(store.hasSubscriptions).toBe(true);
    });

    it('hasSubscriptions 无订阅时为 false', () => {
      expect(store.hasSubscriptions).toBe(false);
    });
  });

  describe('reset', () => {
    it('应重置全部状态', () => {
      store.addSubscription(['ch1'], false);
      store.addSubscription(['ch*'], true);
      store.addMessage({ channel: 'ch1', pattern: null, message: 'hi', timestamp: '1' });
      store.reset();
      expect(store.messages).toEqual([]);
      expect(store.subscriptions).toEqual([]);
      expect(store.patternSubscriptions).toEqual([]);
      expect(store.totalReceived).toBe(0);
      expect(store.ratePerSec).toBe(0);
      expect(store.channelCounts).toEqual({});
    });
  });

  describe('filteredMessages', () => {
    beforeEach(() => {
      store.addMessage({ channel: 'news', pattern: null, message: 'hello', timestamp: '1' });
      store.addMessage({ channel: 'alerts', pattern: null, message: 'warning', timestamp: '2' });
    });

    it('无关键字时返回全部', () => {
      expect(store.filteredMessages).toHaveLength(2);
    });

    it('按频道名过滤', () => {
      store.filterKeyword = 'news';
      expect(store.filteredMessages).toHaveLength(1);
      expect(store.filteredMessages[0].channel).toBe('news');
    });

    it('按消息内容过滤', () => {
      store.filterKeyword = 'warning';
      expect(store.filteredMessages).toHaveLength(1);
    });

    it('大小写不敏感', () => {
      store.filterKeyword = 'ALERTS';
      expect(store.filteredMessages).toHaveLength(1);
    });
  });
});
