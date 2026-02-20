/**
 * 策略管理 API服务
 * 对接量化交易系统的策略管理接口
 */

import { get, post, put, del } from './request'

// ==================== 类型定义 ====================

/**
 * 策略状态
 */
export type StrategyStatus = 'draft' | 'testing' | 'running' | 'paused' | 'stopped' | 'error'

/**
 * 策略类型
 */
export interface StrategyType {
  id: string
  name: string
  code: string
  description: string
  category: string
  parameters: StrategyParameter[]
  risk_level: 'low' | 'medium' | 'high'
  min_capital?: number
  supported_exchanges: string[]
  create_time: string
}

/**
 * 策略参数定义
 */
export interface StrategyParameter {
  name: string
  label: string
  type: 'string' | 'number' | 'boolean' | 'select'
  default_value: any
  required: boolean
  description?: string
  options?: Array<{ label: string; value: any }>
  min?: number
  max?: number
  step?: number
}

/**
 * 策略信息
 */
export interface StrategyInfo {
  id: string
  user_id: string
  strategy_type_id: string
  strategy_type_name?: string
  name: string
  description?: string
  exchange_id: string
  exchange_name?: string
  symbol: string
  status: StrategyStatus
  parameters: Record<string, any>
  initial_capital?: number
  current_capital?: number
  total_pnl?: number
  total_pnl_ratio?: number
  daily_pnl?: number
  daily_pnl_ratio?: number
  win_rate?: number
  sharpe_ratio?: number
  max_drawdown?: number
  total_trades?: number
  error_message?: string
  start_time?: string
  stop_time?: string
  create_time: string
  update_time?: string
}

/**
 * 创建策略请求
 */
export interface CreateStrategyRequest {
  strategy_type_id: string
  name: string
  description?: string
  exchange_id: string
  symbol: string
  parameters: Record<string, any>
  initial_capital?: number
}

/**
 * 更新策略请求
 */
export interface UpdateStrategyRequest {
  name?: string
  description?: string
  parameters?: Record<string, any>
}

/**
 * 策略列表查询参数
 */
export interface StrategyListParams {
  strategy_type_id?: string
  exchange_id?: string
  symbol?: string
  status?: StrategyStatus
  sort?: 'popular' | 'newest' | 'profit'
  page?: number
  page_size?: number
}

/**
 * 策略列表响应
 */
export interface StrategyListResponse {
  total: number
  page: number
  page_size: number
  items: StrategyInfo[]
}

/**
 * 策略类型列表响应
 */
export interface StrategyTypeListResponse {
  total: number
  items: StrategyType[]
}

/**
 * 策略信号
 */
export interface StrategySignal {
  id: string
  strategy_id: string
  strategy_name?: string
  signal_type: 'buy' | 'sell' | 'close_long' | 'close_short'
  symbol: string
  price: number
  quantity?: number
  reason?: string
  confidence?: number
  executed: boolean
  order_id?: string
  signal_time: string
  execute_time?: string
  create_time: string
}

/**
 * 策略信号查询参数
 */
export interface SignalListParams {
  signal_type?: string
  executed?: boolean
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

/**
 * 策略信号列表响应
 */
export interface SignalListResponse {
  total: number
  page: number
  page_size: number
  items: StrategySignal[]
}

// ==================== API方法 ====================

/**
 * 获取策略列表
 */
export function getStrategies(params?: StrategyListParams): Promise<StrategyListResponse> {
  return get<StrategyListResponse>('/strategy/list', params)
}

/**
 * 获取可用策略类型
 */
export function getStrategyTypes(): Promise<StrategyTypeListResponse> {
  return get<StrategyTypeListResponse>('/strategy/types')
}

/**
 * 创建策略
 */
export function createStrategy(data: CreateStrategyRequest): Promise<StrategyInfo> {
  return post<StrategyInfo>('/strategy/create', data)
}

/**
 * 获取策略详情
 */
export function getStrategy(strategyId: string): Promise<StrategyInfo> {
  return get<StrategyInfo>(`/strategy/${strategyId}`)
}

/**
 * 更新策略参数
 */
export function updateStrategy(strategyId: string, data: UpdateStrategyRequest): Promise<StrategyInfo> {
  return put<StrategyInfo>(`/strategy/${strategyId}`, data)
}

/**
 * 删除策略
 */
export function deleteStrategy(strategyId: string): Promise<{ message: string }> {
  return del<{ message: string }>(`/strategy/${strategyId}`)
}

/**
 * 启动策略
 */
export function startStrategy(strategyId: string): Promise<{ message: string }> {
  return post<{ message: string }>(`/strategy/${strategyId}/start`)
}

/**
 * 停止策略
 */
export function stopStrategy(strategyId: string): Promise<{ message: string }> {
  return post<{ message: string }>(`/strategy/${strategyId}/stop`)
}

/**
 * 暂停策略
 */
export function pauseStrategy(strategyId: string): Promise<{ message: string }> {
  return post<{ message: string }>(`/strategy/${strategyId}/pause`)
}

/**
 * 恢复策略
 */
export function resumeStrategy(strategyId: string): Promise<{ message: string }> {
  return post<{ message: string }>(`/strategy/${strategyId}/resume`)
}

/**
 * 获取策略信号历史
 */
export function getStrategySignals(strategyId: string, params?: SignalListParams): Promise<SignalListResponse> {
  return get<SignalListResponse>(`/strategy/${strategyId}/signals`, params)
}

// 导出所有API
export default {
  getStrategies,
  getStrategyTypes,
  createStrategy,
  getStrategy,
  updateStrategy,
  deleteStrategy,
  startStrategy,
  stopStrategy,
  pauseStrategy,
  resumeStrategy,
  getStrategySignals,
}
