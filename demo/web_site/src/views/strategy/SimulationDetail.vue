<template>
  <div class="min-h-screen bg-dark-900">
    <!-- Breadcrumb -->
    <div class="px-6 py-4 border-b border-dark-700">
      <div class="flex items-center gap-2 text-sm text-dark-100">
        <router-link to="/system/user" class="hover:text-primary-500 transition-colors">我的账户</router-link>
        <ChevronRight :size="14" />
        <span class="text-white">{{ strategy.name }} (模拟交易)</span>
      </div>
    </div>

    <!-- 顶部：策略头部信息和控制按钮 -->
    <div class="px-6 py-4 border-b border-dark-700 bg-dark-800/30">
      <div class="flex items-center justify-between">
        <!-- 策略信息 -->
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
            <FlaskConical :size="24" class="text-blue-400" />
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h1 class="text-xl font-bold text-white">{{ strategy.name }}</h1>
              <span class="px-2 py-0.5 text-xs rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">
                模拟交易
              </span>
            </div>
            <div class="flex items-center gap-3 mt-1">
              <span class="text-sm text-dark-100">{{ strategy.symbol }}</span>
              <span class="text-dark-300">·</span>
              <span class="text-sm text-dark-100">{{ strategy.type }}</span>
              <span class="text-dark-300">·</span>
              <span class="text-sm text-dark-100">{{ strategy.timeframe }}</span>
              <RiskBadge :level="strategy.riskLevel" />
              <StatusDot :status="strategy.status" />
            </div>
          </div>
        </div>

        <!-- 实时模拟收益 -->
        <div class="flex items-center gap-6">
          <div class="text-center">
            <div class="text-2xl font-bold" :class="strategy.totalReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
              {{ strategy.totalReturn >= 0 ? '+' : '' }}{{ strategy.totalReturn }}%
            </div>
            <div class="text-xs text-dark-100">模拟总收益率</div>
          </div>
          <div class="text-center">
            <div class="text-sm font-bold" :class="strategy.todayReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
              {{ strategy.todayReturn >= 0 ? '+' : '' }}{{ strategy.todayReturn }}%
            </div>
            <div class="text-xs text-dark-100">今日模拟收益</div>
          </div>
          <div class="text-center">
            <div class="text-sm font-bold text-white">${{ strategy.currentValue.toLocaleString() }}</div>
            <div class="text-xs text-dark-100">当前模拟价值</div>
          </div>
          <div class="text-center">
            <div class="text-sm font-bold text-amber-400">{{ strategy.maxDrawdown }}%</div>
            <div class="text-xs text-dark-100">最大回撤</div>
          </div>
        </div>

        <!-- 策略控制按钮 -->
        <div class="flex items-center gap-2">
          <button
            v-if="strategy.status === 'running'"
            @click="pauseStrategy"
            class="px-4 py-2 bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 rounded-lg transition-colors flex items-center gap-2 text-sm"
          >
            <Pause :size="14" />
            暂停
          </button>
          <button
            v-if="strategy.status === 'paused'"
            @click="resumeStrategy"
            class="px-4 py-2 bg-green-500/20 text-green-400 hover:bg-green-500/30 rounded-lg transition-colors flex items-center gap-2 text-sm"
          >
            <Play :size="14" />
            恢复
          </button>
          <button
            @click="stopStrategy"
            class="px-4 py-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded-lg transition-colors flex items-center gap-2 text-sm"
          >
            <Square :size="14" />
            停止
          </button>
        </div>
      </div>
    </div>

    <!-- 主体内容：左右布局 -->
    <div class="flex h-[calc(100vh-160px)]">
      <!-- 左栏：2/3宽度 - 图表和分析 -->
      <div class="w-2/3 p-6 space-y-4 overflow-y-auto">
        <!-- K线图区域 -->
        <div class="glass-card p-4">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-lg font-bold text-white flex items-center gap-2">
              <CandlestickChart :size="18" class="text-primary-400" />
              K线走势图 · 指标 · 买卖点
            </h2>
            <div class="flex items-center gap-2">
              <!-- 时间周期快速切换 -->
              <div class="flex items-center bg-dark-800/60 rounded-lg p-0.5">
                <button
                  v-for="tf in timeframes"
                  :key="tf.value"
                  @click="changeTimeframe(tf.value)"
                  class="px-2.5 py-1 text-xs rounded-md transition-colors"
                  :class="currentTimeframe === tf.value
                    ? 'bg-primary-500/20 text-primary-400'
                    : 'text-dark-100 hover:text-white'"
                >
                  {{ tf.label }}
                </button>
              </div>
              <!-- 指标开关 -->
              <button
                @click="showIndicators = !showIndicators"
                class="px-3 py-1 text-xs rounded-lg transition-colors"
                :class="showIndicators
                  ? 'bg-blue-500/20 text-blue-400'
                  : 'bg-dark-800/60 text-dark-100'"
              >
                <LineChart :size="12" class="inline mr-1" />
                指标
              </button>
              <!-- 交易标记开关 -->
              <button
                @click="showTradeMarks = !showTradeMarks"
                class="px-3 py-1 text-xs rounded-lg transition-colors"
                :class="showTradeMarks
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : 'bg-dark-800/60 text-dark-100'"
              >
                <Target :size="12" class="inline mr-1" />
                交易点
              </button>
            </div>
          </div>

          <!-- 图表加载指示器 -->
          <div v-if="chartLoading" class="h-[500px] flex items-center justify-center">
            <div class="text-center">
              <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mb-2"></div>
              <p class="text-dark-100 text-sm">加载图表数据...</p>
            </div>
          </div>

          <!-- TradingChart 图表组件 -->
          <TradingChart
            v-else
            ref="tradingChartRef"
            :kline-data="klineData"
            :indicators="showIndicators ? indicatorData : []"
            :trade-marks="showTradeMarks ? tradeMarks : []"
            :height="500"
            :show-volume="true"
            @load-more="handleLoadMore"
            @time-range-change="handleTimeRangeChange"
          />

          <!-- 图表图例说明 -->
          <div class="mt-3 flex items-center gap-4 text-xs text-dark-100">
            <span v-for="ind in indicatorData" :key="ind.name" class="flex items-center gap-1">
              <span class="w-3 h-0.5 rounded" :style="{ backgroundColor: ind.color }"></span>
              {{ ind.name }}
            </span>
            <span class="flex items-center gap-1">
              <span class="text-emerald-400">▲</span> 买入点
            </span>
            <span class="flex items-center gap-1">
              <span class="text-red-400">▼</span> 卖出点
            </span>
          </div>
        </div>

        <!-- 交易量分析 -->
        <div class="glass-card p-4">
          <h2 class="text-sm font-bold text-white mb-3 flex items-center gap-2">
            <Activity :size="16" class="text-purple-400" />
            交易统计
          </h2>
          <div class="grid grid-cols-5 gap-3">
            <div class="text-center p-2.5 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-white">{{ strategy.tradeCount }}</div>
              <div class="text-xs text-dark-100">总交易次数</div>
            </div>
            <div class="text-center p-2.5 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-emerald-400">{{ strategy.winRate }}%</div>
              <div class="text-xs text-dark-100">胜率</div>
            </div>
            <div class="text-center p-2.5 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-white">{{ strategy.profitFactor }}</div>
              <div class="text-xs text-dark-100">盈亏比</div>
            </div>
            <div class="text-center p-2.5 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-white">{{ strategy.avgHoldingTime }}h</div>
              <div class="text-xs text-dark-100">平均持仓时间</div>
            </div>
            <div class="text-center p-2.5 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-white">{{ strategy.signalsToday }}</div>
              <div class="text-xs text-dark-100">今日信号</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右栏：1/3宽度 - 持仓和交易记录 -->
      <div class="w-1/3 p-6 space-y-4 overflow-y-auto border-l border-dark-700">
        <!-- 当前模拟持仓 -->
        <div class="glass-card p-4">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-sm font-bold text-white flex items-center gap-2">
              <Package :size="16" class="text-amber-400" />
              模拟持仓
            </h2>
            <span class="text-xs text-dark-100">{{ positions.length }} 个持仓</span>
          </div>
          <div class="space-y-2">
            <div
              v-for="pos in positions"
              :key="pos.symbol + pos.direction"
              class="p-3 rounded-lg bg-dark-800/50 border-l-4"
              :class="pos.direction === 'long' ? 'border-green-500/50' : 'border-red-500/50'"
            >
              <div class="flex items-center justify-between mb-1.5">
                <div class="flex items-center gap-2">
                  <span class="text-white font-medium text-sm">{{ pos.symbol }}</span>
                  <span
                    class="text-xs px-1.5 py-0.5 rounded"
                    :class="pos.direction === 'long' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'"
                  >
                    {{ pos.direction === 'long' ? '多' : '空' }}
                  </span>
                </div>
                <span class="text-sm font-bold" :class="pos.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ pos.pnl >= 0 ? '+' : '' }}${{ Math.abs(pos.pnl).toFixed(2) }}
                </span>
              </div>
              <div class="grid grid-cols-2 gap-1.5 text-xs">
                <div>
                  <span class="text-dark-200">数量</span>
                  <div class="text-white">{{ pos.amount }}</div>
                </div>
                <div>
                  <span class="text-dark-200">入场价</span>
                  <div class="text-white">${{ pos.entry_price.toLocaleString() }}</div>
                </div>
                <div>
                  <span class="text-dark-200">当前价</span>
                  <div class="text-white">${{ pos.current_price.toLocaleString() }}</div>
                </div>
                <div>
                  <span class="text-dark-200">盈亏率</span>
                  <div :class="pos.pnl_ratio >= 0 ? 'text-emerald-400' : 'text-red-400'">
                    {{ pos.pnl_ratio >= 0 ? '+' : '' }}{{ pos.pnl_ratio }}%
                  </div>
                </div>
              </div>
            </div>
            <div v-if="positions.length === 0" class="text-center py-6 text-dark-100 text-sm">
              暂无模拟持仓
            </div>
          </div>
        </div>

        <!-- 表现分析 -->
        <div class="glass-card p-4">
          <h3 class="text-sm font-bold text-white mb-3">表现分析</h3>
          <div class="grid grid-cols-2 gap-2">
            <div class="text-center p-2 rounded-lg bg-dark-800/50">
              <div class="text-lg font-bold text-white">{{ strategy.sharpeRatio }}</div>
              <div class="text-xs text-dark-100">夏普比率</div>
            </div>
            <div class="text-center p-2 rounded-lg bg-dark-800/50">
              <div class="text-lg font-bold text-white">{{ strategy.calmarRatio }}</div>
              <div class="text-xs text-dark-100">卡玛比率</div>
            </div>
            <div class="text-center p-2 rounded-lg bg-dark-800/50">
              <div class="text-lg font-bold text-white">{{ strategy.sortinoRatio }}</div>
              <div class="text-xs text-dark-100">索提诺比率</div>
            </div>
            <div class="text-center p-2 rounded-lg bg-dark-800/50">
              <div class="text-lg font-bold text-white">${{ strategy.initialCapital.toLocaleString() }}</div>
              <div class="text-xs text-dark-100">初始模拟资金</div>
            </div>
          </div>
        </div>

        <!-- 最近模拟交易 -->
        <div class="glass-card p-4">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-sm font-bold text-white flex items-center gap-2">
              <History :size="16" class="text-purple-400" />
              最近模拟交易
            </h2>
          </div>
          <div class="space-y-1.5">
            <div
              v-for="trade in recentTrades"
              :key="trade.id"
              class="p-2.5 rounded-lg bg-dark-800/30 hover:bg-dark-800/50 transition-colors"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="text-white text-sm font-medium">{{ trade.symbol }}</span>
                  <span
                    class="text-xs px-1.5 py-0.5 rounded"
                    :class="trade.side === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'"
                  >
                    {{ trade.side === 'buy' ? '买入' : '卖出' }}
                  </span>
                </div>
                <span
                  v-if="trade.pnl !== null"
                  class="text-xs font-bold"
                  :class="trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'"
                >
                  {{ trade.pnl >= 0 ? '+' : '' }}${{ Math.abs(trade.pnl).toFixed(2) }}
                </span>
              </div>
              <div class="flex items-center justify-between mt-1 text-xs text-dark-100">
                <span>${{ trade.price.toLocaleString() }}</span>
                <span>x{{ trade.amount }}</span>
                <span>{{ formatTime(trade.time) }}</span>
              </div>
            </div>
            <div v-if="recentTrades.length === 0" class="text-center py-4 text-dark-100 text-sm">
              暂无交易记录
            </div>
          </div>
        </div>

        <!-- 风险指标 -->
        <div class="glass-card p-4">
          <h3 class="text-sm font-bold text-white mb-3">风险指标</h3>
          <div class="space-y-2">
            <div class="flex justify-between items-center">
              <span class="text-xs text-dark-100">VaR (95%)</span>
              <span class="text-white text-sm font-medium">${{ strategy.var.toLocaleString() }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-xs text-dark-100">最大回撤</span>
              <span class="text-white text-sm font-medium">{{ strategy.maxDrawdown }}%</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-xs text-dark-100">波动率</span>
              <span class="text-white text-sm font-medium">{{ strategy.volatility }}%</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-xs text-dark-100">最大连续亏损</span>
              <span class="text-white text-sm font-medium">{{ strategy.maxConsecutiveLosses }} 次</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部：运行日志 -->
    <div class="border-t border-dark-700">
      <div class="px-6 py-3 bg-dark-800/30">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-bold text-white flex items-center gap-2">
            <FileText :size="16" class="text-blue-400" />
            模拟运行日志
          </h3>
          <div class="flex items-center gap-2">
            <button
              v-for="level in logLevels"
              :key="level.value"
              @click="logFilter = level.value"
              class="px-2 py-0.5 text-xs rounded transition-colors"
              :class="logFilter === level.value
                ? 'bg-primary-500/20 text-primary-400'
                : 'text-dark-100 hover:text-white'"
            >
              {{ level.label }}
            </button>
          </div>
        </div>
        <div class="h-28 bg-dark-800/50 rounded-lg p-3 overflow-y-auto font-mono text-xs">
          <div
            v-for="(log, idx) in filteredLogs"
            :key="idx"
            :class="getLogColor(log.level)"
          >
            [{{ formatLogTime(log.time) }}] {{ log.message }}
          </div>
          <div v-if="filteredLogs.length === 0" class="text-dark-100 text-center py-4">
            暂无日志
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ChevronRight, FlaskConical, Pause, Play, Square,
  CandlestickChart, LineChart, Target, Activity,
  Package, History, FileText
} from 'lucide-vue-next'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'
import RiskBadge from '@/components/common/RiskBadge.vue'
import StatusDot from '@/components/common/StatusDot.vue'
import TradingChart from '@/components/charts/TradingChart.vue'
import type { KlineDataPoint, IndicatorData, TradeMarkData } from '@/components/charts/TradingChart.vue'
import simulationApi from '@/utils/simulationApi'
import strategyApi from '@/utils/strategyApi'
import { createStrategyWebSocket, type WebSocketManager } from '@/utils/websocketApi'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const strategyId = computed(() => route.params.id as string)

