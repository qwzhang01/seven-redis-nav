/**
 * 市场数据 API服务
 * 对接量化交易系统的市场数据接口
 */

import { get } from './request'

// ==================== 类型定义 ====================

/**
 * K线周期
 */
export type KlineInterval = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w' | '1M'

/**
 * K线数据
 */
export interface KlineData {
  open_time: number
  open: number
  high: number
  low: number
  close: number
  volume: number
  close_time: number
  quote_volume: number
  trades: number
  taker_buy_base_volume: number
  taker_buy_quote_volume: number
}

/**
 * K线查询参数
 */
export interface KlineParams {
  exchange_id: string
  symbol: string
  interval: KlineInterval
  start_time?: number
  end_time?: number
  limit?: number
}

/**
 * K线数据响应
 */
export interface KlineResponse {
  exchange_id: string
  symbol: string
  interval: KlineInterval
  data: KlineData[]
}

/**
 * 行情数据
 */
export interface TickerData {
  exchange_id: string
  exchange_name?: string
  symbol: string
  last_price: number
  bid_price: number
  bid_quantity: number
  ask_price: number
  ask_quantity: number
  open_price: number
  high_price: number
  low_price: number
  volume: number
  quote_volume: number
  price_change: number
  price_change_percent: number
  weighted_avg_price: number
  prev_close_price: number
  last_quantity: number
  open_time: number
  close_time: number
  first_trade_id?: number
  last_trade_id?: number
  trade_count: number
  update_time: number
}

/**
 * 行情查询参数
 */
export interface TickerParams {
  exchange_id: string
  symbol: string
}

/**
 * 所有交易对行情查询参数
 */
export interface TickersParams {
  exchange_id: string
  symbols?: string[]
}

/**
 * 所有交易对行情响应
 */
export interface TickersResponse {
  exchange_id: string
  tickers: TickerData[]
  update_time: number
}

/**
 * 深度档位
 */
export interface DepthLevel {
  price: number
  quantity: number
}

/**
 * 市场深度数据
 */
export interface DepthData {
  exchange_id: string
  symbol: string
  bids: DepthLevel[]
  asks: DepthLevel[]
  last_update_id: number
  update_time: number
}

/**
 * 深度查询参数
 */
export interface DepthParams {
  exchange_id: string
  symbol: string
  limit?: number
}

/**
 * 成交记录
 */
export interface TradeRecord {
  id: string
  price: number
  quantity: number
  quote_quantity: number
  time: number
  is_buyer_maker: boolean
}

/**
 * 最近成交查询参数
 */
export interface TradesParams {
  exchange_id: string
  symbol: string
  limit?: number
}

/**
 * 最近成交响应
 */
export interface TradesResponse {
  exchange_id: string
  symbol: string
  trades: TradeRecord[]
}

/**
 * 交易对信息
 */
export interface SymbolInfo {
  symbol: string
  base_asset: string
  quote_asset: string
  status: 'trading' | 'halt' | 'break'
  base_asset_precision: number
  quote_asset_precision: number
  order_types: string[]
  price_filter?: {
    min_price: number
    max_price: number
    tick_size: number
  }
  lot_size_filter?: {
    min_qty: number
    max_qty: number
    step_size: number
  }
  min_notional?: number
  is_spot_trading_allowed: boolean
  is_margin_trading_allowed: boolean
}

/**
 * 交易对列表查询参数
 */
export interface SymbolsParams {
  exchange_id: string
  base_asset?: string
  quote_asset?: string
  status?: string
}

/**
 * 交易对列表响应
 */
export interface SymbolsResponse {
  exchange_id: string
  symbols: SymbolInfo[]
}

/**
 * 交易所信息
 */
export interface ExchangeInfo {
  id: string
  code: string
  name: string
  type: 'spot' | 'futures' | 'margin'
  status: 'active' | 'inactive'
  base_url: string
  api_doc_url?: string
  supported_pairs_count: number
  rate_limits?: Array<{
    type: string
    interval: string
    limit: number
  }>
  create_time: string
  update_time?: string
}

/**
 * 交易所列表响应
 */
export interface ExchangesResponse {
  total: number
  exchanges: ExchangeInfo[]
}

// ==================== API方法 ====================

/**
 * 获取K线数据
 */
export function getKlines(params: KlineParams): Promise<KlineResponse> {
  return get<KlineResponse>('/api/v1/c/market/klines', params)
}

/**
 * 获取最新行情
 */
export function getTicker(params: TickerParams): Promise<TickerData> {
  return get<TickerData>('/api/v1/c/market/ticker', params)
}

/**
 * 获取所有交易对行情
 */
export function getTickers(params: TickersParams): Promise<TickersResponse> {
  return get<TickersResponse>('/api/v1/c/market/tickers', params)
}

/**
 * 获取市场深度
 */
export function getDepth(params: DepthParams): Promise<DepthData> {
  return get<DepthData>('/api/v1/c/market/depth', params)
}

/**
 * 获取最近成交
 */
export function getTrades(params: TradesParams): Promise<TradesResponse> {
  return get<TradesResponse>('/api/v1/c/market/trades', params)
}

/**
 * 获取交易对列表
 */
export function getSymbols(params: SymbolsParams): Promise<SymbolsResponse> {
  return get<SymbolsResponse>('/api/v1/c/market/symbols', params)
}

/**
 * 获取交易所列表
 */
export function getExchanges(): Promise<ExchangesResponse> {
  return get<ExchangesResponse>('/api/v1/c/market/exchanges')
}

// ==================== WebSocket相关 ====================

/**
 * WebSocket连接配置
 */
export interface WebSocketConfig {
  url: string
  reconnect?: boolean
  reconnectInterval?: number
  heartbeatInterval?: number
}

/**
 * WebSocket消息类型
 */
export type WSMessageType = 'kline' | 'ticker' | 'depth' | 'trade'

/**
 * WebSocket订阅参数
 */
export interface WSSubscribeParams {
  exchange_id: string
  symbol: string
  type: WSMessageType
  interval?: KlineInterval
}

/**
 * 创建WebSocket连接（示例实现，实际使用时需要根据后端WebSocket协议调整）
 */
export function createWebSocket(config: WebSocketConfig): WebSocket {
  const ws = new WebSocket(config.url)
  
  ws.onopen = () => {
    console.log('WebSocket connected')
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
  
  ws.onclose = () => {
    console.log('WebSocket closed')
    if (config.reconnect) {
      setTimeout(() => {
        createWebSocket(config)
      }, config.reconnectInterval || 5000)
    }
  }
  
  return ws
}

/**
 * 订阅WebSocket数据
 */
export function subscribeWebSocket(ws: WebSocket, params: WSSubscribeParams): void {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      action: 'subscribe',
      ...params,
    }))
  }
}

/**
 * 取消订阅WebSocket数据
 */
export function unsubscribeWebSocket(ws: WebSocket, params: WSSubscribeParams): void {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      action: 'unsubscribe',
      ...params,
    }))
  }
}

// 导出所有API
export default {
  getKlines,
  getTicker,
  getTickers,
  getDepth,
  getTrades,
  getSymbols,
  getExchanges,
  createWebSocket,
  subscribeWebSocket,
  unsubscribeWebSocket,
}
