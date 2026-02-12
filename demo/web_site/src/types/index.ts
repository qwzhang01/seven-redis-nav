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
}

export interface StrategyParam {
  name: string
  label: string
  type: 'number' | 'select' | 'text'
  default: string | number
  options?: string[]
  description?: string
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
