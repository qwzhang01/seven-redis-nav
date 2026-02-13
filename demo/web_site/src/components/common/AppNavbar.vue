<template>
  <nav class="fixed top-0 left-0 right-0 z-50 transition-all duration-300" :class="[scrolled ? 'bg-dark-900/90 backdrop-blur-xl border-b border-white/[0.06] shadow-lg' : 'bg-transparent']">
    <div class="page-container">
      <div class="flex items-center justify-between h-16 lg:h-[72px]">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-3 group">
          <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-500 to-accent-blue flex items-center justify-center text-dark-900 font-extrabold text-sm transition-transform group-hover:scale-105">
            QM
          </div>
          <span class="text-white font-bold text-xl tracking-tight hidden sm:block">
            Quant<span class="gradient-text ml-1">Meta</span>
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
            <router-link to="/system/user" class="hidden sm:flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all">
              <User :size="16" />
              <span>{{ authStore.user?.username || '我的' }}</span>
            </router-link>
            <router-link v-if="authStore.isAdmin" to="/admin" class="hidden sm:flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all">
              <ShieldCheck :size="16" />
            </router-link>
            <button @click="handleLogout" class="btn-outline !py-2 !px-4 text-sm hidden sm:block">
              退出
            </button>
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
import { Menu, X, User, ShieldCheck } from 'lucide-vue-next'
import { MessagePlugin } from 'tdesign-vue-next'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const scrolled = ref(false)
const mobileMenuOpen = ref(false)

const navItems = [
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