// ==================== 图表相关 ====================

const tradingChartRef = ref<InstanceType<typeof TradingChart>>()
const chartLoading = ref(true)
const currentTimeframe = ref('5m')
const showIndicators = ref(true)
const showTradeMarks = ref(true)
const klineData = ref<KlineDataPoint[]>([])
const indicatorData = ref<IndicatorData[]>([])
const tradeMarks = ref<TradeMarkData[]>([])

const timeframes = [
  { label: '1m', value: '1m' },
  { label: '5m', value: '5m' },
  { label: '15m', value: '15m' },
  { label: '1h', value: '1h' },
  { label: '4h', value: '4h' },
  { label: '1D', value: '1d' },
]

// ==================== 模拟策略数据 ====================

const strategy = ref({
  id: '',
  name: '',
  symbol: '',
  type: '',
  timeframe: '5m',
  riskLevel: 'medium' as 'low' | 'medium' | 'high',
  status: 'running',
  totalReturn: 0,
  todayReturn: 0,
  currentValue: 0,
  maxDrawdown: 0,
  tradeCount: 0,
  winRate: 0,
  profitFactor: 0,
  avgHoldingTime: 0,
  signalsToday: 0,
  sharpeRatio: 0,
  calmarRatio: 0,
  sortinoRatio: 0,
  var: 0,
  volatility: 0,
  maxConsecutiveLosses: 0,
  initialCapital: 10000,
  runDays: 0,
})

