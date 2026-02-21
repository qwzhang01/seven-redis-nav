/**
 * 信号相关API类型定义
 * 根据 api.json 的 schema 定义
 */

// ==================== 信号类型 ====================

/**
 * 信号类型
 */
export type SignalType = 'buy' | 'sell' | 'close'

/**
 * 信号状态
 */
export type SignalStatus = 'pending' | 'executed' | 'cancelled'

/**
 * 通知类型
 */
export type NotifyType = 'realtime' | 'daily' | 'weekly'

/**
 * 信号记录
 */
export interface Signal {
  id: string
  strategy_id: string
  strategy_name: string | null
  symbol: string
  exchange: string
  signal_type: SignalType
  price: number | null
  quantity: number | null
  confidence: number | null
  timeframe: string | null
  reason: string | null
  indicators: Record<string, any> | null
  status: SignalStatus
  executed_order_id: string | null
  executed_price: number | null
  executed_at: string | null
  is_public: boolean
  subscriber_count: number
  created_at: string
  updated_at: string
}

/**
 * 信号订阅
 */
export interface SignalSubscription {
  id: string
  strategy_id: string
  notify_type: NotifyType
  is_active: boolean
  created_at: string | null
}

/**
 * 订阅请求
 */
export interface SubscribeSignalRequest {
  strategy_id: string
  notify_type?: NotifyType
}

/**
 * 创建信号请求
 */
export interface CreateSignalRequest {
  strategy_id: string
  strategy_name?: string
  symbol: string
  exchange?: string
  signal_type: SignalType
  price: number
  quantity?: number
  confidence?: number
  timeframe?: string
  reason?: string
  indicators?: Record<string, any>
  is_public?: boolean
}

/**
 * 审核信号请求
 */
export interface ApproveSignalRequest {
  is_public: boolean
  reason?: string
}
