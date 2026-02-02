<template>
  <div class="live-monitor-page">
    <div class="page-header">
      <div class="header-left">
        <h1><t-icon name="dashboard" /> 实盘监控</h1>
        <t-tag theme="success" size="large"><t-icon name="check-circle" /> 运行中</t-tag>
      </div>
      <div class="header-actions">
        <t-button variant="outline" @click="refreshData"><t-icon name="refresh" /> 刷新</t-button>
        <t-button theme="warning" @click="showPauseConfirm = true"><t-icon name="pause" /> 暂停</t-button>
        <t-button theme="danger" @click="showStopConfirm = true"><t-icon name="stop" /> 停止</t-button>
      </div>
    </div>
    
    <!-- 策略概览 -->
    <div class="overview-section">
      <t-card :bordered="false">
        <div class="overview-content">
          <div class="overview-main">
            <div class="strategy-meta">
              <h2>{{ strategyInfo.name }}</h2>
              <div class="meta-tags">
                <t-tag theme="primary">{{ strategyInfo.exchange }}</t-tag>
                <t-tag>{{ strategyInfo.pair }}</t-tag>
                <t-tag variant="outline">运行 {{ strategyInfo.runningDays }} 天</t-tag>
              </div>
            </div>
            <div class="total-pnl" :class="totalPnl >= 0 ? 'positive' : 'negative'">
              <div class="pnl-label">累计收益</div>
              <div class="pnl-value">{{ totalPnl >= 0 ? '+' : '' }}{{ formatPrice(totalPnl) }} USDT</div>
              <div class="pnl-percent">{{ totalPnlPercent >= 0 ? '+' : '' }}{{ totalPnlPercent.toFixed(2) }}%</div>
            </div>
          </div>
          <div class="overview-stats">
            <div class="stat-card" v-for="stat in statsCards" :key="stat.label">
              <div class="stat-icon"><t-icon :name="stat.icon" /></div>
              <div class="stat-info">
                <div class="stat-label">{{ stat.label }}</div>
                <div class="stat-value" :class="stat.class">{{ stat.value }}</div>
              </div>
            </div>
          </div>
        </div>
      </t-card>
    </div>
    
    <!-- 监控面板 -->
    <div class="monitor-panels">
      <div class="left-panel">
        <t-card title="资金曲线" :bordered="false">
          <apexchart type="area" height="280" :options="equityChartOptions" :series="equitySeries" />
        </t-card>
        
        <t-card title="当前持仓" :bordered="false">
          <div v-for="pos in positions" :key="pos.id" class="position-item">
            <div class="position-header">
              <span class="symbol">{{ pos.symbol }}</span>
              <t-tag :theme="pos.side === 'long' ? 'success' : 'danger'" size="small">
                {{ pos.side === 'long' ? '多' : '空' }} {{ pos.leverage }}x
              </t-tag>
            </div>
            <div class="position-details">
              <span>数量: {{ pos.amount }}</span>
              <span>开仓: ${{ formatPrice(pos.entryPrice) }}</span>
              <span>现价: ${{ formatPrice(pos.currentPrice) }}</span>
              <span :class="pos.pnl >= 0 ? 'text-success' : 'text-danger'">
                盈亏: {{ pos.pnl >= 0 ? '+' : '' }}{{ formatPrice(pos.pnl) }}
              </span>
            </div>
            <t-button size="small" variant="outline" @click="closePosition(pos)">平仓</t-button>
          </div>
          <t-empty v-if="!positions.length" description="暂无持仓" />
        </t-card>
      </div>
      
      <div class="right-panel">
        <t-card title="运行状态" :bordered="false">
          <div class="status-list">
            <div class="status-item" v-for="s in statusList" :key="s.label">
              <span class="dot" :class="s.status"></span>
              <span class="label">{{ s.label }}</span>
              <span class="value">{{ s.value }}</span>
            </div>
          </div>
          <div class="last-update">最后更新: {{ lastUpdateTime }}</div>
        </t-card>
        
        <t-card title="风控指标" :bordered="false">
          <div class="risk-item" v-for="r in riskIndicators" :key="r.label">
            <div class="risk-header">
              <span>{{ r.label }}</span>
              <span class="limit">限制: {{ r.limit }}</span>
            </div>
            <t-progress :percentage="r.percent" :color="r.color" />
            <div class="risk-value">{{ r.value }}</div>
          </div>
        </t-card>
        
        <t-card title="最近交易" :bordered="false">
          <div class="trade-list">
            <div v-for="trade in recentTrades" :key="trade.id" class="trade-item">
              <div class="trade-info">
                <span class="symbol">{{ trade.symbol }}</span>
                <t-tag :theme="trade.side === 'buy' ? 'success' : 'danger'" size="small">
                  {{ trade.side === 'buy' ? '买' : '卖' }}
                </t-tag>
                <span class="details">{{ trade.amount }} @ ${{ formatPrice(trade.price) }}</span>
              </div>
              <span class="trade-pnl" :class="trade.pnl >= 0 ? 'text-success' : 'text-danger'">
                {{ trade.pnl >= 0 ? '+' : '' }}{{ formatPrice(trade.pnl) }}
              </span>
            </div>
          </div>
        </t-card>
      </div>
    </div>
    
    <!-- 系统日志 -->
    <t-card title="系统日志" :bordered="false" class="log-card">
      <div class="log-list">
        <div v-for="log in logs" :key="log.id" class="log-item" :class="log.level">
          <span class="time">{{ log.time }}</span>
          <t-tag :theme="log.level === 'error' ? 'danger' : log.level === 'warning' ? 'warning' : 'default'" size="small">
            {{ log.level }}
          </t-tag>
          <span class="message">{{ log.message }}</span>
        </div>
      </div>
    </t-card>
    
    <t-dialog v-model:visible="showPauseConfirm" header="暂停策略" @confirm="pauseStrategy">
      <p>确定要暂停当前策略吗？</p>
    </t-dialog>
    <t-dialog v-model:visible="showStopConfirm" header="停止策略" theme="danger" @confirm="stopStrategy">
      <p>确定要停止当前策略吗？</p>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'