const positions = ref<any[]>([])
const recentTrades = ref<any[]>([])

// ==================== 日志 ====================

const logFilter = ref('all')
const logLevels = [
  { label: '全部', value: 'all' },
  { label: '信息', value: 'info' },
  { label: '交易', value: 'trade' },
  { label: '警告', value: 'warn' },
  { label: '错误', value: 'error' },
]

const logs = ref<any[]>([])

const filteredLogs = computed(() => {
  if (logFilter.value === 'all') return logs.value
  return logs.value.filter((l) => l.level === logFilter.value)
})

// ==================== WebSocket ====================

let wsManager: WebSocketManager | null = null

function initWebSocket() {
  wsManager = createStrategyWebSocket({
    token: authStore.token || '',
    onMessage: (message) => {
      if (!message || !message.type) return

      switch (message.type) {
        case 'kline':
          // 实时K线更新
          if (message.data && tradingChartRef.value) {
            tradingChartRef.value.appendKline(message.data)
          }
          break
        case 'indicator':
          // 实时指标更新
          if (message.data?.indicators) {
            for (const ind of message.data.indicators) {
              tradingChartRef.value?.appendIndicator(ind.name, {
                time: ind.time,
                value: ind.value,
              })
            }
          }
          break
        case 'trade':
          // 新交易点标记
          if (message.data) {
            tradeMarks.value.push(message.data)
            tradingChartRef.value?.updateTradeMarks(tradeMarks.value)
          }
          break
        case 'position':
          // 持仓更新
          if (message.data?.positions) {
            positions.value = message.data.positions
          }
          break
      }
    },
    onOpen: () => {
      // 订阅模拟策略的数据频道
      wsManager?.subscribe([
        `simulation/${strategyId.value}/kline`,
        `simulation/${strategyId.value}/indicator`,
        `simulation/${strategyId.value}/trade`,
        `simulation/${strategyId.value}/position`,
        `simulation/${strategyId.value}/log`,
      ])
    },
  })

  wsManager.connect()
}

