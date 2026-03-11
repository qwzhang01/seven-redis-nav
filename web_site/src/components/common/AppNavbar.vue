<template>
  <nav class="fixed top-0 left-0 right-0 z-50 transition-all duration-300" :class="[scrolled ? 'bg-dark-900/90 backdrop-blur-xl border-b border-white/[0.06] shadow-lg' : 'bg-transparent']">
    <div class="page-container">
      <div class="flex items-center justify-between h-16 lg:h-[72px]">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-3 group">
          <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-500 to-accent-blue flex items-center justify-center text-dark-900 font-extrabold text-sm transition-transform group-hover:scale-105">
            QA
          </div>
          <span class="text-white font-bold text-xl tracking-tight hidden sm:block">
            Quanta<span class="gradient-text ml-1">量元</span>
          </span>
        </router-link>

        <!-- Desktop Nav -->
        <div class="hidden lg:flex items-center gap-1">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
            :class="[
              isActive(item.path)
                ? 'text-primary-500 bg-primary-500/10'
                : 'text-dark-100 hover:text-white hover:bg-white/[0.04]'
            ]"
          >
            {{ item.label }}
          </router-link>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-3">
          <template v-if="authStore.isLoggedIn">
            <!-- User Dropdown -->
            <div class="relative">
              <button 
                @click="userDropdownOpen = !userDropdownOpen"
                class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all"
              >
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center">
                  <User :size="16" class="text-primary-400" />
                </div>
                <span class="hidden sm:block">{{ authStore.user?.username || '我的账户' }}</span>
                <ChevronDown :size="14" class="text-dark-200 transition-transform duration-200" :class="{ 'rotate-180': userDropdownOpen }" />
              </button>
              
              <!-- Dropdown Menu -->
              <transition name="slide-down">
                <div v-if="userDropdownOpen" class="absolute top-full right-0 mt-2 w-48 bg-dark-800/95 backdrop-blur-xl border border-white/[0.06] rounded-lg shadow-lg overflow-hidden z-50">
                  <div class="py-2">
                    <router-link 
                      to="/system/user" 
                      class="flex items-center gap-3 px-4 py-2 text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all"
                      @click="userDropdownOpen = false"
                    >
                      <User :size="16" />
                      <span>我的账户</span>
                    </router-link>
                    <router-link
                        to="/system/running-strategies"
                        class="flex items-center gap-3 px-4 py-2 text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-colors"
                    >
                      <Activity :size="14" />
                      策略实盘
                    </router-link>
                    <router-link 
                      to="/system/user/personal" 
                      class="flex items-center gap-3 px-4 py-2 text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all"
                      @click="userDropdownOpen = false"
                    >
                      <User :size="16" />
                      <span>个人中心</span>
                    </router-link>
                    <router-link 
                      v-if="authStore.isAdmin" 
                      to="/admin" 
                      class="flex items-center gap-3 px-4 py-2 text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all"
                      @click="userDropdownOpen = false"
                    >
                      <ShieldCheck :size="16" />
                      <span>管理后台</span>
                    </router-link>
                    <div class="border-t border-white/[0.06] my-1"></div>
                    <button 
                      @click="handleLogout" 
                      class="flex items-center gap-3 px-4 py-2 text-sm text-dark-100 hover:text-red-400 hover:bg-red-500/10 transition-all w-full text-left"
                    >
                      <LogOut :size="16" />
                      <span>退出登录</span>
                    </button>
                  </div>
                </div>
              </transition>
            </div>
            
            <!-- Close dropdown when clicking outside -->
            <div v-if="userDropdownOpen" class="fixed inset-0 z-40" @click="userDropdownOpen = false"></div>
          </template>
          <template v-else>
            <router-link to="/login" class="hidden sm:block text-sm text-dark-100 hover:text-white px-4 py-2 rounded-lg hover:bg-white/[0.04] transition-all">
              登录
            </router-link>
            <router-link to="/register" class="btn-primary !py-2 !px-4 text-sm hidden sm:block">
              免费注册
            </router-link>
          </template>
          <!-- Mobile Menu Toggle -->
          <button @click="mobileMenuOpen = !mobileMenuOpen" class="lg:hidden p-2 rounded-lg text-dark-100 hover:text-white hover:bg-white/[0.04]">
            <Menu v-if="!mobileMenuOpen" :size="22" />
            <X v-else :size="22" />
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Menu -->
    <transition name="slide-down">
      <div v-if="mobileMenuOpen" class="lg:hidden bg-dark-800/95 backdrop-blur-xl border-b border-white/[0.06]">
        <div class="page-container py-4 space-y-1">
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
          <template v-if="authStore.isLoggedIn">
            <router-link to="/system/user" class="block px-4 py-3 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04]" @click="mobileMenuOpen = false">
              我的账户
            </router-link>
            <router-link to="/system/user/personal" class="block px-4 py-3 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04]" @click="mobileMenuOpen = false">
              个人中心
            </router-link>
            <router-link v-if="authStore.isAdmin" to="/admin" class="block px-4 py-3 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04]" @click="mobileMenuOpen = false">
              管理后台
            </router-link>
            <div class="pt-2 px-4">
              <button @click="handleLogout" class="btn-outline w-full text-sm !py-2.5">退出登录</button>
            </div>
          </template>
          <template v-else>
            <div class="pt-2 px-4 space-y-2">
              <router-link to="/login" class="btn-outline w-full text-sm !py-2.5 block text-center" @click="mobileMenuOpen = false">登录</router-link>
              <router-link to="/register" class="btn-primary w-full text-sm !py-2.5 block text-center" @click="mobileMenuOpen = false">免费注册</router-link>
            </div>
          </template>
        </div>
      </div>
    </transition>
  </nav>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Menu,
  X,
  User,
  ShieldCheck,
  ChevronDown,
  LogOut,
  Activity
} from 'lucide-vue-next'
import { MessagePlugin } from 'tdesign-vue-next'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const scrolled = ref(false)
const mobileMenuOpen = ref(false)
const userDropdownOpen = ref(false)

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

function handleLogout() {
  authStore.logout()
  mobileMenuOpen.value = false
  userDropdownOpen.value = false
  MessagePlugin.success('已退出登录')
  router.push('/')
}

function handleScroll() {
  scrolled.value = window.scrollY > 20
}

onMounted(() => window.addEventListener('scroll', handleScroll))
onUnmounted(() => window.removeEventListener('scroll', handleScroll))
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>