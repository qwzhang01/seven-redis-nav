<template>
  <div class="min-h-screen bg-dark-900 flex flex-col">
    <!-- 顶部导航栏 -->
    <div class="h-16 bg-dark-800 border-b border-white/[0.06] flex items-center justify-between px-6">
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

      <!-- 中间：功能菜单（桌面端） -->
      <div class="hidden lg:flex items-center gap-1">
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
          <div class="relative group hidden lg:block">
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
                  我的账户
                </router-link>
                <router-link 
                  to="/system/running-strategies" 
                  class="flex items-center gap-3 px-4 py-2 text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-colors"
                >
                  <Activity :size="14" />
                  策略实盘
                </router-link>
                <router-link to="/system/user/personal"
                             class="flex items-center gap-3 px-4 py-2 text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-colors">
                  <Settings :size="14" />
                  个人中心
                </router-link>
                <router-link
                    v-if="authStore.isAdmin"
                    to="/admin"
                    class="flex items-center gap-3 px-4 py-2 text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all"
                >
                  <ShieldCheck :size="16" />
                  <span>管理后台</span>
                </router-link>
                <div class="h-px bg-white/[0.06] my-1"></div>
                <button @click="handleLogout"
                        class="flex items-center gap-3 px-4 py-2 text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-colors w-full text-left">
                  <LogOut :size="14" />
                  退出登录
                </button>
              </div>
            </div>
          </div>
        </template>
        <template v-else>
          <router-link to="/login" class="hidden lg:block px-4 py-2 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all">
            登录
          </router-link>
        </template>
        
        <!-- 全屏按钮（桌面端） -->
        <div class="hidden lg:flex items-center gap-4">
          <button 
            @click="toggleFullscreen"
            class="px-3 py-1 text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] rounded-lg transition-colors"
          >
            {{ isFullscreen ? '退出全屏' : '全屏' }}
          </button>
        </div>

        <!-- 移动端汉堡菜单按钮 -->
        <button @click="mobileMenuOpen = !mobileMenuOpen" class="lg:hidden p-2 rounded-lg text-dark-100 hover:text-white hover:bg-white/[0.04] transition-colors">
          <Menu v-if="!mobileMenuOpen" :size="22" />
          <X v-else :size="22" />
        </button>
      </div>
    </div>

    <!-- 移动端菜单 -->
    <transition name="slide-down">
      <div v-if="mobileMenuOpen" class="lg:hidden bg-dark-800/95 backdrop-blur-xl border-b border-white/[0.06] z-40">
        <div class="px-4 py-4 space-y-1">
          <!-- 导航菜单项 -->
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="block px-4 py-3 rounded-lg text-sm font-medium transition-all"
            :class="[
              isActive(item.path) ? 'text-primary-500 bg-primary-500/10' : 'text-dark-100 hover:text-white hover:bg-white/[0.04]'
            ]"
            @click="mobileMenuOpen = false"
          >
            {{ item.label }}
          </router-link>

          <!-- 分割线 -->
          <div class="h-px bg-white/[0.06] my-2"></div>

          <!-- 用户相关菜单 -->
          <template v-if="authStore.isLoggedIn">
            <router-link to="/system/user" class="flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all" @click="mobileMenuOpen = false">
              <User :size="16" />
              我的账户
            </router-link>
            <router-link to="/system/running-strategies" class="flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all" @click="mobileMenuOpen = false">
              <Activity :size="16" />
              策略实盘
            </router-link>
            <router-link to="/system/user/personal" class="flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all" @click="mobileMenuOpen = false">
              <Settings :size="16" />
              个人中心
            </router-link>
            <router-link v-if="authStore.isAdmin" to="/admin" class="flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all" @click="mobileMenuOpen = false">
              <ShieldCheck :size="16" />
              管理后台
            </router-link>
            <div class="pt-2 px-4">
              <button @click="handleLogout" class="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg text-sm text-dark-100 border border-white/[0.08] hover:text-red-400 hover:border-red-500/30 hover:bg-red-500/10 transition-all">
                <LogOut :size="16" />
                退出登录
              </button>
            </div>
          </template>
          <template v-else>
            <div class="px-4 space-y-2">
              <router-link to="/login" class="block text-center py-2.5 rounded-lg text-sm text-dark-100 border border-white/[0.08] hover:text-white hover:bg-white/[0.04] transition-all" @click="mobileMenuOpen = false">登录</router-link>
            </div>
          </template>
        </div>
      </div>
    </transition>
    
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
import {
  User,
  ChevronDown,
  Activity,
  LogOut,
  Settings,
  ShieldCheck,
  Menu,
  X
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import {MessagePlugin} from "tdesign-vue-next";

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const currentTime = ref('')
const isFullscreen = ref(false)
const userDropdownOpen = ref(false)
const mobileMenuOpen = ref(false)

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

function handleLogout() {
  authStore.logout()
  userDropdownOpen.value = false
  MessagePlugin.success('已退出登录')
  router.push('/')
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

.slide-down-enter-active,
.slide-down-leave-active {
  transition: transform 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  transform: translateY(-100%);
}

.gradient-text {
  background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>