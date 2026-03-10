/**
 * 回测相关API类型定义
 */

// ==================== 回测类型 ====================

/**
 * 回测状态
 */
export type BacktestStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

/**
 * 运行回测请求
 */
export interface RunBacktestRequest {
  strategy_type: string
  symbol: string
  timeframe?: string
  start_time: string
  end_time: string
  initial_capital?: number
  commission_rate?: number
  slippage_rate?: number
  params?: Record<string, any>
}

/**
 * 回测结果
 */
export interface BacktestResult {
  id: string
  user_id: string
  strategy_id: string
  strategy_name?: string
  exchange_id: string
  exchange_name?: string
  symbol: string
  status: BacktestStatus
  start_time: string
  end_time: string
  initial_capital: number
  final_capital: number
  total_return: number
  total_return_ratio: number
  annual_return_ratio: number
  max_drawdown: number
  max_drawdown_ratio: number
  sharpe_ratio: number
  sortino_ratio: number
  calmar_ratio: number
  win_rate: number
  profit_factor: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  avg_profit: number
  avg_loss: number
  max_profit: number
  max_loss: number
  avg_holding_time: number
  commission_paid: number
  parameters?: Record<string, any>
  error_message?: string
  run_time?: number
  create_time: string
  complete_time?: string
}

/**
 * 回测历史列表查询参数
 */
export interface BacktestListParams {
  limit?: number
}

/**
 * 回测历史列表响应
 */
export interface BacktestListResponse {
  backtests: BacktestResult[]
  total: number
}

/**
 * 权益曲线数据点
 */
export interface EquityPoint {
  time: string
  equity: number
  cash: number
  position_value: number
  return_ratio: number
  drawdown: number
  drawdown_ratio: number
}

/**
 * 权益曲线响应
 */
export interface EquityCurveResponse {
  backtest_id: string
  initial_capital: number
  final_capital: number
  data: EquityPoint[]
}

/**
 * 回测交易记录
 */
export interface BacktestTrade {
  id: string
  backtest_id: string
  symbol: string
  side: 'buy' | 'sell'
  type: 'open' | 'close'
  price: number
  quantity: number
  commission: number
  pnl?: number
  pnl_ratio?: number
  balance_after: number
  signal_reason?: string
  trade_time: string
}

/**
 * 回测交易记录查询参数
 */
export interface BacktestTradesParams {
  limit?: number
}

/**
 * 回测交易记录响应
 */
export interface BacktestTradesResponse {
  backtest_id: string
  trades: BacktestTrade[]
  total: number
}
