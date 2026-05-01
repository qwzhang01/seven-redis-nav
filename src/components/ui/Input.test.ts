import { describe, it, expect } from 'vitest';
import { mountComponent } from '@/test/utils';
import Input from './Input.vue';

describe('Input', () => {
  it('应该正确渲染默认输入框', () => {
    const wrapper = mountComponent(Input, {
      props: {},
    });

    expect(wrapper.exists()).toBe(true);
    expect(wrapper.find('input').exists()).toBe(true);
    expect(wrapper.find('input').classes()).toContain('ui-input');
    expect(wrapper.find('input').classes()).toContain('ui-input--medium');
    expect(wrapper.find('input').classes()).toContain('ui-input--default');
  });

  it('应该正确绑定 modelValue', () => {
    const wrapper = mountComponent(Input, {
      props: { modelValue: 'hello' },
    });

    const input = wrapper.find('input');
    expect((input.element as HTMLInputElement).value).toBe('hello');
  });

  it('应该渲染不同 size', () => {
    const sizes = ['small', 'medium', 'large'] as const;
    for (const size of sizes) {
      const wrapper = mountComponent(Input, { props: { size } });
      expect(wrapper.find('input').classes()).toContain(`ui-input--${size}`);
    }
  });

  it('应该渲染不同 type', () => {
    const types = ['text', 'password', 'number', 'email', 'search'] as const;
    for (const type of types) {
      const wrapper = mountComponent(Input, { props: { type } });
      expect(wrapper.find('input').attributes('type')).toBe(type);
    }
  });

  it('disabled 为 true 时输入框应被禁用', () => {
    const wrapper = mountComponent(Input, {
      props: { disabled: true },
    });

    const input = wrapper.find('input');
    expect(input.attributes('disabled')).toBeDefined();
    // 验证 disabled 样式效果
    expect(input.classes()).toContain('ui-input');
  });

  it('readonly 为 true 时输入框应为只读', () => {
    const wrapper = mountComponent(Input, {
      props: { readonly: true },
    });

    const input = wrapper.find('input');
    expect(input.attributes('readonly')).toBeDefined();
  });

  it('应该显示 placeholder', () => {
    const wrapper = mountComponent(Input, {
      props: { placeholder: 'Enter text' },
    });

    expect(wrapper.find('input').attributes('placeholder')).toBe('Enter text');
  });

  it('应该渲染状态样式', () => {
    const statuses = ['success', 'warning', 'error'] as const;
    for (const status of statuses) {
      const wrapper = mountComponent(Input, { props: { status } });
      expect(wrapper.find('input').classes()).toContain(`ui-input--${status}`);
    }
  });

  it('应该显示消息文本', () => {
    const wrapper = mountComponent(Input, {
      props: { message: 'Field is required', status: 'error' },
    });

    const message = wrapper.find('.ui-input__message');
    expect(message.exists()).toBe(true);
    expect(message.text()).toBe('Field is required');
    expect(message.classes()).toContain('ui-input__message--error');
  });

  it('输入时应触发 update:modelValue 和 change 事件', async () => {
    const wrapper = mountComponent(Input, {
      props: { modelValue: '' },
    });

    const input = wrapper.find('input');
    await input.setValue('test value');

    expect(wrapper.emitted('update:modelValue')).toBeTruthy();
    expect(wrapper.emitted('update:modelValue')![0]).toEqual(['test value']);
    expect(wrapper.emitted('change')).toBeTruthy();
    expect(wrapper.emitted('change')![0]).toEqual(['test value']);
  });

  it('focus 和 blur 应触发相应事件', async () => {
    const wrapper = mountComponent(Input, {
      props: { modelValue: '' },
    });

    const input = wrapper.find('input');
    await input.trigger('focus');
    expect(wrapper.emitted('focus')).toBeTruthy();

    await input.trigger('blur');
    expect(wrapper.emitted('blur')).toBeTruthy();
  });

  it('禁用输入框不应触发事件', async () => {
    const wrapper = mountComponent(Input, {
      props: { disabled: true, modelValue: '' },
    });

    const input = wrapper.find('input');
    await input.setValue('test');
    expect(wrapper.emitted('update:modelValue')).toBeFalsy();
  });

  it('只读输入框不应触发事件', async () => {
    const wrapper = mountComponent(Input, {
      props: { readonly: true, modelValue: '' },
    });

    const input = wrapper.find('input');
    await input.setValue('test');
    expect(wrapper.emitted('update:modelValue')).toBeFalsy();
  });

  it('应该接受前后图标 props', () => {
    const wrapper = mountComponent(Input, {
      props: { prefixIcon: 'ri-search-line', suffixIcon: 'ri-close-line' },
    });

    // 验证 props 正确传递
    expect((wrapper.props() as Record<string, unknown>).prefixIcon).toBe('ri-search-line');
    expect((wrapper.props() as Record<string, unknown>).suffixIcon).toBe('ri-close-line');
  });
});
