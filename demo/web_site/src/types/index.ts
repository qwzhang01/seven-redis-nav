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

export interface Signal {
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
  signal: Signal
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
  signal: Signal
  status: 'following' | 'stopped'
  startTime: string
  endTime?: string
  followAmount: number
  followRatio: number
  totalReturn: number
}

export interface ApiKey {
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