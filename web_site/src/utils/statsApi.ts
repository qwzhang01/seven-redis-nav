/**
 * 统计分析 API服务
 * 对接量化交易系统的统计分析接口（管理员端）
 */

import { get } from './request'
import type {
  SystemOverview,
  UserStats,
  StrategyStats,
  TradingStats,
  MarketStatsData,
  UserStatsParams,
} from '../types'

// 本地类型别名，供函数签名使用
type MarketStats = MarketStatsData

// 重新导出类型，保持向后兼容
export type {
  SystemOverview,
  UserStats,
  StrategyStats,
  TradingStats,
  UserStatsParams,
}
// 向后兼容别名
export type { MarketStatsData as MarketStats }

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
