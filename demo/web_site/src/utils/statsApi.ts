/**
 * 统计分析 API服务
 * 对接量化交易系统的统计分析接口（管理员端）
 */

import { get } from './request'

// ==================== 类型定义 ====================

/**
 * 系统概览统计
 */
export interface SystemOverview {
  total_users: number
  active_users_today: number
  new_users_today: number
  total_strategies: number
  running_strategies: number
  total_signals: number
  signals_today: number
  subscriptions: number
  ws_connections: number
  ws_channel_stats: Record<string, number>
  timestamp: string
}

/**
 * 用户统计数据
 */
export interface UserStats {
  total_users: number
  user_type_dist: Record<string, number>
  status_dist: Record<string, number>
  daily_new_users: Array<{
    date: string
    count: number
  }>
  days: number
}

/**
 * 策略统计数据
 */
export interface StrategyStats {
  total_strategies: number
  state_dist: Record<string, number>
  strategies: Array<{
    strategy_id: string
    name: string
    state: string
    symbols: string[]
  }>
  signal_by_strategy: Array<{
    strategy_id: string
    strategy_name: string
    signal_count: number
  }>
  signal_type_dist: Record<string, number>
}

/**
 * 交易统计数据
 */
export interface TradingStats {
  active_orders: number
  total_positions: number
  total_equity: number
  account_info: {
    total_balance: number
    available_balance: number
    margin_balance: number
  }
  signals_executed_today: number
  timestamp: string
}

/**
 * 行情数据统计
 */
export interface MarketStats {
  subscribed_symbols: number
  subscriptions_count: number
  running_subscriptions: number
  kline_records_total: number
  market_service_stats: Record<string, any>
  timestamp: string
}

/**
 * 用户统计查询参数
 */
export interface UserStatsParams {
  days?: number
}

// ==================== Admin端API方法 ====================

/**
 * 系统概览统计
 */
export function getSystemOverview(): Promise<SystemOverview> {
  return get<SystemOverview>('/api/v1/m/stats/overview')
}

/**
 * 用户统计数据
 */
export function getUserStats(params?: UserStatsParams): Promise<UserStats> {
  return get<UserStats>('/api/v1/m/stats/users', params)
}

/**
 * 策略统计数据
 */
export function getStrategyStats(): Promise<StrategyStats> {
  return get<StrategyStats>('/api/v1/m/stats/strategies')
}

/**
 * 交易统计数据
 */
export function getTradingStats(): Promise<TradingStats> {
  return get<TradingStats>('/api/v1/m/stats/trading')
}

/**
 * 行情数据统计
 */
export function getMarketStats(): Promise<MarketStats> {
  return get<MarketStats>('/api/v1/m/stats/market')
}

// 导出所有API
export default {
  getSystemOverview,
  getUserStats,
  getStrategyStats,
  getTradingStats,
  getMarketStats,
}