/**
 * 加载模拟策略详情和相关数据
 */
async function loadStrategyInfo() {
  try {
    // 并行加载策略详情、持仓、交易记录、日志
    const [detail, posRes, tradeRes, logRes] = await Promise.all([
      strategyApi.getUserStrategy(strategyId.value),
      simulationApi.getSimPositions(strategyId.value).catch(() => null),
      simulationApi.getSimTrades(strategyId.value, { page: 1, page_size: 10 }).catch(() => null),
      simulationApi.getSimLogs(strategyId.value, { limit: 50 }).catch(() => null),
    ])

    // 填充策略基本信息
    strategy.value = {
      id: detail.strategy_id || detail.id || strategyId.value,
      name: detail.name || '模拟策略',
      symbol: detail.symbols?.[0] || detail.symbol || 'BTC/USDT',
      type: detail.strategy_type || detail.type || '',
      timeframe: detail.timeframe || '5m',
      riskLevel: detail.risk_level || detail.riskLevel || 'medium',
      status: detail.state || detail.status || 'running',
      totalReturn: detail.total_pnl_ratio ?? detail.total_return ?? 0,
      todayReturn: detail.daily_pnl_ratio ?? 0,
      currentValue: detail.current_capital ?? detail.initial_capital ?? 10000,
      maxDrawdown: detail.max_drawdown ?? 0,
      tradeCount: detail.stats?.trade_count ?? 0,
      winRate: detail.win_rate ? (detail.win_rate * 100) : 0,
      profitFactor: detail.stats?.profit_factor ?? 0,
      avgHoldingTime: detail.stats?.avg_holding_hours ?? 0,
      signalsToday: 0,
      sharpeRatio: detail.sharpe_ratio ?? 0,
      calmarRatio: 0,
      sortinoRatio: 0,
      var: 0,
      volatility: 0,
      maxConsecutiveLosses: detail.stats?.max_consecutive_losses ?? 0,
      initialCapital: detail.initial_capital ?? 10000,
      runDays: 0,
    }

    // 填充持仓数据
    if (posRes?.positions) {
      positions.value = posRes.positions.map((p: any) => ({
        symbol: p.symbol,
        direction: p.direction,
        amount: p.amount,
        entry_price: p.entry_price,
        current_price: p.current_price,
        pnl: p.pnl,
        pnl_ratio: p.pnl_ratio,
      }))
    }

    // 填充交易记录
    if (tradeRes?.trades) {
      recentTrades.value = tradeRes.trades.map((t: any) => ({
        id: t.id,
        symbol: t.symbol,
        side: t.side,
        price: t.price,
        amount: t.amount,
        pnl: t.pnl,
        time: t.time,
      }))
    }

    // 填充日志
    if (logRes?.logs) {
      logs.value = logRes.logs
    }
  } catch (error: any) {
    console.error('加载模拟策略数据失败:', error)
  }
}

