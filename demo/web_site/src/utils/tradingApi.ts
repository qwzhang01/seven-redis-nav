/**
 * 交易管理 API服务
 * 对接量化交易系统的交易管理接口
 */

import { get, post, del } from './request'

// ==================== 类型定义 ====================

/**
 * 订单方向
 */
export type OrderSide = 'buy' | 'sell'

/**
 * 订单类型
 */
export type OrderType = 'limit' | 'market' | 'stop_limit' | 'stop_market'

/**
 * 订单状态
 */
export type OrderStatus = 'pending' | 'open' | 'partially_filled' | 'filled' | 'cancelled' | 'rejected' | 'expired'

/**
 * 持仓方向
 */
export type PositionSide = 'long' | 'short'

/**
 * 下单请求
 */
export interface PlaceOrderRequest {
  exchange_id: string
  symbol: string
  side: OrderSide
  type: OrderType
  quantity: number
  price?: number
  stop_price?: number
  time_in_force?: 'GTC' | 'IOC' | 'FOK'
  client_order_id?: string
  strategy_id?: string
}

/**
 * 订单信息
 */
export interface OrderInfo {
  id: string
  user_id: string
  exchange_id: string
  exchange_name?: string
  symbol: string
  side: OrderSide
  type: OrderType
  status: OrderStatus
  quantity: number
  price?: number
  stop_price?: number
  filled_quantity: number
  average_price?: number
  commission?: number
  commission_asset?: string
  time_in_force?: string
  client_order_id?: string
  exchange_order_id?: string
  strategy_id?: string
  strategy_name?: string
  error_message?: string
  create_time: string
  update_time?: string
  filled_time?: string
}

/**
 * 订单列表查询参数
 */
export interface OrderListParams {
  exchange_id?: string
  symbol?: string
  side?: OrderSide
  status?: OrderStatus
  strategy_id?: string
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

/**
 * 订单列表响应
 */
export interface OrderListResponse {
  total: number
  page: number
  page_size: number
  items: OrderInfo[]
}

/**
 * 成交记录
 */
export interface TradeInfo {
  id: string
  order_id: string
  user_id: string
  exchange_id: string
  exchange_name?: string
  symbol: string
  side: OrderSide
  price: number
  quantity: number
  commission: number
  commission_asset: string
  is_maker: boolean
  exchange_trade_id?: string
  strategy_id?: string
  strategy_name?: string
  trade_time: string
  create_time: string
}

/**
 * 成交记录查询参数
 */
export interface TradeListParams {
  exchange_id?: string
  symbol?: string
  side?: OrderSide
  strategy_id?: string
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

/**
 * 成交记录列表响应
 */
export interface TradeListResponse {
  total: number
  page: number
  page_size: number
  items: TradeInfo[]
}

/**
 * 持仓信息
 */
export interface PositionInfo {
  id: string
  user_id: string
  exchange_id: string
  exchange_name?: string
  symbol: string
  side: PositionSide
  quantity: number
  available_quantity: number
  frozen_quantity: number
  average_price: number
  current_price?: number
  unrealized_pnl?: number
  unrealized_pnl_ratio?: number
  realized_pnl?: number
  margin?: number
  leverage?: number
  liquidation_price?: number
  strategy_id?: string
  strategy_name?: string
  open_time: string
  update_time?: string
}

/**
 * 持仓列表查询参数
 */
export interface PositionListParams {
  exchange_id?: string
  symbol?: string
  side?: PositionSide
  strategy_id?: string
}

/**
 * 持仓列表响应
 */
export interface PositionListResponse {
  total: number
  items: PositionInfo[]
}

/**
 * 账户资产信息
 */
export interface AssetInfo {
  asset: string
  free: number
  locked: number
  total: number
  usd_value?: number
}

/**
 * 账户信息
 */
export interface AccountInfo {
  user_id: string
  exchange_id: string
  exchange_name?: string
  account_type: 'spot' | 'margin' | 'futures'
  total_balance: number
  available_balance: number
  frozen_balance: number
  unrealized_pnl?: number
  margin_level?: number
  assets: AssetInfo[]
  update_time: string
}

/**
 * 风险信息
 */
export interface RiskInfo {
  user_id: string
  total_equity: number
  total_margin: number
  margin_level: number
  total_unrealized_pnl: number
  total_realized_pnl: number
  daily_pnl: number
  daily_pnl_ratio: number
  max_drawdown: number
  max_drawdown_ratio: number
  position_count: number
  order_count: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  warnings: string[]
  update_time: string
}

// ==================== API方法 ====================

/**
 * 下单
 */
export function placeOrder(data: PlaceOrderRequest): Promise<OrderInfo> {
  return post<OrderInfo>('/trading/order', data)
}

/**
 * 取消订单
 */
export function cancelOrder(orderId: string): Promise<{ message: string }> {
  return del<{ message: string }>(`/trading/order/${orderId}`)
}

/**
 * 取消所有订单
 */
export function cancelAllOrders(params?: { exchange_id?: string; symbol?: string }): Promise<{ message: string; cancelled_count: number }> {
  return post<{ message: string; cancelled_count: number }>('/trading/order/cancel-all', params)
}

/**
 * 获取订单列表
 */
export function getOrders(params?: OrderListParams): Promise<OrderListResponse> {
  return get<OrderListResponse>('/trading/orders', params)
}

/**
 * 获取订单详情
 */
export function getOrderById(orderId: string): Promise<OrderInfo> {
  return get<OrderInfo>(`/trading/order/${orderId}`)
}

/**
 * 获取成交记录
 */
export function getTrades(params?: TradeListParams): Promise<TradeListResponse> {
  return get<TradeListResponse>('/trading/trades', params)
}

/**
 * 获取持仓列表
 */
export function getPositions(params?: PositionListParams): Promise<PositionListResponse> {
  return get<PositionListResponse>('/trading/positions', params)
}

/**
 * 获取单个持仓详情
 */
export function getPositionBySymbol(symbol: string, params?: { exchange_id?: string }): Promise<PositionInfo> {
  return get<PositionInfo>(`/trading/position/${symbol}`, params)
}

/**
 * 获取账户信息
 */
export function getAccount(params?: { exchange_id?: string }): Promise<AccountInfo> {
  return get<AccountInfo>('/trading/account', params)
}

/**
 * 获取风险信息
 */
export function getRisk(): Promise<RiskInfo> {
  return get<RiskInfo>('/trading/risk')
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
