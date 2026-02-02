import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useTradingStore = defineStore('trading', () => {
  // 当前交易对
  const currentPair = ref({
    symbol: 'BTC/USDT',
    price: 45230.50,
    change: 2.35,
    high24h: 45800,
    low24h: 44200,
    volume24h: 12345
  })
  
  // 订单列表
  const orders = ref([
    { id: 1, time: '12:30:15', pair: 'BTC/USDT', side: 'buy', type: '限价', price: 45000, amount: 0.1, filled: 0, status: 'pending' },
    { id: 2, time: '12:28:30', pair: 'BTC/USDT', side: 'sell', type: '限价', price: 46000, amount: 0.05, filled: 0, status: 'pending' },
    { id: 3, time: '12:15:00', pair: 'ETH/USDT', side: 'buy', type: '止盈止损', price: 3200, amount: 0.5, filled: 0, status: 'pending' }
  ])
  
  // 历史订单
  const historyOrders = ref([
    { id: 101, time: '12:00:00', pair: 'BTC/USDT', side: 'buy', type: '限价', price: 44500, amount: 0.08, fillPrice: 44498, status: 'filled', pnl: null },
    { id: 102, time: '11:45:30', pair: 'BTC/USDT', side: 'sell', type: '市价', price: null, amount: 0.05, fillPrice: 44650, status: 'filled', pnl: 32.50 },
    { id: 103, time: '11:30:00', pair: 'ETH/USDT', side: 'buy', type: '限价', price: 3100, amount: 1.0, fillPrice: 3099, status: 'filled', pnl: null }
  ])
  
  // 持仓
  const positions = ref([
    { pair: 'BTC/USDT', side: 'long', amount: 0.1, entryPrice: 45000, currentPrice: 46200, pnl: 120 }
  ])
  
  // 合约持仓
  const contractPositions = ref([
    { pair: 'BTC/USDT永续', side: 'long', leverage: 10, amount: 0.1, entryPrice: 44500, markPrice: 45230, liqPrice: 42500, pnl: 730 },
    { pair: 'ETH/USDT永续', side: 'short', leverage: 5, amount: 1.0, entryPrice: 2450, markPrice: 2420, liqPrice: 2600, pnl: 30 }
  ])
  
  // K线周期
  const timeframe = ref('1h')
  
  // 更新价格
  const updatePrice = (newPrice) => {
    const oldPrice = currentPair.value.price
    currentPair.value.price = newPrice
    currentPair.value.change = ((newPrice - 45000) / 45000 * 100)
    return newPrice > oldPrice ? 'up' : 'down'
  }
  
  // 计算待成交订单数
  const pendingOrderCount = computed(() => {
    return orders.value.filter(o => o.status === 'pending').length
  })
  
  // 计算总持仓盈亏
  const totalPositionPnL = computed(() => {
    return positions.value.reduce((sum, p) => sum + p.pnl, 0)
  })
  
  // 下单
  const placeOrder = (order) => {
    const newOrder = {
      id: Date.now(),
      time: new Date().toLocaleTimeString(),
      ...order,
      filled: 0,
      status: 'pending'
    }
    orders.value.unshift(newOrder)
    return newOrder
  }
  
  // 取消订单
  const cancelOrder = (orderId) => {
    const index = orders.value.findIndex(o => o.id === orderId)
    if (index > -1) {
      orders.value.splice(index, 1)
      return true
    }
    return false
  }
  
  return {
    currentPair,
    orders,
    historyOrders,
    positions,
    contractPositions,
    timeframe,
    pendingOrderCount,
    totalPositionPnL,
    updatePrice,
    placeOrder,
    cancelOrder
  }
})
