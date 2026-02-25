/**
 * 模拟交易 API服务
 * 对接量化交易系统的模拟交易专用接口
 */

import { get, post } from './request'

// ==================== 类型定义 ====================

/**
 * K线数据点（适配 lightweight-charts）
 */
export interface SimKlineData {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

/**
 * 指标数据点
 */
export interface IndicatorDataPoint {
  time: number
  value: number
}

/**
 * 指标信息
 */
export interface IndicatorInfo {
  name: string
  type: 'line' | 'histogram' | 'area'
  color: string
  pane: 'main' | 'sub' | 'sub2'
  data: IndicatorDataPoint[]
}

/**
 * 交易标记
 */
export interface TradeMark {
  time: number
  position: 'aboveBar' | 'belowBar'
  color: string
  shape: 'arrowUp' | 'arrowDown' | 'circle' | 'square'
  text: string
  side: 'buy' | 'sell'
  price: number
  quantity: number
  pnl: number | null
}

/**
 * 模拟持仓
 */
export interface SimPosition {
  symbol: string
  direction: 'long' | 'short'
  amount: string
  entry_price: number
  current_price: number
  pnl: number
  pnl_ratio: number
  open_time: string
}

/**
 * 模拟交易记录
 */
export interface SimTrade {
  id: string
  symbol: string
  side: 'buy' | 'sell'
  price: number
  amount: number
  value: number
  fee: number
  pnl: number | null
  time: string
}

/**
 * 运行日志
 */
export interface SimLog {
  time: string
  level: 'info' | 'warn' | 'error' | 'trade'
  message: string
}

// ==================== 请求参数类型 ====================

export interface SimKlineParams {
  timeframe?: string
  start_time?: number
  end_time?: number
  limit?: number
}

export interface SimIndicatorParams {
  start_time?: number
  end_time?: number
  limit?: number
}

export interface SimTradeMarkParams {
  start_time?: number
  end_time?: number
  limit?: number
}

export interface SimTradeListParams {
  page?: number
  page_size?: number
}

export interface SimLogParams {
  level?: string
  limit?: number
}

// ==================== 响应类型 ====================

export interface SimKlineResponse {
  strategy_id: string
  symbol: string
  timeframe: string
  data: SimKlineData[]
}

export interface SimIndicatorResponse {
  strategy_id: string
  indicators: IndicatorInfo[]
}

export interface SimTradeMarkResponse {
  strategy_id: string
  marks: TradeMark[]
}

export interface SimPositionResponse {
  strategy_id: string
  positions: SimPosition[]
  total_value: number
  unrealized_pnl: number
}

export interface SimTradeListResponse {
  strategy_id: string
  total: number
  page: number
  page_size: number
  trades: SimTrade[]
}

export interface SimLogResponse {
  strategy_id: string
  logs: SimLog[]
}

// ==================== API方法 ====================

/**
 * 获取模拟K线历史数据
 */
export function getSimKlines(strategyId: string, params?: SimKlineParams): Promise<SimKlineResponse> {
  return get<SimKlineResponse>(`/api/v1/c/simulation/${strategyId}/klines`, params)
}

/**
 * 获取模拟指标数据
 */
export function getSimIndicators(strategyId: string, params?: SimIndicatorParams): Promise<SimIndicatorResponse> {
  return get<SimIndicatorResponse>(`/api/v1/c/simulation/${strategyId}/indicators`, params)
}

/**
 * 获取模拟交易点标记
 */
export function getSimTradeMarks(strategyId: string, params?: SimTradeMarkParams): Promise<SimTradeMarkResponse> {
  return get<SimTradeMarkResponse>(`/api/v1/c/simulation/${strategyId}/trade-marks`, params)
}

/**
 * 获取模拟持仓
 */
export function getSimPositions(strategyId: string): Promise<SimPositionResponse> {
  return get<SimPositionResponse>(`/api/v1/c/simulation/${strategyId}/positions`)
}

/**
 * 获取模拟交易记录
 */
export function getSimTrades(strategyId: string, params?: SimTradeListParams): Promise<SimTradeListResponse> {
  return get<SimTradeListResponse>(`/api/v1/c/simulation/${strategyId}/trades`, params)
}

/**
 * 获取模拟运行日志
 */
export function getSimLogs(strategyId: string, params?: SimLogParams): Promise<SimLogResponse> {
  return get<SimLogResponse>(`/api/v1/c/simulation/${strategyId}/logs`, params)
}

// 导出所有API
export default {
  getSimKlines,
  getSimIndicators,
  getSimTradeMarks,
  getSimPositions,
  getSimTrades,
  getSimLogs,
}
