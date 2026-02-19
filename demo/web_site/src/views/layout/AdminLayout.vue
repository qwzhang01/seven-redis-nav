<template>
  <div class="min-h-screen bg-dark-900 flex">
    <!-- Sidebar -->
    <aside class="w-64 bg-dark-800 border-r border-white/[0.06] flex flex-col fixed h-full z-20">
      <div class="p-6 border-b border-white/[0.06]">
        <router-link to="/admin" class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-500 to-accent-blue flex items-center justify-center text-dark-900 font-extrabold text-sm">
            QM
          </div>
          <div>
            <span class="text-white font-bold text-lg">Quant Meta</span>
            <span class="text-xs text-dark-100 block -mt-0.5">管理后台</span>
          </div>
        </router-link>
      </div>
      <nav class="flex-1 p-4 space-y-1">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200"
          :class="[
            isActive(item.path)
              ? 'bg-primary-500/10 text-primary-500'
              : 'text-dark-100 hover:text-white hover:bg-white/[0.04]',
          ]"
        >
          <component :is="item.icon" :size="18" />
          {{ item.label }}
        </router-link>
      </nav>
      <div class="p-4 border-t border-white/[0.06]">
        <router-link to="/" class="flex items-center gap-2 text-sm text-dark-100 hover:text-primary-500 transition-colors px-4 py-2">
          <ArrowLeft :size="16" />
          返回前台
        </router-link>
      </div>
    </aside>
    <!-- Main Content -->
    <div class="flex-1 ml-64">
      <header class="h-16 border-b border-white/[0.06] bg-dark-800/80 backdrop-blur-xl flex items-center px-8 sticky top-0 z-10">
        <h1 class="text-lg font-semibold text-white">{{ currentTitle }}</h1>
      </header>
      <main class="p-8">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { LayoutDashboard, Zap, Radio, Trophy, ShieldAlert, ArrowLeft, Key, TrendingUp, Database } from 'lucide-vue-next'

const route = useRoute()

const menuItems = [
  { path: '/admin', label: '管理概览', icon: LayoutDashboard },
  { path: '/admin/strategies', label: '策略管理', icon: Zap },
  { path: '/admin/signals', label: '信号接入', icon: Radio },
  { path: '/admin/leaderboard', label: '排行榜配置', icon: Trophy },
  { path: '/admin/api-keys', label: 'API密钥审核', icon: Key },
  { path: '/admin/data-subscription', label: '实时数据订阅', icon: Database },
  { path: '/admin/logs', label: '风控与日志', icon: ShieldAlert },
]

const currentTitle = computed(() => {
  const meta = route.meta.title as string
  return meta || '管理后台'
})

function isActive(path: string): boolean {
  if (path === '/admin') return route.path === '/admin'
  return route.path.startsWith(path)
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
