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
  return get<StrategyListResponse>('/api/v1/m/strategy/list', params)
}

/**
 * 获取可用策略类型
 */
export function getStrategyTypes(): Promise<StrategyTypeListResponse> {
  return get<StrategyTypeListResponse>('/api/v1/m/strategy/types')
}

/**
 * 创建策略
 */
export function createStrategy(data: CreateStrategyRequest): Promise<StrategyInfo> {
  return post<StrategyInfo>('/api/v1/m/strategy/create', data)
}

/**
 * 获取策略详情
 */
export function getStrategy(strategyId: string): Promise<StrategyInfo> {
  return get<StrategyInfo>(`/api/v1/m/strategy/${strategyId}`)
}

/**
 * 更新策略参数
 */
export function updateStrategy(strategyId: string, data: UpdateStrategyRequest): Promise<StrategyInfo> {
  return put<StrategyInfo>(`/api/v1/m/strategy/${strategyId}`, data)
}

/**
 * 删除策略
 */
export function deleteStrategy(strategyId: string): Promise<{ message: string }> {
  return del<{ message: string }>(`/api/v1/m/strategy/${strategyId}`)
}

/**
 * 启动策略
 */
export function startStrategy(strategyId: string): Promise<{ message: string }> {
  return post<{ message: string }>(`/api/v1/m/strategy/${strategyId}/start`)
}

/**
 * 停止策略
 */
export function stopStrategy(strategyId: string): Promise<{ message: string }> {
  return post<{ message: string }>(`/api/v1/m/strategy/${strategyId}/stop`)
}

/**
 * 暂停策略
 */
export function pauseStrategy(strategyId: string): Promise<{ message: string }> {
  return post<{ message: string }>(`/api/v1/m/strategy/${strategyId}/pause`)
}

/**
 * 恢复策略
 */
export function resumeStrategy(strategyId: string): Promise<{ message: string }> {
  return post<{ message: string }>(`/api/v1/m/strategy/${strategyId}/resume`)
}

/**
 * 获取策略信号历史
 */
export function getStrategySignals(strategyId: string, params?: SignalListParams): Promise<SignalListResponse> {
  return get<SignalListResponse>(`/api/v1/m/strategy/${strategyId}/signals`, params)
}

// ==================== C端接口 ====================

/**
 * 获取首页优选策略
 */
export interface FeaturedStrategiesResponse {
  strategies: Array<{
    strategy_id: string
    name: string
    state: string
    symbols: string[]
    timeframes: string[]
    signal_count: number
  }>
  total: number
}

export function getFeaturedStrategies(params?: { limit?: number }): Promise<FeaturedStrategiesResponse> {
  return get<FeaturedStrategiesResponse>('/api/v1/c/strategy/featured', params)
}

/**
 * 获取当前用户的策略列表
 */
export interface UserStrategyListParams {
  state?: string
  page?: number
  page_size?: number
}

export interface UserStrategyListResponse {
  strategies: Array<{
    strategy_id: string
    name: string
    state: string
    symbols: string[]
    timeframes: string[]
  }>
  total: number
  page: number
  page_size: number
}

export function getUserStrategies(params?: UserStrategyListParams): Promise<UserStrategyListResponse> {
  return get<UserStrategyListResponse>('/api/v1/c/strategy/list', params)
}

/**
 * 创建实盘策略
 */
export interface CreateUserStrategyRequest {
  name: string
  strategy_type: string
  symbols: string[]
  params?: Record<string, any>
}

export interface CreateUserStrategyResponse {
  success: boolean
  strategy_id: string
  message: string
}

export function createUserStrategy(data: CreateUserStrategyRequest): Promise<CreateUserStrategyResponse> {
  return post<CreateUserStrategyResponse>('/api/v1/c/strategy/create', data)
}

/**
 * 创建模拟交易策略
 */
export interface CreateSimulateStrategyRequest {
  strategy_type: string
  symbols: string[]
  params?: Record<string, any>
  initial_capital?: number
}

export interface CreateSimulateStrategyResponse {
  success: boolean
  strategy_id: string
  mode: string
  initial_capital: number
  message: string
}

export function createSimulateStrategy(data: CreateSimulateStrategyRequest): Promise<CreateSimulateStrategyResponse> {
  return post<CreateSimulateStrategyResponse>('/api/v1/c/strategy/simulate', data)
}

/**
 * 获取策略详情（C端）
 */
export function getUserStrategy(strategyId: string): Promise<any> {
  return get<any>(`/api/v1/c/strategy/${strategyId}`)
}

/**
 * 更新策略参数（C端）
 */
export function updateUserStrategy(strategyId: string, data: { params?: Record<string, any> }): Promise<{ success: boolean; strategy_id: string; message: string }> {
  return put<{ success: boolean; strategy_id: string; message: string }>(`/api/v1/c/strategy/${strategyId}`, data)
}

/**
 * 删除策略（C端）
 */
export function deleteUserStrategy(strategyId: string): Promise<{ success: boolean; strategy_id: string; message: string }> {
  return del<{ success: boolean; strategy_id: string; message: string }>(`/api/v1/c/strategy/${strategyId}`)
}

