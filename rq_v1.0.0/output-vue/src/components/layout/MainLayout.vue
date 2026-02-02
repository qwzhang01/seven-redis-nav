<template>
  <div class="main-layout">
    <!-- 顶部导航 -->
    <header class="app-header">
      <div class="header-left">
        <div class="logo" @click="$router.push('/trading')">
          <t-icon name="chart-bubble" size="24px" />
          <span>CryptoQuant</span>
        </div>
        <nav class="nav-menu">
          <t-menu
            :value="activeNav"
            mode="horizontal"
            theme="dark"
            @change="handleNavChange"
          >
            <t-menu-item value="trading">
              <template #icon><t-icon name="chart" /></template>
              行情
            </t-menu-item>
            <t-menu-item value="strategy">
              <template #icon><t-icon name="root-list" /></template>
              策略广场
            </t-menu-item>
            <t-menu-item value="my-strategy">
              <template #icon><t-icon name="file-code" /></template>
              我的策略
            </t-menu-item>
            <t-menu-item value="risk">
              <template #icon><t-icon name="secured" /></template>
              风控中心
            </t-menu-item>
          </t-menu>
        </nav>
      </div>
      
      <div class="header-right">
        <!-- 交易模式切换 -->
        <div class="trade-mode-switch" :class="{ paper: isPaperTrading }" @click="toggleMode">
          <div class="mode-indicator"></div>
          <span class="mode-label live">实盘</span>
          <span class="mode-label paper">模拟</span>
        </div>
        
        <!-- 通知 -->
        <t-badge :count="5" :offset="[-6, 6]">
          <t-button theme="default" variant="text" shape="circle" class="header-icon-btn" @click="$router.push('/notifications')">
            <template #icon><t-icon name="notification" /></template>
          </t-button>
        </t-badge>
        
        <!-- 设置 -->
        <t-button theme="default" variant="text" shape="circle" class="header-icon-btn" @click="$router.push('/profile')">
          <template #icon><t-icon name="setting" /></template>
        </t-button>
        
        <!-- 用户菜单 -->
        <t-dropdown :options="userMenuOptions" @click="handleUserMenu">
          <div class="user-menu">
            <t-avatar size="32px">{{ userStore.avatarText }}</t-avatar>
            <span class="user-name">{{ userStore.user.name }}</span>
            <t-icon name="chevron-down" size="16px" />
          </div>
        </t-dropdown>
      </div>
    </header>
    
    <!-- 模拟交易横幅 -->
    <div v-if="isPaperTrading" class="paper-trading-banner">
      <t-icon name="info-circle" />
      <span>当前处于<strong>模拟交易模式</strong>，使用虚拟资金进行交易练习，不会产生真实订单</span>
      <span class="banner-balance">虚拟余额: <strong>{{ formatMoney(userStore.virtualAccount.balance) }} USDT</strong></span>
      <t-button size="small" theme="warning" variant="outline" @click="$router.push('/virtual-account')">
        管理账户
      </t-button>
    </div>
    
    <!-- 主内容区 -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { useUserStore } from '@/stores/user'
import { 
  UserIcon, 
  ChatIcon, 
  MailIcon, 
  ChartPieIcon, 
  StarIcon, 
  NotificationIcon, 
  WalletIcon, 
  PoweroffIcon 
} from 'tdesign-icons-vue-next'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 当前导航
const activeNav = computed(() => {
  const path = route.path
  if (path.includes('trading') || path.includes('contract')) return 'trading'
  if (path.includes('strategy')) return 'strategy'
  if (path.includes('my-strategy')) return 'my-strategy'
  if (path.includes('risk')) return 'risk'
  return 'trading'
})

// 模拟交易模式
const isPaperTrading = computed(() => userStore.isPaperTrading)

// 切换模式
const toggleMode = () => {
  const newMode = userStore.toggleTradeMode()
  MessagePlugin.info(newMode ? '已切换到模拟交易模式' : '已切换到实盘交易模式')
}

