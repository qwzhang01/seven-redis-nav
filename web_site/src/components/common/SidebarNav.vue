<template>
  <div class="w-64 bg-dark-800 border-r border-white/[0.06] min-h-screen flex flex-col">
    <!-- Logo区域 -->
    <div class="p-6 border-b border-white/[0.06]">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500 to-accent-blue flex items-center justify-center text-dark-900 font-extrabold text-sm">
          QM
        </div>
        <div>
          <h1 class="text-white font-bold text-lg">Quant<span class="gradient-text ml-1">Meta</span></h1>
          <p class="text-dark-100 text-xs mt-1">专业量化交易</p>
        </div>
      </div>
    </div>

    <!-- 用户信息 -->
    <div class="p-4 border-b border-white/[0.06]">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center">
          <User :size="18" class="text-primary-400" />
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-white font-medium text-sm truncate">{{ authStore.user?.username || '用户' }}</div>
          <div class="text-dark-100 text-xs mt-1">总资产: ${{ formatNumber(authStore.user?.totalAssets || 0) }}</div>
        </div>
      </div>
    </div>

    <!-- 账户概览 -->
    <div class="p-4 border-b border-white/[0.06]">
      <div class="grid grid-cols-2 gap-3 text-center">
        <div class="bg-dark-700/50 rounded-lg p-2">
          <div class="text-white font-bold text-sm">{{ runningStrategies }}</div>
          <div class="text-dark-100 text-xs">运行策略</div>
        </div>
        <div class="bg-dark-700/50 rounded-lg p-2">
          <div class="text-white font-bold text-sm">{{ followingSignals }}</div>
          <div class="text-dark-100 text-xs">跟单信号</div>
        </div>
      </div>
      <div class="mt-3 grid grid-cols-2 gap-3 text-center">
        <div class="bg-dark-700/50 rounded-lg p-2">
          <div class="text-emerald-400 font-bold text-sm">+{{ totalReturn }}%</div>
          <div class="text-dark-100 text-xs">总收益率</div>
        </div>
        <div class="bg-dark-700/50 rounded-lg p-2">
          <div class="text-white font-bold text-sm">${{ formatNumber(totalAssets) }}</div>
          <div class="text-dark-100 text-xs">总资产</div>
        </div>
      </div>
    </div>

    <!-- 主导航 -->
    <nav class="flex-1 p-4 space-y-1">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 group"
        :class="[
          isActive(item.path)
            ? 'text-primary-500 bg-primary-500/10'
            : 'text-dark-100 hover:text-white hover:bg-white/[0.04]'
        ]"
      >
        <component :is="item.icon" :size="18" />
        <span>{{ item.label }}</span>
        <span v-if="item.badge" class="ml-auto px-2 py-0.5 text-xs rounded-full bg-primary-500/20 text-primary-400">
          {{ item.badge }}
        </span>
      </router-link>
    </nav>

    <!-- 底部操作 -->
    <div class="p-4 border-t border-white/[0.06]">
      <button
        @click="handleLogout"
        class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-dark-100 hover:text-red-400 hover:bg-red-500/10 transition-all duration-200"
      >
        <LogOut :size="18" />
        <span>退出</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  User, 
  TrendingUp, 
  Radio, 
  Trophy, 
  Settings, 
  LogOut,
  BarChart3,
  Zap
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { MessagePlugin } from 'tdesign-vue-next'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navItems = [
  { path: '/system/trading', label: '交易盘面', icon: BarChart3 },
  { path: '/system/strategies', label: '系统策略', icon: Zap },
  { path: '/system/signals', label: '信号广场', icon: Radio, badge: '1200+' },
  { path: '/system/leaderboard', label: '收益排行榜', icon: Trophy },
  { path: '/system/user', label: '我的账户', icon: User },
]

// 模拟数据
const runningStrategies = computed(() => authStore.user?.runningStrategies || 3)
const followingSignals = computed(() => authStore.user?.followingSignals || 5)
const totalReturn = computed(() => authStore.user?.totalReturn || 24.56)
const totalAssets = computed(() => authStore.user?.totalAssets || 12456)

function isActive(path: string): boolean {
  return route.path.startsWith(path)
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value)
}

function handleLogout() {
  authStore.logout()
  MessagePlugin.success('已退出登录')
  router.push('/')
}
</script>

<style scoped>
.gradient-text {
  background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>