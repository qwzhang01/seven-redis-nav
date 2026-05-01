import { describe, it, expect, beforeEach } from 'vitest';
import { mountComponent } from '@/test/utils';
import ListViewer from './ListViewer.vue';
import { createPinia, setActivePinia } from 'pinia';

describe('ListViewer', () => {
  const mockDetail = {
    key: 'test:list',
    key_type: 'list',
    value: {
      type: 'list' as const,
      items: ['item0', 'item1', 'item2'],
    },
    ttl: -1,
    size: 30,
    encoding: 'quicklist',
    length: 3,
    db: 0,
  };

  beforeEach(() => {
    const pinia = createPinia();
    setActivePinia(pinia);
  });

  it('应该正确渲染组件', () => {
    const wrapper = mountComponent(ListViewer, {
      props: { detail: mockDetail },
    });

    expect(wrapper.exists()).toBe(true);
    expect(wrapper.find('.list-viewer').exists()).toBe(true);
    expect(wrapper.find('.lv-table').exists()).toBe(true);
  });

  it('应该显示表头', () => {
    const wrapper = mountComponent(ListViewer, {
      props: { detail: mockDetail },
    });

    const headers = wrapper.findAll('th');
    expect(headers).toHaveLength(2);
    expect(headers[0].text()).toBe('索引');
    expect(headers[1].text()).toBe('值');
  });

  it('应该显示所有列表元素', () => {
    const wrapper = mountComponent(ListViewer, {
      props: { detail: mockDetail },
    });

    const rows = wrapper.findAll('tbody tr');
    expect(rows).toHaveLength(3);

    const indexCells = wrapper.findAll('tbody td.index-cell');
    expect(indexCells).toHaveLength(3);
    expect(indexCells[0].text()).toBe('0');
    expect(indexCells[1].text()).toBe('1');
    expect(indexCells[2].text()).toBe('2');

    const valueCells = wrapper.findAll('tbody td.value-cell');
    expect(valueCells).toHaveLength(3);
    expect(valueCells[0].text()).toBe('item0');
    expect(valueCells[1].text()).toBe('item1');
    expect(valueCells[2].text()).toBe('item2');
  });

  it('应该正确处理空列表', () => {
    const emptyDetail = {
      ...mockDetail,
      value: { type: 'list' as const, items: [] },
      length: 0,
    };

    const wrapper = mountComponent(ListViewer, {
      props: { detail: emptyDetail },
    });

    const rows = wrapper.findAll('tbody tr');
    expect(rows).toHaveLength(0);
  });

  it('应该响应 props 变化', async () => {
    const wrapper = mountComponent(ListViewer, {
      props: { detail: mockDetail },
    });

    const newDetail = {
      ...mockDetail,
      value: { type: 'list' as const, items: ['new-item'] },
      length: 1,
    };

    await wrapper.setProps({ detail: newDetail });
    const rows = wrapper.findAll('tbody tr');
    expect(rows).toHaveLength(1);
    expect(wrapper.find('tbody td.value-cell').text()).toBe('new-item');
  });

  it('应该使用正确的样式类', () => {
    const wrapper = mountComponent(ListViewer, {
      props: { detail: mockDetail },
    });

    expect(wrapper.find('.lv-table').classes()).toContain('lv-table');
    const indexCells = wrapper.findAll('.index-cell');
    indexCells.forEach((cell) => {
      expect(cell.classes()).toContain('index-cell');
    });
    const valueCells = wrapper.findAll('.value-cell');
    valueCells.forEach((cell) => {
      expect(cell.classes()).toContain('value-cell');
    });
  });

  it('长列表应该正确渲染', () => {
    const longDetail = {
      ...mockDetail,
      value: {
        type: 'list' as const,
        items: Array.from({ length: 100 }, (_, i) => `item-${i}`),
      },
      length: 100,
    };

    const wrapper = mountComponent(ListViewer, {
      props: { detail: longDetail },
    });

    const rows = wrapper.findAll('tbody tr');
    expect(rows).toHaveLength(100);
  });
});
