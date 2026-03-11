/**
 * 市场API Mock数据结构
 * 为后端开发提供参考的API响应格式
 */

export interface DepthData {
  bids: Array<{ price: number; amount: number }>
  asks: Array<{ price: number; amount: number }>
  timestamp: number
}

export interface VolumeData {
  time: number
  value: number
}

export interface KlineData {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

/**
 * 深度数据Mock API响应
 */
export const mockDepthData: DepthData = {
  bids: [
    { price: 91400.00, amount: 2.5 },
    { price: 91350.00, amount: 1.8 },
    { price: 91300.00, amount: 3.2 },
    { price: 91250.00, amount: 0.9 },
    { price: 91200.00, amount: 2.1 },
    { price: 91150.00, amount: 1.5 },
    { price: 91100.00, amount: 3.8 },
    { price: 91050.00, amount: 2.3 },
    { price: 91000.00, amount: 1.7 },
    { price: 90950.00, amount: 4.2 }
  ],
  asks: [
    { price: 91500.00, amount: 1.8 },
    { price: 91550.00, amount: 2.4 },
    { price: 91600.00, amount: 1.2 },
    { price: 91650.00, amount: 3.1 },
    { price: 91700.00, amount: 2.7 },
    { price: 91750.00, amount: 1.9 },
    { price: 91800.00, amount: 3.5 },
    { price: 91850.00, amount: 2.2 },
    { price: 91900.00, amount: 1.6 },
    { price: 91950.00, amount: 4.8 }
  ],
  timestamp: Date.now()
}

/**
 * 成交量数据Mock API响应
 */
export const mockVolumeData: VolumeData[] = [
  { time: Math.floor(Date.now() / 1000) - 3600, value: 1250 },
  { time: Math.floor(Date.now() / 1000) - 3540, value: 980 },
  { time: Math.floor(Date.now() / 1000) - 3480, value: 1560 },
  { time: Math.floor(Date.now() / 1000) - 3420, value: 890 },
  { time: Math.floor(Date.now() / 1000) - 3360, value: 2100 },
  { time: Math.floor(Date.now() / 1000) - 3300, value: 1450 },
  { time: Math.floor(Date.now() / 1000) - 3240, value: 1120 },
  { time: Math.floor(Date.now() / 1000) - 3180, value: 980 },
  { time: Math.floor(Date.now() / 1000) - 3120, value: 1650 },
  { time: Math.floor(Date.now() / 1000) - 3060, value: 1340 }
]

/**
 * K线数据Mock API响应
 */
export const mockKlineData: KlineData[] = [
  {
    time: Math.floor(Date.now() / 1000) - 3600,
    open: 91000.00,
    high: 91500.00,
    low: 90800.00,
    close: 91450.00,
    volume: 1250
  },
  {
    time: Math.floor(Date.now() / 1000) - 3540,
    open: 91450.00,
    high: 91800.00,
    low: 91300.00,
    close: 91650.00,
    volume: 980
  },
  {
    time: Math.floor(Date.now() / 1000) - 3480,
    open: 91650.00,
    high: 92000.00,
    low: 91500.00,
    close: 91850.00,
    volume: 1560
  }
]

/**
 * 市场API Mock服务
 */
export class MarketApiMock {
  /**
   * 获取深度数据
   */
  static async getDepth(params: { symbol: string; limit?: number }): Promise<DepthData> {
    return {
      ...mockDepthData,
      bids: mockDepthData.bids.slice(0, params.limit || 10),
      asks: mockDepthData.asks.slice(0, params.limit || 10)
    }
  }

  /**
   * 获取成交量数据
   */
  static async getVolume(params: { symbol: string; interval?: string; limit?: number }): Promise<VolumeData[]> {
    return mockVolumeData.slice(0, params.limit || 60)
  }

  /**
   * 获取K线数据
   */
  static async getKlines(params: { symbol: string; interval: string; limit?: number }): Promise<KlineData[]> {
    return mockKlineData.slice(0, params.limit || 100)
  }

  /**
   * 获取实时价格
   */
  static async getTicker(params: { symbol: string }): Promise<{
    last_price: number
    price_change_percent: number
    high_price: number
    low_price: number
    volume: number
  }> {
    return {
      last_price: 91476.14,
      price_change_percent: 1.24,
      high_price: 92800.00,
      low_price: 89200.00,
      volume: 12345
    }
  }
}

/**
 * WebSocket Mock服务
 */
export class WebSocketMock {
  /**
   * 模拟实时深度数据推送
   */
  static subscribeDepth(symbol: string, callback: (data: DepthData) => void) {
    // 模拟实时数据更新
    setInterval(() => {
      const updatedData = {
        ...mockDepthData,
        timestamp: Date.now(),
        bids: mockDepthData.bids.map(bid => ({
          ...bid,
          amount: bid.amount * (0.95 + Math.random() * 0.1)
        })),
        asks: mockDepthData.asks.map(ask => ({
          ...ask,
          amount: ask.amount * (0.95 + Math.random() * 0.1)
        }))
      }
      callback(updatedData)
    }, 1000)
  }

  /**
   * 模拟实时成交量数据推送
   */
  static subscribeVolume(symbol: string, callback: (data: VolumeData) => void) {
    // 模拟实时数据更新
    setInterval(() => {
      const newData: VolumeData = {
        time: Math.floor(Date.now() / 1000),
        value: Math.random() * 2000 + 500
      }
      callback(newData)
    }, 5000)
  }
}

/**
 * 后端API接口规范文档
 */
export const API_DOCUMENTATION = {
  depth: {
    endpoint: '/api/v1/market/depth',
    method: 'GET',
    params: {
      symbol: 'string (交易对，如 BTC/USDT)',
      limit: 'number (可选，返回的深度档位数，默认10)'
    },
    response: {
      bids: 'Array<{ price: number, amount: number }> (买单深度)',
      asks: 'Array<{ price: number, amount: number }> (卖单深度)',
      timestamp: 'number (数据时间戳)'
    }
  },
  volume: {
    endpoint: '/api/v1/market/volume',
    method: 'GET',
    params: {
      symbol: 'string (交易对)',
      interval: 'string (可选，时间间隔，如 1m, 5m, 1h)',
      limit: 'number (可选，返回的数据点数，默认60)'
    },
    response: 'Array<{ time: number, value: number }> (成交量数据)'
  },
  klines: {
    endpoint: '/api/v1/market/klines',
    method: 'GET',
    params: {
      symbol: 'string (交易对)',
      interval: 'string (时间间隔，如 1m, 5m, 1h, 1d)',
      limit: 'number (可选，返回的K线数量，默认100)'
    },
    response: 'Array<{ time: number, open: number, high: number, low: number, close: number, volume: number }> (K线数据)'
  }
}