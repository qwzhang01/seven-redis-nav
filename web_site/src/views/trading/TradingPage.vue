<template>
  <div class="h-full flex flex-col bg-dark-900 min-h-screen">
    <!-- 顶部价格信息栏 -->
    <div class="bg-dark-800 border-b border-white/[0.06] px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-6">
          <!-- 交易对选择 -->
          <div class="flex items-center gap-3">
            <div class="relative">
              <select 
                v-model="selectedSymbol"
                @change="onSymbolChange"
                class="appearance-none bg-dark-700 border border-white/[0.06] rounded-lg px-4 py-2 pr-8 text-white text-sm focus:outline-none focus:border-primary-500 transition-colors cursor-pointer"
              >
                <option
                  v-for="symbol in availableSymbols" 
                  :key="symbol.value"
                  :value="symbol.value"
                >
                  {{ symbol.value }}
                </option>
              </select>
              <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-dark-100">
                <svg class="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                  <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/>
                </svg>
              </div>
            </div>
            
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
                <span
                    class="text-xs font-bold text-white">{{selectedSymbolInfo?selectedSymbolInfo.value.split('\/')[0] : "BTC"}}</span>
              </div>
              <div>
                <h1 class="text-xl font-bold text-white">{{selectedSymbolInfo?selectedSymbolInfo.value : "BTC/USDT"}}</h1>
                <p class="text-xs text-dark-100">$87987</p>
              </div>
            </div>
          </div>
          
          <div class="flex items-center gap-8">
            <div>
              <div class="text-2xl font-bold text-white">${{ currentPrice }}</div>
              <div class="flex items-center gap-2 mt-1">
                <span :class="priceChange.startsWith('+') ? 'text-green-400' : 'text-red-400'" class="text-sm font-medium">{{ priceChange }}</span>
                <span class="text-dark-100 text-xs">{{ priceChange }}</span>
              </div>
            </div>
            
            <div class="grid grid-cols-4 gap-6 text-sm">
              <div>
                <span class="text-dark-100">24H最高</span>
                <div class="text-white font-medium">${{ high24h }}</div>
              </div>
              <div>
                <span class="text-dark-100">24H最低</span>
                <div class="text-white font-medium">${{ low24h }}</div>
              </div>
              <div>
                <span class="text-dark-100">24H成交量</span>
                <div class="text-white font-medium">{{ volume24h }}</div>
              </div>
              <div>
                <span class="text-dark-100">更新时间</span>
                <div class="text-white font-medium">{{ currentTime }}</div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 text-green-400">
            <div class="w-2 h-2 bg-green-400 rounded-full"></div>
            <span class="text-sm">WebSocket已连接</span>
            <span class="text-dark-100 text-xs">延迟12ms</span>
          </div>
          <div class="text-dark-100 text-sm">版本 1.0.0</div>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="flex-1 grid grid-cols-1 xl:grid-cols-4 gap-4 p-4">
      <!-- 左侧：图表区域（在大屏幕上占3/4宽度） -->
      <div class="xl:col-span-3 space-y-4">
        <!-- 图表控制栏 -->
        <div class="bg-dark-800 rounded-lg border border-white/[0.06] p-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div class="flex gap-1">
                <button 
                  v-for="chartType in ['蜡烛图', '折线图', '面积图']" 
                  :key="chartType"
                  class="px-3 py-1 text-sm rounded transition-colors"
                  :class="activeChartType === chartType 
                    ? 'bg-primary-500 text-white' 
                    : 'bg-dark-700 text-dark-100 hover:text-white'"
                >
                  {{ chartType }}
                </button>
              </div>
              
              <div class="flex gap-1">
                <button 
                  v-for="period in timePeriods" 
                  :key="period"
                  @click="changeTimePeriod(period)"
                  class="px-3 py-1 text-sm rounded transition-colors"
                  :class="selectedPeriod === period 
                    ? 'bg-primary-500 text-white' 
                    : 'bg-dark-700 text-dark-100 hover:text-white'"
                >
                  {{ period }}
                </button>
              </div>
              
              <div class="flex items-center gap-2 text-sm text-dark-100">
                <span>指标：</span>
                <select v-model="selectedIndicator" class="bg-dark-700 border border-white/[0.06] rounded px-2 py-1 text-white">
                  <option value="">无指标</option>
                  <option value="MA">MA(10,20)</option>
                  <option value="EMA">EMA(12,26)</option>
                  <option value="BOLL">BOLL</option>
                  <option value="MACD">MACD</option>
                </select>
              </div>
            </div>
            
            <div class="flex items-center gap-3">
              <button class="px-3 py-1 bg-dark-700 text-dark-100 hover:text-white rounded text-sm transition-colors">
                全屏
              </button>
              <button class="px-3 py-1 bg-dark-700 text-dark-100 hover:text-white rounded text-sm transition-colors">
                截图
              </button>
            </div>
          </div>
        </div>

        <!-- K线图表区域 -->
        <div class="bg-dark-800 rounded-lg border border-white/[0.06] min-h-[500px]">
          <TradingChart
            ref="tradingChartRef"
            :kline-data="klineData"
            :indicators="indicators"
            :trade-marks="tradeMarks"
            :height="520"
            :show-volume="true"
            @load-more="loadMoreKlineData"
            @time-range-change="handleTimeRangeChange"
          />
        </div>

        <!-- 深度图和成交量 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-dark-800 rounded-lg border border-white/[0.06] p-4">
            <h3 class="text-sm font-semibold text-white mb-3">深度图</h3>
            <div class="h-32 bg-dark-700/50 rounded flex items-center justify-center">
              <span class="text-dark-100 text-sm">深度图表区域</span>
            </div>
          </div>
          <div class="bg-dark-800 rounded-lg border border-white/[0.06] p-4">
            <h3 class="text-sm font-semibold text-white mb-3">成交量</h3>
            <div class="h-32 bg-dark-700/50 rounded flex items-center justify-center">
              <span class="text-dark-100 text-sm">成交量图表区域</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：交易面板（在大屏幕上占1/4宽度） -->
      <div class="xl:col-span-1 space-y-4">
        <!-- 交易操作面板 -->
        <div class="bg-dark-800 rounded-lg border border-white/[0.06] p-4">
          <div class="flex border-b border-white/[0.06] mb-4">
            <button 
              v-for="tab in tradeTabs" 
              :key="tab"
              @click="activeTradeTab = tab"
              class="flex-1 py-3 text-center font-medium transition-colors"
              :class="activeTradeTab === tab 
                ? 'text-primary-500 border-b-2 border-primary-500' 
                : 'text-dark-100 hover:text-white'"
            >
              {{ tab }}
            </button>
          </div>
          
          <!-- 杠杆选择 -->
          <div class="mb-4">
            <label class="text-sm text-dark-100 mb-2 block">杠杆倍数</label>
            <div class="grid grid-cols-4 gap-2">
              <button 
                v-for="leverage in [1, 5, 10, 20]" 
                :key="leverage"
                @click="selectedLeverage = leverage"
                class="py-2 text-xs rounded transition-colors"
                :class="selectedLeverage === leverage 
                  ? 'bg-primary-500 text-white' 
                  : 'bg-dark-700 text-dark-100 hover:text-white'"
              >
                {{ leverage }}x
              </button>
            </div>
          </div>
          
          <!-- 交易表单 -->
          <div class="space-y-3">
            <div>
              <label class="text-sm text-dark-100 mb-2 block">价格 (USDT)</label>
              <input 
                v-model="tradePrice"
                type="number" 
                class="w-full bg-dark-700 border border-white/[0.06] rounded-lg px-3 py-2 text-white placeholder-dark-300 focus:outline-none focus:border-primary-500 transition-colors text-sm"
                placeholder="输入价格"
              />
            </div>
            <div>
              <label class="text-sm text-dark-100 mb-2 block">数量 (BTC)</label>
              <input 
                v-model="tradeAmount"
                type="number" 
                class="w-full bg-dark-700 border border-white/[0.06] rounded-lg px-3 py-2 text-white placeholder-dark-300 focus:outline-none focus:border-primary-500 transition-colors text-sm"
                placeholder="输入数量"
              />
            </div>
            <div class="grid grid-cols-4 gap-1">
              <button 
                v-for="percent in [25, 50, 75, 100]" 
                :key="percent"
                @click="setTradeAmount(percent)"
                class="py-1 text-xs bg-dark-700 text-dark-100 hover:text-white rounded transition-colors"
              >
                {{ percent }}%
              </button>
            </div>
            
            <!-- 账户信息 -->
            <div class="bg-dark-700/50 rounded p-3 space-y-2 text-xs">
              <div class="flex justify-between">
                <span class="text-dark-100">可用余额</span>
                <span class="text-white">{{ accountBalance }} USDT</span>
              </div>
              <div class="flex justify-between">
                <span class="text-dark-100">所需保证金</span>
                <span class="text-white">{{ (parseFloat(tradePrice.replace(/,/g, '')) * parseFloat(tradeAmount) / selectedLeverage).toFixed(2) }} USDT</span>
              </div>
              <div class="flex justify-between">
                <span class="text-dark-100">手续费(预估)</span>
                <span class="text-white">{{ (parseFloat(tradePrice.replace(/,/g, '')) * parseFloat(tradeAmount) * 0.0004).toFixed(2) }} USDT</span>
              </div>
              <div class="flex justify-between">
                <span class="text-dark-100">预估强平价</span>
                <span class="text-white">{{ (parseFloat(tradePrice.replace(/,/g, '')) * 0.95).toFixed(2) }} USDT</span>
              </div>
            </div>
            
            <button 
              @click="placeOrder"
              class="w-full py-3 rounded-lg font-medium transition-colors text-sm"
              :class="activeTradeTab === '买入' 
                ? 'bg-green-500 hover:bg-green-600 text-white' 
                : 'bg-red-500 hover:bg-red-600 text-white'"
            >
              {{ activeTradeTab }} {{ selectedSymbolInfo?.value || 'BTC' }}
            </button>
          </div>
        </div>

        <!-- 止盈止损设置 -->
        <div class="bg-dark-800 rounded-lg border border-white/[0.06] p-4">
          <h3 class="text-sm font-semibold text-white mb-3">止盈止损</h3>
          <div class="space-y-3">
            <div>
              <label class="text-sm text-dark-100 mb-2 block">止盈价格</label>
              <input 
                v-model="takeProfitPrice"
                type="number" 
                class="w-full bg-dark-700 border border-white/[0.06] rounded-lg px-3 py-2 text-white placeholder-dark-300 focus:outline-none focus:border-primary-500 transition-colors text-sm"
                placeholder="输入止盈价格"
              />
            </div>
            <div>
              <label class="text-sm text-dark-100 mb-2 block">止损价格</label>
              <input 
                v-model="stopLossPrice"
                type="number" 
                class="w-full bg-dark-700 border border-white/[0.06] rounded-lg px-3 py-2 text-white placeholder-dark-300 focus:outline-none focus:border-primary-500 transition-colors text-sm"
                placeholder="输入止损价格"
              />
            </div>
            <button class="w-full py-2 bg-dark-700 text-dark-100 hover:text-white rounded text-sm transition-colors">
              设置止盈止损
            </button>
          </div>
        </div>

        <!-- 当前委托 -->
        <div class="bg-dark-800 rounded-lg border border-white/[0.06] p-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold text-white">当前委托</h3>
            <button @click="cancelAllOrders" class="text-xs text-red-400 hover:text-red-300 transition-colors">
              一键撤单
            </button>
          </div>
          
          <div class="space-y-2 max-h-40 overflow-y-auto">
            <div 
              v-for="order in currentOrders" 
              :key="order.id"
              class="flex items-center justify-between p-2 bg-dark-700/30 rounded text-xs hover:bg-dark-700/50 transition-colors"
            >
              <div class="flex items-center gap-2">
                <div 
                  class="w-2 h-2 rounded-full" 
                  :class="order.type === '买入' ? 'bg-green-500' : 'bg-red-500'"
                ></div>
                <div>
                  <div class="text-white font-medium">{{ order.pair }}</div>
                  <div class="text-dark-100">{{ order.type }}</div>
                </div>
              </div>
              <div class="text-right">
                <div class="text-white font-medium">${{ order.price }}</div>
                <div class="text-dark-100">{{ order.amount }}</div>
              </div>
              <button 
                @click="cancelOrder(order.id)"
                class="text-red-400 hover:text-red-300 transition-colors"
              >
                <X :size="12" />
              </button>
            </div>
            
            <div v-if="currentOrders.length === 0" class="text-center py-4">
              <Clock :size="16" class="text-dark-200 mx-auto mb-1" />
              <p class="text-dark-100 text-xs">暂无委托订单</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部：历史订单表格 -->
    <div class="bg-dark-800 border-t border-white/[0.06] mt-4">
      <div class="p-4">
        <h3 class="text-sm font-semibold text-white mb-3">历史订单</h3>
        
        <div class="overflow-x-auto">
          <table class="w-full text-xs">
            <thead class="bg-dark-700/50">
              <tr>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">时间</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">交易对</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">方向</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">类型</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">价格</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">数量</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">已成交</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">状态</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/[0.06]">
              <tr v-for="order in historyOrders" :key="order.id" class="hover:bg-dark-700/30 transition-colors">
                <td class="px-3 py-2 text-white">{{ order.time }}</td>
                <td class="px-3 py-2 text-white">{{ order.pair }}</td>
                <td class="px-3 py-2">
                  <span :class="order.direction === '买入' ? 'text-green-400' : 'text-red-400'">{{ order.direction }}</span>
                </td>
                <td class="px-3 py-2 text-white">{{ order.type }}</td>
                <td class="px-3 py-2 text-white">${{ order.price }}</td>
                <td class="px-3 py-2 text-white">{{ order.amount }}</td>
                <td class="px-3 py-2 text-white">{{ order.filled || 0 }}</td>
                <td class="px-3 py-2">
                  <span :class="getStatusColor(order.status)">{{ order.status }}</span>
                </td>
              </tr>
            </tbody>
          </table>
          
          <div v-if="historyOrders.length === 0" class="text-center py-6">
            <FileText :size="20" class="text-dark-200 mx-auto mb-2" />
            <p class="text-dark-100 text-sm">暂无历史订单记录</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { TrendingUp, Clock, X, FileText } from 'lucide-vue-next'
