/**
 * 信号相关API类型定义
 * 根据 api.json 的 schema 定义
 */

// ==================== 信号类型 ====================

/**
 * 信号类型
 */
export type SignalType = 'buy' | 'sell' | 'close'

/**
 * 信号状态
 */
export type SignalStatus = 'pending' | 'executed' | 'cancelled'

/**
 * 通知类型
 */
export type NotifyType = 'realtime' | 'daily' | 'weekly'

/**
 * 信号记录
 */
export interface Signal {
  id: string
  strategy_id: string
  strategy_name: string | null
  symbol: string
  exchange: string
  signal_type: SignalType
  price: number | null
  quantity: number | null
  confidence: number | null
  timeframe: string | null
  reason: string | null
  indicators: Record<string, any> | null
  status: SignalStatus
  executed_order_id: string | null
  executed_price: number | null
  executed_at: string | null
  is_public: boolean
  subscriber_count: number
  created_at: string
  updated_at: string
}

/**
 * 信号订阅
 */
export interface SignalSubscription {
  id: string
  strategy_id: string
  notify_type: NotifyType
  is_active: boolean
  created_at: string | null
}

/**
 * 订阅请求
 */
export interface SubscribeSignalRequest {
  strategy_id: string
  notify_type?: NotifyType
}

/**
 * 创建信号请求
 */
export interface CreateSignalRequest {
  strategy_id: string
  strategy_name?: string
  symbol: string
  exchange?: string
  signal_type: SignalType
  price: number
  quantity?: number
  confidence?: number
  timeframe?: string
  reason?: string
  indicators?: Record<string, any>
  is_public?: boolean
}

/**
 * 审核信号请求
 */
export interface ApproveSignalRequest {
  is_public: boolean
  reason?: string
}

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
  items: SignalHistoryRecord[]
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
  statistics: DrawdownStatistics
  drawdownCurve: number[]
  labels: string[]

}

export interface DrawdownStatistics {
  currentDrawdown: number
  maxDrawdown: number
  avgDrawdown: number
  maxDrawdownDate: string
  maxDrawdownDuration: number
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

/** 创建跟单请求（信号详情页） */
export interface CreateSignalFollowRequest {
  signalId: string
  signalName: string
  exchange: string
  followAmount: number
  followRatio?: number
  stopLoss: number
}

/** 创建跟单响应（信号详情页） */
export interface CreateSignalFollowResponse {
  id: string
  signalId: string
  followAmount: number
  followRatio: number
  stopLoss: number
  status: string
}

// ==================== 跟单列表相关类型 ====================

/** 跟单列表项（对应 GET /api/v1/c/follows/list 响应中的 items） */
export interface FollowListItem {
  id: string
  signalId: string
  signalName: string
  exchange: string
  status: 'following' | 'stopped' | 'paused'
  followAmount: number
  currentValue: number
  totalReturn: number
  todayReturn: number
  maxDrawdown: number
  winRate: number
  followRatio: number
  stopLoss: number
  riskLevel: string
  totalTrades: number
  followDays: number
  startTime: string
  stopTime: string | null
  createTime: string
}

/** 跟单列表响应 */
export interface FollowListResponse {
  records: FollowListItem[]
  total: number
  page: number
  pageSize: number
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
  tradingPair: string
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

/** 更新跟单配置请求（信号详情页） */
export interface UpdateSignalFollowConfigRequest {
  followRatio?: number
  stopLoss?: number
  followAmount?: number
}

/** 更新跟单配置响应 */
export interface UpdateSignalFollowConfigResponse {
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
export interface SignalSubscribeResponse {
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

// ==================== K线数据（公共） ====================

/** K线数据点（轻量图表格式） */
export interface KlineDataPoint {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

/** K线查询参数（信号页面用） */
export interface SignalKlineParams {
  symbol: string
  interval: string
  limit?: number
  startTime?: number
  endTime?: number
}

/** K线响应（信号页面用） */
export interface SignalKlineResponse {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}
