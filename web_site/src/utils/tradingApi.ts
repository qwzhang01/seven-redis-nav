/**
 * 交易管理 API服务
 * 对接量化交易系统的交易管理接口
 */

import { get, post, del } from './request'
import type {
  OrderSide,
  OrderType,
  OrderStatus,
  PositionSide,
  PlaceOrderRequest,
  OrderInfo,
  OrderListParams,
  OrderListResponse,
  TradeInfo,
  TradeListParams,
  TradeListResponse,
  PositionInfo,
  PositionListParams,
  PositionListResponse,
  AssetInfo,
  AccountInfo,
  RiskInfo,
} from '../types'

// 重新导出类型，保持向后兼容
export type {
  OrderSide,
  OrderType,
  OrderStatus,
  PositionSide,
  PlaceOrderRequest,
  OrderInfo,
  OrderListParams,
  OrderListResponse,
  TradeInfo,
  TradeListParams,
  TradeListResponse,
  PositionInfo,
  PositionListParams,
  PositionListResponse,
  AssetInfo,
  AccountInfo,
  RiskInfo,
}

// ==================== API方法 ====================

/**
 * 下单
 */
export function placeOrder(data: PlaceOrderRequest): Promise<OrderInfo> {
  return post<OrderInfo>('/api/v1/c/trading/order', data)
}

/**
 * 取消订单
 */
export function cancelOrder(orderId: string): Promise<{ message: string }> {
  return del<{ message: string }>(`/api/v1/c/trading/order/${orderId}`)
}

/**
 * 取消所有订单
 * 文档中 symbol 作为查询参数而非Body
 */
export function cancelAllOrders(params?: { symbol?: string }): Promise<{ success: boolean; cancelled_count: number; message: string }> {
  return post<{ success: boolean; cancelled_count: number; message: string }>('/api/v1/c/trading/order/cancel-all', params)
}

/**
 * 获取订单列表
 */
export function getOrders(params?: OrderListParams): Promise<OrderListResponse> {
  return get<OrderListResponse>('/api/v1/c/trading/orders', params)
}

/**
 * 获取订单详情
 */
export function getOrderById(orderId: string): Promise<OrderInfo> {
  return get<OrderInfo>(`/api/v1/c/trading/order/${orderId}`)
}

/**
 * 获取成交记录
 */
export function getTrades(params?: TradeListParams): Promise<TradeListResponse> {
  return get<TradeListResponse>('/api/v1/c/trading/trades', params)
}

/**
 * 获取持仓列表
 * 文档中无查询参数
 */
export function getPositions(): Promise<PositionListResponse> {
  return get<PositionListResponse>('/api/v1/c/trading/positions')
}

/**
 * 获取单个持仓详情
 * 文档中无额外查询参数
 */
export function getPositionBySymbol(symbol: string): Promise<PositionInfo> {
  return get<PositionInfo>(`/api/v1/c/trading/position/${symbol}`)
}

/**
 * 获取账户信息
 * 文档中无查询参数
 */
export function getAccount(): Promise<AccountInfo> {
  return get<AccountInfo>('/api/v1/c/trading/account')
}

/**
 * 获取风险信息
 */
export function getRisk(): Promise<RiskInfo> {
  return get<RiskInfo>('/api/v1/c/trading/risk')
}

// 导出所有API
export default {
  placeOrder,
  cancelOrder,
  cancelAllOrders,
  getOrders,
  getOrderById,
  getTrades,
  getPositions,
  getPositionBySymbol,
  getAccount,
  getRisk,
}