import { MessagePlugin } from 'tdesign-vue-next'
import marketApi from '@/utils/marketApi'
import tradingApi from '@/utils/tradingApi'
import websocketApi from '@/utils/websocketApi'
import TradingChart from '@/components/charts/TradingChart.vue'
import DepthChart from '@/components/charts/DepthChart.vue'
import {KlineDataPoint, IndicatorData, TradeMarkData, EnumItem} from '@/types'

// TradingChart组件引用
const tradingChartRef = ref<InstanceType<typeof TradingChart>>()

// K线数据相关
const klineData = ref<KlineDataPoint[]>([])
const indicators = ref<IndicatorData[]>([])
const tradeMarks = ref<TradeMarkData[]>([])
const selectedPeriod = ref('1H')
const selectedIndicator = ref('')
const activeChartType = ref('蜡烛图')

// 时间周期选项
const timePeriods = ['1m', '5m', '15m', '1H', '4H', '1D', '1W', '1M']

// 响应式数据
const currentTime = ref('')
const activeTradeTab = ref('买入')
const selectedLeverage = ref(1)
const tradePrice = ref('91476')
const tradeAmount = ref('0.1')
const takeProfitPrice = ref('')
const stopLossPrice = ref('')
const loading = ref(false)

// 市场数据
const currentPrice = ref('91,476.14')
const priceChange = ref('+1.24%')
const high24h = ref('92,800.00')
const low24h = ref('89,200.00')
const volume24h = ref('12,345 BTC')

