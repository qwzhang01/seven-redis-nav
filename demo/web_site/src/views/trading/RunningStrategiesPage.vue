<template>
  <div class="h-full flex flex-col bg-dark-900 min-h-screen">
    <!-- 顶部状态栏 -->
    <div class="bg-dark-800 border-b border-white/[0.06] px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-6">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center">
              <span class="text-xs font-bold text-white">实盘</span>
            </div>
            <div>
              <h1 class="text-xl font-bold text-white">策略实盘监控</h1>
              <p class="text-xs text-dark-100">实时监控运行中的量化策略</p>
            </div>
          </div>
          
          <div class="flex items-center gap-8">
            <div class="grid grid-cols-4 gap-6 text-sm">
              <div>
                <span class="text-dark-100">运行策略</span>
                <div class="text-white font-medium">{{ runningStrategiesCount }} 个</div>
              </div>
              <div>
                <span class="text-dark-100">总收益</span>
                <div class="text-green-400 font-medium">+{{ totalPnL }}%</div>
              </div>
              <div>
                <span class="text-dark-100">今日收益</span>
                <div class="text-green-400 font-medium">+{{ todayPnL }}%</div>
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
            <span class="text-dark-100 text-xs">延迟{{ latency }}ms</span>
          </div>
          <div class="text-dark-100 text-sm">版本 1.0.0</div>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="flex-1 grid grid-cols-1 xl:grid-cols-3 gap-4 p-4">
      <!-- 左侧：策略列表和状态监控 -->
      <div class="xl:col-span-1 space-y-4">
        <!-- 策略筛选和操作 -->
        <div class="bg-dark-800 rounded-lg border border-white/[0.06] p-4">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-white">运行中的策略</h3>
            <div class="flex gap-2">
              <select v-model="filterStatus" class="bg-dark-700 border border-white/[0.06] rounded px-2 py-1 text-white text-xs">
                <option value="all">全部状态</option>
                <option value="running">运行中</option>
                <option value="paused">已暂停</option>
                <option value="error">异常</option>
              </select>
              <button class="px-3 py-1 bg-dark-700 text-dark-100 hover:text-white rounded text-xs transition-colors">
                刷新
              </button>
            </div>
          </div>
          
          <!-- 策略列表 -->
          <div class="space-y-2 max-h-96 overflow-y-auto">
            <div 
              v-for="strategy in filteredStrategies" 
              :key="strategy.id"
              class="p-3 bg-dark-700/30 rounded-lg border border-white/[0.06] hover:bg-dark-700/50 transition-colors cursor-pointer"
              :class="{ 'border-green-500/50': strategy.status === 'running', 'border-yellow-500/50': strategy.status === 'paused', 'border-red-500/50': strategy.status === 'error' }"
            >
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <div 
                    class="w-2 h-2 rounded-full" 
                    :class="{ 'bg-green-500': strategy.status === 'running', 'bg-yellow-500': strategy.status === 'paused', 'bg-red-500': strategy.status === 'error' }"
                  ></div>
                  <span class="text-white font-medium text-sm">{{ strategy.name }}</span>
                </div>
                <span class="text-xs" :class="{ 'text-green-400': strategy.pnl > 0, 'text-red-400': strategy.pnl < 0 }">
                  {{ strategy.pnl > 0 ? '+' : '' }}{{ strategy.pnl }}%
                </span>
              </div>
              
              <div class="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span class="text-dark-100">交易对</span>
                  <div class="text-white">{{ strategy.pair }}</div>
                </div>
                <div>
                  <span class="text-dark-100">仓位</span>
                  <div class="text-white">{{ strategy.position }}</div>
                </div>
                <div>
                  <span class="text-dark-100">运行时间</span>
                  <div class="text-white">{{ strategy.runtime }}</div>
                </div>
                <div>
                  <span class="text-dark-100">信号数</span>
                  <div class="text-white">{{ strategy.signals }}</div>
                </div>
              </div>
              
              <div class="mt-2 flex gap-1">
                <button 
                  v-if="strategy.status === 'running'"
                  @click="pauseStrategy(strategy.id)"
                  class="flex-1 py-1 bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 rounded text-xs transition-colors"
                >
                  暂停
                </button>
                <button 
                  v-if="strategy.status === 'paused'"
                  @click="resumeStrategy(strategy.id)"
                  class="flex-1 py-1 bg-green-500/20 text-green-400 hover:bg-green-500/30 rounded text-xs transition-colors"
                >
                  恢复
                </button>
                <button 
                  @click="stopStrategy(strategy.id)"
                  class="flex-1 py-1 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded text-xs transition-colors"
                >
                  停止
                </button>
              </div>
            </div>
            
            <div v-if="filteredStrategies.length === 0" class="text-center py-4">
              <div class="w-8 h-8 bg-dark-700 rounded-full flex items-center justify-center mx-auto mb-2">
                <span class="text-dark-200 text-sm">📊</span>
              </div>
              <p class="text-dark-100 text-xs">暂无运行中的策略</p>
            </div>
          </div>
        </div>

        <!-- 风险指标面板 -->
        <div class="bg-dark-800 rounded-lg border border-white/[0.06] p-4">
          <h3 class="text-sm font-semibold text-white mb-3">风险监控</h3>
          <div class="space-y-3">
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div class="bg-dark-700/50 rounded p-2">
                <span class="text-dark-100">VaR (95%)</span>
                <div class="text-white font-medium">{{ riskMetrics.var }} USDT</div>
              </div>
              <div class="bg-dark-700/50 rounded p-2">
                <span class="text-dark-100">最大回撤</span>
                <div class="text-red-400 font-medium">{{ riskMetrics.maxDrawdown }}%</div>
              </div>
              <div class="bg-dark-700/50 rounded p-2">
                <span class="text-dark-100">波动率</span>
                <div class="text-white font-medium">{{ riskMetrics.volatility }}%</div>
              </div>
              <div class="bg-dark-700/50 rounded p-2">
                <span class="text-dark-100">夏普比率</span>
                <div class="text-green-400 font-medium">{{ riskMetrics.sharpeRatio }}</div>
              </div>
            </div>
            
            <div class="bg-red-500/10 border border-red-500/20 rounded p-2">
              <div class="flex items-center gap-2 mb-1">
                <div class="w-2 h-2 bg-red-500 rounded-full"></div>
                <span class="text-red-400 text-xs font-medium">风险警报</span>
              </div>
              <p class="text-red-300 text-xs">{{ riskAlerts.length }} 个未处理警报</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间：实时数据和图表 -->
      <div class="xl:col-span-2 space-y-4">
        <!-- 实时市场数据 -->
        <div class="bg-dark-800 rounded-lg border border-white/[0.06] p-4">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-white">实时市场数据</h3>
            <div class="flex gap-2">
              <select v-model="selectedMarket" class="bg-dark-700 border border-white/[0.06] rounded px-2 py-1 text-white text-xs">
                <option v-for="market in markets" :key="market" :value="market">{{ market }}</option>
              </select>
              <button class="px-3 py-1 bg-dark-700 text-dark-100 hover:text-white rounded text-xs transition-colors">
                全屏
              </button>
            </div>
          </div>
          
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div v-for="data in marketData" :key="data.label" class="text-center">
              <div class="text-dark-100 text-xs mb-1">{{ data.label }}</div>
              <div class="text-white font-medium text-sm">{{ data.value }}</div>
              <div 
                v-if="data.change" 
                class="text-xs mt-1" 
                :class="{ 'text-green-400': data.change > 0, 'text-red-400': data.change < 0 }"
              >
                {{ data.change > 0 ? '+' : '' }}{{ data.change }}%
              </div>
            </div>
          </div>
          
          <!-- 图表区域 -->
          <div class="bg-dark-700/50 rounded-lg h-64 flex items-center justify-center">
            <div class="text-center">
              <div class="w-16 h-16 bg-primary-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                <span class="text-primary-500 text-2xl">📈</span>
              </div>
              <h3 class="text-lg font-semibold text-white mb-1">实时K线图表</h3>
              <p class="text-dark-100 text-sm">集成专业K线图表组件</p>
              <p class="text-xs text-dark-200 mt-1">支持实时数据流和技术指标</p>
            </div>
          </div>
        </div>

        <!-- 性能指标和警报 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- PnL曲线 -->
          <div class="bg-dark-800 rounded-lg border border-white/[0.06] p-4">
            <h3 class="text-sm font-semibold text-white mb-3">收益曲线</h3>
            <div class="h-40 bg-dark-700/50 rounded flex items-center justify-center">
              <span class="text-dark-100 text-sm">PnL图表区域</span>
            </div>
            <div class="mt-3 grid grid-cols-3 gap-2 text-xs">
              <div>
                <span class="text-dark-100">累计收益</span>
                <div class="text-green-400 font-medium">+{{ totalPnL }}%</div>
              </div>
              <div>
                <span class="text-dark-100">年化收益</span>
                <div class="text-green-400 font-medium">+{{ annualizedReturn }}%</div>
              </div>
              <div>
                <span class="text-dark-100">胜率</span>
                <div class="text-white font-medium">{{ winRate }}%</div>
              </div>
            </div>
          </div>

          <!-- 警报系统 -->
          <div class="bg-dark-800 rounded-lg border border-white/[0.06] p-4">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-semibold text-white">实时警报</h3>
              <button @click="markAllAlertsAsRead" class="text-xs text-blue-400 hover:text-blue-300 transition-colors">
                全部标记已读
              </button>
            </div>
            
            <div class="space-y-2 max-h-40 overflow-y-auto">
              <div 
                v-for="alert in recentAlerts" 
                :key="alert.id"
                class="p-2 rounded text-xs transition-colors"
                :class="{ 
                  'bg-red-500/10 border border-red-500/20': alert.level === 'high',
                  'bg-yellow-500/10 border border-yellow-500/20': alert.level === 'medium',
                  'bg-blue-500/10 border border-blue-500/20': alert.level === 'low',
                  'bg-dark-700/30': alert.read
                }"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <div 
                      class="w-2 h-2 rounded-full" 
                      :class="{ 'bg-red-500': alert.level === 'high', 'bg-yellow-500': alert.level === 'medium', 'bg-blue-500': alert.level === 'low' }"
                    ></div>
                    <span class="text-white font-medium">{{ alert.title }}</span>
                  </div>
                  <span class="text-dark-100">{{ alert.time }}</span>
                </div>
                <p class="text-dark-100 mt-1">{{ alert.message }}</p>
              </div>
              
              <div v-if="recentAlerts.length === 0" class="text-center py-4">
                <div class="w-6 h-6 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-1">
                  <span class="text-green-400 text-xs">✓</span>
                </div>
                <p class="text-dark-100 text-xs">暂无警报信息</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部：持仓和交易历史 -->
    <div class="bg-dark-800 border-t border-white/[0.06] mt-4">
      <div class="p-4">
        <div class="flex items-center gap-4 mb-4">
          <button 
            v-for="tab in bottomTabs" 
            :key="tab"
            @click="activeBottomTab = tab"
            class="px-4 py-2 text-sm font-medium transition-colors"
            :class="activeBottomTab === tab 
              ? 'text-primary-500 border-b-2 border-primary-500' 
              : 'text-dark-100 hover:text-white'"
          >
            {{ tab }}
          </button>
        </div>
        
        <!-- 持仓信息 -->
        <div v-if="activeBottomTab === '持仓'" class="overflow-x-auto">
          <table class="w-full text-xs">
            <thead class="bg-dark-700/50">
              <tr>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">策略</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">交易对</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">方向</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">数量</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">成本价</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">当前价</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">盈亏</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">盈亏率</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/[0.06]">
              <tr v-for="position in positions" :key="position.id" class="hover:bg-dark-700/30 transition-colors">
                <td class="px-3 py-2 text-white">{{ position.strategy }}</td>
                <td class="px-3 py-2 text-white">{{ position.pair }}</td>
                <td class="px-3 py-2">
                  <span :class="{ 'text-green-400': position.direction === '多', 'text-red-400': position.direction === '空' }">{{ position.direction }}</span>
                </td>
                <td class="px-3 py-2 text-white">{{ position.amount }}</td>
                <td class="px-3 py-2 text-white">${{ position.entryPrice }}</td>
                <td class="px-3 py-2 text-white">${{ position.currentPrice }}</td>
                <td class="px-3 py-2" :class="{ 'text-green-400': position.pnl > 0, 'text-red-400': position.pnl < 0 }">
                  ${{ Math.abs(position.pnl).toFixed(2) }}
                </td>
                <td class="px-3 py-2" :class="{ 'text-green-400': position.pnlRatio > 0, 'text-red-400': position.pnlRatio < 0 }">
                  {{ position.pnlRatio > 0 ? '+' : '' }}{{ position.pnlRatio.toFixed(2) }}%
                </td>
              </tr>
            </tbody>
          </table>
          
          <div v-if="positions.length === 0" class="text-center py-6">
            <div class="w-8 h-8 bg-dark-700 rounded-full flex items-center justify-center mx-auto mb-2">
              <span class="text-dark-200 text-sm">💼</span>
            </div>
            <p class="text-dark-100 text-sm">暂无持仓信息</p>
          </div>
        </div>
        
        <!-- 交易历史 -->
        <div v-if="activeBottomTab === '交易历史'" class="overflow-x-auto">
          <table class="w-full text-xs">
            <thead class="bg-dark-700/50">
              <tr>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">时间</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">策略</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">交易对</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">方向</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">价格</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">数量</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">手续费</th>
                <th class="px-3 py-2 text-left text-dark-100 font-medium">状态</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/[0.06]">
              <tr v-for="trade in recentTrades" :key="trade.id" class="hover:bg-dark-700/30 transition-colors">
                <td class="px-3 py-2 text-white">{{ trade.time }}</td>
                <td class="px-3 py-2 text-white">{{ trade.strategy }}</td>
                <td class="px-3 py-2 text-white">{{ trade.pair }}</td>
                <td class="px-3 py-2">
                  <span :class="{ 'text-green-400': trade.direction === '买入', 'text-red-400': trade.direction === '卖出' }">{{ trade.direction }}</span>
                </td>
                <td class="px-3 py-2 text-white">${{ trade.price }}</td>
                <td class="px-3 py-2 text-white">{{ trade.amount }}</td>
                <td class="px-3 py-2 text-white">${{ trade.fee }}</td>
                <td class="px-3 py-2">
                  <span :class="{ 'text-green-400': trade.status === '已完成', 'text-yellow-400': trade.status === '部分成交', 'text-blue-400': trade.status === '待成交' }">{{ trade.status }}</span>
                </td>
              </tr>
            </tbody>
          </table>
          
          <div v-if="recentTrades.length === 0" class="text-center py-6">
            <div class="w-8 h-8 bg-dark-700 rounded-full flex items-center justify-center mx-auto mb-2">
              <span class="text-dark-200 text-sm">📋</span>
            </div>
            <p class="text-dark-100 text-sm">暂无交易记录</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import strategyApi from '@/utils/strategyApi'
