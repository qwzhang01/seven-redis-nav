<template>
  <div class="min-h-screen bg-dark-900 flex flex-col">
    <!-- 顶部导航栏 -->
    <div class="h-16 bg-dark-800 border-b border-white/[0.06] flex items-center justify-between px-6">
      <!-- 左侧：Quant Meta标志 -->
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500 to-accent-blue flex items-center justify-center text-dark-900 font-extrabold text-sm">
            QM
          </div>
          <div>
            <h1 class="text-white font-bold text-lg">量元<span
                class="gradient-text ml-1">Quanta</span></h1>
          </div>
        </div>
      </div>

      <!-- 中间：功能菜单 -->
      <div class="flex items-center gap-1">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="px-4 py-2 text-sm font-medium transition-all duration-200 rounded-lg"
          :class="[
            isActive(item.path)
              ? 'text-primary-500 bg-primary-500/10'
              : 'text-dark-100 hover:text-white hover:bg-white/[0.04]'
          ]"
        >
          {{ item.label }}
        </router-link>
      </div>

      <!-- 右侧：操作提示和状态信息 -->
      <div class="flex items-center gap-4">
        <!-- 个人中心跳转 -->
        <template v-if="authStore.isLoggedIn">
          <div class="relative group">
            <button class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all">
              <User :size="16" />
              <span>{{ authStore.user?.username || '我的' }}</span>
              <ChevronDown :size="14" class="transition-transform group-hover:rotate-180" />
            </button>
            
            <!-- 下拉菜单 -->
            <div class="absolute top-full right-0 mt-2 w-48 bg-dark-800 border border-white/[0.06] rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
              <div class="py-2">
                <router-link 
                  to="/system/user" 
                  class="flex items-center gap-3 px-4 py-2 text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-colors"
                >
                  <User :size="14" />
                  个人中心
                </router-link>
                <router-link 
                  to="/system/running-strategies" 
                  class="flex items-center gap-3 px-4 py-2 text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-colors"
                >
                  <Activity :size="14" />
                  策略实盘
                </router-link>
                <div class="h-px bg-white/[0.06] my-1"></div>
                <button class="flex items-center gap-3 px-4 py-2 text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-colors w-full text-left">
                  <LogOut :size="14" />
                  退出登录
                </button>
              </div>
            </div>
          </div>
        </template>
        <template v-else>
          <router-link to="/login" class="px-4 py-2 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all">
            登录
          </router-link>
        </template>
        
        <!-- 操作提示 -->
        <!-- 状态信息 -->
        <div class="flex items-center gap-4">
          <button 
            @click="toggleFullscreen"
            class="px-3 py-1 text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] rounded-lg transition-colors"
          >
            {{ isFullscreen ? '退出全屏' : '全屏' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- 主要内容区域 -->
    <div class="flex-1 overflow-auto">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { User, ChevronDown, Activity, LogOut } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const currentTime = ref('')
const isFullscreen = ref(false)

const navItems = [
  { path: '/index', label: '首页' },
  { path: '/system/trading', label: '交易' },
  { path: '/system/strategies', label: '系统策略' },
  { path: '/system/signals', label: '信号广场' },
  { path: '/system/leaderboard', label: '收益排行榜' },
]

function isActive(path: string): boolean {
  return route.path.startsWith(path)
}

function updateTime() {
  currentTime.value = new Date().toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

function goToHome() {
  router.push('/')
}

function openNewWindow() {
  window.open(window.location.href, '_blank')
}

onMounted(() => {
  updateTime()
  const timer = setInterval(updateTime, 1000)
  
  onUnmounted(() => {
    clearInterval(timer)
  })
})
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

.gradient-text {
  background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>