// ==================== 数据加载 ====================

/**
 * 生成模拟K线数据（演示用，实际应调用API）
 */
function generateMockKlineData(count: number, endTime?: number): KlineDataPoint[] {
  const data: KlineDataPoint[] = []
  const interval = 5 * 60 // 5分钟
  const now = endTime || Math.floor(Date.now() / 1000)
  let price = 91000

  for (let i = count - 1; i >= 0; i--) {
    const time = now - i * interval
    const change = (Math.random() - 0.48) * 200
    const open = price
    const close = price + change
    const high = Math.max(open, close) + Math.random() * 100
    const low = Math.min(open, close) - Math.random() * 100
    const volume = Math.random() * 50 + 10

    data.push({
      time,
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
      volume: parseFloat(volume.toFixed(2)),
    })

    price = close
  }

  return data
}

/**
 * 生成模拟指标数据
 */
function generateMockIndicators(klines: KlineDataPoint[]): IndicatorData[] {
  // MA20
  const ma20Data: Array<{ time: number; value: number }> = []
  for (let i = 19; i < klines.length; i++) {
    const sum = klines.slice(i - 19, i + 1).reduce((acc, k) => acc + k.close, 0)
    ma20Data.push({ time: klines[i].time, value: parseFloat((sum / 20).toFixed(2)) })
  }

  // MA60
  const ma60Data: Array<{ time: number; value: number }> = []
  for (let i = 59; i < klines.length; i++) {
    const sum = klines.slice(i - 59, i + 1).reduce((acc, k) => acc + k.close, 0)
    ma60Data.push({ time: klines[i].time, value: parseFloat((sum / 60).toFixed(2)) })
  }

  // RSI (简化版)
  const rsiData: Array<{ time: number; value: number }> = []
  for (let i = 14; i < klines.length; i++) {
    let gains = 0, losses = 0
    for (let j = i - 13; j <= i; j++) {
      const diff = klines[j].close - klines[j - 1].close
      if (diff > 0) gains += diff
      else losses -= diff
    }
    const avgGain = gains / 14
    const avgLoss = losses / 14
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss
    const rsi = 100 - 100 / (1 + rs)
    rsiData.push({ time: klines[i].time, value: parseFloat(rsi.toFixed(2)) })
  }

  return [
    { name: 'MA20', type: 'line', color: '#2196F3', pane: 'main', data: ma20Data },
    { name: 'MA60', type: 'line', color: '#FF9800', pane: 'main', data: ma60Data },
    { name: 'RSI(14)', type: 'line', color: '#AB47BC', pane: 'sub', data: rsiData },
  ]
}

