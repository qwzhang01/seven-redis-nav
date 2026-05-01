import { describe, it, expect, beforeEach } from 'vitest';
import { mountComponent } from '@/test/utils';
import ZSetViewer from './ZSetViewer.vue';
import { createPinia, setActivePinia } from 'pinia';

describe('ZSetViewer', () => {
  const mockDetail = {
    key: 'test:zset',
    key_type: 'zset',
    value: {
      type: 'zset' as const,
      members: [
        [1.5, 'member1'],
        [2.0, 'member2'],
        [3.5, 'member3'],
      ],
    },
    ttl: -1,
    size: 50,
    encoding: 'ziplist',
    length: 3,
    db: 0,
  };

  beforeEach(() => {
    const pinia = createPinia();
    setActivePinia(pinia);
  });

  it('应该正确渲染组件', () => {
    const wrapper = mountComponent(ZSetViewer, {
      props: { detail: mockDetail },
    });

    expect(wrapper.exists()).toBe(true);
    expect(wrapper.find('.zset-viewer').exists()).toBe(true);
    expect(wrapper.find('.zv-table').exists()).toBe(true);
  });

  it('应该显示表头', () => {
    const wrapper = mountComponent(ZSetViewer, {
      props: { detail: mockDetail },
    });

    const headers = wrapper.findAll('th');
    expect(headers).toHaveLength(2);
    expect(headers[0].text()).toBe('分数');
    expect(headers[1].text()).toBe('成员');
  });

  it('应该显示所有有序集合成员', () => {
    const wrapper = mountComponent(ZSetViewer, {
      props: { detail: mockDetail },
    });

    const rows = wrapper.findAll('tbody tr');
    expect(rows).toHaveLength(3);

    const scoreCells = wrapper.findAll('tbody td.score-cell');
    expect(scoreCells).toHaveLength(3);
    expect(scoreCells[0].text()).toBe('1.5');
    expect(scoreCells[1].text()).toBe('2');
    expect(scoreCells[2].text()).toBe('3.5');

    const memberCells = wrapper.findAll('tbody td.member-cell');
    expect(memberCells).toHaveLength(3);
    expect(memberCells[0].text()).toBe('member1');
    expect(memberCells[1].text()).toBe('member2');
    expect(memberCells[2].text()).toBe('member3');
  });

  it('应该正确处理空有序集合', () => {
    const emptyDetail = {
      ...mockDetail,
      value: { type: 'zset' as const, members: [] },
      length: 0,
    };

    const wrapper = mountComponent(ZSetViewer, {
      props: { detail: emptyDetail },
    });

    const rows = wrapper.findAll('tbody tr');
    expect(rows).toHaveLength(0);
  });

  it('应该响应 props 变化', async () => {
    const wrapper = mountComponent(ZSetViewer, {
      props: { detail: mockDetail },
    });

    const newDetail = {
      ...mockDetail,
      value: {
        type: 'zset' as const,
        members: [[99, 'new-member']],
      },
      length: 1,
    };

    await wrapper.setProps({ detail: newDetail });
    const rows = wrapper.findAll('tbody tr');
    expect(rows).toHaveLength(1);
    expect(wrapper.find('tbody td.score-cell').text()).toBe('99');
    expect(wrapper.find('tbody td.member-cell').text()).toBe('new-member');
  });

  it('应该使用正确的样式类', () => {
    const wrapper = mountComponent(ZSetViewer, {
      props: { detail: mockDetail },
    });

    expect(wrapper.find('.zv-table').classes()).toContain('zv-table');
    const scoreCells = wrapper.findAll('.score-cell');
    scoreCells.forEach((cell) => {
      expect(cell.classes()).toContain('score-cell');
    });
    const memberCells = wrapper.findAll('.member-cell');
    memberCells.forEach((cell) => {
      expect(cell.classes()).toContain('member-cell');
    });
  });

  it('大量成员应该正确渲染', () => {
    const largeDetail = {
      ...mockDetail,
      value: {
        type: 'zset' as const,
        members: Array.from({ length: 100 }, (_, i) => [i * 0.5, `member-${i}`]),
      },
      length: 100,
    };

    const wrapper = mountComponent(ZSetViewer, {
      props: { detail: largeDetail },
    });

    const rows = wrapper.findAll('tbody tr');
    expect(rows).toHaveLength(100);
  });
});
