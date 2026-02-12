<template>
  <div class="pt-24 pb-16">
    <div class="page-container">
      <!-- Header -->
      <div class="mb-10">
        <div class="flex items-center gap-4 mb-4">
          <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center">
            <UserIcon :size="32" class="text-primary-400" />
          </div>
          <div>
            <h1 class="text-2xl md:text-3xl font-extrabold text-white">我的账户</h1>
            <p class="text-dark-100">管理您的策略、信号跟单与账户设置</p>
          </div>
        </div>
      </div>

      <!-- Stats Overview -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        <div v-for="stat in overviewStats" :key="stat.label" class="glass-card p-5">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-9 h-9 rounded-lg flex items-center justify-center" :class="stat.iconBg">
              <component :is="stat.icon" :size="18" :class="stat.iconColor" />
            </div>
            <span class="text-sm text-dark-100">{{ stat.label }}</span>
          </div>
          <div class="text-2xl font-bold" :class="stat.valueColor || 'text-white'">{{ stat.value }}</div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="glass-card p-1.5 mb-8 inline-flex gap-1">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          @click="activeTab = tab.value"
          class="px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
          :class="activeTab === tab.value ? 'bg-primary-500/15 text-primary-400' : 'text-dark-100 hover:text-white hover:bg-white/[0.04]'"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- My Strategies -->
      <div v-if="activeTab === 'strategies'" class="space-y-4">
        <div class="flex items-center gap-3 mb-4">
          <button
            v-for="status in ['all', 'running', 'ended'] as const"
            :key="status"
            @click="strategyFilter = status"
            class="text-sm px-3 py-1.5 rounded-lg transition-all"
            :class="strategyFilter === status ? 'bg-primary-500/10 text-primary-400' : 'text-dark-100 hover:text-white'"
          >
            {{ status === 'all' ? '全部' : status === 'running' ? '运行中' : '已结束' }}
          </button>
        </div>
        <div
          v-for="item in filteredUserStrategies" 
          :key="item.id"
          class="glass-card-hover p-6 flex items-center gap-6 cursor-pointer"
          @click="$router.push(`/system/running-strategies/${item.id}`)"
        >
          <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center shrink-0">
            <Zap :size="18" class="text-primary-400" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <h4 class="text-white font-semibold text-sm">{{ item.name }}</h4>
              <StatusDot :status="item.status" />
            </div>
            <div class="flex items-center gap-4 text-xs text-dark-100">
              <span>启动: {{ item.startTime }}</span>
              <span v-if="item.endTime">结束: {{ item.endTime }}</span>
            </div>
          </div>
          <div class="text-right">
            <div class="text-lg font-bold" :class="item.totalReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
              {{ item.totalReturn >= 0 ? '+' : '' }}{{ item.totalReturn.toFixed(2) }}%
            </div>
            <div class="text-xs text-dark-100">总收益</div>
          </div>
          <ChevronRight :size="16" class="text-dark-200 shrink-0" />
        </div>
        <div v-if="filteredUserStrategies.length === 0" class="text-center py-12 text-dark-100">
          暂无策略记录
        </div>
      </div>

      <!-- My Signals -->
      <div v-if="activeTab === 'signals'" class="space-y-4">
        <div class="flex items-center gap-3 mb-4">
          <button
            v-for="status in ['all', 'following', 'stopped'] as const"
            :key="status"
            @click="signalFilter = status"
            class="text-sm px-3 py-1.5 rounded-lg transition-all"
            :class="signalFilter === status ? 'bg-primary-500/10 text-primary-400' : 'text-dark-100 hover:text-white'"
          >
            {{ status === 'all' ? '全部' : status === 'following' ? '跟随中' : '已停止' }}
          </button>
        </div>
        <div
          v-for="item in filteredUserSignals"
          :key="item.id"
          class="glass-card-hover p-6 flex items-center gap-6"
        >
          <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-blue/20 to-accent-purple/20 flex items-center justify-center shrink-0">
            <Radio :size="18" class="text-blue-400" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <h4 class="text-white font-semibold text-sm">{{ item.name }}</h4>
              <StatusDot :status="item.status" />
            </div>
            <div class="flex items-center gap-4 text-xs text-dark-100">
              <span>跟单资金: {{ item.followAmount }} USDT</span>
              <span>比例: {{ item.followRatio * 100 }}%</span>
            </div>
          </div>
          <div class="text-right">
            <div class="text-lg font-bold" :class="item.totalReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
              {{ item.totalReturn >= 0 ? '+' : '' }}{{ item.totalReturn.toFixed(2) }}%
            </div>
            <div class="text-xs text-dark-100">总收益</div>
          </div>
          <ChevronRight :size="16" class="text-dark-200 shrink-0" />
        </div>
        <div v-if="filteredUserSignals.length === 0" class="text-center py-12 text-dark-100">
          暂无跟单记录
        </div>
      </div>

      <!-- Profit Stats -->
      <div v-if="activeTab === 'profit'" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="glass-card p-6 text-center">
            <div class="text-3xl font-bold text-emerald-400">+24.56%</div>
            <div class="text-sm text-dark-100 mt-1">总收益率</div>
          </div>
          <div class="glass-card p-6 text-center">
            <div class="text-3xl font-bold text-white">$2,456.78</div>
            <div class="text-sm text-dark-100 mt-1">总收益 (USDT)</div>
          </div>
          <div class="glass-card p-6 text-center">
            <div class="text-3xl font-bold text-amber-400">8.32%</div>
            <div class="text-sm text-dark-100 mt-1">最大回撤</div>
          </div>
        </div>
        <div class="glass-card p-6">
          <h3 class="text-white font-bold mb-4">收益曲线</h3>
          <ReturnCurveChart :data="profitCurve" :height="300" color="#10b981" />
        </div>
      </div>

      <!-- API Management -->
      <div v-if="activeTab === 'api'" class="space-y-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-white font-bold">API 密钥管理</h3>
          <button class="btn-primary !py-2 !px-4 text-sm flex items-center gap-1.5">
            <Plus :size="14" /> 添加密钥
          </button>
        </div>
        
        <!-- Add API Key Form -->
        <div class="glass-card p-6 mb-6">
          <h4 class="text-white font-semibold mb-4">添加API密钥</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-sm text-dark-100 mb-2">交易所</label>
              <select class="w-full bg-dark-600 border border-dark-500 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none">
                <option value="">选择交易所</option>
                <option value="binance">Binance</option>
                <option value="okx">OKX</option>
                <option value="huobi">Huobi</option>
              </select>
            </div>
            <div>
              <label class="block text-sm text-dark-100 mb-2">标签</label>
              <input type="text" placeholder="请输入密钥标签" class="w-full bg-dark-600 border border-dark-500 rounded-lg px-3 py-2 text-white text-sm placeholder-dark-300 focus:border-primary-500 focus:outline-none">
            </div>
            <div class="md:col-span-2">
              <label class="block text-sm text-dark-100 mb-2">API Key</label>
              <input type="text" placeholder="请输入API Key" class="w-full bg-dark-600 border border-dark-500 rounded-lg px-3 py-2 text-white text-sm placeholder-dark-300 focus:border-primary-500 focus:outline-none">
            </div>
            <div class="md:col-span-2">
              <label class="block text-sm text-dark-100 mb-2">Secret Key</label>
              <input type="password" placeholder="请输入Secret Key" class="w-full bg-dark-600 border border-dark-500 rounded-lg px-3 py-2 text-white text-sm placeholder-dark-300 focus:border-primary-500 focus:outline-none">
            </div>
          </div>
          <div class="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4 mb-4">
            <div class="flex items-start gap-3">
              <AlertTriangle :size="16" class="text-amber-400 mt-0.5 shrink-0" />
              <div class="text-sm">
                <p class="text-amber-400 font-medium mb-1">安全提示</p>
                <p class="text-amber-300">API密钥需要经过后台审核才能用于交易。请确保密钥权限设置正确，仅开启必要的交易权限。</p>
              </div>
            </div>
          </div>
          <button class="btn-primary w-full">提交审核</button>
        </div>

        <!-- API Keys List -->
        <div
          v-for="key in apiKeys"
          :key="key.id"
          class="glass-card p-6 flex items-center gap-6"
        >
          <div class="w-10 h-10 rounded-lg bg-dark-600 flex items-center justify-center shrink-0">
            <Key :size="18" class="text-primary-400" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <h4 class="text-white font-semibold text-sm">{{ key.label }}</h4>
              <span class="text-xs px-2 py-0.5 rounded bg-dark-600 text-dark-100">{{ key.exchange }}</span>
              <span
                class="text-xs px-2 py-0.5 rounded font-medium"
                :class="getReviewStatusClass(key.reviewStatus)"
              >
                {{ getReviewStatusText(key.reviewStatus) }}
              </span>
            </div>
            <div class="text-xs text-dark-200 font-mono">{{ maskApiKey(key.apiKey) }}</div>
            <div v-if="key.reviewStatus !== 'pending' && key.reviewReason" class="text-xs text-dark-100 mt-1">
              审核原因: {{ key.reviewReason }}
            </div>
          </div>
          <div class="flex items-center gap-2">
            <StatusDot :status="key.status" />
            <button class="p-2 rounded-lg text-dark-100 hover:text-red-400 hover:bg-red-500/10 transition-all">
              <Trash2 :size="14" />
            </button>
          </div>
        </div>
        <div v-if="apiKeys.length === 0" class="text-center py-12 text-dark-100">
          暂未绑定 API 密钥
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { User as UserIcon, Zap, Radio, ChevronRight, Plus, Key, Trash2, TrendingUp, Wallet, BarChart3, KeyRound, AlertTriangle } from 'lucide-vue-next'
import StatusDot from '@/components/common/StatusDot.vue'
import ReturnCurveChart from '@/components/charts/ReturnCurveChart.vue'