/**
 * 生成模拟交易标记
 */
function generateMockTradeMarks(klines: KlineDataPoint[]): TradeMarkData[] {
  const marks: TradeMarkData[] = []
  const tradeInterval = Math.floor(klines.length / 10)

  for (let i = tradeInterval; i < klines.length; i += tradeInterval + Math.floor(Math.random() * 5)) {
    const isBuy = Math.random() > 0.5
    marks.push({
      time: klines[i].time,
      position: isBuy ? 'belowBar' : 'aboveBar',
      color: isBuy ? '#26a69a' : '#ef5350',
      shape: isBuy ? 'arrowUp' : 'arrowDown',
      text: isBuy
        ? `买入 ${klines[i].close.toFixed(0)}`
        : `卖出 ${klines[i].close.toFixed(0)}`,
    })
  }

  return marks
}

/**
 * 加载初始数据
 */
async function loadInitialData() {
  chartLoading.value = true
  try {
    // 尝试从API获取，如果失败则使用Mock数据
    try {
      const [klinesRes, indicatorsRes, marksRes] = await Promise.all([
        simulationApi.getSimKlines(strategyId.value, {
          timeframe: currentTimeframe.value,
          limit: 500,
        }),
        simulationApi.getSimIndicators(strategyId.value, { limit: 500 }),
        simulationApi.getSimTradeMarks(strategyId.value, { limit: 100 }),
      ])

      klineData.value = klinesRes.data
      indicatorData.value = klinesRes.data.length > 0
        ? indicatorsRes.indicators
        : []
      tradeMarks.value = marksRes.marks
    } catch {
      // API未就绪，使用Mock数据
      const mockKlines = generateMockKlineData(300)
      klineData.value = mockKlines
      indicatorData.value = generateMockIndicators(mockKlines)
      tradeMarks.value = generateMockTradeMarks(mockKlines)
    }
  } finally {
    chartLoading.value = false
  }
}

