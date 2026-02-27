/**
 * 信号管理 API服务
 * 对接量化交易系统的信号管理接口
 * 
 * C端信号基础URL: /api/v1/c/signal
 * C端跟单基础URL: /api/v1/c/follows
 * Admin端基础URL: /api/v1/m/signal
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

// ==================== 信号广场相关类型 ====================

/** 信号列表查询参数 */
export interface SignalListParams {
  platform?: string
  type?: 'live' | 'simulated'
  min_days?: number
  search?: string
  sort_by?: 'return_desc' | 'return_asc' | 'drawdown_asc' | 'followers'
  page?: number
  page_size?: number
}

/** 信号列表响应 */
export interface SignalListResponse {
  items: Signal[]
  total: number
  page: number
  pages: number
}

// ==================== 信号详情相关类型 ====================

/** 风险参数 */
export interface RiskParameters {
  maxPositionSize: number
  stopLossPercentage: number
  takeProfitPercentage: number
  riskRewardRatio: number
  volatilityFilter: boolean
}

/** 绩效指标 */
export interface PerformanceMetrics {
  sharpeRatio: number
  winRate: number
  profitFactor: number
  averageHoldingPeriod: number
  maxConsecutiveLosses: number
}

/** 通知设置 */
export interface NotificationSettings {
  emailAlerts: boolean
  pushNotifications: boolean
  telegramBot: boolean
  discordWebhook: boolean
  alertThreshold: number
}

/** 持仓信息 */
export interface SignalPosition {
  symbol: string
  side: 'long' | 'short'
  amount: number
  entryPrice: number
  currentPrice: number
  pnl: number
  pnlPercent: number
}

/** 信号提供者信息 */
export interface SignalProvider {
  id: string
  name: string
  avatar: string
  verified: boolean
  bio: string
  totalSignals: number
  avgReturn: number
  totalFollowers: number
  rating: number
  joinDate: string
  experience: string
  badges: string[]
}

/** 信号详情响应 */
export interface SignalDetailResponse {
  id: string
  name: string
  description: string
  platform: string
  type: 'live' | 'simulated'
  status: 'running' | 'paused' | 'stopped'
  exchange: string
  tradingPair: string
  timeframe: string
  signalFrequency: 'high' | 'medium' | 'low'
  followers: number
  cumulativeReturn: number
  maxDrawdown: number
  runDays: number
  returnCurve: number[]
  returnCurveLabels: string[]
  riskParameters: RiskParameters
  performanceMetrics: PerformanceMetrics
  notificationSettings: NotificationSettings
  positions: SignalPosition[]
  provider: SignalProvider
  createdAt: string
  updatedAt: string
}

/** 收益曲线数据点 */
export interface ReturnCurvePoint {
  date: string
  cumulative_return: number
  drawdown: number
}

/** 收益曲线响应 */
export interface SignalReturnCurveResponse {
  signal_id: string
  period: string
  curve: ReturnCurvePoint[]
}

/** 信号历史记录项 */
export interface SignalHistoryRecord {
  id: string
  action: 'buy' | 'sell'
  symbol: string
  price: number
  amount: number
  time: string
  strength: 'strong' | 'medium' | 'weak'
  pnl: number | null
  status: 'open' | 'closed'
}

/** 信号历史记录响应 */
export interface SignalHistoryResponse {
  total: number
  page: number
  pageSize: number
  records: SignalHistoryRecord[]
}

/** 月度收益项 */
export interface MonthlyReturnItem {
  month: string
  return_rate: number
  trade_count: number
}

/** 月度收益响应 */
export interface SignalMonthlyReturnsResponse {
  signal_id: string
  monthly_returns: MonthlyReturnItem[]
}

/** 回撤曲线数据点 */
export interface DrawdownPoint {
  date: string
  drawdown: number
}

/** 回撤分析响应 */
export interface SignalDrawdownResponse {
  signal_id: string
  max_drawdown: number
  current_drawdown: number
  avg_drawdown: number
  drawdown_curve: DrawdownPoint[]
}

/** 用户评价项 */
export interface SignalReview {
  id: string
  user_id: string
  username: string
  avatar?: string
  rating: number
  content: string
  likes: number
  is_liked: boolean
  created_at: string
}

