import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { title: '注册' }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/auth/ForgotPassword.vue'),
    meta: { title: '忘记密码' }
  },
  {
    path: '/',
    component: () => import('@/components/layout/MainLayout.vue'),
    children: [
      {
        path: 'trading',
        name: 'Trading',
        component: () => import('@/views/trading/TradingView.vue'),
        meta: { title: '交易' }
      },
      {
        path: 'contract',
        name: 'Contract',
        component: () => import('@/views/trading/ContractView.vue'),
        meta: { title: '合约交易' }
      },
      {
        path: 'strategy',
        name: 'Strategy',
        component: () => import('@/views/strategy/StrategySquare.vue'),
        meta: { title: '策略广场' }
      },
      {
        path: 'strategy/:id',
        name: 'StrategyDetail',
        component: () => import('@/views/strategy/StrategyDetail.vue'),
        meta: { title: '策略详情' }
      },
      {
        path: 'my-strategy',
        name: 'MyStrategy',
        component: () => import('@/views/strategy/MyStrategy.vue'),
        meta: { title: '我的策略' }
      },
      {
        path: 'backtest',
        name: 'Backtest',
        component: () => import('@/views/backtest/BacktestConfig.vue'),
        meta: { title: '回测配置' }
      },
      {
        path: 'backtest-result',
        name: 'BacktestResult',
        component: () => import('@/views/backtest/BacktestResult.vue'),
        meta: { title: '回测结果' }
      },
      {
        path: 'live-config',
        name: 'LiveConfig',
        component: () => import('@/views/live/LiveConfig.vue'),
        meta: { title: '实盘配置' }
      },
      {
        path: 'live-monitor',
        name: 'LiveMonitor',
        component: () => import('@/views/live/LiveMonitor.vue'),
        meta: { title: '实盘监控' }
      },
      {
        path: 'risk',
        name: 'Risk',
        component: () => import('@/views/risk/RiskCenter.vue'),
        meta: { title: '风控中心' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/ProfileView.vue'),
        meta: { title: '个人中心' }
      },
      {
        path: 'virtual-account',
        name: 'VirtualAccount',
        component: () => import('@/views/paper/VirtualAccount.vue'),
        meta: { title: '虚拟账户' }
      },
      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('@/views/notification/NotificationView.vue'),
        meta: { title: '消息中心' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'CryptoQuant'} - 加密货币量化交易平台`
  next()
})

export default router
