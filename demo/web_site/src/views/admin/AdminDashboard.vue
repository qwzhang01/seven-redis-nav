<template>
  <div class="space-y-8">
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <div v-for="stat in stats" :key="stat.label" class="glass-card p-6">
        <div class="flex items-center justify-between mb-4">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center" :class="stat.iconBg">
            <component :is="stat.icon" :size="20" :class="stat.iconColor" />
          </div>
          <span class="text-xs px-2 py-0.5 rounded-full" :class="stat.changeBg">{{ stat.change }}</span>
        </div>
        <div class="text-2xl font-bold text-white">{{ stat.value }}</div>
        <div class="text-sm text-dark-100 mt-1">{{ stat.label }}</div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="glass-card p-6">
        <h3 class="text-white font-bold mb-4">最新策略活动</h3>
        <div class="space-y-3">
          <div v-for="(item, i) in recentStrategies" :key="i" class="flex items-center gap-3 p-3 rounded-lg bg-dark-800/50">
            <div class="w-2 h-2 rounded-full" :class="item.status === 'active' ? 'bg-emerald-400' : 'bg-dark-200'" />
            <div class="flex-1 min-w-0">
              <div class="text-sm text-white truncate">{{ item.name }}</div>
              <div class="text-xs text-dark-100">{{ item.time }}</div>
            </div>
            <span class="text-xs font-medium" :class="item.return >= 0 ? 'text-emerald-400' : 'text-red-400'">
              {{ item.return >= 0 ? '+' : '' }}{{ item.return }}%
            </span>
          </div>
        </div>
      </div>

      <div class="glass-card p-6">
        <h3 class="text-white font-bold mb-4">最新信号接入</h3>
        <div class="space-y-3">
          <div v-for="(item, i) in recentSignals" :key="i" class="flex items-center gap-3 p-3 rounded-lg bg-dark-800/50">
            <div class="w-2 h-2 rounded-full" :class="item.verified ? 'bg-emerald-400' : 'bg-amber-400'" />
            <div class="flex-1 min-w-0">
              <div class="text-sm text-white truncate">{{ item.name }}</div>
              <div class="text-xs text-dark-100">{{ item.platform }} · {{ item.time }}</div>
            </div>
            <span class="text-xs px-2 py-0.5 rounded" :class="item.verified ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'">
              {{ item.verified ? '已验证' : '待审核' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Zap, Radio, Users, TrendingUp } from 'lucide-vue-next'

const stats = [
  { label: '活跃策略', value: '24', icon: Zap, iconBg: 'bg-primary-500/10', iconColor: 'text-primary-400', change: '+3', changeBg: 'bg-emerald-500/10 text-emerald-400' },
  { label: '接入信号', value: '156', icon: Radio, iconBg: 'bg-blue-500/10', iconColor: 'text-blue-400', change: '+12', changeBg: 'bg-emerald-500/10 text-emerald-400' },
  { label: '总用户数', value: '5,231', icon: Users, iconBg: 'bg-purple-500/10', iconColor: 'text-purple-400', change: '+89', changeBg: 'bg-emerald-500/10 text-emerald-400' },
  { label: '平台收益率', value: '+18.4%', icon: TrendingUp, iconBg: 'bg-emerald-500/10', iconColor: 'text-emerald-400', change: '+2.1%', changeBg: 'bg-emerald-500/10 text-emerald-400' },
]

const recentStrategies = [
  { name: '网格交易 BTC #12', status: 'active', time: '5分钟前', return: 2.34 },
  { name: '趋势跟踪 ETH #8', status: 'active', time: '12分钟前', return: -1.02 },
  { name: '均值回归 SOL #3', status: 'stopped', time: '1小时前', return: 5.67 },
  { name: '动量突破 BNB #6', status: 'active', time: '2小时前', return: 0.89 },
  { name: 'DCA定投 DOT #1', status: 'active', time: '3小时前', return: 3.21 },
]

const recentSignals = [
  { name: 'Alpha Pro #15', platform: 'Binance', time: '10分钟前', verified: true },
  { name: 'Sigma Elite #22', platform: 'OKX', time: '30分钟前', verified: false },
  { name: 'Quant Master #9', platform: 'Bybit', time: '1小时前', verified: true },
  { name: 'Nexus Prime #4', platform: 'Gate.io', time: '2小时前', verified: false },
  { name: 'Omega X #7', platform: 'Bitget', time: '3小时前', verified: true },
]
</script>