/** 评价列表响应 */
export interface SignalReviewsResponse {
  items: SignalReview[]
  total: number
  page: number
  pages: number
  rating_distribution: Record<string, number>
  average_rating: number
}

/** 提交评价请求 */
export interface SubmitReviewRequest {
  rating: number
  content: string
}

/** 提交评价响应 */
export interface SubmitReviewResponse {
  id: string
  signal_id: string
  rating: number
  content: string
  created_at: string
}

/** 点赞响应 */
export interface ToggleLikeResponse {
  liked: boolean
  total_likes: number
}

/** 创建跟单请求 */
export interface CreateFollowRequest {
  amount: number
  ratio?: number
  stopLoss: number
}

/** 创建跟单响应 */
export interface CreateFollowResponse {
  follow_id: string
  signal_id: string
  amount: number
  ratio: number
  stop_loss: number
  status: string
}

// ==================== 跟单详情相关类型 ====================

/** 跟单持仓 */
export interface FollowPosition {
  id: string
  symbol: string
  side: 'long' | 'short'
  amount: number
  entryPrice: number
  currentPrice: number
  pnl: number
  pnlPercent: number
}

/** 交易点位 */
export interface TradingPoint {
  id: string
  type: 'buy' | 'sell'
  symbol: string
  price: number
  amount: number
  time: string
}

/** 跟单详情响应 */
export interface FollowDetailResponse {
  id: string
  signalId: string
  signalName: string
  exchange: string
  status: 'following' | 'paused' | 'stopped'
  totalReturn: number
  todayReturn: number
  followAmount: number
  currentValue: number
  maxDrawdown: number
  currentDrawdown: number
  followDays: number
  winRate: number
  followRatio: number
  stopLoss: number
  startTime: string
  riskLevel: 'low' | 'medium' | 'high'
  currentPrice: number
  priceChange24h: number
  volume24h: string
  totalTrades: number
  winTrades: number
  lossTrades: number
  avgWin: number
  avgLoss: number
  profitFactor: number
  returnCurve: number[]
  returnCurveLabels: string[]
  positions: FollowPosition[]
  tradingPoints: TradingPoint[]
}

/** 跟单收益对比统计 */
export interface ComparisonStats {
  returnDiff: number
  avgSlippage: number
  copyRate: number
  followFinalReturn: number
  signalFinalReturn: number
}

/** 跟单收益对比响应 */
export interface FollowComparisonResponse {
  follow_id: string
  labels: string[]
  followCurve: number[]
  signalCurve: number[]
  statistics: ComparisonStats
}

/** 跟单交易记录 */
export interface FollowTradeRecord {
  id: string
  side: 'buy' | 'sell'
  symbol: string
  price: number
  amount: number
  total: number
  pnl: number | null
  time: string
  signalTime?: string
  slippage?: number
}

/** 跟单交易记录响应 */
export interface FollowTradesResponse {
  total: number
  page: number
  records: FollowTradeRecord[]
}

/** 跟单事件日志项 */
export interface FollowEvent {
  id: string
  type: 'trade' | 'risk' | 'success' | 'error' | 'system'
  typeLabel: string
  message: string
  time: string
  metadata?: Record<string, any>
}

/** 跟单事件日志响应 */
export interface FollowEventsResponse {
  total: number
  records: FollowEvent[]
}

/** 仓位分布项 */
export interface PositionDistributionItem {
  name: string
  value: number
  percentage?: number
}

/** 仓位详情项 */
export interface PositionDetail {
  symbol: string
  side: 'long' | 'short'
  quantity: number
  entry_price: number
  current_price: number
  unrealized_pnl: number
  ratio: number
}

/** 仓位分布响应 */
export interface FollowPositionsResponse {
  follow_id: string
  positions: PositionDetail[]
  total_value: number
  usage_rate: number
  distribution: PositionDistributionItem[]
}

/** 更新跟单配置请求 */
export interface UpdateFollowConfigRequest {
  followRatio?: number
  stopLoss?: number
  followAmount?: number
}

/** 更新跟单配置响应 */
export interface UpdateFollowConfigResponse {
  follow_id: string
  follow_ratio: number
  stop_loss: number
  follow_amount: number
}

/** 停止跟单请求 */
export interface StopFollowRequest {
  closePositions?: boolean
  reason?: string
}

