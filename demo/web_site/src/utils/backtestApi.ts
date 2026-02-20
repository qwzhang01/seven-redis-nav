/**
 * 回测管理 API服务
 * 对接量化交易系统的回测接口
 */

import { get, post, del } from './request'

// ==================== 类型定义 ====================

/**
 * 回测状态
 */
export type BacktestStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

/**
 * 运行回测请求
 */
export interface RunBacktestRequest {
  strategy_id: string
  exchange_id: string
  symbol: string
  start_time: string
  end_time: string
  initial_capital: number
  parameters?: Record<string, any>
  commission_rate?: number
  slippage_rate?: number
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
  strategy_id?: string
  exchange_id?: string
  symbol?: string
  status?: BacktestStatus
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

/**
 * 回测历史列表响应
 */
export interface BacktestListResponse {
  total: number
  page: number
  page_size: number
  items: BacktestResult[]
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
  side?: 'buy' | 'sell'
  type?: 'open' | 'close'
  page?: number
  page_size?: number
}

/**
 * 回测交易记录响应
 */
export interface BacktestTradesResponse {
  backtest_id: string
  total: number
  page: number
  page_size: number
  trades: BacktestTrade[]
}

// ==================== API方法 ====================

/**
 * 运行策略回测
 */
export function runBacktest(data: RunBacktestRequest): Promise<BacktestResult> {
  return post<BacktestResult>('/api/v1/c/backtest/run', data)
}

/**
 * 获取回测历史列表
 */
export function getBacktestList(params?: BacktestListParams): Promise<BacktestListResponse> {
  return get<BacktestListResponse>('/api/v1/c/backtest/list', params)
}

/**
 * 获取回测结果
 */
export function getBacktestResult(backtestId: string): Promise<BacktestResult> {
  return get<BacktestResult>(`/api/v1/c/backtest/${backtestId}`)
}

/**
 * 获取回测权益曲线
 */
export function getEquityCurve(backtestId: string): Promise<EquityCurveResponse> {
  return get<EquityCurveResponse>(`/api/v1/c/backtest/${backtestId}/equity`)
}

/**
 * 获取回测交易记录
 */
export function getBacktestTrades(backtestId: string, params?: BacktestTradesParams): Promise<BacktestTradesResponse> {
  return get<BacktestTradesResponse>(`/api/v1/c/backtest/${backtestId}/trades`, params)
}

/**
 * 删除回测记录
 */
export function deleteBacktest(backtestId: string): Promise<{ message: string }> {
  return del<{ message: string }>(`/api/v1/c/backtest/${backtestId}`)
}

// 导出所有API
export default {
  runBacktest,
  getBacktestList,
  getBacktestResult,
  getEquityCurve,
  getBacktestTrades,
  deleteBacktest,
}
