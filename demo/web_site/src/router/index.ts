import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginPage.vue'),
    meta: { title: '登录', guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterPage.vue'),
    meta: { title: '注册', guest: true },
  },
  {
    path: '/',
    redirect: '/index'
  },
  {
    path: '/index',
    component: () => import('@/views/layout/AppLayout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/home/HomePage.vue'),
        meta: { title: '首页' },
      },
    ],
  },
  {
    path: '/system',
    component: () => import('@/views/layout/SystemLayout.vue'),
    children: [
      {
        path: 'trading',
        name: 'Trading',
        component: () => import('@/views/trading/TradingPage.vue'),
        meta: { title: '交易盘面' },
      },
      {
        path: 'running-strategies',
        name: 'RunningStrategies',
        component: () => import('@/views/trading/RunningStrategiesPage.vue'),
        meta: { title: '策略实盘监控' },
      },
      {
        path: 'strategies',
        name: 'StrategyList',
        component: () => import('@/views/strategy/StrategyList.vue'),
        meta: { title: '系统策略' },
      },
      {
        path: 'strategies/:id',
        name: 'StrategyDetail',
        component: () => import('@/views/strategy/StrategyDetail.vue'),
        meta: { title: '策略详情' },
      },
      {
        path: 'running-strategies/:id',
        name: 'RunningStrategyDetail',
        component: () => import('@/views/strategy/RunningStrategyDetail.vue'),
        meta: { title: '策略运行详情', requiresAuth: true },
      },
      {
        path: 'signals',
        name: 'SignalList',
        component: () => import('@/views/signal/SignalList.vue'),
        meta: { title: '信号广场' },
      },
      {
        path: 'signals/:id',
        name: 'SignalDetail',
        component: () => import('@/views/signal/SignalDetail.vue'),
        meta: { title: '信号详情' },
      },
      {
        path: 'leaderboard',
        name: 'Leaderboard',
        component: () => import('@/views/leaderboard/LeaderboardPage.vue'),
        meta: { title: '收益排行榜' },
      },
      {
        path: 'user',
        name: 'UserCenter',
        component: () => import('@/views/user/UserCenter.vue'),
        meta: { title: '我的', requiresAuth: true },
      },
      {
        path: 'user/signal-follow/:id',
        name: 'SignalFollowDetail',
        component: () => import('@/views/user/SignalFollowDetail.vue'),
        meta: { title: '跟单详情', requiresAuth: true },
      },
    ],
  },
  {
    path: '/admin',
    component: () => import('@/views/layout/AdminLayout.vue'),
    meta: { title: '管理后台', requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/AdminDashboard.vue'),
        meta: { title: '管理概览', requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'strategies',
        name: 'AdminStrategies',
        component: () => import('@/views/admin/AdminStrategies.vue'),
        meta: { title: '策略管理', requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'signals',
        name: 'AdminSignals',
        component: () => import('@/views/admin/AdminSignals.vue'),
        meta: { title: '信号接入', requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'leaderboard',
        name: 'AdminLeaderboard',
        component: () => import('@/views/admin/AdminLeaderboard.vue'),
        meta: { title: '排行榜配置', requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'logs',
        name: 'AdminLogs',
        component: () => import('@/views/admin/AdminLogs.vue'),
        meta: { title: '风控与日志', requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'api-keys',
        name: 'AdminApiKeys',
        component: () => import('@/views/admin/AdminApiKeys.vue'),
        meta: { title: 'API密钥审核', requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'data-subscription',
        name: 'AdminDataSubscription',
        component: () => import('@/views/admin/AdminDataSubscription.vue'),
        meta: { title: '实时数据订阅', requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/AdminUsers.vue'),
        meta: { title: '用户管理', requiresAuth: true, requiresAdmin: true },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '404' },
  },
  {
    path: '/trading',
    redirect: '/system/trading'
  },
  {
    path: '/strategies',
    redirect: '/system/strategies'
  },
  {
    path: '/strategies/:id',
    redirect: '/system/strategies/:id'
  },
  {
    path: '/signals',
    redirect: '/system/signals'
  },
  {
    path: '/signals/:id',
    redirect: '/system/signals/:id'
  },
  {
    path: '/leaderboard',
    redirect: '/system/leaderboard'
  },
  {
    path: '/running-strategies',
    redirect: '/system/running-strategies'
  },
  {
    path: '/running-strategies/:id',
    redirect: '/system/running-strategies/:id'
  },
  {
    path: '/user',
    redirect: '/system/user'
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition || { top: 0 }
  },
})

router.beforeEach((to, _from, next) => {
  const title = to.meta.title as string
  document.title = title ? `${title} - Quant Meta` : 'Quant Meta'

  const authStore = useAuthStore()

  if (to.meta.guest && authStore.isLoggedIn) {
    return next('/')
  }

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return next('/')
  }

  next()
})

export default router
