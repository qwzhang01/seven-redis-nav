<template>
  <div class="trading-page">
    <!-- 交易类型切换 -->
    <div class="trade-type-tabs">
      <t-button
        :theme="tradeType === 'spot' ? 'primary' : 'default'"
        variant="text"
        @click="tradeType = 'spot'"
      >
        现货交易
      </t-button>
      <t-button
        :theme="tradeType === 'contract' ? 'primary' : 'default'"
        variant="text"
        @click="$router.push('/contract')"
      >
        <t-icon name="trending-up" /> 合约交易
      </t-button>
    </div>
    
    <!-- 交易对信息 -->
    <div class="trading-header">
      <t-dropdown :options="pairOptions" @click="changePair">
        <div class="pair-selector">
          <span class="pair-name">{{ tradingStore.currentPair.symbol }}</span>
          <t-icon name="chevron-down" />
        </div>
      </t-dropdown>
      
      <div class="pair-price" :class="priceDirection">
        ${{ formatPrice(tradingStore.currentPair.price) }}
      </div>
      
      <t-tag
        :theme="tradingStore.currentPair.change >= 0 ? 'success' : 'danger'"
        variant="light"
      >
        {{ tradingStore.currentPair.change >= 0 ? '+' : '' }}{{ tradingStore.currentPair.change.toFixed(2) }}%
      </t-tag>
      
      <div class="pair-stats">
        <div class="stat-item">
          <span class="stat-label">24h高</span>
          <span class="stat-value">${{ formatPrice(tradingStore.currentPair.high24h) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">24h低</span>
          <span class="stat-value">${{ formatPrice(tradingStore.currentPair.low24h) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">成交量</span>
          <span class="stat-value">{{ formatNumber(tradingStore.currentPair.volume24h) }} BTC</span>
        </div>
      </div>
    </div>
    
    <!-- 主内容区 -->
    <div class="trading-main">
      <!-- 图表区域 -->
      <div class="chart-section">
        <div class="chart-toolbar">
          <!-- 周期选择 -->
          <t-radio-group v-model="timeframe" variant="default-filled" size="small">
            <t-radio-button value="1m">1m</t-radio-button>
            <t-radio-button value="5m">5m</t-radio-button>
            <t-radio-button value="1h">1h</t-radio-button>
            <t-radio-button value="4h">4h</t-radio-button>
            <t-radio-button value="1d">1d</t-radio-button>
          </t-radio-group>
          
          <!-- 指标选择 -->
          <t-dropdown :options="indicatorOptions" trigger="click" @click="toggleIndicator">
            <t-button variant="outline" size="small">
              <t-icon name="chart-bar" /> 技术指标
              <t-tag size="small" theme="primary">{{ activeIndicators.length }}</t-tag>
            </t-button>
          </t-dropdown>
          
          <!-- 画线工具 -->
          <t-button variant="outline" size="small" @click="showDrawingPanel = true">
            <t-icon name="edit-1" /> 画线
          </t-button>
        </div>
        
        <!-- 活跃指标 -->
        <div class="active-indicators">
          <t-tag
            v-for="ind in activeIndicators"
            :key="ind"
            closable
            @close="removeIndicator(ind)"
          >
            {{ ind }}
          </t-tag>
        </div>
        
        <!-- TradingView K线图 -->
        <div class="chart-container" ref="chartContainerRef"></div>
        
        <!-- 连接状态 -->
        <div class="connection-status">
          <span class="status-dot" :class="{ connected: wsConnected }"></span>
          <span>{{ wsConnected ? '实时数据已连接' : '连接中...' }}</span>
        </div>
      </div>
      
      <!-- 订单面板 -->
      <div class="order-panel">
        <OrderPanel />
      </div>
    </div>
    
    <!-- 订单列表 -->
    <div class="orders-section">
      <OrderList />
    </div>
    
    <!-- 画线工具面板 -->
    <t-drawer
      v-model:visible="showDrawingPanel"
      header="画线工具"
      :size="300"
      placement="right"
    >
      <DrawingTools @select="handleDrawingTool" />
    </t-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { createChart } from 'lightweight-charts'
import { useTradingStore } from '@/stores/trading'
import OrderPanel from '@/components/trading/OrderPanel.vue'
import OrderList from '@/components/trading/OrderList.vue'
import DrawingTools from '@/components/trading/DrawingTools.vue'

const tradingStore = useTradingStore()

// 状态
const tradeType = ref('spot')
const timeframe = ref('1h')
const priceDirection = ref('up')
const wsConnected = ref(true)
const showDrawingPanel = ref(false)
const chartContainerRef = ref(null)
let chart = null
let candleSeries = null

// 活跃指标
const activeIndicators = ref(['MA(7,25,99)', 'EMA(12,26)', 'MACD'])

// 交易对选项
const pairOptions = [
  { content: 'BTC/USDT', value: 'BTC/USDT' },
  { content: 'ETH/USDT', value: 'ETH/USDT' },
  { content: 'BNB/USDT', value: 'BNB/USDT' },
  { content: 'SOL/USDT', value: 'SOL/USDT' }
]

// 指标选项
const indicatorOptions = [
  { content: 'MA 均线', value: 'MA' },
  { content: 'EMA 指数均线', value: 'EMA' },
  { content: 'BOLL 布林带', value: 'BOLL' },
  { content: 'MACD', value: 'MACD' },
  { content: 'RSI', value: 'RSI' },
  { content: 'KDJ', value: 'KDJ' }
]

// 切换交易对
const changePair = (data) => {
  tradingStore.currentPair.symbol = data.value
}

// 切换指标
const toggleIndicator = (data) => {
  const index = activeIndicators.value.findIndex(i => i.includes(data.value))
  if (index > -1) {
    activeIndicators.value.splice(index, 1)
  } else {
    activeIndicators.value.push(data.value)
  }
}

// 移除指标
const removeIndicator = (indicator) => {
  const index = activeIndicators.value.indexOf(indicator)
  if (index > -1) {
    activeIndicators.value.splice(index, 1)
  }
}

// 画线工具选择
const handleDrawingTool = (tool) => {
  console.log('Selected drawing tool:', tool)
  showDrawingPanel.value = false
}

// 格式化价格
const formatPrice = (price) => {
  return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// 格式化数字
const formatNumber = (num) => {
  return num.toLocaleString('en-US')
}

// 初始化图表
const initChart = () => {
  if (!chartContainerRef.value) return
  
  chart = createChart(chartContainerRef.value, {
    width: chartContainerRef.value.clientWidth,
    height: 450,
    layout: {
      background: { color: '#0d1117' },
      textColor: 'rgba(255, 255, 255, 0.6)'
    },
    grid: {
      vertLines: { color: '#21262d' },
      horzLines: { color: '#21262d' }
    },
    crosshair: {
      mode: 1
    },
    rightPriceScale: {
      borderColor: '#30363d'
    },
    timeScale: {
      borderColor: '#30363d',
      timeVisible: true
    }
  })
  
  candleSeries = chart.addCandlestickSeries({
    upColor: '#00A870',
    downColor: '#E34D59',
    borderUpColor: '#00A870',
    borderDownColor: '#E34D59',
    wickUpColor: '#00A870',
    wickDownColor: '#E34D59'
  })
  
  // 生成模拟数据
  const data = generateKlineData()
  candleSeries.setData(data)
  
  // 自适应宽度
  window.addEventListener('resize', handleResize)
}

// 生成K线数据
const generateKlineData = () => {
  const data = []
  let price = 45000
  const now = Math.floor(Date.now() / 1000)
  
  for (let i = 200; i >= 0; i--) {
    const time = now - i * 3600
    const open = price + (Math.random() - 0.5) * 500
    const close = open + (Math.random() - 0.5) * 400
    const high = Math.max(open, close) + Math.random() * 200
    const low = Math.min(open, close) - Math.random() * 200
    data.push({ time, open, high, low, close })
    price = close
  }
  
  return data
}

// 处理窗口大小变化
const handleResize = () => {
  if (chart && chartContainerRef.value) {
    chart.applyOptions({ width: chartContainerRef.value.clientWidth })
  }
}

// 模拟实时价格更新
let priceUpdateTimer = null
const startPriceUpdate = () => {
  priceUpdateTimer = setInterval(() => {
    const change = (Math.random() - 0.5) * 100
    const direction = tradingStore.updatePrice(tradingStore.currentPair.price + change)
    priceDirection.value = direction
  }, 3000)
}

onMounted(() => {
  initChart()
  startPriceUpdate()
})

onUnmounted(() => {
  if (chart) {
    chart.remove()
  }
  window.removeEventListener('resize', handleResize)
  if (priceUpdateTimer) {
    clearInterval(priceUpdateTimer)
  }
})
</script>

<style lang="less" scoped>
.trading-page {
  background: #0d1117;
  min-height: calc(100vh - 56px);
}

.trade-type-tabs {
  padding: 12px 24px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  display: flex;
  gap: 8px;
  
  :deep(.t-button) {
    color: rgba(255, 255, 255, 0.6);
    font-size: 15px;
    padding: 8px 16px;
    
    &:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.1);
    }
    
    &.t-button--theme-primary {
      color: var(--brand);
      font-weight: 500;
      
      &:hover {
        color: var(--brand);
        background: rgba(18, 95, 255, 0.15);
      }
    }
  }
}

.trading-header {
  padding: 16px 24px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  display: flex;
  align-items: center;
  gap: 24px;
}

.pair-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #21262d;
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  
  .pair-name {
    font-size: 18px;
    font-weight: bold;
  }
}

.pair-price {
  font-size: 24px;
  font-weight: bold;
  transition: color 0.3s;
  
  &.up {
    color: var(--green);
  }
  
  &.down {
    color: var(--red);
  }
}

.pair-stats {
  display: flex;
  gap: 24px;
  margin-left: auto;
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
  
  .stat-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  .stat-label {
    color: rgba(255, 255, 255, 0.4);
  }
  
  .stat-value {
    color: #fff;
  }
}

.trading-main {
  display: grid;
  grid-template-columns: 1fr 360px;
}

.chart-section {
  border-right: 1px solid #30363d;
}

.chart-toolbar {
  padding: 12px 16px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  display: flex;
  align-items: center;
  gap: 16px;
}

.active-indicators {
  padding: 8px 16px;
  background: #161b22;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chart-container {
  height: 450px;
  background: #0d1117;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #666;
    
    &.connected {
      background: var(--green);
    }
  }
}

.order-panel {
  background: #161b22;
}

.orders-section {
  background: #161b22;
  border-top: 1px solid #30363d;
  padding: 16px 24px;
}
</style>
