/**
 * 排行榜 API服务
 * 对接量化交易系统的排行榜接口
 */

import { get, post } from './request'
import type {
  RankType,
  Period,
  SortBy,
  LeaderboardApiEntry,
  LeaderboardOverviewResponse,
  LeaderboardResponse,
  LeaderboardOverviewParams,
  StrategyLeaderboardParams,
  SignalLeaderboardParams,
  RefreshLeaderboardResponse,
} from '../types'

// 重新导出类型，保持向后兼容
export type {
  RankType,
  Period,
  SortBy,
  LeaderboardOverviewResponse,
  LeaderboardResponse,
  LeaderboardOverviewParams,
  StrategyLeaderboardParams,
  SignalLeaderboardParams,
  RefreshLeaderboardResponse,
}
// 向后兼容别名
export type { LeaderboardApiEntry as LeaderboardEntry }

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
