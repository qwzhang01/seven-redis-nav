/**
 * 市场数据 API服务
 * 对接量化交易系统的市场数据接口
 */

import { get, post, put, del } from './request'

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

/**
 * 订阅行情数据
 */
export interface SubscribeMarketRequest {
  symbols: string[]
  exchange?: string
  market_type?: string
}

export interface SubscribeMarketResponse {
  success: boolean
  message: string
  symbols: string[]
}

export function subscribeMarket(data: SubscribeMarketRequest): Promise<SubscribeMarketResponse> {
  return post<SubscribeMarketResponse>('/api/v1/c/market/subscribe', data)
}

/**
 * 取消行情订阅
 */
export function unsubscribeMarket(data: SubscribeMarketRequest): Promise<SubscribeMarketResponse> {
  return post<SubscribeMarketResponse>('/api/v1/c/market/unsubscribe', data)
}

/**
 * 获取K线数据（路径参数方式）
 */
export interface KlinePathParams {
  timeframe?: string
  limit?: number
}

export function getKlineBySymbol(symbol: string, params?: KlinePathParams): Promise<any> {
  return get<any>(`/api/v1/c/market/kline/${symbol}`, params)
}

/**
 * 获取最新Tick数据
 */
export function getTickBySymbol(symbol: string): Promise<any> {
  return get<any>(`/api/v1/c/market/tick/${symbol}`)
}

/**
 * 获取市场深度数据
 */
export function getDepthBySymbol(symbol: string, params?: { limit?: number }): Promise<any> {
  return get<any>(`/api/v1/c/market/depth/${symbol}`, params)
}

/**
 * 获取已订阅的交易对列表
 */
export interface SubscribedSymbolsParams {
  exchange?: string
  market_type?: string
}

export interface SubscribedSymbolsResponse {
  exchange: string
  market_type: string
  symbols: string[]
}

export function getSubscribedSymbols(params?: SubscribedSymbolsParams): Promise<SubscribedSymbolsResponse> {
  return get<SubscribedSymbolsResponse>('/api/v1/c/market/symbols', params)
}

/**
 * 获取行情服务统计信息
 */
export function getMarketStats(): Promise<Record<string, any>> {
  return get<Record<string, any>>('/api/v1/c/market/stats')
}

// ==================== Admin端订阅管理接口 ====================

/**
 * 订阅配置
 */
export interface SubscriptionConfig {
  id: string
  name: string
  exchange: string
  market_type: string
  data_type: string
  symbols: string[]
  interval?: string
  status: 'running' | 'paused' | 'stopped'
  created_at: string
  updated_at: string
  last_sync_time?: string
  total_records: number
  error_count: number
  last_error?: string
  config: {
    auto_restart: boolean
    max_retries: number
    batch_size: number
    sync_interval: number
  }
}

/**
 * 创建订阅配置
 */
export interface CreateSubscriptionRequest {
  name: string
  exchange: string
  market_type?: string
  data_type: string
  symbols: string[]
  interval?: string
  config?: {
    auto_restart?: boolean
    max_retries?: number
    batch_size?: number
    sync_interval?: number
  }
}

export function createSubscription(data: CreateSubscriptionRequest): Promise<{ success: boolean; message: string; data: SubscriptionConfig }> {
  return post<{ success: boolean; message: string; data: SubscriptionConfig }>('/api/v1/m/market/subscriptions', data)
}

/**
 * 获取订阅列表
 */
export interface GetSubscriptionsParams {
  exchange?: string
  data_type?: string
  status?: string
  search?: string
  page?: number
  page_size?: number
}

export interface GetSubscriptionsResponse {
  items: SubscriptionConfig[]
  total: number
  page: number
  page_size: number
}

export function getSubscriptions(params?: GetSubscriptionsParams): Promise<GetSubscriptionsResponse> {
  return get<GetSubscriptionsResponse>('/api/v1/m/market/subscriptions', params)
}

/**
 * 获取订阅统计信息
 */
export interface SubscriptionStatistics {
  total_subscriptions: number
  running_subscriptions: number
  paused_subscriptions: number
  stopped_subscriptions: number
  total_records: number
  total_errors: number
  by_exchange: Record<string, number>
  by_data_type: Record<string, number>
}

export function getSubscriptionStatistics(): Promise<{ success: boolean; data: SubscriptionStatistics }> {
  return get<{ success: boolean; data: SubscriptionStatistics }>('/api/v1/m/market/subscriptions/statistics')
}

/**
 * 获取订阅详情
 */
export function getSubscriptionDetail(subscriptionId: string): Promise<{ success: boolean; data: SubscriptionConfig }> {
  return get<{ success: boolean; data: SubscriptionConfig }>(`/api/v1/m/market/subscriptions/${subscriptionId}`)
}

/**
 * 更新订阅配置
 */
export interface UpdateSubscriptionRequest {
  name?: string
  symbols?: string[]
  interval?: string
  config?: {
    auto_restart?: boolean
    max_retries?: number
    batch_size?: number
    sync_interval?: number
  }
}

export function updateSubscription(subscriptionId: string, data: UpdateSubscriptionRequest): Promise<{ success: boolean; message: string; data: SubscriptionConfig }> {
  return put<{ success: boolean; message: string; data: SubscriptionConfig }>(`/api/v1/m/market/subscriptions/${subscriptionId}`, data)
}

/**
 * 删除订阅
 */
export function deleteSubscription(subscriptionId: string): Promise<{ success: boolean; message: string }> {
  return del<{ success: boolean; message: string }>(`/api/v1/m/market/subscriptions/${subscriptionId}`)
}

/**
 * 启动订阅
 */
