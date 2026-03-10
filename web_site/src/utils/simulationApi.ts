/**
 * 模拟交易 API服务
 * 对接量化交易系统的模拟交易专用接口
 */

import { get, post } from './request'
import type {
  SimKlineData,
  IndicatorDataPoint,
  IndicatorInfo,
  TradeMark,
  SimPosition,
  SimTrade,
  SimLog,
  SimKlineParams,
  SimIndicatorParams,
  SimTradeMarkParams,
  SimTradeListParams,
  SimLogParams,
  SimKlineResponse,
  SimIndicatorResponse,
  SimTradeMarkResponse,
  SimPositionResponse,
  SimTradeListResponse,
  SimLogResponse,
} from '../types'

// 重新导出类型，保持向后兼容
export type {
  SimKlineData,
  IndicatorDataPoint,
  IndicatorInfo,
  TradeMark,
  SimPosition,
  SimTrade,
  SimLog,
  SimKlineParams,
  SimIndicatorParams,
  SimTradeMarkParams,
  SimTradeListParams,
  SimLogParams,
  SimKlineResponse,
  SimIndicatorResponse,
  SimTradeMarkResponse,
  SimPositionResponse,
  SimTradeListResponse,
  SimLogResponse,
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
