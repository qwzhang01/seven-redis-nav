/**
 * 策略相关API类型定义
 * 根据 api.json 的 schema 定义
 */

// ==================== 策略类型 ====================

/**
 * 策略状态
 */
export type StrategyStatus = 'draft' | 'testing' | 'running' | 'paused' | 'stopped' | 'error'

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
  created_at: string
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
  created_at: string
  updated_at?: string
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
  created_at: string
}

// ==================== C端策略接口类型 ====================

/**
 * 创建用户策略请求
 */
export interface CreateUserStrategyRequest {
  name: string
  strategy_type: string
  symbols: string[]
  params?: Record<string, any>
}

/**
 * 创建模拟策略请求
 */
export interface CreateSimulateStrategyRequest {
  strategy_id: string
  strategy_type: string
  symbols: string[]
  params?: Record<string, any>
  initial_capital?: number
}

// ==================== 策略API扩展类型 ====================

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
  strategies: StrategyInfo[]
}

/**
 * 策略类型列表响应
 */
export interface StrategyTypeListResponse {
  total: number
  items: StrategyType[]
}

/**
 * 策略信号查询参数
 */
export interface StrategySignalListParams {
  limit?: number
}

/**
 * 策略信号列表响应
 */
export interface StrategySignalListResponse {
  strategy_id: string
  signals: StrategySignal[]
  total: number
}

/**
 * 预设策略列表查询参数
 */
export interface PresetStrategyListParams {
  keyword?: string
  market_type?: string
  strategy_type?: string
  risk_level?: string
  page?: number
  page_size?: number
}

/**
 * 预设策略列表响应
 */
export interface PresetStrategyListResponse {
  strategies: any[]
  total: number
  page: number
  page_size: number
}

/**
 * 我的策略列表查询参数
 */
export interface MyStrategyListParams {
  mode?: string
  status?: string
  page?: number
  page_size?: number
}

/**
 * 我的策略列表响应
 */
export interface MyStrategyListResponse {
  items: any[]
  total: number
  page: number
  page_size: number
}

/**
 * 首页优选策略响应
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

/**
 * 用户策略列表查询参数
 */
export interface UserStrategyListParams {
  state?: string
  page?: number
  page_size?: number
}

/**
 * 用户策略列表响应
 */
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

/**
 * 创建用户策略响应
 */
export interface CreateUserStrategyResponse {
  success: boolean
  strategy_id: string
  message: string
}

/**
 * 创建模拟策略响应
 */
export interface CreateSimulateStrategyResponse {
  success: boolean
  strategy_id: string
  mode: string
  initial_capital: number
  message: string
}