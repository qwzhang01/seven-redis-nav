/**
 * WebSocket API服务
 * 对接量化交易系统的WebSocket实时推送接口
 */

// ==================== 类型定义 ====================

/**
 * WebSocket连接配置
 */
export interface WebSocketConfig {
  url: string
  token?: string
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatInterval?: number
  onOpen?: () => void
  onClose?: (event: CloseEvent) => void
  onError?: (error: Event) => void
  onMessage?: (data: any) => void
}

/**
 * WebSocket消息类型
 */
export type WSMessageType = 
  | 'connected' 
  | 'subscribed' 
  | 'unsubscribed' 
  | 'pong' 
  | 'error'
  | 'ticker' 
  | 'kline' 
  | 'depth'
  | 'signal'
  | 'strategy_status'
  | 'order_update'
  | 'trade'
  | 'position'
  | 'account'

/**
 * WebSocket消息
 */
export interface WSMessage {
  type: WSMessageType
  channel?: string
  data?: any
  message?: string
  channels?: string[]
  timestamp?: string
}

/**
 * WebSocket订阅参数
 */
export interface WSSubscribeParams {
  action: 'subscribe' | 'unsubscribe'
  channels: string[]
}

// ==================== WebSocket管理类 ====================

/**
 * WebSocket连接管理器
 */
export class WebSocketManager {
  private ws: WebSocket | null = null
  private config: WebSocketConfig
  private reconnectAttempts = 0
  private heartbeatTimer: number | null = null
  private reconnectTimer: number | null = null
  private isManualClose = false

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnect: true,
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
      ...config,
    }
  }

  /**
   * 连接WebSocket
   */
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.warn('WebSocket already connected')
      return
    }

    this.isManualClose = false
    const url = this.config.token 
      ? `${this.config.url}?token=${this.config.token}`
      : this.config.url

    try {
      this.ws = new WebSocket(url)
      this.setupEventHandlers()
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      this.handleReconnect()
    }
  }

  /**
   * 设置事件处理器
   */
  private setupEventHandlers(): void {
    if (!this.ws) return

    this.ws.onopen = () => {
      console.log('WebSocket connected:', this.config.url)
      this.reconnectAttempts = 0
      this.startHeartbeat()
      this.config.onOpen?.()
    }

    this.ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data)
        this.handleMessage(message)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      this.config.onError?.(error)
    }

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason)
      this.stopHeartbeat()
      this.config.onClose?.(event)

      if (!this.isManualClose && this.config.reconnect) {
        this.handleReconnect()
      }
    }
  }

  /**
   * 处理消息
   */
  private handleMessage(message: WSMessage): void {
    if (message.type === 'pong') {
      // 心跳响应，不需要特殊处理
      return
    }

    this.config.onMessage?.(message)
  }

  /**
   * 发送消息
   */
  send(data: any): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket is not connected')
      return
    }

    try {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      this.ws.send(message)
    } catch (error) {
      console.error('Failed to send WebSocket message:', error)
    }
  }

  /**
   * 订阅频道
   */
  subscribe(channels: string[]): void {
    this.send({
      action: 'subscribe',
      channels,
    })
  }

  /**
   * 取消订阅频道
   */
  unsubscribe(channels: string[]): void {
    this.send({
      action: 'unsubscribe',
      channels,
    })
  }

  /**
   * 开始心跳
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()
    if (this.config.heartbeatInterval) {
      this.heartbeatTimer = window.setInterval(() => {
        this.send({ action: 'ping' })
      }, this.config.heartbeatInterval)
    }
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 处理重连
   */
  private handleReconnect(): void {
    if (this.reconnectTimer) {
      return
    }

    if (
      this.config.maxReconnectAttempts &&
      this.reconnectAttempts >= this.config.maxReconnectAttempts
    ) {
      console.error('Max reconnect attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.config.reconnectInterval! * this.reconnectAttempts

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`)

    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, delay)
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.isManualClose = true
    this.stopHeartbeat()

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * 获取连接状态
   */
  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }

  /**
   * 是否已连接
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

// ==================== 预定义的WebSocket管理器 ====================

/**
 * 创建行情WebSocket连接
 */
export function createMarketWebSocket(config: Omit<WebSocketConfig, 'url'>): WebSocketManager {
  const baseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
  return new WebSocketManager({
    ...config,
    url: `${baseUrl}/ws/market`,
  })
}

/**
 * 创建策略信号WebSocket连接
 */
export function createStrategyWebSocket(config: Omit<WebSocketConfig, 'url'>): WebSocketManager {
  const baseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
  return new WebSocketManager({
    ...config,
    url: `${baseUrl}/ws/strategy`,
  })
}

/**
 * 创建交易事件WebSocket连接（需要认证）
 */
export function createTradingWebSocket(token: string, config?: Omit<WebSocketConfig, 'url' | 'token'>): WebSocketManager {
  const baseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
  return new WebSocketManager({
    ...config,
    url: `${baseUrl}/ws/trading`,
    token,
  })
}

// ==================== 频道工具函数 ====================

/**
 * 构建Ticker频道名称
 */
export function tickerChannel(symbol: string): string {
  return `ticker/${symbol}`
}

/**
 * 构建K线频道名称
 */
export function klineChannel(symbol: string, timeframe: string): string {
  return `kline/${symbol}/${timeframe}`
}

/**
 * 构建深度频道名称
 */
export function depthChannel(symbol: string): string {
  return `depth/${symbol}`
}

/**
 * 构建策略频道名称
 */
export function strategyChannel(strategyId: string): string {
  return `strategy/${strategyId}`
}

// 导出所有API
export default {
  WebSocketManager,
  createMarketWebSocket,
  createStrategyWebSocket,
  createTradingWebSocket,
  tickerChannel,
  klineChannel,
  depthChannel,
  strategyChannel,
}
