import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import BrowserWorkspace from './BrowserWorkspace.vue'
import { useDataStore } from '@/stores/data'
import { useConnectionStore } from '@/stores/connection'
import { keyGet } from '@/ipc/data.ts'

// Mock child components
vi.mock('./StringViewer.vue', () => ({
  default: {
    template: '<div class="mock-string-viewer">String Viewer</div>',
    props: ['detail']
  }
}))

vi.mock('./HashViewer.vue', () => ({
  default: {
    template: '<div class="mock-hash-viewer">Hash Viewer</div>',
    props: ['detail']
  }
}))

vi.mock('./ListViewer.vue', () => ({
  default: {
    template: '<div class="mock-list-viewer">List Viewer</div>',
    props: ['detail']
  }
}))

vi.mock('./SetViewer.vue', () => ({
  default: {
    template: '<div class="mock-set-viewer">Set Viewer</div>',
    props: ['detail']
  }
}))

vi.mock('./ZSetViewer.vue', () => ({
  default: {
    template: '<div class="mock-zset-viewer">ZSet Viewer</div>',
    props: ['detail']
  }
}))

// Mock IPC functions
vi.mock('@/ipc/data.ts', () => ({
  keyGet: vi.fn(),
  keySet: vi.fn(),
  keyDelete: vi.fn(),
  keyRename: vi.fn(),
  keyTtlSet: vi.fn()
}))