/**
 * 加载更多历史数据（拖动触发）
 */
async function handleLoadMore(endTime: number) {
  try {
    try {
      const res = await simulationApi.getSimKlines(strategyId.value, {
        timeframe: currentTimeframe.value,
        end_time: endTime * 1000,
        limit: 200,
      })
      if (res.data.length > 0 && tradingChartRef.value) {
        tradingChartRef.value.prependKlineData(res.data)
      }
    } catch {
      // API未就绪，使用Mock数据
      const moreData = generateMockKlineData(100, endTime)
      if (moreData.length > 0 && tradingChartRef.value) {
        tradingChartRef.value.prependKlineData(moreData)
      }
    }
  } catch (error) {
    console.error('加载更多数据失败:', error)
  }
}

/**
 * 切换时间周期
 */
async function changeTimeframe(tf: string) {
  currentTimeframe.value = tf
  await loadInitialData()
}

function handleTimeRangeChange(_from: number, _to: number) {
  // 可用于统计可见范围内的交易数据等
}

// ==================== 策略控制 ====================

async function pauseStrategy() {
  const dlg = DialogPlugin.confirm({
    header: '确认暂停模拟策略',
    body: '确定要暂停该模拟策略吗？暂停后策略将停止模拟交易，但保留当前模拟持仓。',
    theme: 'warning' as const,
    confirmBtn: '确认暂停',
    cancelBtn: '取消',
    onConfirm: async () => {
      dlg.hide()
      try {
        await strategyApi.pauseUserStrategy(strategyId.value)
        strategy.value.status = 'paused'
        MessagePlugin.success('模拟策略已暂停')
      } catch (error: any) {
        MessagePlugin.error(error.message || '暂停模拟策略失败')
      }
    },
    onCancel: () => dlg.hide(),
  })
}

async function resumeStrategy() {
  const dlg = DialogPlugin.confirm({
    header: '确认恢复模拟策略',
    body: '确定要恢复该模拟策略吗？恢复后策略将继续执行模拟交易逻辑。',
    theme: 'info' as const,
    confirmBtn: '确认恢复',
    cancelBtn: '取消',
    onConfirm: async () => {
      dlg.hide()
      try {
        await strategyApi.resumeUserStrategy(strategyId.value)
        strategy.value.status = 'running'
        MessagePlugin.success('模拟策略已恢复')
      } catch (error: any) {
        MessagePlugin.error(error.message || '恢复模拟策略失败')
      }
    },
    onCancel: () => dlg.hide(),
  })
}

async function stopStrategy() {
  const dlg = DialogPlugin.confirm({
    header: '确认停止模拟策略',
    body: '确定要停止该模拟策略吗？停止后将结束所有模拟交易。此操作不可撤销。',
    theme: 'danger' as const,
    confirmBtn: '确认停止',
    cancelBtn: '取消',
    onConfirm: async () => {
      dlg.hide()
      try {
        await strategyApi.stopUserStrategy(strategyId.value)
        strategy.value.status = 'stopped'
        MessagePlugin.success('模拟策略已停止')
      } catch (error: any) {
        MessagePlugin.error(error.message || '停止模拟策略失败')
      }
    },
    onCancel: () => dlg.hide(),
  })
}

// ==================== 工具方法 ====================

function formatTime(time: string): string {
  const date = new Date(time)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

function formatLogTime(time: string): string {
  const date = new Date(time)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
}

function getLogColor(level: string): string {
  const colors: Record<string, string> = {
    info: 'text-dark-100',
    trade: 'text-blue-400',
    warn: 'text-amber-400',
    error: 'text-red-400',
  }
  return colors[level] || 'text-dark-100'
}

// ==================== 生命周期 ====================

onMounted(async () => {
  strategy.value.id = strategyId.value
  // 并行加载策略信息和图表数据
  await Promise.all([
    loadStrategyInfo(),
    loadInitialData(),
  ])
  initWebSocket()
})

onBeforeUnmount(() => {
  if (wsManager) {
    wsManager.disconnect()
    wsManager = null
  }
})
</script>
