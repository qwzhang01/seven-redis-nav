import { describe, it, expect, beforeEach } from 'vitest';
import { mountComponent } from '@/test/utils';
import SetViewer from './SetViewer.vue';
import { createPinia, setActivePinia } from 'pinia';

describe('SetViewer', () => {
  const mockDetail = {
    key: 'test:set',
    key_type: 'set',
    value: {
      type: 'set' as const,
      members: ['member1', 'member2', 'member3'],
    },
    ttl: -1,
    size: 30,
    encoding: 'hashtable',
    length: 3,
    db: 0,
  };

  beforeEach(() => {
    const pinia = createPinia();
    setActivePinia(pinia);
  });

  it('应该正确渲染组件', () => {
    const wrapper = mountComponent(SetViewer, {
      props: { detail: mockDetail },
    });

    expect(wrapper.exists()).toBe(true);
    expect(wrapper.find('.set-viewer').exists()).toBe(true);
    expect(wrapper.find('.sv-grid').exists()).toBe(true);
  });

  it('应该显示所有集合成员', () => {
    const wrapper = mountComponent(SetViewer, {
      props: { detail: mockDetail },
    });

    const cards = wrapper.findAll('.sv-card');
    expect(cards).toHaveLength(3);

    const members = wrapper.findAll('.sv-member');
    expect(members).toHaveLength(3);
    expect(members[0].text()).toBe('member1');
    expect(members[1].text()).toBe('member2');
    expect(members[2].text()).toBe('member3');
  });

  it('应该正确处理空集合', () => {
    const emptyDetail = {
      ...mockDetail,
      value: { type: 'set' as const, members: [] },
      length: 0,
    };

    const wrapper = mountComponent(SetViewer, {
      props: { detail: emptyDetail },
    });

    const cards = wrapper.findAll('.sv-card');
    expect(cards).toHaveLength(0);
  });

  it('应该响应 props 变化', async () => {
    const wrapper = mountComponent(SetViewer, {
      props: { detail: mockDetail },
    });

    const newDetail = {
      ...mockDetail,
      value: {
        type: 'set' as const,
        members: ['new-member'],
      },
      length: 1,
    };

    await wrapper.setProps({ detail: newDetail });
    const cards = wrapper.findAll('.sv-card');
    expect(cards).toHaveLength(1);
    expect(wrapper.find('.sv-member').text()).toBe('new-member');
  });

  it('应该使用正确的样式类', () => {
    const wrapper = mountComponent(SetViewer, {
      props: { detail: mockDetail },
    });

    expect(wrapper.find('.sv-grid').classes()).toContain('sv-grid');
    const cards = wrapper.findAll('.sv-card');
    cards.forEach((card) => {
      expect(card.classes()).toContain('sv-card');
    });
    const members = wrapper.findAll('.sv-member');
    members.forEach((m) => {
      expect(m.classes()).toContain('sv-member');
    });
  });

  it('大量成员应该正确渲染', () => {
    const largeDetail = {
      ...mockDetail,
      value: {
        type: 'set' as const,
        members: Array.from({ length: 100 }, (_, i) => `member-${i}`),
      },
      length: 100,
    };

    const wrapper = mountComponent(SetViewer, {
      props: { detail: largeDetail },
    });

    const cards = wrapper.findAll('.sv-card');
    expect(cards).toHaveLength(100);
  });
});
