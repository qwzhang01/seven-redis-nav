<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold text-white">风控与日志</h2>
      <div class="flex items-center gap-3">
        <t-select v-model="logLevel" placeholder="日志级别" size="medium" style="width: 140px">
          <t-option label="全部" value="all" />
          <t-option label="INFO" value="info" />
          <t-option label="WARN" value="warn" />
          <t-option label="ERROR" value="error" />
        </t-select>
        <button class="btn-outline !py-2 !px-4 text-sm flex items-center gap-1.5">
          <Download :size="14" /> 导出日志
        </button>
      </div>
    </div>

    <!-- Risk Alerts -->
    <div class="glass-card p-6">
      <h3 class="text-white font-bold mb-4 flex items-center gap-2">
        <ShieldAlert :size="18" class="text-amber-400" />
        风控告警
      </h3>
      <div class="space-y-3">
        <div v-for="(alert, i) in alerts" :key="i" class="p-4 rounded-xl flex items-start gap-3"
             :class="alert.level === 'error' ? 'bg-red-500/5 border border-red-500/10' : alert.level === 'warn' ? 'bg-amber-500/5 border border-amber-500/10' : 'bg-dark-800/50'">
          <div class="w-2 h-2 rounded-full mt-1.5 shrink-0"
               :class="alert.level === 'error' ? 'bg-red-400' : alert.level === 'warn' ? 'bg-amber-400' : 'bg-blue-400'" />
          <div class="flex-1 min-w-0">
            <div class="text-sm text-white">{{ alert.message }}</div>
            <div class="text-xs text-dark-100 mt-1">{{ alert.time }}</div>
          </div>
          <span class="text-xs px-2 py-0.5 rounded shrink-0"
                :class="alert.level === 'error' ? 'bg-red-500/10 text-red-400' : alert.level === 'warn' ? 'bg-amber-500/10 text-amber-400' : 'bg-blue-500/10 text-blue-400'">
            {{ alert.level.toUpperCase() }}
          </span>
        </div>
      </div>
    </div>

    <!-- System Logs -->
    <div class="glass-card p-6">
      <h3 class="text-white font-bold mb-4 flex items-center gap-2">
        <FileText :size="18" class="text-primary-400" />
        系统日志
      </h3>
      <div class="bg-dark-900 rounded-xl p-4 font-mono text-xs leading-6 max-h-96 overflow-y-auto">
        <div v-for="(log, i) in filteredLogs" :key="i" class="flex gap-4">
          <span class="text-dark-200 shrink-0">{{ log.time }}</span>
          <span class="shrink-0 w-12"
                :class="log.level === 'ERROR' ? 'text-red-400' : log.level === 'WARN' ? 'text-amber-400' : 'text-blue-400'">
            [{{ log.level }}]
          </span>
          <span class="text-dark-100">{{ log.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ShieldAlert, FileText, Download } from 'lucide-vue-next'

const logLevel = ref('all')

const alerts = [
  { level: 'error', message: '策略 "动量突破 BTC #9" 触发最大回撤限制(25%)，已自动停止', time: '2分钟前' },
  { level: 'warn', message: '信号 "Alpha Pro #15" 连续3笔亏损交易，建议关注', time: '15分钟前' },
  { level: 'warn', message: 'Binance API 响应延迟升高(>500ms)，可能影响下单速度', time: '30分钟前' },
  { level: 'info', message: '排行榜数据已更新(156条信号)', time: '1小时前' },
  { level: 'error', message: 'OKX WebSocket 连接断开，正在重连...', time: '2小时前' },
]

const logs = [
  { time: '14:32:15', level: 'INFO', message: 'Strategy grid-btc-12 opened LONG position BTC/USDT 0.05 @ 67,234.50' },
  { time: '14:32:10', level: 'INFO', message: 'Signal alpha-pro-15 synced 3 new trades from Binance' },
  { time: '14:31:58', level: 'WARN', message: 'Strategy momentum-bnb-6 approaching max drawdown threshold (18.5%/20%)' },
  { time: '14:31:45', level: 'ERROR', message: 'Failed to execute order for signal sigma-elite-22: Insufficient balance' },
  { time: '14:31:30', level: 'INFO', message: 'Leaderboard refresh completed: 156 signals ranked' },
  { time: '14:31:15', level: 'INFO', message: 'New follower registered for signal nexus-prime-4 (total: 342)' },
  { time: '14:30:58', level: 'WARN', message: 'API rate limit warning: Binance 1100/1200 requests in last minute' },
  { time: '14:30:45', level: 'INFO', message: 'Strategy dca-dot-1 completed scheduled buy: 15 DOT @ $6.82' },
  { time: '14:30:30', level: 'ERROR', message: 'WebSocket reconnection to OKX failed (attempt 3/5)' },
  { time: '14:30:15', level: 'INFO', message: 'Risk check passed for 24 active strategies' },
  { time: '14:29:58', level: 'INFO', message: 'User account api-key-update: Binance key rotated successfully' },
  { time: '14:29:45', level: 'WARN', message: 'Signal quant-master-9 PnL deviation >5% from expected' },
]

const filteredLogs = computed(() => {
  if (logLevel.value === 'all') return logs
  return logs.filter((l) => l.level === logLevel.value.toUpperCase())
})
</script>
