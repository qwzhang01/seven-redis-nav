import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDataStore } from './data'
import { useConnectionStore } from './connection'
import { keyGet, keySet, keyDelete, keyRename, keyTtlSet } from '@/ipc/data'

// Mock IPC functions
vi.mock('@/ipc/data', () => ({
  keyGet: vi.fn(),
  keySet: vi.fn(),
  keyDelete: vi.fn(),
  keyRename: vi.fn(),
  keyTtlSet: vi.fn()
}))

// Mock connection store
vi.mock('./connection', () => ({
  useConnectionStore: vi.fn()
}))

describe('Data Store', () => {
  let dataStore: ReturnType<typeof useDataStore>
  let mockConnectionStore: any

  const mockKeyDetail = {
    key: 'test:key',
    key_type: 'string' as const,
    value: { type: 'string' as const, value: 'test value' },
    ttl: -1,
    size: 10,
    encoding: 'raw',
    length: 1,
    db: 0
  }

  beforeEach(() => {
    setActivePinia(createPinia())

    // Reset all mocks
    vi.clearAllMocks()

    // Setup connection store mock
    mockConnectionStore = {
      activeConnId: 'test-connection'
    }
    ;(useConnectionStore as any).mockReturnValue(mockConnectionStore)

    dataStore = useDataStore()
  })

  describe('Initial State', () => {
    it('应该正确初始化状态', () => {
      expect(dataStore.currentKey).toBe(null)
      expect(dataStore.loading).toBe(false)
      expect(dataStore.editingField).toBe(null)
    })
  })

  describe('loadKey', () => {
    it('应该成功加载键', async () => {
      ;(keyGet as any).mockResolvedValue(mockKeyDetail)

      await dataStore.loadKey('test:key')

      expect(keyGet).toHaveBeenCalledWith('test-connection', 'test:key')
      expect(dataStore.currentKey).toEqual(mockKeyDetail)
      expect(dataStore.loading).toBe(false)
    })

    it('应该在加载过程中设置loading状态', async () => {
      let resolvePromise: (value: any) => void
      const promise = new Promise(resolve => {
        resolvePromise = resolve
      })
      ;(keyGet as any).mockReturnValue(promise)

      const loadPromise = dataStore.loadKey('test:key')

      expect(dataStore.loading).toBe(true)

      resolvePromise!(mockKeyDetail)
      await loadPromise

      expect(dataStore.loading).toBe(false)
    })

    it('没有活动连接时应该不执行操作', async () => {
      mockConnectionStore.activeConnId = null

      await dataStore.loadKey('test:key')

      expect(keyGet).not.toHaveBeenCalled()
    })

    it('应该处理加载错误', async () => {
      ;(keyGet as any).mockRejectedValue(new Error('Connection failed'))

      await expect(dataStore.loadKey('test:key')).rejects.toThrow('Connection failed')
      expect(dataStore.loading).toBe(false)
    })
  })

  describe('createKey', () => {
    it('应该成功创建键', async () => {
      ;(keySet as any).mockResolvedValue(undefined)

      await dataStore.createKey('new:key', 'value', 'string')

      expect(keySet).toHaveBeenCalledWith('test-connection', 'new:key', 'value', 'string')
    })

    it('没有活动连接时应该不执行操作', async () => {
      mockConnectionStore.activeConnId = null

      await dataStore.createKey('new:key', 'value', 'string')

      expect(keySet).not.toHaveBeenCalled()
    })
  })

  describe('updateKey', () => {
    it('应该成功更新键', async () => {
      ;(keySet as any).mockResolvedValue(undefined)
      ;(keyGet as any).mockResolvedValue(mockKeyDetail)

      await dataStore.updateKey('test:key', 'updated value', 'string')

      expect(keySet).toHaveBeenCalledWith('test-connection', 'test:key', 'updated value', 'string')
      expect(keyGet).toHaveBeenCalledWith('test-connection', 'test:key')
    })

    it('应该重新加载更新后的键', async () => {
      ;(keySet as any).mockResolvedValue(undefined)
      ;(keyGet as any).mockResolvedValue(mockKeyDetail)

      await dataStore.updateKey('test:key', 'updated value', 'string')

      expect(dataStore.currentKey).toEqual(mockKeyDetail)
    })
  })

  describe('deleteKey', () => {
    it('应该成功删除键', async () => {
      ;(keyDelete as any).mockResolvedValue(undefined)

      await dataStore.deleteKey('test:key')

      expect(keyDelete).toHaveBeenCalledWith('test-connection', 'test:key')
    })

    it('删除当前键时应该清除currentKey', async () => {
      dataStore.currentKey = mockKeyDetail
      ;(keyDelete as any).mockResolvedValue(undefined)

      await dataStore.deleteKey('test:key')

      expect(dataStore.currentKey).toBe(null)
    })

    it('删除非当前键时不应该清除currentKey', async () => {
      dataStore.currentKey = mockKeyDetail
      ;(keyDelete as any).mockResolvedValue(undefined)

      await dataStore.deleteKey('other:key')

      expect(dataStore.currentKey).toEqual(mockKeyDetail)
    })
  })

  describe('renameKey', () => {
    it('应该成功重命名键', async () => {
      ;(keyRename as any).mockResolvedValue(undefined)
      ;(keyGet as any).mockResolvedValue(mockKeyDetail)

      await dataStore.renameKey('old:key', 'new:key')

      expect(keyRename).toHaveBeenCalledWith('test-connection', 'old:key', 'new:key')
      expect(keyGet).toHaveBeenCalledWith('test-connection', 'new:key')
    })
  })

  describe('setTtl', () => {
    it('应该成功设置TTL', async () => {
      ;(keyTtlSet as any).mockResolvedValue(undefined)
      ;(keyGet as any).mockResolvedValue(mockKeyDetail)

      await dataStore.setTtl('test:key', 3600)

      expect(keyTtlSet).toHaveBeenCalledWith('test-connection', 'test:key', 3600)
      expect(keyGet).toHaveBeenCalledWith('test-connection', 'test:key')
    })
  })

  describe('setEditingField', () => {
    it('应该设置编辑字段', () => {
      dataStore.setEditingField('field1')
      expect(dataStore.editingField).toBe('field1')
    })

    it('应该清除编辑字段', () => {
      dataStore.editingField = 'field1'
      dataStore.setEditingField(null)
      expect(dataStore.editingField).toBe(null)
    })
  })

  describe('clearCurrentKey', () => {
    it('应该清除当前键', () => {
      dataStore.currentKey = mockKeyDetail
      dataStore.clearCurrentKey()
      expect(dataStore.currentKey).toBe(null)
    })
  })

  describe('Error Handling', () => {
    it('应该处理IPC错误', async () => {
      ;(keyGet as any).mockRejectedValue(new Error('IPC Error'))

      await expect(dataStore.loadKey('test:key')).rejects.toThrow('IPC Error')
      expect(dataStore.loading).toBe(false)
    })

    it('应该处理连接丢失错误', async () => {
      mockConnectionStore.activeConnId = null

      await dataStore.loadKey('test:key')
      expect(keyGet).not.toHaveBeenCalled()
    })
  })

  describe('State Transitions', () => {
    it('应该在操作期间正确管理loading状态', async () => {
      let resolvePromise: (value: any) => void
      const promise = new Promise(resolve => {
        resolvePromise = resolve
      })
      ;(keyGet as any).mockReturnValue(promise)

      const loadPromise = dataStore.loadKey('test:key')

      // 检查loading状态变化
      expect(dataStore.loading).toBe(true)

      resolvePromise!(mockKeyDetail)
      await loadPromise

      expect(dataStore.loading).toBe(false)
    })

    it('应该正确更新currentKey状态', async () => {
      ;(keyGet as any).mockResolvedValue(mockKeyDetail)

      await dataStore.loadKey('test:key')
      expect(dataStore.currentKey).toEqual(mockKeyDetail)

      dataStore.clearCurrentKey()
      expect(dataStore.currentKey).toBe(null)
    })
  })
})
