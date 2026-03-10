<template>
  <div class="min-h-screen bg-dark-900">
    <!-- Breadcrumb -->
    <div class="px-6 py-4 border-b border-dark-700">
      <div class="flex items-center gap-2 text-sm text-dark-100">
        <router-link to="/system/user" class="hover:text-primary-500 transition-colors">我的账户</router-link>
        <ChevronRight :size="14" />
        <span class="text-white">{{ strategy.name }}</span>
      </div>
    </div>

    <!-- Top Section: Strategy Header with Controls -->
    <div class="px-6 py-4 border-b border-dark-700 bg-dark-800/30">
      <div class="flex items-center justify-between">
        <!-- Strategy Info -->
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center">
            <Zap :size="24" class="text-primary-400" />
          </div>
          <div>
            <h1 class="text-xl font-bold text-white">{{ strategy.name }}</h1>
            <div class="flex items-center gap-3 mt-1">
              <span class="text-sm text-dark-100">{{ strategy.market }}</span>
              <span class="text-dark-300">·</span>
              <span class="text-sm text-dark-100">{{ strategy.type }}</span>
              <RiskBadge :level="strategy.riskLevel" />
              <StatusDot :status="strategy.status" />
            </div>
          </div>
        </div>

        <!-- Real-time Performance -->
        <div class="flex items-center gap-6">
          <div class="text-center">
            <div class="text-2xl font-bold" :class="strategy.totalReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
              {{ strategy.totalReturn >= 0 ? '+' : '' }}{{ strategy.totalReturn }}%
            </div>
            <div class="text-xs text-dark-100">总收益率</div>
          </div>
          
          <div class="flex items-center gap-4">
            <div class="text-center">
              <div class="text-sm font-bold" :class="strategy.todayReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
                {{ strategy.todayReturn >= 0 ? '+' : '' }}{{ strategy.todayReturn }}%
              </div>
              <div class="text-xs text-dark-100">今日收益</div>
            </div>
            <div class="text-center">
              <div class="text-sm font-bold text-white">${{ strategy.currentValue.toLocaleString() }}</div>
              <div class="text-xs text-dark-100">当前价值</div>
            </div>
          </div>
        </div>

        <!-- Strategy Controls -->
        <div class="flex items-center gap-2">
          <button 
            v-if="strategy.status === 'running'"
            @click="pauseStrategy"
            class="px-4 py-2 bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 rounded-lg transition-colors flex items-center gap-2 text-sm"
          >
            <Pause :size="14" />
            暂停策略
          </button>
          <button 
            v-if="strategy.status === 'paused'"
            @click="resumeStrategy"
            class="px-4 py-2 bg-green-500/20 text-green-400 hover:bg-green-500/30 rounded-lg transition-colors flex items-center gap-2 text-sm"
          >
            <Play :size="14" />
            恢复策略
          </button>
          <button 
            @click="stopStrategy"
            class="px-4 py-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded-lg transition-colors flex items-center gap-2 text-sm"
          >
            <Square :size="14" />
            停止策略
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content: Left-Right Layout -->
    <div class="flex h-[calc(100vh-160px)]">
      <!-- Left Column: 2/3 width -->
      <div class="w-2/3 p-6 space-y-6 overflow-y-auto">
        <!-- Real-time Market Data -->
        <div class="glass-card p-6">
          <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <TrendingUp :size="18" class="text-emerald-400" />
            实时行情
          </h2>
          <div class="grid grid-cols-4 gap-4">
            <div class="text-center p-3 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-white">$91,476.14</div>
              <div class="text-xs text-dark-100">BTC价格</div>
            </div>
            <div class="text-center p-3 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-white">+1.5%</div>
              <div class="text-xs text-dark-100">24h涨跌</div>
            </div>
            <div class="text-center p-3 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-white">$3,521.23</div>
              <div class="text-xs text-dark-100">ETH价格</div>
            </div>
            <div class="text-center p-3 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-white">+2.1%</div>
              <div class="text-xs text-dark-100">24h涨跌</div>
            </div>
          </div>
        </div>

        <!-- Charting Area -->
        <div class="glass-card p-6">
          <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <BarChart3 :size="18" class="text-blue-400" />
            价格走势图
          </h2>
          <div class="h-64 bg-dark-800/50 rounded-lg flex items-center justify-center text-dark-100">
            图表区域 - 实时价格走势图
          </div>
        </div>

        <!-- Trading Volume -->
        <div class="glass-card p-6">
          <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Activity :size="18" class="text-purple-400" />
            交易量分析
          </h2>
          <div class="grid grid-cols-3 gap-4">
            <div class="text-center p-3 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-white">$1.2B</div>
              <div class="text-xs text-dark-100">24h交易量</div>
            </div>
            <div class="text-center p-3 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-white">156</div>
              <div class="text-xs text-dark-100">总交易次数</div>
            </div>
            <div class="text-center p-3 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-white">5</div>
              <div class="text-xs text-dark-100">今日信号</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: 1/3 width -->
      <div class="w-1/3 p-6 space-y-6 overflow-y-auto border-l border-dark-700">
        <!-- Current Positions -->
        <div class="glass-card p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-bold text-white flex items-center gap-2">
              <Package :size="18" class="text-amber-400" />
              当前持仓
            </h2>
            <span class="text-sm text-dark-100">{{ positions.length }} 个持仓</span>
          </div>
          <div class="space-y-3">
            <div 
              v-for="position in positions" 
              :key="position.id"
              class="p-4 rounded-lg bg-dark-800/50 border-l-4"
              :class="position.direction === 'long' ? 'border-green-500/50' : 'border-red-500/50'"
            >
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-3">
                  <span class="text-white font-medium">{{ position.symbol }}</span>
                  <span class="text-xs px-2 py-1 rounded" :class="position.direction === 'long' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'">
                    {{ position.direction === 'long' ? '多' : '空' }}
                  </span>
                </div>
                <span class="text-sm font-bold" :class="position.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'">
                  ${{ Math.abs(position.pnl).toLocaleString() }}
                </span>
              </div>
              <div class="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span class="text-dark-100">数量</span>
                  <div class="text-white">{{ position.amount }}</div>
                </div>
                <div>
                  <span class="text-dark-100">入场价</span>
                  <div class="text-white">${{ position.entryPrice.toLocaleString() }}</div>
                </div>
                <div>
                  <span class="text-dark-100">当前价</span>
                  <div class="text-white">${{ position.currentPrice.toLocaleString() }}</div>
                </div>
                <div>
                  <span class="text-dark-100">盈亏率</span>
                  <div class="text-white">{{ position.pnlRatio >= 0 ? '+' : '' }}{{ position.pnlRatio }}%</div>
                </div>
              </div>
            </div>
            <div v-if="positions.length === 0" class="text-center py-8 text-dark-100">
              暂无持仓
            </div>
          </div>
        </div>

        <!-- Performance Analytics -->
        <div class="glass-card p-6">
          <h3 class="text-lg font-bold text-white mb-4">表现分析</h3>
          <div class="grid grid-cols-2 gap-4">
            <div class="text-center p-3 rounded-lg bg-dark-800/50">
              <div class="text-xl font-bold text-white">{{ strategy.sharpeRatio }}</div>
              <div class="text-xs text-dark-100">夏普比率</div>
            </div>
            <div class="text-center p-3 rounded-lg bg-dark-800/50">
              <div class="text-xl font-bold text-white">{{ strategy.calmarRatio }}</div>
              <div class="text-xs text-dark-100">卡玛比率</div>
            </div>
            <div class="text-center p-3 rounded-lg bg-dark-800/50">
              <div class="text-xl font-bold text-white">{{ strategy.sortinoRatio }}</div>
              <div class="text-xs text-dark-100">索提诺比率</div>
            </div>
            <div class="text-center p-3 rounded-lg bg-dark-800/50">
              <div class="text-xl font-bold text-white">{{ strategy.winRate }}%</div>
              <div class="text-xs text-dark-100">胜率</div>
            </div>
          </div>
        </div>

        <!-- Risk Metrics -->
        <div class="glass-card p-6">
          <h3 class="text-lg font-bold text-white mb-4">风险指标</h3>
          <div class="space-y-3">
            <div class="flex justify-between items-center">
              <span class="text-sm text-dark-100">VaR (95%)</span>
              <span class="text-white font-medium">${{ strategy.var.toLocaleString() }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-dark-100">最大回撤</span>
              <span class="text-white font-medium">{{ strategy.maxDrawdown }}%</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-dark-100">波动率</span>
              <span class="text-white font-medium">{{ strategy.volatility }}%</span>
            </div>
          </div>
        </div>

        <!-- Recent Trades -->
        <div class="glass-card p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-bold text-white flex items-center gap-2">
              <History :size="18" class="text-purple-400" />
              最近交易
            </h2>
            <button class="text-sm text-primary-400 hover:text-primary-300 transition-colors">查看全部</button>
          </div>
          <div class="space-y-2">
            <div 
              v-for="trade in recentTrades" 
              :key="trade.id"
              class="p-3 rounded-lg bg-dark-800/30 hover:bg-dark-800/50 transition-colors"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <span class="text-white text-sm font-medium">{{ trade.symbol }}</span>
                  <span class="text-xs px-2 py-1 rounded" :class="trade.side === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'">
                    {{ trade.side === 'buy' ? '买入' : '卖出' }}
                  </span>
                </div>
                <span class="text-sm font-bold" :class="trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'">
                  ${{ Math.abs(trade.pnl).toLocaleString() }}
                </span>
              </div>
              <div class="flex items-center justify-between mt-1 text-xs text-dark-100">
                <span>价格: ${{ trade.price.toLocaleString() }}</span>
                <span>数量: {{ trade.amount }}</span>
                <span>{{ trade.time }}</span>
              </div>
            </div>
            <div v-if="recentTrades.length === 0" class="text-center py-6 text-dark-100">
              暂无交易记录
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Section: Logs -->
    <div v-if="strategy.id" class="border-t border-dark-700">
      <div class="px-6 py-4 bg-dark-800/30">
        <h3 class="text-lg font-bold text-white mb-3 flex items-center gap-2">
          <FileText :size="18" class="text-blue-400" />
          策略运行日志
        </h3>
        <div class="h-32 bg-dark-800/50 rounded-lg p-4 overflow-y-auto font-mono text-sm">
          <div class="text-emerald-400">[19:03:23] 策略运行正常，当前持仓3个</div>
          <div class="text-dark-100">[19:02:15] 检测到市场波动，调整参数...</div>
          <div class="text-blue-400">[19:01:45] 执行买入 ETH/USDT 数量: 5</div>
          <div class="text-red-400">[19:00:30] 执行卖出 BTC/USDT 数量: 0.1</div>
          <div class="text-dark-100">[18:59:12] 监控市场数据更新完成</div>
          <div class="text-amber-400">[18:58:05] 风险检查通过，继续运行</div>
        </div>
      </div>
    </div>

    <!-- Not Found -->
    <div v-else class="min-h-screen flex items-center justify-center">
      <div class="text-center">
        <p class="text-dark-100 text-lg">策略不存在</p>
        <router-link to="/system/user" class="btn-outline mt-4 inline-block">返回我的账户</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  Zap, ChevronRight, TrendingUp, BarChart3, History, Pause, Play, Square, Activity, Package, FileText 
} from 'lucide-vue-next'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'
import RiskBadge from '@/components/common/RiskBadge.vue'
import StatusDot from '@/components/common/StatusDot.vue'
import strategyApi from '@/utils/strategyApi'