const activeTab = ref('strategies')
const strategyFilter = ref('all')
const signalFilter = ref('all')

const tabs = [
  { label: '我的策略', value: 'strategies' },
  { label: '信号跟单', value: 'signals' },
  { label: '收益统计', value: 'profit' },
  { label: 'API管理', value: 'api' },
]

const overviewStats = [
  { label: '运行策略', value: '3', icon: Zap, iconBg: 'bg-primary-500/10', iconColor: 'text-primary-400' },
  { label: '跟单信号', value: '5', icon: Radio, iconBg: 'bg-blue-500/10', iconColor: 'text-blue-400' },
  { label: '总收益率', value: '+24.56%', icon: TrendingUp, iconBg: 'bg-emerald-500/10', iconColor: 'text-emerald-400', valueColor: 'text-emerald-400' },
  { label: '总资产', value: '$12,456', icon: Wallet, iconBg: 'bg-amber-500/10', iconColor: 'text-amber-400' },
]

const userStrategies = [
  { id: '1', name: '网格交易 BTC #1', status: 'running', startTime: '2025-11-01', endTime: null, totalReturn: 12.45 },
  { id: '2', name: '趋势跟踪 ETH #3', status: 'running', startTime: '2025-10-15', endTime: null, totalReturn: 8.32 },
  { id: '3', name: '均值回归 SOL #2', status: 'ended', startTime: '2025-08-01', endTime: '2025-10-01', totalReturn: -3.21 },
  { id: '4', name: '动量突破 BNB #5', status: 'running', startTime: '2025-12-01', endTime: null, totalReturn: 5.67 },
]

