import { describe, it, expect, beforeEach } from 'vitest'
import { mountComponent, waitForNextTick } from '@/test/utils'
import HashViewer from './HashViewer.vue'
import { createPinia, setActivePinia } from 'pinia'

describe('HashViewer', () => {
  const mockDetail = {
    key: 'test:hash',
    key_type: 'hash',
    value: {
      fields: [
        ['name', 'John Doe'],
        ['email', 'john@example.com'],
        ['age', '30']
      ]
    },
    ttl: 3600,
    size: 45,
    encoding: 'hashtable',
    length: 3,
    db: 0
  }

  beforeEach(() => {
    const pinia = createPinia()
    setActivePinia(pinia)
  })

  it('应该正确渲染组件', () => {
    const wrapper = mountComponent(HashViewer, {
      props: { detail: mockDetail }
    })

    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.hash-viewer').exists()).toBe(true)
    expect(wrapper.find('.hv-table').exists()).toBe(true)
  })

  it('应该显示表头', () => {
    const wrapper = mountComponent(HashViewer, {
      props: { detail: mockDetail }
    })

    const headers = wrapper.findAll('th')
    expect(headers).toHaveLength(3)
    expect(headers[0].text()).toBe('字段')
    expect(headers[1].text()).toBe('值')
    expect(headers[2].text()).toBe('操作')
  })

  it('应该显示所有哈希字段', () => {
    const wrapper = mountComponent(HashViewer, {
      props: { detail: mockDetail }
    })

    const rows = wrapper.findAll('tbody tr')
    expect(rows).toHaveLength(3)

    const cells = wrapper.findAll('tbody td.field-cell')
    expect(cells).toHaveLength(3)
    expect(cells[0].text()).toBe('name')
    expect(cells[1].text()).toBe('email')
    expect(cells[2].text()).toBe('age')
  })

  it('应该显示所有哈希值', () => {
    const wrapper = mountComponent(HashViewer, {
      props: { detail: mockDetail }
    })

    const cells = wrapper.findAll('tbody td.value-cell')
    expect(cells).toHaveLength(3)
    expect(cells[0].text()).toBe('John Doe')
    expect(cells[1].text()).toBe('john@example.com')
    expect(cells[2].text()).toBe('30')
  })

  it('应该显示编辑按钮', () => {
    const wrapper = mountComponent(HashViewer, {
      props: { detail: mockDetail }
    })

    const editButtons = wrapper.findAll('.act-btn.edit')
    expect(editButtons).toHaveLength(3)
    expect(editButtons[0].find('i').classes()).toContain('ri-edit-line')
  })

  it('点击编辑按钮应该进入编辑模式', async () => {
    const wrapper = mountComponent(HashViewer, {
      props: { detail: mockDetail }
    })

    const editButton = wrapper.findAll('.act-btn.edit')[0]
    await editButton.trigger('click')

    await waitForNextTick()

    const input = wrapper.find('.inline-input')
    expect(input.exists()).toBe(true)
    expect((input.element as HTMLInputElement).value).toBe('John Doe')

    const saveButton = wrapper.find('.act-btn.save')
    const cancelButton = wrapper.find('.act-btn.cancel')
    expect(saveButton.exists()).toBe(true)
    expect(cancelButton.exists()).toBe(true)
  })

  it('双击值应该进入编辑模式', async () => {
    const wrapper = mountComponent(HashViewer, {
      props: { detail: mockDetail }
    })

    const valueSpan = wrapper.findAll('tbody td.value-cell span')[0]
    await valueSpan.trigger('dblclick')

    await waitForNextTick()

    const input = wrapper.find('.inline-input')
    expect(input.exists()).toBe(true)
    expect((input.element as HTMLInputElement).value).toBe('John Doe')
  })

  it('按Enter键应该保存编辑', async () => {
    const wrapper = mountComponent(HashViewer, {
      props: { detail: mockDetail }
    })

    const editButton = wrapper.findAll('.act-btn.edit')[0]
    await editButton.trigger('click')
    await waitForNextTick()

    const input = wrapper.find('.inline-input')
    await input.setValue('Updated Name')
    await input.trigger('keydown.enter')

    await waitForNextTick()

    // 应该退出编辑模式
    expect(wrapper.find('.inline-input').exists()).toBe(false)
  })

  it('按Escape键应该取消编辑', async () => {
    const wrapper = mountComponent(HashViewer, {
      props: { detail: mockDetail }
    })

    const editButton = wrapper.findAll('.act-btn.edit')[0]
    await editButton.trigger('click')
    await waitForNextTick()

    const input = wrapper.find('.inline-input')
    await input.setValue('Updated Name')
    await input.trigger('keydown.escape')

    await waitForNextTick()

    // 应该退出编辑模式，值不变
    expect(wrapper.find('.inline-input').exists()).toBe(false)
    const valueSpan = wrapper.findAll('tbody td.value-cell span')[0]
    expect(valueSpan.text()).toBe('John Doe')
  })

  it('点击保存按钮应该保存编辑', async () => {
    const wrapper = mountComponent(HashViewer, {
      props: { detail: mockDetail }
    })

    const editButton = wrapper.findAll('.act-btn.edit')[0]
    await editButton.trigger('click')
    await waitForNextTick()

    const input = wrapper.find('.inline-input')
    await input.setValue('Updated Name')

    const saveButton = wrapper.find('.act-btn.save')
    await saveButton.trigger('click')

    await waitForNextTick()

    // 应该退出编辑模式
    expect(wrapper.find('.inline-input').exists()).toBe(false)
  })

  it('点击取消按钮应该取消编辑', async () => {
    const wrapper = mountComponent(HashViewer, {
      props: { detail: mockDetail }
    })

    const editButton = wrapper.findAll('.act-btn.edit')[0]
    await editButton.trigger('click')
    await waitForNextTick()

    const input = wrapper.find('.inline-input')
    await input.setValue('Updated Name')

    const cancelButton = wrapper.find('.act-btn.cancel')
    await cancelButton.trigger('click')

    await waitForNextTick()

    // 应该退出编辑模式，值不变
    expect(wrapper.find('.inline-input').exists()).toBe(false)
    const valueSpan = wrapper.findAll('tbody td.value-cell span')[0]
    expect(valueSpan.text()).toBe('John Doe')
  })

  it('应该正确处理空哈希', () => {
    const emptyDetail = {
      ...mockDetail,
      value: { fields: [] },
      length: 0
    }

    const wrapper = mountComponent(HashViewer, {
      props: { detail: emptyDetail }
    })

    const rows = wrapper.findAll('tbody tr')
    expect(rows).toHaveLength(0)
  })

  it('应该使用正确的样式类', () => {
    const wrapper = mountComponent(HashViewer, {
      props: { detail: mockDetail }
    })

    const table = wrapper.find('.hv-table')
    expect(table.exists()).toBe(true)
    expect(table.classes()).toContain('hv-table')

    const fieldCells = wrapper.findAll('.field-cell')
    expect(fieldCells).toHaveLength(3)
    fieldCells.forEach(cell => {
      expect(cell.classes()).toContain('field-cell')
    })

    const valueCells = wrapper.findAll('.value-cell')
    expect(valueCells).toHaveLength(3)
    valueCells.forEach(cell => {
      expect(cell.classes()).toContain('value-cell')
    })
  })

  it('应该响应props变化', async () => {
    const wrapper = mountComponent(HashViewer, {
      props: { detail: mockDetail }
    })

    const newDetail = {
      ...mockDetail,
      value: {
        fields: [
          ['new_field', 'new_value']
        ]
      }
    }

    await wrapper.setProps({ detail: newDetail })

    const rows = wrapper.findAll('tbody tr')
    expect(rows).toHaveLength(1)

    const fieldCell = wrapper.find('tbody td.field-cell')
    expect(fieldCell.text()).toBe('new_field')

    const valueCell = wrapper.find('tbody td.value-cell')
    expect(valueCell.text()).toBe('new_value')
  })

  it('应该具有正确的可访问性属性', () => {
    const wrapper = mountComponent(HashViewer, {
      props: { detail: mockDetail }
    })

    const table = wrapper.find('table')
    expect(table.attributes('role')).toBeUndefined() // 可以根据需要添加

    const buttons = wrapper.findAll('button')
    buttons.forEach(button => {
      expect(button.attributes('type')).toBe('button')
    })
  })
})