export function startSubscription(subscriptionId: string): Promise<{ success: boolean; message: string; data: any }> {
  return post<{ success: boolean; message: string; data: any }>(`/api/v1/m/market/subscriptions/${subscriptionId}/start`)
}

/**
 * 暂停订阅
 */
export function pauseSubscription(subscriptionId: string): Promise<{ success: boolean; message: string; data: any }> {
  return post<{ success: boolean; message: string; data: any }>(`/api/v1/m/market/subscriptions/${subscriptionId}/pause`)
}

/**
 * 停止订阅
 */
export function stopSubscription(subscriptionId: string): Promise<{ success: boolean; message: string; data: any }> {
  return post<{ success: boolean; message: string; data: any }>(`/api/v1/m/market/subscriptions/${subscriptionId}/stop`)
}

// ==================== Admin端同步任务管理接口 ====================

/**
 * 同步任务
 */
export interface SyncTask {
  id: string
  subscription_id: string
  subscription_name: string
  exchange: string
  symbols: string[]
  data_type: string
  start_time: string
  end_time: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  total_records: number
  synced_records: number
  error_message?: string
  created_at: string
  updated_at: string
  completed_at?: string
}

/**
 * 创建同步任务
 */
export interface CreateSyncTaskRequest {
  subscription_id: string
  start_time: string
  end_time: string
}

export function createSyncTask(data: CreateSyncTaskRequest): Promise<{ success: boolean; message: string; data: SyncTask }> {
  return post<{ success: boolean; message: string; data: SyncTask }>('/api/v1/m/market/sync-tasks', data)
}

/**
 * 获取同步任务列表
 */
export interface GetSyncTasksParams {
  subscription_id?: string
  status?: string
  page?: number
  page_size?: number
}

export interface GetSyncTasksResponse {
  success: boolean
  data: {
    items: SyncTask[]
    total: number
    page: number
    page_size: number
  }
}

export function getSyncTasks(params?: GetSyncTasksParams): Promise<GetSyncTasksResponse> {
  return get<GetSyncTasksResponse>('/api/v1/m/market/sync-tasks', params)
}

/**
 * 获取同步任务详情
 */
export function getSyncTaskDetail(taskId: string): Promise<{ success: boolean; data: SyncTask }> {
  return get<{ success: boolean; data: SyncTask }>(`/api/v1/m/market/sync-tasks/${taskId}`)
}

/**
 * 取消同步任务
 */
export function cancelSyncTask(taskId: string): Promise<{ success: boolean; message: string; data: any }> {
  return post<{ success: boolean; message: string; data: any }>(`/api/v1/m/market/sync-tasks/${taskId}/cancel`)
}

// ==================== Admin端历史数据同步接口 ====================

/**
 * 历史同步任务
 */
export interface HistoricalSyncTask {
  id: string
  name: string
  exchange: string
  data_type: string
  symbols: string[]
  interval?: string
  start_time: string
  end_time: string
  batch_size: number
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  total_records: number
  synced_records: number
  error_message?: string
  created_at: string
  updated_at: string
  completed_at?: string
}

/**
 * 创建历史数据同步任务
 */
export interface CreateHistoricalSyncRequest {
  name: string
  exchange: string
  data_type: string
  symbols: string[]
  interval?: string
  start_time: string
  end_time: string
  batch_size?: number
}

export function createHistoricalSync(data: CreateHistoricalSyncRequest): Promise<{ success: boolean; message: string; data: HistoricalSyncTask }> {
  return post<{ success: boolean; message: string; data: HistoricalSyncTask }>('/api/v1/m/market/historical-sync', data)
}

/**
 * 获取历史同步任务列表
 */
export interface GetHistoricalSyncParams {
  exchange?: string
  data_type?: string
  status?: string
  page?: number
  page_size?: number
}

export interface GetHistoricalSyncResponse {
  success: boolean
  data: {
    items: HistoricalSyncTask[]
    total: number
    page: number
    page_size: number
  }
}

export function getHistoricalSyncTasks(params?: GetHistoricalSyncParams): Promise<GetHistoricalSyncResponse> {
  return get<GetHistoricalSyncResponse>('/api/v1/m/market/historical-sync', params)
}

/**
 * 获取历史同步任务详情
 */
export function getHistoricalSyncDetail(taskId: string): Promise<{ success: boolean; data: HistoricalSyncTask }> {
  return get<{ success: boolean; data: HistoricalSyncTask }>(`/api/v1/m/market/historical-sync/${taskId}`)
}

/**
 * 取消历史同步任务
 */
export function cancelHistoricalSync(taskId: string): Promise<{ success: boolean; message: string; data: any }> {
  return post<{ success: boolean; message: string; data: any }>(`/api/v1/m/market/historical-sync/${taskId}/cancel`)
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
  // C端接口
  getKlines,
  getTicker,
  getTickers,
  getDepth,
  getTrades,
  getSymbols,
  getExchanges,
  subscribeMarket,
  unsubscribeMarket,
  getKlineBySymbol,
  getTickBySymbol,
  getDepthBySymbol,
  getSubscribedSymbols,
  getMarketStats,
  // Admin端订阅管理接口
  createSubscription,
  getSubscriptions,
  getSubscriptionStatistics,
  getSubscriptionDetail,
  updateSubscription,
  deleteSubscription,
  startSubscription,
  pauseSubscription,
  stopSubscription,
  // Admin端同步任务管理接口
  createSyncTask,
  getSyncTasks,
  getSyncTaskDetail,
  cancelSyncTask,
  // Admin端历史数据同步接口
  createHistoricalSync,
  getHistoricalSyncTasks,
  getHistoricalSyncDetail,
  cancelHistoricalSync,
  // WebSocket相关
  createWebSocket,
  subscribeWebSocket,
  unsubscribeWebSocket,
}
