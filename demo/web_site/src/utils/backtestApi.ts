/**
 * 回测管理 API服务
 * 对接量化交易系统的回测接口
 */

import { get, post, del } from './request'
import type {
  BacktestStatus,
  RunBacktestRequest,
  BacktestResult,
  BacktestListParams,
  BacktestListResponse,
  EquityPoint,
  EquityCurveResponse,
  BacktestTrade,
  BacktestTradesParams,
  BacktestTradesResponse,
} from '../types'

// 重新导出类型，保持向后兼容
export type {
  BacktestStatus,
  RunBacktestRequest,
  BacktestResult,
  BacktestListParams,
  BacktestListResponse,
  EquityPoint,
  EquityCurveResponse,
  BacktestTrade,
  BacktestTradesParams,
  BacktestTradesResponse,
}

// ==================== API方法 ====================

/**
 * 运行策略回测
 * 响应包含 success, backtest_id, message
 */
export function runBacktest(data: RunBacktestRequest): Promise<{ success: boolean; backtest_id: string; message: string }> {
  return post<{ success: boolean; backtest_id: string; message: string }>('/api/v1/c/backtest/run', data)
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
export function deleteBacktest(backtestId: string): Promise<{ success: boolean; backtest_id: string; message: string }> {
  return del<{ success: boolean; backtest_id: string; message: string }>(`/api/v1/c/backtest/${backtestId}`)
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
