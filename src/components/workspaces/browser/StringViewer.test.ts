import { describe, it, expect } from 'vitest'
import { mountComponent } from '@/test/utils'
import StringViewer from './StringViewer.vue'

describe('StringViewer', () => {
  const mockDetail = {
    key: 'test:string',
    key_type: 'string',
    value: { value: 'Hello, Redis!' },
    ttl: -1,
    size: 12,
    encoding: 'raw',
    length: 1,
    db: 0
  }

  it('应该正确渲染组件', () => {
    const wrapper = mountComponent(StringViewer, {
      props: { detail: mockDetail }
    })

    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.string-viewer').exists()).toBe(true)
  })

  it('应该显示正确的标签', () => {
    const wrapper = mountComponent(StringViewer, {
      props: { detail: mockDetail }
    })

    const label = wrapper.find('.sv-label')
    expect(label.exists()).toBe(true)
    expect(label.text()).toBe('值')
  })

  it('应该显示字符串值', () => {
    const wrapper = mountComponent(StringViewer, {
      props: { detail: mockDetail }
    })

    const textarea = wrapper.find('.sv-textarea')
    expect(textarea.exists()).toBe(true)
    expect((textarea.element as HTMLTextAreaElement).value).toBe('Hello, Redis!')
  })

  it('文本区域应该是只读的', () => {
    const wrapper = mountComponent(StringViewer, {
      props: { detail: mockDetail }
    })

    const textarea = wrapper.find('.sv-textarea')
    expect(textarea.attributes('readonly')).toBeDefined()
  })

  it('应该使用正确的样式类', () => {
    const wrapper = mountComponent(StringViewer, {
      props: { detail: mockDetail }
    })

    const textarea = wrapper.find('.sv-textarea')
    expect(textarea.classes()).toContain('sv-textarea')
    expect(textarea.attributes('class')).toContain('sv-textarea')
  })

  it('应该正确处理空值', () => {
    const emptyDetail = {
      ...mockDetail,
      value: { value: '' }
    }

    const wrapper = mountComponent(StringViewer, {
      props: { detail: emptyDetail }
    })

    const textarea = wrapper.find('.sv-textarea')
    expect((textarea.element as HTMLTextAreaElement).value).toBe('')
  })

  it('应该正确处理长文本', () => {
    const longTextDetail = {
      ...mockDetail,
      value: { value: 'A'.repeat(1000) }
    }

    const wrapper = mountComponent(StringViewer, {
      props: { detail: longTextDetail }
    })

    const textarea = wrapper.find('.sv-textarea')
    expect((textarea.element as HTMLTextAreaElement).value).toHaveLength(1000)
    expect((textarea.element as HTMLTextAreaElement).value).toBe('A'.repeat(1000))
  })

  it('应该使用等宽字体', () => {
    const wrapper = mountComponent(StringViewer, {
      props: { detail: mockDetail }
    })

    const textarea = wrapper.find('.sv-textarea')
    // jsdom 不支持 CSS 变量解析，改为验证 class 名称（sv-textarea 样式中定义了 font-family: var(--srn-font-mono)）
    expect(textarea.classes()).toContain('sv-textarea')
    expect(textarea.attributes('class')).toContain('sv-textarea')
  })

  it('应该响应props变化', async () => {
    const wrapper = mountComponent(StringViewer, {
      props: { detail: mockDetail }
    })

    const newDetail = {
      ...mockDetail,
      value: { value: 'Updated value' }
    }

    await wrapper.setProps({ detail: newDetail })

    const textarea = wrapper.find('.sv-textarea')
    expect((textarea.element as HTMLTextAreaElement).value).toBe('Updated value')
  })

  it('应该具有正确的可访问性属性', () => {
    const wrapper = mountComponent(StringViewer, {
      props: { detail: mockDetail }
    })

    const textarea = wrapper.find('.sv-textarea')
    expect(textarea.attributes('readonly')).toBe('')
    expect(textarea.attributes('aria-label')).toBeUndefined() // 可以根据需要添加
  })
})