/**
 * 启动策略（C端）
 */
export function startUserStrategy(strategyId: string): Promise<{ success: boolean; strategy_id: string; message: string }> {
  return post<{ success: boolean; strategy_id: string; message: string }>(`/api/v1/c/strategy/${strategyId}/start`)
}

/**
 * 停止策略（C端）
 */
export function stopUserStrategy(strategyId: string): Promise<{ success: boolean; strategy_id: string; message: string }> {
  return post<{ success: boolean; strategy_id: string; message: string }>(`/api/v1/c/strategy/${strategyId}/stop`)
}

/**
 * 暂停策略（C端）
 */
export function pauseUserStrategy(strategyId: string): Promise<{ success: boolean; strategy_id: string; message: string }> {
  return post<{ success: boolean; strategy_id: string; message: string }>(`/api/v1/c/strategy/${strategyId}/pause`)
}

/**
 * 恢复策略（C端）
 */
export function resumeUserStrategy(strategyId: string): Promise<{ success: boolean; strategy_id: string; message: string }> {
  return post<{ success: boolean; strategy_id: string; message: string }>(`/api/v1/c/strategy/${strategyId}/resume`)
}

/**
 * 订阅策略
 */
export function subscribeStrategy(strategyId: string): Promise<{ success: boolean; strategy_id: string; username: string; message: string }> {
  return post<{ success: boolean; strategy_id: string; username: string; message: string }>(`/api/v1/c/strategy/${strategyId}/subscribe`)
}

/**
 * 取消订阅策略
 */
export function unsubscribeStrategy(strategyId: string): Promise<{ success: boolean; strategy_id: string; username: string; message: string }> {
  return del<{ success: boolean; strategy_id: string; username: string; message: string }>(`/api/v1/c/strategy/${strategyId}/subscribe`)
}

/**
 * 收藏策略
 */
export function favoriteStrategy(strategyId: string): Promise<{ success: boolean; strategy_id: string; username: string; message: string }> {
  return post<{ success: boolean; strategy_id: string; username: string; message: string }>(`/api/v1/c/strategy/${strategyId}/favorite`)
}

/**
 * 取消收藏策略
 */
export function unfavoriteStrategy(strategyId: string): Promise<{ success: boolean; strategy_id: string; username: string; message: string }> {
  return del<{ success: boolean; strategy_id: string; username: string; message: string }>(`/api/v1/c/strategy/${strategyId}/favorite`)
}

/**
 * 点赞策略
 */
export function likeStrategy(strategyId: string): Promise<{ success: boolean; strategy_id: string; username: string; message: string }> {
  return post<{ success: boolean; strategy_id: string; username: string; message: string }>(`/api/v1/c/strategy/${strategyId}/like`)
}

/**
 * 取消点赞策略
 */
export function unlikeStrategy(strategyId: string): Promise<{ success: boolean; strategy_id: string; username: string; message: string }> {
  return del<{ success: boolean; strategy_id: string; username: string; message: string }>(`/api/v1/c/strategy/${strategyId}/like`)
}

/**
 * 获取策略性能指标（C端）
 */
export function getUserStrategyPerformance(strategyId: string): Promise<any> {
  return get<any>(`/api/v1/c/strategy/${strategyId}/performance`)
}

/**
 * 获取策略信号历史（C端）
 */
export function getUserStrategySignals(strategyId: string, params?: { limit?: number }): Promise<any> {
  return get<any>(`/api/v1/c/strategy/${strategyId}/signals`, params)
}

// ==================== Admin端额外接口 ====================

/**
 * 发布策略
 */
export function publishStrategy(strategyId: string): Promise<{ success: boolean; strategy_id: string; message: string }> {
  return post<{ success: boolean; strategy_id: string; message: string }>(`/api/v1/m/strategy/${strategyId}/publish`)
}

/**
 * 下架策略
 */
export function unpublishStrategy(strategyId: string): Promise<{ success: boolean; strategy_id: string; message: string }> {
  return post<{ success: boolean; strategy_id: string; message: string }>(`/api/v1/m/strategy/${strategyId}/unpublish`)
}

/**
 * 获取策略性能指标（Admin端）
 */
export function getStrategyPerformance(strategyId: string): Promise<any> {
  return get<any>(`/api/v1/m/strategy/${strategyId}/performance`)
}

// 导出所有API
export default {
  // M端接口
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
  publishStrategy,
  unpublishStrategy,
  getStrategyPerformance,
  // C端接口
  getFeaturedStrategies,
  getUserStrategies,
  createUserStrategy,
  createSimulateStrategy,
  getUserStrategy,
  updateUserStrategy,
  deleteUserStrategy,
  startUserStrategy,
  stopUserStrategy,
  pauseUserStrategy,
  resumeUserStrategy,
  subscribeStrategy,
  unsubscribeStrategy,
  favoriteStrategy,
  unfavoriteStrategy,
  likeStrategy,
  unlikeStrategy,
  getUserStrategyPerformance,
  getUserStrategySignals,
}
