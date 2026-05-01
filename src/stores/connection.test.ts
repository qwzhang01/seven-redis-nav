import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useConnectionStore } from './connection'
import {
  connectionList,
  connectionSave,
  connectionDelete,
  connectionOpen,
  connectionClose,
  connectionOpenTemp,
  dbSelect
} from '@/ipc/connection.ts'
import { listenConnectionState } from '@/ipc/event.ts'

// Mock IPC functions
vi.mock('@/ipc/connection.ts', () => ({
  connectionList: vi.fn(),
  connectionSave: vi.fn(),
  connectionDelete: vi.fn(),
  connectionOpen: vi.fn(),
  connectionClose: vi.fn(),
  connectionOpenTemp: vi.fn(),
  dbSelect: vi.fn()
}))

// Mock event IPC
vi.mock('@/ipc/event.ts', () => ({
  listenConnectionState: vi.fn().mockResolvedValue(vi.fn())
}))

describe('Connection Store', () => {
  let connectionStore: ReturnType<typeof useConnectionStore>

  const mockConnections = [
    {
      id: 'conn1',
      name: 'Local Redis',
      group_name: 'Development',
      host: 'localhost',
      port: 6379,
      password: null,
      auth_db: 0,
      timeout_ms: 5000,
      sort_order: 0
    },
    {
      id: 'conn2',
      name: 'Production Redis',
      group_name: 'Production',
      host: 'redis.prod.com',
      port: 6379,
      password: 'secret',
      auth_db: 0,
      timeout_ms: 5000,
      sort_order: 1
    }
  ]

  const mockDbStats = [
    { index: 0, key_count: 100 },
    { index: 1, key_count: 50 }
  ]

  const mockQuickConnect = {
    host: 'localhost',
    port: 6379,
    password: undefined,
    timeout_ms: 5000
  }

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    connectionStore = useConnectionStore()
  })

  afterEach(() => {
    if (connectionStore.unlistenFn !== null) {
      connectionStore.stopListening()
    }
  })

  describe('Initial State', () => {
    it('应该正确初始化状态', () => {
      expect(connectionStore.connections).toEqual([])
      expect(connectionStore.activeConnId).toBe(null)
      expect(connectionStore.sessionStates).toEqual({})
      expect(connectionStore.dbStats).toEqual([])
      expect(connectionStore.currentDb).toBe(0)
      expect(connectionStore.serverVersion).toBe(null)
      expect(connectionStore.tempConnectionConfig).toBe(null)
      expect(connectionStore.unlistenFn).toBe(null)
    })

    it('应该正确计算computed属性', () => {
      expect(connectionStore.activeConnection).toBe(null)
      expect(connectionStore.isConnected).toBe(false)
      expect(connectionStore.isTempConnection).toBe(false)
    })
  })

  describe('loadConnections', () => {
    it('应该成功加载连接列表', async () => {
      ;(connectionList as any).mockResolvedValue(mockConnections)

      await connectionStore.loadConnections()

      expect(connectionList).toHaveBeenCalled()
      expect(connectionStore.connections).toEqual(mockConnections)
    })

    it('应该处理加载错误', async () => {
      ;(connectionList as any).mockRejectedValue(new Error('Load failed'))

      await expect(connectionStore.loadConnections()).rejects.toThrow('Load failed')
    })
  })

  describe('saveConnection', () => {
    it('应该成功保存连接', async () => {
      const newConfig = { ...mockConnections[0], id: '', name: 'New Connection' }
      ;(connectionSave as any).mockResolvedValue('new-conn-id')
      ;(connectionList as any).mockResolvedValue([...mockConnections, { ...newConfig, id: 'new-conn-id' }])

      const result = await connectionStore.saveConnection(newConfig)

      expect(connectionSave).toHaveBeenCalledWith(newConfig)
      expect(connectionList).toHaveBeenCalled()
      expect(result).toBe('new-conn-id')
    })
  })

  describe('deleteConnection', () => {
    beforeEach(async () => {
      ;(connectionList as any).mockResolvedValue(mockConnections)
      await connectionStore.loadConnections()
    })

    it('应该成功删除连接', async () => {
      ;(connectionDelete as any).mockResolvedValue(undefined)
      ;(connectionList as any).mockResolvedValue([mockConnections[1]])

      await connectionStore.deleteConnection('conn1')

      expect(connectionDelete).toHaveBeenCalledWith('conn1')
      expect(connectionList).toHaveBeenCalled()
    })

    it('删除活动连接时应该清除activeConnId', async () => {
      connectionStore.activeConnId = 'conn1'

      await connectionStore.deleteConnection('conn1')

      expect(connectionStore.activeConnId).toBe(null)
    })

    it('删除非活动连接时不应该清除activeConnId', async () => {
      connectionStore.activeConnId = 'conn2'

      await connectionStore.deleteConnection('conn1')

      expect(connectionStore.activeConnId).toBe('conn2')
    })
  })

  describe('openConnection', () => {
    beforeEach(async () => {
      connectionStore.activeConnId = null
      ;(connectionOpen as any).mockResolvedValue(undefined)
      ;(dbSelect as any).mockResolvedValue(mockDbStats)
    })

    it('应该成功打开连接', async () => {
      await connectionStore.openConnection('conn1')

      expect(connectionOpen).toHaveBeenCalledWith('conn1')
      expect(connectionStore.activeConnId).toBe('conn1')
      expect(connectionStore.sessionStates['conn1']).toBe('connected')
      expect(dbSelect).toHaveBeenCalledWith('conn1', 0)
      expect(connectionStore.dbStats).toEqual(mockDbStats)
      expect(connectionStore.currentDb).toBe(0)
    })
  })

  describe('openTempConnection', () => {
    beforeEach(async () => {
      connectionStore.activeConnId = null
      ;(connectionOpenTemp as any).mockResolvedValue('temp-conn-id')
      ;(dbSelect as any).mockResolvedValue(mockDbStats)
      await connectionStore.openTempConnection(mockQuickConnect)
    })

    it('应该成功打开临时连接', async () => {
      expect(connectionOpenTemp).toHaveBeenCalledWith(mockQuickConnect)
      expect(connectionStore.activeConnId).toBe('temp-conn-id')
      expect(connectionStore.sessionStates['temp-conn-id']).toBe('connected')
      expect(connectionStore.tempConnectionConfig).toEqual(mockQuickConnect)
      expect(dbSelect).toHaveBeenCalledWith('temp-conn-id', 0)
      expect(connectionStore.dbStats).toEqual(mockDbStats)
      expect(connectionStore.currentDb).toBe(0)
    })
  })

  describe('saveTempConnection', () => {
    beforeEach(async () => {
      connectionStore.activeConnId = 'temp-conn-id'
      ;(connectionOpenTemp as any).mockResolvedValue('temp-conn-id')
      ;(dbSelect as any).mockResolvedValue(mockDbStats)
      await connectionStore.openTempConnection(mockQuickConnect)
    })

    it('应该成功保存临时连接', async () => {
      ;(connectionSave as any).mockResolvedValue('new-conn-id')
      ;(connectionList as any).mockResolvedValue(mockConnections)
      ;(connectionClose as any).mockResolvedValue(undefined)
      ;(connectionOpen as any).mockResolvedValue(undefined)

      const newId = await connectionStore.saveTempConnection('My Redis')

      expect(connectionSave).toHaveBeenCalled()
      expect(connectionClose).toHaveBeenCalledWith('temp-conn-id')
      expect(connectionOpen).toHaveBeenCalledWith('new-conn-id')
      expect(newId).toBe('new-conn-id')
      expect(connectionStore.activeConnId).toBe('new-conn-id')
      expect(connectionStore.sessionStates['new-conn-id']).toBe('connected')
      expect(connectionStore.tempConnectionConfig).toBe(null)
    })

    it('没有临时连接时应该抛出错误', async () => {
      connectionStore.activeConnId = null

      await expect(connectionStore.saveTempConnection('My Redis')).rejects.toThrow('No temporary connection to save')
    })
  })

  describe('closeConnection', () => {
    it('应该成功关闭连接', async () => {
      connectionStore.activeConnId = 'conn1'
      ;(connectionClose as any).mockResolvedValue(undefined)

      await connectionStore.closeConnection('conn1')

      expect(connectionClose).toHaveBeenCalledWith('conn1')
      expect(connectionStore.sessionStates['conn1']).toBe('disconnected')
      expect(connectionStore.activeConnId).toBe(null)
    })

    it('关闭非活动连接时不应该清除状态', async () => {
      connectionStore.activeConnId = 'conn2'
      ;(connectionClose as any).mockResolvedValue(undefined)

      await connectionStore.closeConnection('conn1')

      expect(connectionClose).toHaveBeenCalledWith('conn1')
      expect(connectionStore.sessionStates['conn1']).toBe('disconnected')
      expect(connectionStore.activeConnId).toBe('conn2')
    })
  })

  describe('selectDb', () => {
    beforeEach(async () => {
      ;(connectionOpen as any).mockResolvedValue(undefined)
      ;(dbSelect as any).mockResolvedValue(mockDbStats)
      await connectionStore.openConnection('conn1')
    })

    it('应该成功选择数据库', async () => {
      const newDbStats = [{ db: 1, keys: 50, expires: 5, avg_ttl: 1800 }]
      ;(dbSelect as any).mockResolvedValue(newDbStats)

      await connectionStore.selectDb(1)

      expect(dbSelect).toHaveBeenCalledWith('conn1', 1)
      expect(connectionStore.dbStats).toEqual(newDbStats)
      expect(connectionStore.currentDb).toBe(1)
    })

    it('没有活动连接时应该不执行操作', async () => {
      connectionStore.activeConnId = null
      vi.clearAllMocks()

      await connectionStore.selectDb(1)

      expect(dbSelect).not.toHaveBeenCalled()
    })
  })

  describe('startListening', () => {
    beforeEach(() => {
      connectionStore.activeConnId = 'conn1'
    })

    it('应该开始监听连接状态', async () => {
      const mockUnlistenFn = vi.fn()
      ;(listenConnectionState as any).mockResolvedValue(mockUnlistenFn)

      await connectionStore.startListening()

      expect(listenConnectionState).toHaveBeenCalled()
      expect(connectionStore.unlistenFn).toBe(mockUnlistenFn)
    })

    it('已经监听时应该不重复监听', async () => {
      const mockUnlistenFn = vi.fn()
      ;(listenConnectionState as any).mockResolvedValue(mockUnlistenFn)
      connectionStore.unlistenFn = mockUnlistenFn

      await connectionStore.startListening()

      expect(listenConnectionState).not.toHaveBeenCalled()
    })
  })

  describe('stopListening', () => {
    it('应该停止监听连接状态', async () => {
      const mockUnlistenFn = vi.fn()
      connectionStore.unlistenFn = mockUnlistenFn

      await connectionStore.stopListening()

      expect(mockUnlistenFn).toHaveBeenCalled()
      expect(connectionStore.unlistenFn).toBe(null)
    })
  })

  describe('Connection State Events', () => {
    it('应该处理连接状态变化事件', async () => {
      connectionStore.activeConnId = 'conn1'
      let eventCallback: any = null
      ;(listenConnectionState as any).mockImplementation((callback: (event: any) => void) => {
        eventCallback = callback
        return Promise.resolve(vi.fn())
      })

      await connectionStore.startListening()

      eventCallback({
        conn_id: 'conn1',
        state: 'disconnected'
      })

      expect(connectionStore.sessionStates['conn1']).toBe('disconnected')
      expect(connectionStore.dbStats).toEqual([])
    })

    it('活动连接断开时应该清除数据库统计', async () => {
      connectionStore.activeConnId = 'conn1'
      connectionStore.dbStats = mockDbStats
      let eventCallback: any = null
      ;(listenConnectionState as any).mockImplementation((callback: (event: any) => void) => {
        eventCallback = callback
        return Promise.resolve(vi.fn())
      })

      await connectionStore.startListening()

      eventCallback({
        conn_id: 'conn1',
        state: 'disconnected'
      })

      expect(connectionStore.sessionStates['conn1']).toBe('disconnected')
      expect(connectionStore.dbStats).toEqual([])
    })
  })

  describe('Computed Properties', () => {
    it('应该正确计算activeConnection', async () => {
      ;(connectionList as any).mockResolvedValue(mockConnections)
      await connectionStore.loadConnections()
      connectionStore.activeConnId = 'conn1'

      expect(connectionStore.activeConnection).toEqual(mockConnections[0])
    })

    it('应该正确计算isConnected', () => {
      connectionStore.activeConnId = 'conn1'
      connectionStore.sessionStates.conn1 = 'connected'

      expect(connectionStore.isConnected).toBe(true)

      connectionStore.sessionStates.conn1 = 'disconnected'
      expect(connectionStore.isConnected).toBe(false)

      connectionStore.activeConnId = null
      expect(connectionStore.isConnected).toBe(false)
    })

    it('应该正确计算isTempConnection', () => {
      connectionStore.activeConnId = 'temp-conn-id'
      expect(connectionStore.isTempConnection).toBe(true)

      connectionStore.activeConnId = 'conn1'
      expect(connectionStore.isTempConnection).toBe(false)
    })
  })
})