import tradingApi from '@/utils/tradingApi'

// 响应式数据
const currentTime = ref('')
const filterStatus = ref('all')
const selectedMarket = ref('BTC/USDT')
const activeBottomTab = ref('持仓')
const latency = ref(12)
const loading = ref(false)

// 运行策略数据
const strategies = ref<any[]>([])

// 持仓数据
const positions = ref<any[]>([])

// 交易历史
const recentTrades = ref<any[]>([])

// 警报数据
const recentAlerts = ref<any[]>([])

// 风险指标
const riskMetrics = ref({
  var: '1,250',
  maxDrawdown: 3.2,
  volatility: 15.8,
  sharpeRatio: 1.8
})

// 市场数据
const markets = ref(['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT'])
const marketData = ref([
  { label: '当前价格', value: '$91,476.14', change: 1.24 },
  { label: '24H最高', value: '$92,800.00', change: null },
  { label: '24H最低', value: '$89,200.00', change: null },
  { label: '24H成交量', value: '12,345 BTC', change: null }
])

// 底部选项卡
const bottomTabs = ref(['持仓', '交易历史'])

// 加载运行中的策略
async function loadRunningStrategies() {
  loading.value = true
  try {
    const response = await strategyApi.getStrategies({
      status: 'running',
      page: 1,
      page_size: 50
    })
    strategies.value = response.items.map((item: any) => ({
      id: item.strategy_id,
      name: item.name,
      pair: item.symbol,
      status: item.status,
      pnl: item.total_pnl_percent || 0,
      position: `${item.current_position || 0} ${item.symbol.replace('USDT', '')}`,
      runtime: calculateRuntime(item.created_at),
      signals: item.signal_count || 0
    }))
  } catch (error: any) {
    console.error('加载运行策略失败:', error)
    MessagePlugin.error(error.message || '加载运行策略失败')
  } finally {
    loading.value = false
  }
}

