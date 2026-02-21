/**
 * 信号管理 API服务
 * 对接量化交易系统的信号管理接口
 */

import { get, post, put, del } from './request'
import type {
  SignalType,
  SignalStatus,
  NotifyType,
  Signal,
  SignalSubscription,
  SubscribeSignalRequest,
  CreateSignalRequest,
  ApproveSignalRequest,
} from '../types'

// ==================== 本地扩展类型 ====================
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
 * 审核信号响应
 */
export interface ApproveSignalResponse {
  success: boolean
  signal: Signal
  message: string
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
export function subscribeSignal(data: SubscribeSignalRequest): Promise<SubscribeResponse> {
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