/** 停止跟单响应 */
export interface StopFollowResponse {
  follow_id: string
  status: string
  closed_positions: boolean
  finalReturn?: number
  stoppedAt?: string
}

// ==================== 策略历史信号类型 ====================

/** 策略历史信号响应 */
export interface StrategySignalHistoryResponse {
  strategy_id: string
  items: Signal[]
  total: number
  page: number
  pages: number
}

/** 订阅响应 */
export interface SubscribeResponse {
  id: string
  strategy_id: string
  notify_type: NotifyType
  is_active: boolean
  message: string
}

/** 订阅列表响应 */
export interface SubscriptionListResponse {
  items: SignalSubscription[]
  total: number
}

/** 审核信号响应 */
export interface ApproveSignalResponse {
  success: boolean
  signal: Signal
  message: string
}

/** 创建信号响应 */
export interface CreateSignalResponse {
  success: boolean
  signal: Signal
  message: string
}

// ==================== C端API — 信号广场 ====================

/**
 * 获取公开信号列表（信号广场）
 */
export function getSignalList(params?: SignalListParams): Promise<SignalListResponse> {
  return get<SignalListResponse>('/api/v1/c/signal/list', params)
}

/**
 * 获取平台列表（筛选项）
 */
export function getSignalPlatforms(): Promise<string[]> {
  return get<string[]>('/api/v1/c/signal/platforms')
}

/**
 * 获取我的信号订阅列表
 */