// 账户信息
const accountBalance = ref('10,000')
const accountInfo = ref<any>(null)

// 交易选项卡
const tradeTabs = ['买入', '卖出']

// 当前委托
const currentOrders = ref<any[]>([])

// 历史订单
const historyOrders = ref<any[]>([])

// WebSocket连接管理器
let wsManager: any = null

// 交易对相关
const selectedSymbol = ref<string>("")
const availableSymbols = ref<EnumItem[]>([])
const selectedSymbolInfo = ref<EnumItem>()

// 深度图数据
const depthData = ref({
  bids: [],
  asks: []
})

// 成交量数据
const volumeData = ref([])

// 深度图组件引用
const depthChartRef = ref<InstanceType<typeof DepthChart>>()

// ==================== K线数据相关方法 ====================
/**
 * 加载K线数据
 */
async function loadKlineData() {
  try {
    if(!selectedSymbol || !selectedSymbol.value){
      return
    }
    const rawData = await marketApi.getKlines({
      symbol: selectedSymbol.value,
      interval: selectedPeriod.value.toLowerCase() as any,
      limit: 1000
    })
    
    if (rawData && rawData.length > 0) {
      const mapped = rawData.map((item: any) => ({
        time: item.time ?? Math.floor((item.timestamp || 0) / 1000),
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
        volume: item.volume || 0,
      }))
      // 按时间升序排序，并去除重复时间戳（lightweight-charts 要求时间严格递增）
      mapped.sort((a, b) => a.time - b.time)
      const deduplicated: typeof mapped = []
      for (const item of mapped) {
        if (deduplicated.length === 0 || item.time > deduplicated[deduplicated.length - 1].time) {
          deduplicated.push(item)
        }
      }
      klineData.value = deduplicated
    }
  } catch (error) {
    console.error('加载K线数据失败:', error)
    MessagePlugin.error('加载K线数据失败')
  }
}

