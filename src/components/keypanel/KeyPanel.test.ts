import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import KeyPanel from './KeyPanel.vue';
import { useConnectionStore } from '@/stores/connection';
import { useKeyBrowserStore } from '@/stores/keyBrowser';
import { keyGet } from '@/ipc/data';
import type { KeyMeta } from '@/types/data';

vi.mock('@tanstack/vue-virtual', () => ({
  useVirtualizer: (optionsRef: { value: { count: number } }) => ({
    value: {
      getVirtualItems: () => Array.from({ length: optionsRef.value.count }, (_, index) => ({
        index,
        key: index,
        start: index * 34,
        size: 34,
      })),
      getTotalSize: () => optionsRef.value.count * 34,
      scrollToIndex: vi.fn(),
    },
  }),
}));

vi.mock('@/ipc/data', () => ({
  keyGet: vi.fn(),
  keySet: vi.fn(),
  keysScan: vi.fn(),
  keysBulkDelete: vi.fn(),
  keysBulkTtl: vi.fn(),
}));

vi.mock('@/ipc/phase4', () => ({
  exportDbJson: vi.fn(),
  exportKeysJson: vi.fn(),
}));

vi.mock('file-saver', () => ({
  saveAs: vi.fn(),
}));

function mkKey(key: string): KeyMeta {
  return { key, key_type: 'string', ttl: -1, size: 0, encoding: 'raw' };
}

function prepareStores(keys: KeyMeta[] = [mkKey('k1'), mkKey('k2'), mkKey('k3')]) {
  const connStore = useConnectionStore();
  connStore.activeConnId = 'conn-1';
  connStore.sessionStates = { 'conn-1': 'connected' };

  const keyBrowserStore = useKeyBrowserStore();
  keyBrowserStore.keys = keys;

  return { connStore, keyBrowserStore };
}

describe('KeyPanel 批量选择交互', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    (keyGet as unknown as ReturnType<typeof vi.fn>).mockImplementation((_connId: string, key: string) => ({
      key,
      key_type: 'string',
      ttl: -1,
      size: 0,
      value: '',
    }));
  });

  it('普通点击后首次 Shift 点击应选择正确的闭区间范围', async () => {
    const { keyBrowserStore } = prepareStores();
    const wrapper = mount(KeyPanel);
    const items = wrapper.findAll('.key-item');

    await items[0].trigger('click');
    await items[2].trigger('click', { shiftKey: true });

    expect([...keyBrowserStore.selectedKeys].sort()).toEqual(['k1', 'k2', 'k3']);
    wrapper.unmount();
  });

  it('普通点击只打开详情，不显示批量选择数量和操作栏', async () => {
    const { keyBrowserStore } = prepareStores();
    const wrapper = mount(KeyPanel);

    await wrapper.findAll('.key-item')[0].trigger('click');

    expect(keyBrowserStore.selectedKey).toBe('k1');
    expect(keyBrowserStore.selectedKeys.size).toBe(0);
    expect(wrapper.text()).not.toContain('已选');
    wrapper.unmount();
  });

  it('批量模式下当前详情 key 不作为额外选中项显示', () => {
    const { keyBrowserStore } = prepareStores();
    keyBrowserStore.selectKey('k1');
    keyBrowserStore.toggleSelect('k2');

    const wrapper = mount(KeyPanel);
    const items = wrapper.findAll('.key-item');

    expect(items[0].classes()).not.toContain('active');
    expect(items[0].classes()).not.toContain('multi-selected');
    expect(items[1].classes()).toContain('multi-selected');
    wrapper.unmount();
  });
});