const showPauseConfirm = ref(false)
const showStopConfirm = ref(false)
const lastUpdateTime = ref(new Date().toLocaleString())

const strategyInfo = ref({
  name: 'BTC网格交易策略',
  exchange: 'Binance',
  pair: 'BTC/USDT',
  runningDays: 45
})

const totalPnl = ref(2580.50)
const totalPnlPercent = ref(25.81)

const statsCards = computed(() => [
  { icon: 'wallet', label: '初始资金', value: '10,000 USDT' },
  { icon: 'chart-pie', label: '当前资产', value: '12,580.50 USDT' },
  { icon: 'calendar', label: '今日盈亏', value: '+156.80 USDT', class: 'text-success' },
  { icon: 'swap', label: '总交易次数', value: '328' }
])

const positions = ref([
  { id: 1, symbol: 'BTC/USDT', side: 'long', leverage: 10, amount: 0.15, entryPrice: 44850, currentPrice: 45230, pnl: 57 },
  { id: 2, symbol: 'ETH/USDT', side: 'short', leverage: 5, amount: 2.5, entryPrice: 2480, currentPrice: 2450, pnl: 75 }
])

const statusList = ref([
  { label: '策略引擎', value: '运行中', status: 'online' },
  { label: '交易所连接', value: '正常', status: 'online' },
  { label: '数据同步', value: '实时', status: 'online' },
  { label: '风控状态', value: '正常', status: 'warning' }
])

const riskIndicators = computed(() => [
  { label: '今日亏损', limit: '5%', value: '1.2%', percent: 24, color: '#00A870' },
  { label: '最大回撤', limit: '20%', value: '8.5%', percent: 42.5, color: '#00A870' },
  { label: '持仓数量', limit: '5个', value: '2 / 5', percent: 40, color: '#0052D9' }
])

const recentTrades = ref([
  { id: 1, symbol: 'BTC/USDT', side: 'sell', amount: 0.1, price: 45180, pnl: 32.5 },
  { id: 2, symbol: 'BTC/USDT', side: 'buy', amount: 0.15, price: 44850, pnl: 0 },
  { id: 3, symbol: 'ETH/USDT', side: 'sell', amount: 1.5, price: 2510, pnl: 45 }
])

const logs = ref([
  { id: 1, level: 'info', time: '10:25:32', message: '订单成交: 卖出 BTC 0.1 @ 45180' },
  { id: 2, level: 'warning', time: '10:20:15', message: '网络延迟增加: 150ms' },
  { id: 3, level: 'info', time: '09:15:20', message: '订单成交: 买入 BTC 0.15 @ 44850' },
  { id: 4, level: 'error', time: '昨天 23:45', message: 'API请求失败，已自动重试' }
])

const equityChartOptions = {
  chart: { type: 'area', toolbar: { show: false }, background: 'transparent' },
  theme: { mode: 'dark' },
  colors: ['#0052D9'],
  fill: { type: 'gradient', gradient: { opacityFrom: 0.7, opacityTo: 0.2 } },
  stroke: { curve: 'smooth', width: 2 },
  xaxis: { type: 'datetime', labels: { style: { colors: '#666' } } },
  yaxis: { labels: { style: { colors: '#666' } } },
  grid: { borderColor: '#21262d' }
}

