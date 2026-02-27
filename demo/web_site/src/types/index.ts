// ==================== 导出API类型 ====================
export * from './api/user'
export * from './api/market'
export * from './api/strategy'
export * from './api/signal'
export * from './api/backtest'
export * from './api/leaderboard'
export * from './api/simulation'
export * from './api/stats'
export * from './api/system'
export * from './api/trading'
export * from './api/websocket'
export * from './common'

// ==================== 导出组件类型 ====================
export * from './components'

// 导入需要在UI层使用的API类型
import type { SubscriptionConfig } from './api/market'

// ==================== UI层类型定义 ====================

/**
 * UI层策略类型（用于前端展示）
 */
export interface Strategy {
  id: string
  name: string
  description: string
  market: string
  type: string
  riskLevel: 'low' | 'medium' | 'high'
  returnRate: number
  maxDrawdown: number
  runDays: number
  status: 'active' | 'stopped'
  params?: StrategyParam[]
  logic?: string
  riskTip?: string
  // 新增详细参数
  exchange: string
  tradingPair: string
  timeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d' | '1w'
  capitalAllocation: {
    initialCapital: number
    maxPositionSize: number
    riskPerTrade: number
    rebalancingFrequency: 'daily' | 'weekly' | 'monthly'
  }
  riskManagement: {
    stopLoss: number
    takeProfit: number
    trailingStop: boolean
    maxConcurrentTrades: number
    dailyLossLimit: number
    weeklyLossLimit: number
  }
  advancedSettings: {
    slippageTolerance: number
    commissionRate: number
    useMarketOrders: boolean
    allowShortSelling: boolean
    enableHedging: boolean
    backtestPeriod: number
  }
}

/**
 * UI层策略参数类型
 */
export interface StrategyParam {
  name: string
  label: string
  type: 'number' | 'select' | 'text' | 'boolean' | 'range'
  default: string | number | boolean
  options?: string[]
  description?: string
  min?: number
  max?: number
  step?: number
  required?: boolean
}

/**
 * UI层信号类型（用于前端展示）
 */
export interface UISignal {
  id: string
  name: string
  platform: string
  type: 'simulated' | 'live'
  cumulativeReturn: number
  maxDrawdown: number
  runDays: number
  status: 'running' | 'stopped'
  followers: number
  returnCurve?: number[]
  returnCurveLabels?: string[]
  positions?: Position[]
  description?: string
  // 新增详细参数
  exchange: string
  tradingPair: string
  timeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d' | '1w'
  signalFrequency: 'high' | 'medium' | 'low'
  riskParameters: {
    maxPositionSize: number
    stopLossPercentage: number
    takeProfitPercentage: number
    riskRewardRatio: number
    volatilityFilter: boolean
  }
  notificationSettings: {
    emailAlerts: boolean
    pushNotifications: boolean
    telegramBot: boolean
    discordWebhook: boolean
    alertThreshold: number
  }
  performanceMetrics: {
    sharpeRatio: number
    winRate: number
    profitFactor: number
    averageHoldingPeriod: number
    maxConsecutiveLosses: number
  }
}

/**
 * UI层持仓类型
 */
export interface Position {
  symbol: string
  side: 'long' | 'short'
  amount: number
  entryPrice: number
  currentPrice: number
  pnl: number
  pnlPercent: number
}

export interface LeaderboardEntry {
  rank: number
  signal: UISignal
}

export interface UserStrategy {
  id: string
  strategy: Strategy
  status: 'running' | 'ended'
  startTime: string
  endTime?: string
  totalReturn: number
  config: Record<string, unknown>
}

export interface UserSignalFollow {
  id: string
  signal: UISignal
  status: 'following' | 'stopped'
  startTime: string
  endTime?: string
  followAmount: number
  followRatio: number
  totalReturn: number
}

/**
 * UI层API密钥类型（用于前端展示，扩展自API类型）
 */
export interface UIApiKey {
  id: string
  exchange: string
  label: string
  apiKey: string
  createdAt: string
  status: 'active' | 'disabled'
  reviewStatus: 'pending' | 'approved' | 'rejected'
  reviewReason?: string
  reviewedBy?: string
  reviewedAt?: string
  userId: string
  userName: string
}

/**
 * API密钥类型别名（向后兼容）
 */
export type ApiKey = UIApiKey

// ==================== 数据订阅类型别名 ====================

/**
 * UI层数据订阅类型（映射到API的SubscriptionConfig）
 */
export type DataSubscription = SubscriptionConfig

// SyncTask 已在 api/market.ts 中定义，直接使用