// 用户菜单选项
const userMenuOptions = [
  { content: '个人中心', value: 'profile', prefixIcon: () => h(UserIcon) },
  { content: '社区资讯', value: 'community', prefixIcon: () => h(ChatIcon) },
  { content: '消息中心', value: 'notifications', prefixIcon: () => h(MailIcon) },
  { content: '市场总览', value: 'market', prefixIcon: () => h(ChartPieIcon) },
  { content: '自选管理', value: 'watchlist', prefixIcon: () => h(StarIcon) },
  { content: '价格预警', value: 'alert', prefixIcon: () => h(NotificationIcon) },
  { content: '虚拟账户', value: 'virtual-account', prefixIcon: () => h(WalletIcon) },
  { divider: true },
  { content: '退出登录', value: 'logout', prefixIcon: () => h(PoweroffIcon), theme: 'error' }
]

// 处理导航切换
const handleNavChange = (value) => {
  router.push(`/${value}`)
}

// 处理用户菜单
const handleUserMenu = (data) => {
  if (data.value === 'logout') {
    userStore.logout()
    router.push('/login')
    MessagePlugin.success('已退出登录')
  } else {
    router.push(`/${data.value}`)
  }
}

// 格式化金额
const formatMoney = (value) => {
  return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<style lang="less" scoped>
.main-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #1a1a2e;
  padding: 0 24px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 32px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  font-weight: bold;
  color: var(--brand);
  cursor: pointer;
  
  &:hover {
    opacity: 0.9;
  }
}

.nav-menu {
  :deep(.t-menu) {
    background: transparent;
    border: none;
    
    .t-menu__item {
      color: rgba(255, 255, 255, 0.7);
      
      &:hover {
        color: #fff;
      }
      
      &.t-is-active {
        color: #fff;
        background: transparent;
        
        &::after {
          background-color: var(--brand);
        }
      }
    }
  }
}

.header-right {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
  
  // 修复按钮在深色背景下的可见性
  :deep(.t-button) {
    color: rgba(255, 255, 255, 0.85);
    
    &:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.1);
    }
  }
  
  // 通知和设置按钮容器
  :deep(.t-badge) {
    display: inline-flex;
    
    .t-button {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.15);
      
      &:hover {
        background: rgba(255, 255, 255, 0.15);
        border-color: rgba(255, 255, 255, 0.25);
      }
    }
  }
}

// 顶部图标按钮样式
.header-icon-btn {
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  color: rgba(255, 255, 255, 0.85) !important;
  
  &:hover {
    background: rgba(255, 255, 255, 0.15) !important;
    border-color: rgba(255, 255, 255, 0.25) !important;
    color: #fff !important;
  }
}

// 交易模式切换器
.trade-mode-switch {
  display: flex;
  align-items: center;
  position: relative;
  background: #30363d;
  border-radius: 20px;
  padding: 4px;
  cursor: pointer;
  
  .mode-indicator {
    position: absolute;
    width: 50%;
    height: calc(100% - 8px);
    background: var(--brand);
    border-radius: 16px;
    transition: transform 0.3s ease;
    left: 4px;
  }
  
  .mode-label {
    padding: 6px 16px;
    font-size: 13px;
    z-index: 1;
    transition: color 0.3s;
    
    &.live {
      color: #fff;
    }
    
    &.paper {
      color: rgba(255, 255, 255, 0.5);
    }
  }
  
  &.paper {
    .mode-indicator {
      transform: translateX(100%);
      background: var(--paper);
    }
    
    .mode-label.live {
      color: rgba(255, 255, 255, 0.5);
    }
    
    .mode-label.paper {
      color: #fff;
    }
  }
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 20px;
  cursor: pointer;
  color: #fff;
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .user-name {
    font-size: 14px;
  }
}

// 模拟交易横幅
.paper-trading-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: linear-gradient(90deg, rgba(255, 152, 0, 0.15), rgba(255, 152, 0, 0.05));
  border-bottom: 1px solid rgba(255, 152, 0, 0.3);
  color: var(--paper);
  font-size: 14px;
  
  .banner-balance {
    margin-left: auto;
    margin-right: 16px;
  }
}

.main-content {
  flex: 1;
}

// 路由过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
