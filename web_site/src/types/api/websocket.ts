/**
 * WebSocket相关API类型定义
 */

// ==================== WebSocket类型 ====================

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
  /** 交易WS连接成功时返回的用户ID */
  user_id?: string
  /** 交易WS连接成功时返回的已订阅频道列表 */
  subscribed_channels?: string[]
}

/**
 * WebSocket订阅参数
 */
export interface WSSubscribeParams {
  action: 'subscribe' | 'unsubscribe'
  channels: string[]
}
