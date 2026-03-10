/**
 * 统计分析相关API类型定义
 */

// ==================== 统计类型 ====================

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
export interface MarketStatsData {
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