/**
 * 加载更多历史K线数据
 */
async function loadMoreKlineData(endTime: number) {
  try {
    const rawData = await marketApi.getKlines({
      symbol: selectedSymbol.value,
      interval: selectedPeriod.value.toLowerCase() as any,
      limit: 500,
      end_time: endTime * 1000
    })
    
    if (rawData && rawData.length > 0) {
      const mapped = rawData.map((item: any) => ({
        time: item.time ?? Math.floor((item.timestamp || 0) / 1000),
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
        volume: item.volume || 0,
      }))
      // 按时间升序排序，并去除重复时间戳（lightweight-charts 要求时间严格递增）
      mapped.sort((a, b) => a.time - b.time)
      const deduplicated: typeof mapped = []
      for (const item of mapped) {
        if (deduplicated.length === 0 || item.time > deduplicated[deduplicated.length - 1].time) {
          deduplicated.push(item)
        }
      }
      klineData.value = Array.from(deduplicated.values()).sort((a, b) => a.time - b.time)
    }
  } catch (error) {
    console.error('加载更多K线数据失败:', error)
  }
}

/**
 * 切换时间周期
 */
async function changeTimePeriod(period: string) {
  selectedPeriod.value = period
  await loadKlineData()
  changeWebSocketSubscription()
}