const equitySeries = ref([{
  name: '资产',
  data: Array.from({ length: 168 }, (_, i) => [Date.now() - (167 - i) * 3600000, 10000 + Math.random() * 3000])
}])

const formatPrice = (p) => p?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'

const refreshData = () => {
  lastUpdateTime.value = new Date().toLocaleString()
  MessagePlugin.success('数据已刷新')
}

const closePosition = (pos) => MessagePlugin.success(`${pos.symbol} 平仓委托已提交`)
const pauseStrategy = () => { showPauseConfirm.value = false; MessagePlugin.warning('策略已暂停') }
const stopStrategy = () => { showStopConfirm.value = false; MessagePlugin.success('策略已停止') }

let timer = null
onMounted(() => { timer = setInterval(() => lastUpdateTime.value = new Date().toLocaleString(), 5000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style lang="less" scoped>
.live-monitor-page { padding: 24px; background: #0d1117; min-height: calc(100vh - 56px); }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;
  .header-left { display: flex; align-items: center; gap: 16px;
    h1 { margin: 0; font-size: 24px; color: #fff; display: flex; align-items: center; gap: 8px; }
  }
  .header-actions { display: flex; gap: 12px; }
}

.overview-section { margin-bottom: 24px;
  :deep(.t-card) { background: #161b22; border: none; }
}

.overview-content {
  .overview-main { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid #30363d;
    .strategy-meta { h2 { margin: 0 0 12px; font-size: 20px; color: #fff; } .meta-tags { display: flex; gap: 8px; } }
    .total-pnl { text-align: right;
      .pnl-label { font-size: 14px; color: rgba(255,255,255,0.6); margin-bottom: 4px; }
      .pnl-value { font-size: 32px; font-weight: bold; }
      .pnl-percent { font-size: 18px; }
      &.positive { .pnl-value, .pnl-percent { color: var(--green); } }
      &.negative { .pnl-value, .pnl-percent { color: var(--red); } }
    }
  }
  .overview-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
    .stat-card { display: flex; align-items: center; gap: 16px; padding: 16px; background: #21262d; border-radius: 8px;
      .stat-icon { width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; background: rgba(0,82,217,0.2); border-radius: 8px; font-size: 24px; color: var(--primary); }
      .stat-info { .stat-label { font-size: 13px; color: rgba(255,255,255,0.6); margin-bottom: 4px; } .stat-value { font-size: 18px; font-weight: 600; color: #fff; } }
    }
  }
}

.text-success { color: var(--green) !important; }
.text-danger { color: var(--red) !important; }

.monitor-panels { display: grid; grid-template-columns: 1fr 380px; gap: 24px; margin-bottom: 24px;
  :deep(.t-card) { background: #161b22; border: none; margin-bottom: 16px; &:last-child { margin-bottom: 0; } }
}

.position-item { padding: 16px; background: #21262d; border-radius: 8px; margin-bottom: 12px;
  .position-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; .symbol { font-weight: 600; color: #fff; } }
  .position-details { display: flex; gap: 16px; font-size: 13px; color: rgba(255,255,255,0.7); margin-bottom: 12px; }
}

.status-list { .status-item { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid #30363d;
  .dot { width: 8px; height: 8px; border-radius: 50%; &.online { background: var(--green); } &.warning { background: #E37318; } }
  .label { flex: 1; color: rgba(255,255,255,0.8); } .value { color: rgba(255,255,255,0.6); font-size: 13px; }
} }
.last-update { margin-top: 12px; font-size: 13px; color: rgba(255,255,255,0.5); }

.risk-item { margin-bottom: 16px;
  .risk-header { display: flex; justify-content: space-between; margin-bottom: 8px; color: rgba(255,255,255,0.8); .limit { font-size: 12px; color: rgba(255,255,255,0.5); } }
  .risk-value { text-align: right; font-size: 13px; color: rgba(255,255,255,0.6); margin-top: 4px; }
}

.trade-list { .trade-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #30363d;
  .trade-info { display: flex; align-items: center; gap: 8px; font-size: 13px; color: rgba(255,255,255,0.7); .symbol { color: #fff; font-weight: 500; } }
  .trade-pnl { font-weight: 500; }
} }

.log-card { :deep(.t-card) { background: #161b22; border: none; } }
.log-list { max-height: 200px; overflow-y: auto;
  .log-item { display: flex; align-items: center; gap: 12px; padding: 8px 0; font-size: 13px; border-bottom: 1px solid #21262d;
    .time { color: rgba(255,255,255,0.5); width: 80px; } .message { color: rgba(255,255,255,0.8); }
  }
}
</style>
