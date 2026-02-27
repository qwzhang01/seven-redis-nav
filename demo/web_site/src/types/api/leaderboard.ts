/**
 * 排行榜相关API类型定义
 */

// ==================== 排行榜类型 ====================

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
export interface LeaderboardApiEntry {
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
  strategy_ranking: LeaderboardApiEntry[]
  signal_ranking: LeaderboardApiEntry[]
}

/**
 * 排行榜列表响应
 */
export interface LeaderboardResponse {
  items: LeaderboardApiEntry[]
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