const userSignals = [
  { id: '1', name: 'Alpha Pro #1', status: 'following', followAmount: 5000, followRatio: 1, totalReturn: 15.23 },
  { id: '2', name: 'Sigma Elite #3', status: 'following', followAmount: 2000, followRatio: 0.5, totalReturn: 8.91 },
  { id: '3', name: 'Quant Master #7', status: 'stopped', followAmount: 3000, followRatio: 1, totalReturn: -2.45 },
  { id: '4', name: 'Nexus Prime #2', status: 'following', followAmount: 10000, followRatio: 0.25, totalReturn: 22.67 },
]

const apiKeys = [
  { id: '1', label: 'Binance 主账户', exchange: 'Binance', apiKey: 'aBc***...***xYz', status: 'active', reviewStatus: 'pending' },
  { id: '2', label: 'OKX 跟单账户', exchange: 'OKX', apiKey: 'dEf***...***uVw', status: 'active', reviewStatus: 'approved' },
  { id: '3', label: 'Huobi 测试账户', exchange: 'Huobi', apiKey: 'gHi***...***jKl', status: 'disabled', reviewStatus: 'rejected', reviewReason: '密钥权限过大，存在安全风险' },
]

const profitCurve = Array.from({ length: 60 }, (_, i) => {
  return parseFloat((Math.sin(i / 10) * 5 + i * 0.4 + (Math.random() - 0.3) * 3).toFixed(2))
})

const filteredUserStrategies = computed(() => {
  if (strategyFilter.value === 'all') return userStrategies
  return userStrategies.filter((s) => s.status === strategyFilter.value)
})

const filteredUserSignals = computed(() => {
  if (signalFilter.value === 'all') return userSignals
  return userSignals.filter((s) => s.status === signalFilter.value)
})

const getReviewStatusClass = (status: string) => {
  switch (status) {
    case 'pending': return 'bg-amber-500/20 text-amber-400'
    case 'approved': return 'bg-emerald-500/20 text-emerald-400'
    case 'rejected': return 'bg-red-500/20 text-red-400'
    default: return 'bg-dark-600 text-dark-100'
  }
}

const getReviewStatusText = (status: string) => {
  switch (status) {
    case 'pending': return '审核中'
    case 'approved': return '已通过'
    case 'rejected': return '已拒绝'
    default: return status
  }
}

const maskApiKey = (key: string) => {
  if (key.length <= 8) return key
  return key.substring(0, 6) + '*'.repeat(key.length - 10) + key.substring(key.length - 4)
}
</script>