/**
 * 处理时间范围变化
 */
function handleTimeRangeChange(from: number, to: number) {
  console.log('时间范围变化:', new Date(from * 1000), new Date(to * 1000))
}

// ==================== WebSocket实时数据 ====================

/**
 * 初始化WebSocket连接
 */
function initWebSocket() {
  try {
    wsManager = websocketApi.createMarketWebSocket({
      onOpen: () => {
        console.log('WebSocket连接已建立')
        subscribeToChannels()
      },
      onMessage: handleWebSocketMessage,
      onError: (error) => {
        console.error('WebSocket错误:', error)
      },
      onClose: (event) => {
        console.log('WebSocket连接已关闭:', event.code, event.reason)
      },
      reconnect: true,
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000
    })
    
    wsManager.connect()
  } catch (error) {
    console.error('初始化WebSocket失败:', error)
  }
}

/**
 * 订阅频道
 */
function subscribeToChannels() {
  if (wsManager && wsManager.isConnected) {
    wsManager.subscribe([`kline/${selectedSymbol.value}/${selectedPeriod.value}`])
  }
}

/**
 * 切换WebSocket订阅频道
 */
function changeWebSocketSubscription() {
  if (wsManager && wsManager.isConnected) {
    wsManager.subscribe([`kline/${selectedSymbol.value}/${selectedPeriod.value}`])
  }
}