const route = useRoute()
const router = useRouter()
const strategyId = computed(() => route.params.id as string)
const loading = ref(true)

// 策略数据
const strategy = ref({
  id: '',
  name: '',
  market: '',
  type: '',
  riskLevel: 'medium' as 'low' | 'medium' | 'high',
  status: 'running',
  totalReturn: 0,
  runDays: 0,
  maxDrawdown: 0,
  tradeCount: 0,
  winRate: 0,
  todayReturn: 0,
  currentValue: 0,
  activePositions: 0,
  signalsToday: 0,
  sharpeRatio: 0,
  calmarRatio: 0,
  sortinoRatio: 0,
  var: 0,
  maxDrawdownPeriod: 0,
  volatility: 0,
})

const positions = ref<any[]>([])
const recentTrades = ref<any[]>([])
const logs = ref<any[]>([])

/**
 * 加载策略详情
 */
async function loadStrategyData() {
  loading.value = true
  try {
    // 并行加载策略详情和性能数据
    const [detail, performance, signals] = await Promise.all([
      strategyApi.getUserStrategy(strategyId.value),
      strategyApi.getUserStrategyPerformance(strategyId.value).catch(() => null),
      strategyApi.getUserStrategySignals(strategyId.value, { limit: 10 }).catch(() => null),
    ])

    // 填充策略基本信息
    strategy.value = {
      id: detail.strategy_id || detail.id || strategyId.value,
      name: detail.name || '策略',
      market: detail.symbols?.[0] || detail.market || '',
      type: detail.strategy_type || detail.type || '',
      riskLevel: detail.risk_level || detail.riskLevel || 'medium',
      status: detail.state || detail.status || 'running',
      totalReturn: performance?.performance?.total_return ?? detail.total_return ?? 0,
      runDays: performance?.performance?.running_seconds ? Math.floor(performance.performance.running_seconds / 86400) : (detail.running_days ?? 0),
      maxDrawdown: performance?.performance?.max_drawdown ?? detail.max_drawdown ?? 0,
      tradeCount: performance?.performance?.trade_count ?? detail.stats?.trade_count ?? 0,
      winRate: performance?.performance?.win_rate ? (performance.performance.win_rate * 100) : (detail.win_rate ?? 0),
      todayReturn: detail.daily_pnl_ratio ?? 0,
      currentValue: detail.current_capital ?? detail.initial_capital ?? 10000,
      activePositions: 0,
      signalsToday: signals?.total ?? 0,
      sharpeRatio: performance?.performance?.sharpe_ratio ?? 0,
      calmarRatio: 0,
      sortinoRatio: 0,
      var: 0,
      maxDrawdownPeriod: 0,
      volatility: 0,
    }
  } catch (error: any) {
    console.error('加载策略数据失败:', error)
    MessagePlugin.error(error.message || '加载策略数据失败')
  } finally {
    loading.value = false
  }
}

