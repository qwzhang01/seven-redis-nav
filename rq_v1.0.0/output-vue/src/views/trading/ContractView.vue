<template>
  <div class="contract-page">
    <!-- 交易类型切换 -->
    <div class="trade-type-tabs">
      <t-button
        :theme="'default'"
        variant="text"
        @click="$router.push('/trading')"
      >
        现货交易
      </t-button>
      <t-button
        :theme="'primary'"
        variant="text"
      >
        <t-icon name="trending-up" /> 合约交易
      </t-button>
    </div>
    
    <!-- 合约信息头部 -->
    <div class="contract-header">
      <t-dropdown :options="pairOptions" @click="changePair">
        <div class="pair-selector">
          <span class="pair-name">{{ currentPair.symbol }}</span>
          <t-tag theme="warning" size="small">永续</t-tag>
          <t-icon name="chevron-down" />
        </div>
      </t-dropdown>
      
      <div class="pair-price" :class="priceDirection">
        ${{ formatPrice(currentPair.price) }}
      </div>
      
      <t-tag
        :theme="currentPair.change >= 0 ? 'success' : 'danger'"
        variant="light"
      >
        {{ currentPair.change >= 0 ? '+' : '' }}{{ currentPair.change.toFixed(2) }}%
      </t-tag>
      
      <div class="contract-stats">
        <div class="stat-item">
          <span class="stat-label">标记价格</span>
          <span class="stat-value">${{ formatPrice(currentPair.markPrice) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">指数价格</span>
          <span class="stat-value">${{ formatPrice(currentPair.indexPrice) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">资金费率</span>
          <span class="stat-value" :class="currentPair.fundingRate >= 0 ? 'text-success' : 'text-danger'">
            {{ currentPair.fundingRate >= 0 ? '+' : '' }}{{ currentPair.fundingRate.toFixed(4) }}%
          </span>
        </div>
        <div class="stat-item">
          <span class="stat-label">24h成交量</span>
          <span class="stat-value">{{ formatNumber(currentPair.volume24h) }} USDT</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">持仓量</span>
          <span class="stat-value">{{ formatNumber(currentPair.openInterest) }} BTC</span>
        </div>
      </div>
    </div>
    
    <!-- 主内容区 -->
    <div class="contract-main">
      <!-- 左侧图表区域 -->
      <div class="chart-section">
        <div class="chart-toolbar">
          <!-- 周期选择 -->
          <t-radio-group v-model="timeframe" variant="default-filled" size="small">
            <t-radio-button value="1m">1m</t-radio-button>
            <t-radio-button value="5m">5m</t-radio-button>
            <t-radio-button value="15m">15m</t-radio-button>
            <t-radio-button value="1h">1h</t-radio-button>
            <t-radio-button value="4h">4h</t-radio-button>
            <t-radio-button value="1d">1d</t-radio-button>
          </t-radio-group>
          
          <!-- 图表类型 -->
          <t-radio-group v-model="chartType" variant="default-filled" size="small">
            <t-radio-button value="candle">
              <t-icon name="chart-candlestick" />
            </t-radio-button>
            <t-radio-button value="line">
              <t-icon name="chart-line" />
            </t-radio-button>
            <t-radio-button value="depth">
              <t-icon name="chart-area" />
            </t-radio-button>
          </t-radio-group>
          
          <!-- 指标 -->
          <t-dropdown :options="indicatorOptions" trigger="click" @click="toggleIndicator">
            <t-button variant="outline" size="small">
              <t-icon name="chart-bar" /> 指标
              <t-tag size="small" theme="primary">{{ activeIndicators.length }}</t-tag>
            </t-button>
          </t-dropdown>
        </div>
        
        <!-- K线图 -->
        <div class="chart-container" ref="chartContainerRef"></div>
        
        <!-- 深度图 -->
        <div v-if="chartType === 'depth'" class="depth-chart">
          <apexchart
            type="area"
            height="400"
            :options="depthChartOptions"
            :series="depthSeries"
          />
        </div>
      </div>
      
      <!-- 右侧订单面板 -->
      <div class="order-section">
        <!-- 杠杆调整 -->
        <div class="leverage-panel">
          <div class="leverage-header">
            <span>杠杆倍数</span>
            <t-button variant="text" size="small" @click="showLeverageModal = true">
              调整杠杆
            </t-button>
          </div>
          <div class="leverage-display">
            <span class="leverage-value">{{ leverage }}x</span>
            <t-slider
              v-model="leverage"
              :min="1"
              :max="125"
              :step="1"
              :marks="{ 1: '1x', 25: '25x', 50: '50x', 75: '75x', 100: '100x', 125: '125x' }"
            />
          </div>
        </div>
        
        <!-- 保证金模式 -->
        <div class="margin-mode">
          <t-radio-group v-model="marginMode" variant="default-filled" size="small">
            <t-radio-button value="cross">全仓</t-radio-button>
            <t-radio-button value="isolated">逐仓</t-radio-button>
          </t-radio-group>
        </div>
        
        <!-- 开仓方向 -->
        <div class="position-tabs">
          <div 
            class="position-tab" 
            :class="{ active: positionSide === 'long', long: positionSide === 'long' }"
            @click="positionSide = 'long'"
          >
            <t-icon name="arrow-up" /> 开多
          </div>
          <div 
            class="position-tab" 
            :class="{ active: positionSide === 'short', short: positionSide === 'short' }"
            @click="positionSide = 'short'"
          >
            <t-icon name="arrow-down" /> 开空
          </div>
        </div>
        
        <!-- 订单类型 -->
        <t-tabs v-model="orderType">
          <t-tab-panel value="limit" label="限价" />
          <t-tab-panel value="market" label="市价" />
          <t-tab-panel value="stop" label="计划委托" />
        </t-tabs>
        
        <!-- 订单输入 -->
        <div class="order-inputs">
          <div class="input-group" v-if="orderType !== 'market'">
            <label>价格</label>
            <t-input-number
              v-model="orderPrice"
              :decimal-places="2"
              theme="column"
              placeholder="输入价格"
            >
              <template #suffix>USDT</template>
            </t-input-number>
          </div>
          
          <div class="input-group">
            <label>数量</label>
            <t-input-number
              v-model="orderAmount"
              :decimal-places="4"
              theme="column"
              placeholder="输入数量"
            >
              <template #suffix>{{ currentPair.symbol.split('/')[0] }}</template>
            </t-input-number>
          </div>
          
          <!-- 快捷选择 -->
          <div class="quick-amount">
            <t-button size="small" variant="outline" @click="setAmountPercent(25)">25%</t-button>
            <t-button size="small" variant="outline" @click="setAmountPercent(50)">50%</t-button>
            <t-button size="small" variant="outline" @click="setAmountPercent(75)">75%</t-button>
            <t-button size="small" variant="outline" @click="setAmountPercent(100)">100%</t-button>
          </div>
          
          <!-- 订单信息 -->
          <div class="order-info">
            <div class="info-row">
              <span>可用保证金</span>
              <span>{{ formatPrice(availableMargin) }} USDT</span>
            </div>
            <div class="info-row">
              <span>开仓成本</span>
              <span>{{ formatPrice(positionCost) }} USDT</span>
            </div>
            <div class="info-row" v-if="orderType !== 'market'">
              <span>预估强平价</span>
              <span :class="positionSide === 'long' ? 'text-danger' : 'text-success'">
                {{ formatPrice(liquidationPrice) }} USDT
              </span>
            </div>
          </div>
          
          <!-- 止盈止损 -->
          <t-collapse>
            <t-collapse-panel header="止盈止损" value="tp-sl">
              <div class="tp-sl-inputs">
                <div class="input-group">
                  <label>止盈价格</label>
                  <t-input-number
                    v-model="takeProfitPrice"
                    :decimal-places="2"
                    theme="column"
                    placeholder="止盈价格"
                  />
                </div>
                <div class="input-group">
                  <label>止损价格</label>
                  <t-input-number
                    v-model="stopLossPrice"
                    :decimal-places="2"
                    theme="column"
                    placeholder="止损价格"
                  />
                </div>
              </div>
            </t-collapse-panel>
          </t-collapse>
          
          <!-- 提交按钮 -->
          <t-button
            :theme="positionSide === 'long' ? 'success' : 'danger'"
            block
            @click="submitOrder"
          >
            {{ positionSide === 'long' ? '开多' : '开空' }} {{ currentPair.symbol.split('/')[0] }}
          </t-button>
        </div>
      </div>
    </div>
    
    <!-- 持仓和订单区域 -->
    <div class="positions-section">
      <t-tabs v-model="bottomTab">
        <t-tab-panel value="positions" label="当前持仓">
          <t-table
            :data="positions"
            :columns="positionColumns"
            row-key="id"
            stripe
            hover
          >
            <template #side="{ row }">
              <t-tag :theme="row.side === 'long' ? 'success' : 'danger'" variant="light">
                {{ row.side === 'long' ? '多' : '空' }} {{ row.leverage }}x
              </t-tag>
            </template>
            <template #pnl="{ row }">
              <span :class="row.pnl >= 0 ? 'text-success' : 'text-danger'">
                {{ row.pnl >= 0 ? '+' : '' }}{{ formatPrice(row.pnl) }} USDT
                <small>({{ row.pnlPercent >= 0 ? '+' : '' }}{{ row.pnlPercent.toFixed(2) }}%)</small>
              </span>
            </template>
            <template #operation="{ row }">
              <t-button size="small" theme="warning" variant="text" @click="closePosition(row)">
                平仓
              </t-button>
              <t-button size="small" variant="text" @click="editTpSl(row)">
                止盈止损
              </t-button>
            </template>
          </t-table>
        </t-tab-panel>
        
        <t-tab-panel value="orders" label="当前委托">
          <t-table
            :data="openOrders"
            :columns="orderColumns"
            row-key="id"
            stripe
            hover
          >
            <template #side="{ row }">
              <t-tag :theme="row.side === 'buy' ? 'success' : 'danger'" variant="light">
                {{ row.side === 'buy' ? '买入' : '卖出' }}
              </t-tag>
            </template>
            <template #operation="{ row }">
              <t-button size="small" theme="danger" variant="text" @click="cancelOrder(row)">
                撤单
              </t-button>
            </template>
          </t-table>
        </t-tab-panel>
        
        <t-tab-panel value="history" label="历史成交" />
        <t-tab-panel value="pnl" label="盈亏记录" />
      </t-tabs>
    </div>
    
    <!-- 杠杆调整弹窗 -->
    <t-dialog
      v-model:visible="showLeverageModal"
      header="调整杠杆"
      :confirm-on-enter="true"
      @confirm="confirmLeverage"
    >
      <div class="leverage-modal">
        <div class="leverage-input">
          <t-input-number
            v-model="tempLeverage"
            :min="1"
            :max="125"
            theme="column"
          />
          <span class="leverage-unit">x</span>
        </div>
        <t-slider
          v-model="tempLeverage"
          :min="1"
          :max="125"
          :step="1"
        />
        <div class="leverage-presets">
          <t-button v-for="l in [5, 10, 20, 50, 100, 125]" :key="l" variant="outline" size="small" @click="tempLeverage = l">
            {{ l }}x
          </t-button>
        </div>
        <t-alert theme="warning">
          <p>高杠杆交易存在较大风险，请谨慎操作。杠杆越高，强平价格越接近开仓价。</p>
        </t-alert>
      </div>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { createChart } from 'lightweight-charts'
import { MessagePlugin } from 'tdesign-vue-next'

// 状态
const timeframe = ref('1h')
const chartType = ref('candle')
const orderType = ref('limit')
const positionSide = ref('long')
const marginMode = ref('cross')
const leverage = ref(10)
const tempLeverage = ref(10)
const orderPrice = ref(45000)
const orderAmount = ref(0.01)
const takeProfitPrice = ref(null)
const stopLossPrice = ref(null)
const priceDirection = ref('up')
const bottomTab = ref('positions')
const showLeverageModal = ref(false)
const chartContainerRef = ref(null)
let chart = null
let candleSeries = null

// 活跃指标
const activeIndicators = ref(['MA', 'BOLL'])

// 当前交易对
const currentPair = ref({
  symbol: 'BTC/USDT',
  price: 45123.45,
  markPrice: 45120.00,
  indexPrice: 45125.00,
  change: 2.35,
  fundingRate: 0.0100,
  volume24h: 3254789012,
  openInterest: 125678
})

// 交易对选项
const pairOptions = [
  { content: 'BTC/USDT 永续', value: 'BTC/USDT' },
  { content: 'ETH/USDT 永续', value: 'ETH/USDT' },
  { content: 'BNB/USDT 永续', value: 'BNB/USDT' },
  { content: 'SOL/USDT 永续', value: 'SOL/USDT' }
]

// 指标选项
const indicatorOptions = [
  { content: 'MA 均线', value: 'MA' },
  { content: 'EMA 指数均线', value: 'EMA' },
  { content: 'BOLL 布林带', value: 'BOLL' },
  { content: 'RSI', value: 'RSI' },
  { content: 'MACD', value: 'MACD' }
]

// 可用保证金
const availableMargin = ref(50000)

// 计算开仓成本
const positionCost = computed(() => {
  return (orderPrice.value * orderAmount.value) / leverage.value
})

// 计算预估强平价
const liquidationPrice = computed(() => {
  const entry = orderPrice.value
  const margin = positionCost.value
  const size = orderAmount.value
  const maintenanceMargin = 0.005 // 维持保证金率
  
  if (positionSide.value === 'long') {
    return entry - (margin - size * entry * maintenanceMargin) / size
  } else {
    return entry + (margin - size * entry * maintenanceMargin) / size
  }
})

// 持仓数据
const positions = ref([
  {
    id: 1,
    symbol: 'BTC/USDT',
    side: 'long',
    leverage: 10,
    size: 0.5,
    entryPrice: 44500,
    markPrice: 45123.45,
    margin: 2225,
    pnl: 311.73,
    pnlPercent: 14.01,
    liquidationPrice: 40050
  },
  {
    id: 2,
    symbol: 'ETH/USDT',
    side: 'short',
    leverage: 20,
    size: 5,
    entryPrice: 2450,
    markPrice: 2420,
    margin: 612.5,
    pnl: 150,
    pnlPercent: 24.49,
    liquidationPrice: 2575
  }
])

// 持仓表格列
const positionColumns = [
  { colKey: 'symbol', title: '合约', width: 120 },
  { colKey: 'side', title: '方向', width: 100 },
  { colKey: 'size', title: '持仓数量', width: 120 },
  { colKey: 'entryPrice', title: '开仓价格', width: 120 },
  { colKey: 'markPrice', title: '标记价格', width: 120 },
  { colKey: 'liquidationPrice', title: '强平价格', width: 120 },
  { colKey: 'margin', title: '保证金', width: 120 },
  { colKey: 'pnl', title: '未实现盈亏', width: 180 },
  { colKey: 'operation', title: '操作', width: 150, fixed: 'right' }
]

// 委托订单
const openOrders = ref([
  {
    id: 1,
    symbol: 'BTC/USDT',
    type: '限价',
    side: 'buy',
    price: 44000,
    amount: 0.1,
    filled: 0,
    time: '2024-01-15 14:30:25'
  }
])

// 订单表格列
const orderColumns = [
  { colKey: 'symbol', title: '合约', width: 120 },
  { colKey: 'type', title: '类型', width: 80 },
  { colKey: 'side', title: '方向', width: 80 },
  { colKey: 'price', title: '价格', width: 120 },
  { colKey: 'amount', title: '数量', width: 100 },
  { colKey: 'filled', title: '已成交', width: 100 },
  { colKey: 'time', title: '时间', width: 180 },
  { colKey: 'operation', title: '操作', width: 80, fixed: 'right' }
]

// 深度图配置
const depthChartOptions = {
  chart: {
    type: 'area',
    toolbar: { show: false },
    background: 'transparent'
  },
  theme: { mode: 'dark' },
  colors: ['#00A870', '#E34D59'],
  fill: {
    type: 'gradient',
    gradient: {
      opacityFrom: 0.7,
      opacityTo: 0.3
    }
  },
  stroke: { curve: 'stepline', width: 2 },
  xaxis: {
    type: 'numeric',
    labels: { style: { colors: '#666' } }
  },
  yaxis: {
    labels: { style: { colors: '#666' } }
  },
  tooltip: {
    theme: 'dark'
  },
  legend: { show: false }
}

const depthSeries = ref([
  {
    name: '买单',
    data: [
      [44000, 50], [44200, 80], [44400, 120], [44600, 180], [44800, 250], [45000, 350]
    ]
  },
  {
    name: '卖单',
    data: [
      [45000, 350], [45200, 280], [45400, 200], [45600, 150], [45800, 100], [46000, 60]
    ]
  }
])

// 方法
const changePair = (data) => {
  currentPair.value.symbol = data.value
}

const toggleIndicator = (data) => {
  const index = activeIndicators.value.indexOf(data.value)
  if (index > -1) {
    activeIndicators.value.splice(index, 1)
  } else {
    activeIndicators.value.push(data.value)
  }
}

const setAmountPercent = (percent) => {
  const maxAmount = (availableMargin.value * leverage.value) / orderPrice.value
  orderAmount.value = parseFloat((maxAmount * percent / 100).toFixed(4))
}

const submitOrder = () => {
  MessagePlugin.success(`${positionSide.value === 'long' ? '开多' : '开空'}委托已提交`)
}

const closePosition = (position) => {
  MessagePlugin.success(`${position.symbol} 平仓委托已提交`)
}

const cancelOrder = (order) => {
  const index = openOrders.value.findIndex(o => o.id === order.id)
  if (index > -1) {
    openOrders.value.splice(index, 1)
    MessagePlugin.success('委托已撤销')
  }
}

const editTpSl = (position) => {
  MessagePlugin.info('止盈止损设置')
}

const confirmLeverage = () => {
  leverage.value = tempLeverage.value
  showLeverageModal.value = false
  MessagePlugin.success(`杠杆已调整为 ${leverage.value}x`)
}

const formatPrice = (price) => {
  return price?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'
}

const formatNumber = (num) => {
  if (num >= 1000000000) {
    return (num / 1000000000).toFixed(2) + 'B'
  } else if (num >= 1000000) {
    return (num / 1000000).toFixed(2) + 'M'
  }
  return num?.toLocaleString('en-US') || '0'
}

// 初始化图表
const initChart = () => {
  if (!chartContainerRef.value) return
  
  chart = createChart(chartContainerRef.value, {
    width: chartContainerRef.value.clientWidth,
    height: 400,
    layout: {
      background: { color: '#0d1117' },
      textColor: 'rgba(255, 255, 255, 0.6)'
    },
    grid: {
      vertLines: { color: '#21262d' },
      horzLines: { color: '#21262d' }
    },
    crosshair: { mode: 1 },
    rightPriceScale: { borderColor: '#30363d' },
    timeScale: { borderColor: '#30363d', timeVisible: true }
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
    currentPair.value.price += change
    currentPair.value.markPrice = currentPair.value.price - 3 + Math.random() * 6
    currentPair.value.indexPrice = currentPair.value.price - 2 + Math.random() * 4
    priceDirection.value = change > 0 ? 'up' : 'down'
    
    // 更新持仓盈亏
    positions.value.forEach(pos => {
      if (pos.symbol === 'BTC/USDT') {
        pos.markPrice = currentPair.value.markPrice
        if (pos.side === 'long') {
          pos.pnl = (pos.markPrice - pos.entryPrice) * pos.size
        } else {
          pos.pnl = (pos.entryPrice - pos.markPrice) * pos.size
        }
        pos.pnlPercent = (pos.pnl / pos.margin) * 100
      }
    })
  }, 3000)
}

onMounted(() => {
  initChart()
  startPriceUpdate()
})

onUnmounted(() => {
  if (chart) chart.remove()
  window.removeEventListener('resize', handleResize)
  if (priceUpdateTimer) clearInterval(priceUpdateTimer)
})
</script>

<style lang="less" scoped>
.contract-page {
  background: #0d1117;
  min-height: calc(100vh - 56px);
}

.trade-type-tabs {
  padding: 12px 24px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  display: flex;
  gap: 8px;
}

.contract-header {
  padding: 16px 24px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
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
  
  &.up { color: var(--green); }
  &.down { color: var(--red); }
}

.contract-stats {
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

.text-success { color: var(--green) !important; }
.text-danger { color: var(--red) !important; }

.contract-main {
  display: grid;
  grid-template-columns: 1fr 400px;
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

.chart-container {
  height: 400px;
  background: #0d1117;
}

.depth-chart {
  height: 400px;
  padding: 16px;
}

.order-section {
  background: #161b22;
  padding: 16px;
}

.leverage-panel {
  margin-bottom: 16px;
  padding: 12px;
  background: #21262d;
  border-radius: 8px;
  
  .leverage-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .leverage-display {
    .leverage-value {
      font-size: 24px;
      font-weight: bold;
      color: var(--primary);
      display: block;
      text-align: center;
      margin-bottom: 12px;
    }
  }
}

.margin-mode {
  margin-bottom: 16px;
}

.position-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
  
  .position-tab {
    padding: 12px;
    text-align: center;
    border-radius: 6px;
    cursor: pointer;
    background: #21262d;
    color: rgba(255, 255, 255, 0.6);
    transition: all 0.2s;
    
    &.active.long {
      background: rgba(0, 168, 112, 0.2);
      color: var(--green);
      border: 1px solid var(--green);
    }
    
    &.active.short {
      background: rgba(227, 77, 89, 0.2);
      color: var(--red);
      border: 1px solid var(--red);
    }
    
    &:hover:not(.active) {
      background: #30363d;
    }
  }
}

.order-inputs {
  .input-group {
    margin-bottom: 12px;
    
    label {
      display: block;
      margin-bottom: 6px;
      color: rgba(255, 255, 255, 0.6);
      font-size: 13px;
    }
  }
  
  .quick-amount {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    
    .t-button {
      flex: 1;
    }
  }
  
  .order-info {
    padding: 12px;
    background: #21262d;
    border-radius: 6px;
    margin-bottom: 16px;
    
    .info-row {
      display: flex;
      justify-content: space-between;
      padding: 6px 0;
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
      
      &:not(:last-child) {
        border-bottom: 1px solid #30363d;
      }
    }
  }
}

.tp-sl-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  
  .input-group {
    margin-bottom: 0;
  }
}

.positions-section {
  background: #161b22;
  border-top: 1px solid #30363d;
  padding: 16px 24px;
}

.leverage-modal {
  .leverage-input {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-bottom: 24px;
    
    .leverage-unit {
      font-size: 24px;
      color: rgba(255, 255, 255, 0.6);
    }
  }
  
  .leverage-presets {
    display: flex;
    gap: 8px;
    margin: 16px 0;
    
    .t-button {
      flex: 1;
    }
  }
}
</style>
