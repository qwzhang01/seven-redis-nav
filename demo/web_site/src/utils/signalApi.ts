/**
 * 信号管理 API服务
 * 对接量化交易系统的信号管理接口
 */

import { get, post, put, del } from './request'

// ==================== 类型定义 ====================

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
 * 信号列表查询参数
 */
export interface SignalListParams {
  symbol?: string
  signal_type?: SignalType
  strategy_id?: string
  page?: number
  page_size?: number
}

/**
 * 信号列表响应
 */
export interface SignalListResponse {
  items: Signal[]
  total: number
  page: number
  pages: number
}

/**
 * 策略历史信号响应
 */
export interface StrategySignalHistoryResponse {
  strategy_id: string
  items: Signal[]
  total: number
  page: number
  pages: number
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
export interface SubscribeRequest {
  strategy_id: string
  notify_type?: NotifyType
}

/**
 * 订阅响应
 */
export interface SubscribeResponse {
  id: string
  strategy_id: string
  notify_type: NotifyType
  is_active: boolean
  message: string
}

/**
 * 订阅列表响应
 */
export interface SubscriptionListResponse {
  items: SignalSubscription[]
  total: number
}

/**
 * 审核信号请求
 */
export interface ApproveSignalRequest {
  is_public: boolean
  reason?: string
}

/**
 * 审核信号响应
 */
export interface ApproveSignalResponse {
  success: boolean
  signal: Signal
  message: string
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
 * 创建信号响应
 */
export interface CreateSignalResponse {
  success: boolean
  signal: Signal
  message: string
}

// ==================== C端API方法 ====================

/**
 * 获取公开信号列表（信号广场）
 */
export function getSignalList(params?: SignalListParams): Promise<SignalListResponse> {
  return get<SignalListResponse>('/api/v1/c/signal/list', params)
}

/**
 * 获取信号详情
 */
export function getSignalDetail(signalId: string): Promise<Signal> {
  return get<Signal>(`/api/v1/c/signal/${signalId}`)
}

/**
 * 获取策略历史信号
 */
export function getStrategySignalHistory(
  strategyId: string,
  params?: { page?: number; page_size?: number }
): Promise<StrategySignalHistoryResponse> {
  return get<StrategySignalHistoryResponse>(`/api/v1/c/signal/strategy/${strategyId}/history`, params)
}

/**
 * 订阅策略信号通知
 */
export function subscribeSignal(data: SubscribeRequest): Promise<SubscribeResponse> {
  return post<SubscribeResponse>('/api/v1/c/signal/subscribe', data)
}

/**
 * 获取我的信号订阅列表
 */
export function getMySubscriptions(): Promise<SubscriptionListResponse> {
  return get<SubscriptionListResponse>('/api/v1/c/signal/subscriptions')
}

/**
 * 取消信号订阅
 */
export function unsubscribeSignal(subscriptionId: string): Promise<{ success: boolean; message: string }> {
  return del<{ success: boolean; message: string }>(`/api/v1/c/signal/subscriptions/${subscriptionId}`)
}

// ==================== Admin端API方法 ====================

/**
 * 获取待审核信号列表
 */
export function getPendingSignals(params?: { page?: number; page_size?: number }): Promise<SignalListResponse> {
  return get<SignalListResponse>('/api/v1/m/signal/pending', params)
}

/**
 * 审核信号（设置是否公开）
 */
export function approveSignal(signalId: string, data: ApproveSignalRequest): Promise<ApproveSignalResponse> {
  return put<ApproveSignalResponse>(`/api/v1/m/signal/${signalId}/approve`, data)
}

/**
 * 手动创建信号记录
 */
export function createSignal(data: CreateSignalRequest): Promise<CreateSignalResponse> {
  return post<CreateSignalResponse>('/api/v1/m/signal/', data)
}

// 导出所有API
export default {
  // C端接口
  getSignalList,
  getSignalDetail,
  getStrategySignalHistory,
  subscribeSignal,
  getMySubscriptions,
  unsubscribeSignal,
  // Admin端接口
  getPendingSignals,
  approveSignal,
  createSignal,
}