/**
 * 处理WebSocket消息
 */
function handleWebSocketMessage(data: any) {
  if (data.type === 'kline' && data.symbol === selectedSymbol.value) {
    const klinePoint: KlineDataPoint = {
      time: Math.floor(new Date(data.timestamp).getTime() / 1000),
      open: data.open,
      high: data.high,
      low: data.low,
      close: data.close,
      volume: data.volume
    }
    
    if (tradingChartRef.value) {
      tradingChartRef.value.appendKline(klinePoint)
    }
    
    currentPrice.value = data.close.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })
    
  } else if (data.type === 'ticker' && data.symbol === selectedSymbol.value) {
    currentPrice.value = data.last_price.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })
    priceChange.value = `${data.price_change_percent >= 0 ? '+' : ''}${data.price_change_percent.toFixed(2)}%`
  }
}

// ==================== 交易对相关方法 ====================

/**
 * 加载可用的交易对列表
 */
async function loadAvailableSymbols() {
  try {
    const response = await marketApi.getSymbols()
    
    if (response.items && response.items.length > 0) {
      availableSymbols.value = response.items

      selectedSymbol.value = response.items[0].value
      selectedSymbolInfo.value = response.items[0]
    }
  } catch (error) {
    console.error('加载交易对列表失败:', error)
    MessagePlugin.error('加载交易对列表失败')
  }
}

/**
 * 处理交易对变更
 */
async function onSymbolChange() {
  if (!selectedSymbol.value) return
  
  // 更新选中的交易对信息
  const symbolInfo = availableSymbols.value.find(s => s.value ===
      selectedSymbol.value)
  if (symbolInfo) {
    selectedSymbolInfo.value = symbolInfo
    
    // 重新加载所有数据
    await Promise.all([
      loadMarketData(),
      loadKlineData(),
      loadOrders(),
      loadHistoryOrders()
    ])
    
    // 更新WebSocket订阅
    changeWebSocketSubscription()
  }
}

// ==================== 现有方法 ====================

/**
 * 加载账户信息
 */
async function loadAccountInfo() {
  try {
    const account = await tradingApi.getAccount()
    accountInfo.value = account
    accountBalance.value = account.total_balance.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })
  } catch (error) {
    console.error('加载账户信息失败:', error)
  }
}

/**
 * 加载订单列表
 */
async function loadOrders() {
  try {
    const response = await tradingApi.getOrders({
      symbol: selectedSymbol.value,
      status: 'active',
      limit: 20
    })
    currentOrders.value = response.orders.map((order: any) => ({
      id: order.order_id,
      pair: order.symbol,
      type: order.side === 'buy' ? '买入' : '卖出',
      price: order.price.toLocaleString('en-US'),
      amount: `${order.quantity} ${selectedSymbolInfo.value?.value || 'BTC'}`,
      time: new Date(order.created_at).toLocaleTimeString('zh-CN', { hour12: false })
    }))
  } catch (error) {
    console.error('加载订单失败:', error)
  }
}

/**
 * 加载历史订单
 */
async function loadHistoryOrders() {
  try {
    const response = await tradingApi.getOrders({
      symbol: selectedSymbol.value,
      limit: 20
    })
    historyOrders.value = response.orders.map((order: any) => ({
      id: order.order_id,
      time: new Date(order.created_at).toLocaleTimeString('zh-CN', { hour12: false }),
      pair: order.symbol,
      direction: order.side === 'buy' ? '买入' : '卖出',
      type: order.type === 'limit' ? '限价单' : '市价单',
      price: order.price.toLocaleString('en-US'),
      amount: `${order.quantity} ${selectedSymbolInfo.value || 'BTC'}`,
      filled: order.filled_quantity || 0,
      status: order.status === 'filled' ? '已完成' : order.status === 'partially_filled' ? '部分成交' : order.status === 'open' ? '待成交' : '已撤销'
    }))
  } catch (error) {
    console.error('加载历史订单失败:', error)
  }
}

