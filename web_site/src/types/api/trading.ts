/**
 * 交易管理相关API类型定义
 */

// ==================== 交易基础类型 ====================

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
  symbol: string
  side: OrderSide
  order_type: OrderType
  quantity: number
  price?: number
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
  status?: 'active' | 'all'
  symbol?: string
  limit?: number
}

/**
 * 订单列表响应
 */
export interface OrderListResponse {
  orders: OrderInfo[]
  total: number
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
  symbol?: string
  order_id?: string
  limit?: number
}

/**
 * 成交记录列表响应
 */
export interface TradeListResponse {
  trades: TradeInfo[]
  total: number
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
  // 文档中无查询参数
}

/**
 * 持仓列表响应
 */
export interface PositionListResponse {
  positions: PositionInfo[]
  total_value: number
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