describe('BrowserWorkspace Integration Tests', () => {
  let wrapper: any
  let dataStore: ReturnType<typeof useDataStore>
  let connectionStore: ReturnType<typeof useConnectionStore>

  const mockKeyDetail = {
    key: 'test:string:key',
    key_type: 'string' as const,
    value: { type: 'string' as const, value: 'test value' },
    ttl: -1,
    size: 10,
    encoding: 'raw',
    length: 1,
    db: 0
  }

  const mockHashDetail = {
    key: 'test:hash:key',
    key_type: 'hash' as const,
    value: { type: 'hash' as const, fields: [['field1', 'value1'], ['field2', 'value2']] as [string, string][] },
    ttl: 3600,
    size: 100,
    encoding: 'hashtable',
    length: 2,
    db: 0
  }

  beforeEach(async () => {
    setActivePinia(createPinia())
    dataStore = useDataStore()
    connectionStore = useConnectionStore()

    // Setup mock connection
    connectionStore.activeConnId = 'test-connection'
    connectionStore.sessionStates = { 'test-connection': 'connected' }

    vi.clearAllMocks()
  })

  describe('Empty State', () => {
    it('没有当前键时应该显示空状态', () => {
      dataStore.currentKey = null

      wrapper = mount(BrowserWorkspace)

      expect(wrapper.find('.bw-empty').exists()).toBe(true)
      expect(wrapper.find('.bw-empty i').classes()).toContain('ri-key-2-line')
      expect(wrapper.find('.bw-empty p').text()).toBe('从左侧选择一个键查看详情')
    })
  })

  describe('Key Display', () => {
    beforeEach(() => {
      dataStore.currentKey = mockKeyDetail
    })

    it('应该正确显示键信息', () => {
      wrapper = mount(BrowserWorkspace)

      expect(wrapper.find('.bw-header').exists()).toBe(true)
      expect(wrapper.find('.bw-type-badge').text()).toBe('string')
      expect(wrapper.find('.bw-type-badge').classes()).toContain('type-string')
      expect(wrapper.find('.bw-key-text').text()).toBe('test:string:key')
    })

    it('应该正确显示元数据', () => {
      wrapper = mount(BrowserWorkspace)

      const meta = wrapper.find('.bw-meta')
      expect(meta.text()).toContain('DB 0')
      expect(meta.text()).toContain('TTL: 永久')
      expect(meta.text()).toContain('10 B')
      expect(meta.text()).toContain('raw')
      expect(meta.text()).toContain('1 个元素')
    })

    it('应该支持不同的键类型样式', () => {
      dataStore.currentKey = mockHashDetail
      wrapper = mount(BrowserWorkspace)

      expect(wrapper.find('.bw-type-badge').text()).toBe('hash')
      expect(wrapper.find('.bw-type-badge').classes()).toContain('type-hash')
      expect(wrapper.find('.bw-meta').text()).toContain('TTL: 1h 0m')
      expect(wrapper.find('.bw-meta').text()).toContain('100 B')
    })
  })

  describe('Tab Navigation', () => {
    beforeEach(() => {
      dataStore.currentKey = mockKeyDetail
      wrapper = mount(BrowserWorkspace)
    })

    it('应该正确显示标签页', () => {
      const tabs = wrapper.findAll('.bw-tab')
      expect(tabs).toHaveLength(3)
      expect(tabs[0].text()).toBe('数据')
      expect(tabs[1].text()).toBe('原始 (JSON)')
      expect(tabs[2].text()).toBe('相关命令')
    })

    it('应该默认激活数据标签页', () => {
      expect(wrapper.find('.bw-tab.active').text()).toBe('数据')
      expect(wrapper.find('.mock-string-viewer').exists()).toBe(true)
    })

    it('应该支持标签页切换', async () => {
      const tabs = wrapper.findAll('.bw-tab')

      // 切换到原始标签页
      await tabs[1].trigger('click')
      expect(wrapper.find('.bw-tab.active').text()).toBe('原始 (JSON)')
      expect(wrapper.find('.bw-raw').exists()).toBe(true)

      // 切换到命令标签页
      await tabs[2].trigger('click')
      expect(wrapper.find('.bw-tab.active').text()).toBe('相关命令')
      expect(wrapper.find('.bw-commands').exists()).toBe(true)

      // 切换回数据标签页
      await tabs[0].trigger('click')
      expect(wrapper.find('.bw-tab.active').text()).toBe('数据')
      expect(wrapper.find('.mock-string-viewer').exists()).toBe(true)
    })
  })

  describe('Data Viewer Integration', () => {
    it('应该根据键类型显示对应的查看器', () => {
      dataStore.currentKey = mockKeyDetail
      wrapper = mount(BrowserWorkspace)

      expect(wrapper.find('.mock-string-viewer').exists()).toBe(true)
      expect(wrapper.findComponent({ name: 'StringViewer' }).props('detail')).toEqual(mockKeyDetail)
    })

    it('应该支持哈希类型查看器', () => {
      dataStore.currentKey = mockHashDetail
      wrapper = mount(BrowserWorkspace)

      expect(wrapper.find('.mock-hash-viewer').exists()).toBe(true)
      expect(wrapper.findComponent({ name: 'HashViewer' }).props('detail')).toEqual(mockHashDetail)
    })

    it('不支持的键类型应该显示错误信息', () => {
      dataStore.currentKey = { ...mockKeyDetail, key_type: 'unsupported' as any, value: { type: 'string' as const, value: 'test value' } }
      wrapper = mount(BrowserWorkspace)

      expect(wrapper.find('.bw-unsupported').exists()).toBe(true)
      expect(wrapper.find('.bw-unsupported p').text()).toContain('暂不支持 unsupported 类型的查看器')
    })
  })

  describe('Raw JSON Display', () => {
    beforeEach(() => {
      dataStore.currentKey = mockKeyDetail
      wrapper = mount(BrowserWorkspace)
    })

    it('应该正确显示原始JSON数据', async () => {
      await wrapper.findAll('.bw-tab')[1].trigger('click')

      const rawContent = wrapper.find('.bw-raw')
      expect(rawContent.exists()).toBe(true)
      expect(rawContent.text()).toContain('"test value"')
    })
  })

  describe('Commands Display', () => {
    beforeEach(() => {
      dataStore.currentKey = mockKeyDetail
      wrapper = mount(BrowserWorkspace)
    })

    it('应该显示相关命令列表', async () => {
      await wrapper.findAll('.bw-tab')[2].trigger('click')

      const commands = wrapper.findAll('.bw-cmd-item')
      expect(commands.length).toBeGreaterThan(0)
      expect(commands[0].text()).toContain('GET')
      expect(commands[1].text()).toContain('SET')
    })
  })

  describe('Action Buttons', () => {
    beforeEach(() => {
      dataStore.currentKey = mockKeyDetail
      wrapper = mount(BrowserWorkspace)
    })

    it('应该显示所有操作按钮', () => {
      const buttons = wrapper.findAll('.bw-btn')
      expect(buttons).toHaveLength(4)

      expect(buttons[0].find('i').classes()).toContain('ri-refresh-line')
      expect(buttons[1].find('i').classes()).toContain('ri-edit-line')
      expect(buttons[2].find('i').classes()).toContain('ri-time-line')
      expect(buttons[3].find('i').classes()).toContain('ri-delete-bin-line')
    })

    it('刷新按钮应该调用数据加载', async () => {
      const keyGetMock = vi.fn().mockResolvedValue(mockKeyDetail)
      vi.mocked(keyGet).mockImplementation(keyGetMock)

      await wrapper.findAll('.bw-btn')[0].trigger('click')

      expect(keyGetMock).toHaveBeenCalledWith('test-connection', 'test:string:key')
    })

    it('重命名按钮应该打开对话框', async () => {
      await wrapper.findAll('.bw-btn')[1].trigger('click')

      expect(wrapper.vm.showRenameDialog).toBe(true)
      expect(wrapper.vm.newKeyName).toBe('test:string:key')
    })

    it('TTL按钮应该打开对话框', async () => {
      await wrapper.findAll('.bw-btn')[2].trigger('click')

      expect(wrapper.vm.showTtlDialog).toBe(true)
    })

    it('删除按钮应该打开对话框', async () => {
      await wrapper.findAll('.bw-btn')[3].trigger('click')

      expect(wrapper.vm.showDeleteDialog).toBe(true)
    })
  })

  describe('Dialog Interactions', () => {
    beforeEach(() => {
      dataStore.currentKey = mockKeyDetail
      wrapper = mount(BrowserWorkspace)
    })

    it('删除对话框应该要求确认输入', async () => {
      await wrapper.findAll('.bw-btn')[3].trigger('click')

      expect(wrapper.find('.modal-overlay').exists()).toBe(true)
      expect(wrapper.find('.key-confirm-name').text()).toBe('test:string:key')

      const confirmButton = wrapper.find('.btn-danger')
      expect(confirmButton.attributes('disabled')).toBeDefined()
    })

    it('重命名对话框应该验证输入', async () => {
      await wrapper.findAll('.bw-btn')[1].trigger('click')

      const saveButton = wrapper.find('.btn-save')
      expect(saveButton.attributes('disabled')).toBeDefined()

      await wrapper.find('.confirm-input').setValue('new:key:name')
      expect(saveButton.attributes('disabled')).toBeUndefined()
    })

    it('TTL对话框应该支持单位选择', async () => {
      await wrapper.findAll('.bw-btn')[2].trigger('click')

      const ttlInput = wrapper.find('input[type="number"]')
      const unitSelect = wrapper.find('.ttl-unit')

      await ttlInput.setValue(60)
      await unitSelect.setValue('m')

      expect(wrapper.vm.ttlValue).toBe(60)
      expect(wrapper.vm.ttlUnit).toBe('m')
      expect(wrapper.vm.ttlInSeconds).toBe(3600)
    })
  })

  describe('Toast Notifications', () => {
    beforeEach(() => {
      dataStore.currentKey = mockKeyDetail
      wrapper = mount(BrowserWorkspace)
    })

    it('成功操作应该显示成功提示', async () => {
      const keyGetMock = vi.fn().mockResolvedValue(mockKeyDetail)
      vi.mocked(keyGet).mockImplementation(keyGetMock)

      await wrapper.vm.handleRefresh()

      expect(wrapper.vm.toast).toEqual({ msg: '已刷新', type: 'success' })
      expect(wrapper.find('.bw-toast').exists()).toBe(true)
      expect(wrapper.find('.bw-toast').text()).toContain('已刷新')
    })

    it('错误操作应该显示错误提示', async () => {
      const keyGetMock = vi.fn().mockRejectedValue(new Error('Connection failed'))
      vi.mocked(keyGet).mockImplementation(keyGetMock)

      await wrapper.vm.handleRefresh()

      expect(wrapper.vm.toast.msg).toContain('刷新失败');
      expect(wrapper.vm.toast.type).toBe('error');
    })
  })

  describe('Connection State Integration', () => {
    it('没有活动连接时应该禁用操作', async () => {
      connectionStore.activeConnId = null
      dataStore.currentKey = mockKeyDetail
      wrapper = mount(BrowserWorkspace)

      const keyGetMock = vi.fn()
      vi.mocked(keyGet).mockImplementation(keyGetMock)

      await wrapper.vm.handleRefresh()

      expect(keyGetMock).not.toHaveBeenCalled()
    })
  })
})