/**
 * 加载市场行情
 */
async function loadMarketData() {
  try {
    if(!selectedSymbol || !selectedSymbol.value){
      return
    }
    const ticker = await marketApi.getTicker({
      exchange_id: 'binance',
      symbol: selectedSymbol.value
    })
    currentPrice.value = ticker.last_price.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })
    priceChange.value = `${ticker.price_change_percent >= 0 ? '+' : ''}${ticker.price_change_percent.toFixed(2)}%`
    high24h.value = ticker.high_price.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })
    low24h.value = ticker.low_price.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })
    volume24h.value =
        `${ticker.volume.toLocaleString('en-US')} ${selectedSymbolInfo?selectedSymbolInfo.value : 'BTC'}`
    tradePrice.value = ticker.last_price.toFixed(2)
  } catch (error) {
    console.error('加载市场数据失败:', error)
  }
}

// 计算属性
const totalAmount = computed(() => {
  const price = parseFloat(tradePrice.value.replace(/,/g, '')) || 0
  const amount = parseFloat(tradeAmount.value) || 0
  return (price * amount).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
})

// 方法
function setTradeAmount(percent: number) {
  const maxAmount = 1.0
  tradeAmount.value = (maxAmount * (percent / 100)).toFixed(4)
}

async function placeOrder() {
  if (!tradePrice.value || !tradeAmount.value) {
    MessagePlugin.warning('请输入价格和数量')
    return
  }
  
  loading.value = true
  try {
    const order = await tradingApi.placeOrder({
      symbol: selectedSymbol.value,
      side: activeTradeTab.value === '买入' ? 'buy' : 'sell',
      order_type: 'limit',
      quantity: parseFloat(tradeAmount.value),
      price: parseFloat(tradePrice.value.replace(/,/g, ''))
    })
    
    MessagePlugin.success(`${activeTradeTab.value}订单已提交`)
    
    await loadOrders()
    await loadHistoryOrders()
    
    tradePrice.value = currentPrice.value
    tradeAmount.value = '0.1'
  } catch (error: any) {
    console.error('下单失败:', error)
    MessagePlugin.error(error.message || '下单失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function cancelOrder(orderId: string) {
  try {
    await tradingApi.cancelOrder(orderId)
    MessagePlugin.success('订单已撤销')
    await loadOrders()
    await loadHistoryOrders()
  } catch (error: any) {
    console.error('撤销订单失败:', error)
    MessagePlugin.error(error.message || '撤销订单失败')
  }
}

async function cancelAllOrders() {
  if (currentOrders.value.length === 0) {
    MessagePlugin.warning('没有可撤销的订单')
    return
  }
  
  try {
    await tradingApi.cancelAllOrders({
      symbol: selectedSymbol.value
    })
    MessagePlugin.success('所有订单已撤销')
    await loadOrders()
    await loadHistoryOrders()
  } catch (error: any) {
    console.error('撤销所有订单失败:', error)
    MessagePlugin.error(error.message || '撤销所有订单失败')
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case '已完成': return 'text-green-400'
    case '部分成交': return 'text-yellow-400'
    case '待成交': return 'text-blue-400'
    case '已撤销': return 'text-dark-100'
    default: return 'text-white'
  }
}

// 更新时间
function updateTime() {
  currentTime.value = new Date().toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 生命周期
onMounted(async () => {
  updateTime()
  const timer = setInterval(updateTime, 1000)
  
  // 加载初始数据
  await Promise.all([
    loadAvailableSymbols(),
    loadAccountInfo(),
    loadMarketData(),
    loadKlineData(),
    loadOrders(),
    loadHistoryOrders()
  ])
  
  // 初始化WebSocket
  initWebSocket()
  
  onUnmounted(() => {
    clearInterval(timer)
    if (wsManager) {
      wsManager.disconnect()
    }
  })
})

// 监听交易对变化
watch(() => selectedSymbol.value, (newSymbol, oldSymbol) => {
  if (newSymbol && newSymbol !== oldSymbol) {
    onSymbolChange()
  }
})

// 监听时间周期变化
watch(() => selectedPeriod.value, () => {
  changeWebSocketSubscription()
})
</script>

<style scoped>
/* 自定义滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 表格样式优化 */
table {
  border-collapse: separate;
  border-spacing: 0;
  width: 100%;
  min-width: 800px;
}

th, td {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  white-space: nowrap;
}

/* 输入框焦点样式 */
input:focus {
  box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
  outline: none;
}

/* 按钮悬停效果 */
button:hover {
  transform: translateY(-1px);
  transition: all 0.2s ease;
}

/* 卡片阴影效果 */
.bg-dark-800 {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* 响应式设计优化 - 确保布局不会重叠 */
@media (max-width: 1280px) {
  /* 在大屏幕以下时，切换为单列布局 */
  .grid.grid-cols-1.xl\:grid-cols-4 {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  
  /* 确保左侧图表区域占据完整宽度 */
  .xl\:col-span-3 {
    grid-column: span 1;
  }
  
  /* 确保右侧交易面板占据完整宽度 */
  .xl\:col-span-1 {
    grid-column: span 1;
  }
  
  /* 调整图表区域高度 */
  .min-h-\[500px\] {
    min-height: 400px;
  }
  
  /* 调整深度图和成交量布局 */
  .grid.grid-cols-1.md\:grid-cols-2 {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}

@media (max-width: 768px) {
  /* 在移动设备上进一步优化布局 */
  .p-4 {
    padding: 1rem;
  }
  
  .gap-4 {
    gap: 1rem;
  }
  
  .min-h-\[500px\] {
    min-height: 300px;
  }
  
  /* 调整顶部信息栏布局 */
  .flex.items-center.justify-between {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  /* 调整图表控制栏布局 */
  .flex.items-center.gap-4 {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  /* 调整交易面板布局 */
  .grid.grid-cols-4 {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  /* 确保表格在小屏幕上可以水平滚动 */
  .overflow-x-auto {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  
  table {
    min-width: 900px;
  }
}

@media (max-width: 480px) {
  /* 在超小屏幕上进一步优化 */
  .p-4 {
    padding: 0.75rem;
  }
  
  .gap-4 {
    gap: 0.75rem;
  }
  
  .min-h-\[500px\] {
    min-height: 250px;
  }
  
  /* 调整按钮大小 */
  .px-3.py-1 {
    padding-left: 0.5rem;
    padding-right: 0.5rem;
    padding-top: 0.25rem;
    padding-bottom: 0.25rem;
  }
  
  /* 调整输入框大小 */
  .px-3.py-2 {
    padding-left: 0.5rem;
    padding-right: 0.5rem;
    padding-top: 0.375rem;
    padding-bottom: 0.375rem;
  }
}

/* 动画效果 */
.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { 
    opacity: 0; 
    transform: translateY(10px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}

/* 确保布局容器正确堆叠 */
.flex-col {
  display: flex;
  flex-direction: column;
}

.grid {
  display: grid;
}

/* 防止内容溢出 */
.overflow-hidden {
  overflow: hidden;
}

.overflow-y-auto {
  overflow-y: auto;
}

/* 确保历史订单表格正确显示在底部 */
.mt-4 {
  margin-top: 1rem;
}

/* 主内容区域的最小高度控制 */
.min-h-screen {
  min-height: 100vh;
}

.flex-1 {
  flex: 1 1 0%;
}

/* 确保网格布局正确工作 */
.grid-cols-1 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.xl\:grid-cols-4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.xl\:col-span-3 {
  grid-column: span 3 / span 3;
}

.xl\:col-span-1 {
  grid-column: span 1 / span 1;
}
</style>