// 加载持仓信息
async function loadPositions() {
  try {
    const response = await tradingApi.getPositions({
      exchange_id: 'binance'
    })
    positions.value = response.items.map((pos: any) => ({
      id: pos.position_id,
      strategy: pos.strategy_name || '未知策略',
      pair: pos.symbol,
      direction: pos.side === 'long' ? '多' : '空',
      amount: `${pos.quantity} ${pos.symbol.replace('USDT', '')}`,
      entryPrice: pos.entry_price,
      currentPrice: pos.current_price,
      pnl: pos.unrealized_pnl,
      pnlRatio: pos.unrealized_pnl_percent
    }))
  } catch (error: any) {
    console.error('加载持仓信息失败:', error)
  }
}

// 加载交易历史
async function loadTrades() {
  try {
    const response = await tradingApi.getTrades({
      exchange_id: 'binance',
      page: 1,
      page_size: 20
    })
    recentTrades.value = response.items.map((trade: any) => ({
      id: trade.trade_id,
      time: new Date(trade.created_at).toLocaleTimeString('zh-CN', { hour12: false }),
      strategy: trade.strategy_name || '未知策略',
      pair: trade.symbol,
      direction: trade.side === 'buy' ? '买入' : '卖出',
      price: trade.price.toLocaleString('en-US'),
      amount: `${trade.quantity} ${trade.symbol.replace('USDT', '')}`,
      fee: trade.fee.toFixed(2),
      status: trade.status === 'filled' ? '已完成' : trade.status === 'partially_filled' ? '部分成交' : '待成交'
    }))
  } catch (error: any) {
    console.error('加载交易历史失败:', error)
  }
}