function getStatusText(status: string) {
  const statusMap: Record<string, string> = {
    'running': '运行中',
    'paused': '已暂停',
    'stopped': '已停止',
    'ended': '已结束'
  }
  return statusMap[status] || status
}

async function pauseStrategy() {
  const dlg = DialogPlugin.confirm({
    header: '确认暂停策略',
    body: '确定要暂停该策略吗？暂停后策略将停止交易，但保留当前持仓。',
    theme: 'warning' as const,
    confirmBtn: '确认暂停',
    cancelBtn: '取消',
    onConfirm: async () => {
      dlg.hide()
      try {
        await strategyApi.pauseUserStrategy(strategyId.value)
        strategy.value.status = 'paused'
        MessagePlugin.success('策略已暂停')
      } catch (error: any) {
        MessagePlugin.error(error.message || '暂停策略失败')
      }
    },
    onCancel: () => dlg.hide(),
  })
}

async function resumeStrategy() {
  const dlg = DialogPlugin.confirm({
    header: '确认恢复策略',
    body: '确定要恢复该策略吗？恢复后策略将继续执行交易逻辑。',
    theme: 'info' as const,
    confirmBtn: '确认恢复',
    cancelBtn: '取消',
    onConfirm: async () => {
      dlg.hide()
      try {
        await strategyApi.resumeUserStrategy(strategyId.value)
        strategy.value.status = 'running'
        MessagePlugin.success('策略已恢复')
      } catch (error: any) {
        MessagePlugin.error(error.message || '恢复策略失败')
      }
    },
    onCancel: () => dlg.hide(),
  })
}

async function stopStrategy() {
  const dlg = DialogPlugin.confirm({
    header: '确认停止策略',
    body: '确定要停止该策略吗？停止后策略将平仓所有持仓并结束运行。此操作不可撤销。',
    theme: 'danger' as const,
    confirmBtn: '确认停止',
    cancelBtn: '取消',
    onConfirm: async () => {
      dlg.hide()
      try {
        await strategyApi.stopUserStrategy(strategyId.value)
        strategy.value.status = 'stopped'
        MessagePlugin.success('策略已停止')
      } catch (error: any) {
        MessagePlugin.error(error.message || '停止策略失败')
      }
    },
    onCancel: () => dlg.hide(),
  })
}

onMounted(() => {
  loadStrategyData()
})
</script>