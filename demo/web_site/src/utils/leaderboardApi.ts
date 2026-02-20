/**
 * 排行榜 API服务
 * 对接量化交易系统的排行榜接口
 */

import { get, post } from './request'

// ==================== 类型定义 ====================

/**
 * 排名类型
 */
export type RankType = 'strategy' | 'signal'

/**
 * 统计周期
 */
export type Period = 'daily' | 'weekly' | 'monthly' | 'all_time'

/**
 * 排序字段
 */
export type SortBy = 'total_return' | 'sharpe_ratio' | 'win_rate' | 'annual_return'

/**
 * 排行榜条目
 */
export interface LeaderboardEntry {
  id: string
  rank_type: RankType
  period: Period
  rank_position: number
  entity_id: string
  entity_name: string
  entity_type: string
  owner_id: string | null
  owner_name: string | null
  total_return: number | null
  annual_return: number | null
  max_drawdown: number | null
  sharpe_ratio: number | null
  win_rate: number | null
  total_trades: number | null
  profit_factor: number | null
  stat_start_time: string | null
  stat_end_time: string | null
  snapshot_time: string | null
}

/**
 * 综合排行榜响应
 */
export interface LeaderboardOverviewResponse {
  period: Period
  snapshot_time: string | null
  strategy_ranking: LeaderboardEntry[]
  signal_ranking: LeaderboardEntry[]
}

/**
 * 排行榜列表响应
 */
export interface LeaderboardResponse {
  items: LeaderboardEntry[]
  total: number
  period: Period
  sort_by?: SortBy
  snapshot_time: string | null
}

/**
 * 综合排行榜查询参数
 */
export interface LeaderboardOverviewParams {
  period?: Period
  limit?: number
}

/**
 * 策略排行榜查询参数
 */
export interface StrategyLeaderboardParams {
  period?: Period
  sort_by?: SortBy
  limit?: number
}

/**
 * 信号排行榜查询参数
 */
export interface SignalLeaderboardParams {
  period?: Period
  limit?: number
}

/**
 * 刷新排行榜响应
 */
export interface RefreshLeaderboardResponse {
  success: boolean
  message: string
  snapshot_time: string
}

// ==================== C端API方法 ====================

/**
 * 获取综合排行榜
 */
export function getLeaderboardOverview(params?: LeaderboardOverviewParams): Promise<LeaderboardOverviewResponse> {
  return get<LeaderboardOverviewResponse>('/api/v1/c/leaderboard', params)
}

/**
 * 策略收益排行榜
 */
export function getStrategyLeaderboard(params?: StrategyLeaderboardParams): Promise<LeaderboardResponse> {
  return get<LeaderboardResponse>('/api/v1/c/leaderboard/strategy', params)
}

/**
 * 信号准确率排行榜
 */
export function getSignalLeaderboard(params?: SignalLeaderboardParams): Promise<LeaderboardResponse> {
  return get<LeaderboardResponse>('/api/v1/c/leaderboard/signal', params)
}

// ==================== Admin端API方法 ====================

/**
 * 手动刷新排行榜快照
 */
export function refreshLeaderboard(): Promise<RefreshLeaderboardResponse> {
  return post<RefreshLeaderboardResponse>('/api/v1/m/leaderboard/refresh')
}

// 导出所有API
export default {
  // C端接口
  getLeaderboardOverview,
  getStrategyLeaderboard,
  getSignalLeaderboard,
  // Admin端接口
  refreshLeaderboard,
}
