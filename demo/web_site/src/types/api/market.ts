/**
 * 市场数据相关API类型定义
 * 根据 api.json 的 schema 定义
 */

// ==================== K线数据 ====================

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

// ==================== 行情数据 ====================

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

// ==================== 市场深度 ====================

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

// ==================== 成交记录 ====================

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

// ==================== 交易对信息 ====================

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

// ==================== 行情订阅 ====================

/**
 * 订阅行情请求
 */
export interface SubscribeRequest {
  symbols: string[]
  exchange?: string
  market_type?: string
}

/**
 * 订阅行情响应
 */
export interface SubscribeResponse {
  success: boolean
  message: string
  symbols: string[]
}

// ==================== Admin端数据订阅管理 ====================

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
 * 创建订阅请求
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

/**
 * 更新订阅请求
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

/**
 * 订阅统计信息
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

// ==================== 同步任务 ====================

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
 * 创建同步任务请求
 */
export interface CreateSyncTaskRequest {
  subscription_id: string
  start_time: string
  end_time: string
}

// ==================== 历史数据同步 ====================

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
 * 创建历史同步请求
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