export function getMySubscriptions(): Promise<SubscriptionListResponse> {
  return get<SubscriptionListResponse>('/api/v1/c/signal/subscriptions')
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

// ==================== C端API — 信号详情页 ====================

/**
 * 获取信号详情
 */
export function getSignalDetail(signalId: string): Promise<SignalDetailResponse> {
  return get<SignalDetailResponse>(`/api/v1/c/signal/${signalId}`)
}

/**
 * 获取信号收益曲线
 */
export function getSignalReturnCurve(
  signalId: string,
  params?: { period?: '7d' | '30d' | '90d' | '180d' | 'all' }
): Promise<SignalReturnCurveResponse> {
  return get<SignalReturnCurveResponse>(`/api/v1/c/signal/${signalId}/return-curve`, params)
}

/**
 * 获取信号历史记录
 */
export function getSignalHistory(
  signalId: string,
  params?: { page?: number; pageSize?: number }
): Promise<SignalHistoryResponse> {
  return get<SignalHistoryResponse>(`/api/v1/c/signal/${signalId}/history`, params)
}

/**
 * 获取信号提供者信息
 */
export function getSignalProvider(signalId: string): Promise<SignalProvider> {
  return get<SignalProvider>(`/api/v1/c/signal/${signalId}/provider`)
}

/**
 * 获取月度收益分布
 */
export function getSignalMonthlyReturns(
  signalId: string,
  params?: { months?: number }
): Promise<SignalMonthlyReturnsResponse> {
  return get<SignalMonthlyReturnsResponse>(`/api/v1/c/signal/${signalId}/monthly-returns`, params)
}

/**
 * 获取回撤分析数据
 */
export function getSignalDrawdown(signalId: string): Promise<SignalDrawdownResponse> {
  return get<SignalDrawdownResponse>(`/api/v1/c/signal/${signalId}/drawdown`)
}

/**
 * 获取用户评价列表
 */
export function getSignalReviews(
  signalId: string,
  params?: { page?: number; page_size?: number; sort?: 'latest' | 'highest' | 'lowest' | 'most_liked' }
): Promise<SignalReviewsResponse> {
  return get<SignalReviewsResponse>(`/api/v1/c/signal/${signalId}/reviews`, params)
}

/**
 * 提交用户评价
 */
export function submitSignalReview(
  signalId: string,
  data: SubmitReviewRequest
): Promise<SubmitReviewResponse> {
  return post<SubmitReviewResponse>(`/api/v1/c/signal/${signalId}/reviews`, data)
}

/**
 * 评价点赞/取消点赞
 */
export function toggleReviewLike(
  signalId: string,
  reviewId: string
): Promise<ToggleLikeResponse> {
  return post<ToggleLikeResponse>(`/api/v1/c/signal/${signalId}/reviews/${reviewId}/like`)
}

/**
 * 创建跟单
 */
export function createFollow(
  signalId: string,
  data: CreateFollowRequest
): Promise<CreateFollowResponse> {
  return post<CreateFollowResponse>(`/api/v1/c/signal/${signalId}/follow`, data)
}

/**
 * 订阅策略信号通知
 */
export function subscribeSignal(data: SubscribeSignalRequest): Promise<SubscribeResponse> {
  return post<SubscribeResponse>('/api/v1/c/signal/subscribe', data)
}

/**
 * 取消信号订阅
 */
export function unsubscribeSignal(subscriptionId: string): Promise<{ success: boolean; message: string }> {
  return del<{ success: boolean; message: string }>(`/api/v1/c/signal/subscriptions/${subscriptionId}`)
}

// ==================== C端API — 跟单详情页 ====================

/**
 * 获取跟单详情
 */
export function getFollowDetail(followId: string): Promise<FollowDetailResponse> {
  return get<FollowDetailResponse>(`/api/v1/c/follows/${followId}`)
}

/**
 * 获取跟单收益对比数据
 */
export function getFollowComparison(followId: string): Promise<FollowComparisonResponse> {
  return get<FollowComparisonResponse>(`/api/v1/c/follows/${followId}/comparison`)
}

/**
 * 获取跟单交易记录
 */
export function getFollowTrades(
  followId: string,
  params?: { page?: number; page_size?: number; side?: 'buy' | 'sell' }
): Promise<FollowTradesResponse> {
  return get<FollowTradesResponse>(`/api/v1/c/follows/${followId}/trades`, params)
}

/**
 * 获取跟单事件日志
 */
export function getFollowEvents(
  followId: string,
  params?: { page?: number; page_size?: number; type?: 'trade' | 'risk' | 'success' | 'error' | 'system' }
): Promise<FollowEventsResponse> {
  return get<FollowEventsResponse>(`/api/v1/c/follows/${followId}/events`, params)
}

/**
 * 获取跟单仓位分布
 */
export function getFollowPositions(followId: string): Promise<FollowPositionsResponse> {
  return get<FollowPositionsResponse>(`/api/v1/c/follows/${followId}/positions`)
}

/**
 * 更新跟单配置
 */
export function updateFollowConfig(
  followId: string,
  data: UpdateFollowConfigRequest
): Promise<UpdateFollowConfigResponse> {
  return put<UpdateFollowConfigResponse>(`/api/v1/c/follows/${followId}/config`, data)
}

/**
 * 停止跟单
 */
export function stopFollow(
  followId: string,
  data?: StopFollowRequest
): Promise<StopFollowResponse> {
  return post<StopFollowResponse>(`/api/v1/c/follows/${followId}/stop`, data)
}

// ==================== Admin端API ====================

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

// ==================== K线数据（公共） ====================

/** K线数据点 */
export interface KlineDataPoint {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

/** K线查询参数 */
export interface KlineParams {
  symbol: string
  interval: string
  limit?: number
  startTime?: number
  endTime?: number
}

/** K线响应 */
export interface KlineResponse {
  symbol: string
  interval: string
  klines: KlineDataPoint[]
}

/**
 * 获取K线数据
 */
export function getKlineData(params: KlineParams): Promise<KlineResponse> {
  let { symbol, interval, limit } = params
  symbol = symbol.replace('/', '-')
  return get<KlineResponse>(`/api/v1/c/market/kline/${encodeURIComponent(symbol)}`, {
    timeframe: interval,
    limit
  })
}


// ==================== 默认导出 ====================

export default {
  // C端 — 信号广场
  getSignalList,
  getSignalPlatforms,
  getMySubscriptions,
  getStrategySignalHistory,
  // C端 — 信号详情
  getSignalDetail,
  getSignalReturnCurve,
  getSignalHistory,
  getSignalProvider,
  getSignalMonthlyReturns,
  getSignalDrawdown,
  getSignalReviews,
  submitSignalReview,
  toggleReviewLike,
  createFollow,
  subscribeSignal,
  unsubscribeSignal,
  // C端 — 跟单详情
  getFollowDetail,
  getFollowComparison,
  getFollowTrades,
  getFollowEvents,
  getFollowPositions,
  updateFollowConfig,
  stopFollow,
  // K线
  getKlineData,
  // Admin端
  getPendingSignals,
  approveSignal,
  createSignal,
}
