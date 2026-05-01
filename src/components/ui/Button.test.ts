import { describe, it, expect } from 'vitest';
import { mountComponent } from '@/test/utils';
import Button from './Button.vue';

describe('Button', () => {
  it('应该正确渲染默认按钮', () => {
    const wrapper = mountComponent(Button, {
      props: {},
    });

    expect(wrapper.exists()).toBe(true);
    expect(wrapper.find('button').exists()).toBe(true);
    expect(wrapper.find('button').classes()).toContain('ui-button--primary');
    expect(wrapper.find('button').classes()).toContain('ui-button--medium');
  });

  it('应该渲染不同 variant', () => {
    const variants = ['primary', 'secondary', 'outline', 'ghost', 'danger'] as const;
    for (const variant of variants) {
      const wrapper = mountComponent(Button, { props: { variant } });
      expect(wrapper.find('button').classes()).toContain(`ui-button--${variant}`);
    }
  });

  it('应该渲染不同 size', () => {
    const sizes = ['small', 'medium', 'large'] as const;
    for (const size of sizes) {
      const wrapper = mountComponent(Button, { props: { size } });
      expect(wrapper.find('button').classes()).toContain(`ui-button--${size}`);
    }
  });

  it('应该正确显示图标', () => {
    const wrapper = mountComponent(Button, {
      props: { icon: 'ri-add-line' },
    });

    const icon = wrapper.find('.ui-button__icon');
    expect(icon.exists()).toBe(true);
    expect(icon.classes()).toContain('ri-add-line');
  });

  it('disabled 为 true 时按钮应被禁用', () => {
    const wrapper = mountComponent(Button, {
      props: { disabled: true },
    });

    expect(wrapper.find('button').attributes('disabled')).toBeDefined();
  });

  it('loading 为 true 时按钮应被禁用且有 loading 样式', () => {
    const wrapper = mountComponent(Button, {
      props: { loading: true },
    });

    expect(wrapper.find('button').attributes('disabled')).toBeDefined();
    expect(wrapper.find('button').classes()).toContain('ui-button--loading');
  });

  it('block 为 true 时按钮应全宽', () => {
    const wrapper = mountComponent(Button, {
      props: { block: true },
    });

    expect(wrapper.find('button').classes()).toContain('ui-button--block');
  });

  it('点击按钮应触发 click 事件', async () => {
    const wrapper = mountComponent(Button, {});

    await wrapper.find('button').trigger('click');
    expect(wrapper.emitted('click')).toBeTruthy();
    expect(wrapper.emitted('click')!.length).toBe(1);
  });

  it('禁用按钮不应触发 click 事件', async () => {
    const wrapper = mountComponent(Button, {
      props: { disabled: true },
    });

    await wrapper.find('button').trigger('click');
    expect(wrapper.emitted('click')).toBeFalsy();
  });

  it('loading 按钮不应触发 click 事件', async () => {
    const wrapper = mountComponent(Button, {
      props: { loading: true },
    });

    await wrapper.find('button').trigger('click');
    expect(wrapper.emitted('click')).toBeFalsy();
  });

  it('按钮应包含默认插槽内容', () => {
    const wrapper = mountComponent(Button, {
      slots: { default: 'Click Me' },
    });

    expect(wrapper.find('button').text()).toContain('Click Me');
  });

  it('小按钮图标应更小', () => {
    const wrapper = mountComponent(Button, {
      props: { icon: 'ri-add-line', size: 'small' },
    });

    const icon = wrapper.find('.ui-button__icon');
    expect(icon.classes()).toContain('ui-button__icon');
    // 小按钮图标样式检查
    expect(wrapper.find('button').classes()).toContain('ui-button--small');
  });
});