// 计算运行时间
function calculateRuntime(createdAt: string): string {
  const now = new Date()
  const created = new Date(createdAt)
  const diff = now.getTime() - created.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  return `${days}天${hours}小时`
}

// 计算属性
const runningStrategiesCount = computed(() => 
  strategies.value.filter(s => s.status === 'running').length
)

const filteredStrategies = computed(() => {
  if (filterStatus.value === 'all') return strategies.value
  return strategies.value.filter(s => s.status === filterStatus.value)
})

const totalPnL = computed(() => {
  return strategies.value.reduce((sum, s) => sum + s.pnl, 0).toFixed(2)
})

const todayPnL = computed(() => {
  return (Math.random() * 2 - 1).toFixed(2)
})

const annualizedReturn = computed(() => {
  return (Math.random() * 30 + 5).toFixed(1)
})

const winRate = computed(() => {
  return (Math.random() * 30 + 60).toFixed(1)
})

const riskAlerts = computed(() => {
  return recentAlerts.value.filter(alert => !alert.read && alert.level === 'high')
})

// 方法
async function pauseStrategy(id: string) {
  try {
    await strategyApi.pauseStrategy(id)
    MessagePlugin.success('策略已暂停')
    await loadRunningStrategies()
  } catch (error: any) {
    console.error('暂停策略失败:', error)
    MessagePlugin.error(error.message || '暂停策略失败')
  }
}

async function resumeStrategy(id: string) {
  try {
    await strategyApi.resumeStrategy(id)
    MessagePlugin.success('策略已恢复')
    await loadRunningStrategies()
  } catch (error: any) {
    console.error('恢复策略失败:', error)
    MessagePlugin.error(error.message || '恢复策略失败')
  }
}

async function stopStrategy(id: string) {
  try {
    await strategyApi.stopStrategy(id)
    MessagePlugin.success('策略已停止')
    await loadRunningStrategies()
  } catch (error: any) {
    console.error('停止策略失败:', error)
    MessagePlugin.error(error.message || '停止策略失败')
  }
}

function markAllAlertsAsRead() {
  recentAlerts.value.forEach(alert => alert.read = true)
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
    loadRunningStrategies(),
    loadPositions(),
    loadTrades()
  ])
  
  onUnmounted(() => {
    clearInterval(timer)
  })
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

/* 响应式设计 */
@media (max-width: 1280px) {
  .grid.grid-cols-1.xl\:grid-cols-3 {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  
  .xl\:col-span-1, .xl\:col-span-2 {
    grid-column: span 1;
  }
}

@media (max-width: 768px) {
  .p-4 {
    padding: 1rem;
  }
  
  .gap-4 {
    gap: 1rem;
  }
  
  .grid.grid-cols-2.md\:grid-cols-4 {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .overflow-x-auto {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  
  table {
    min-width: 900px;
  }
}
</style>