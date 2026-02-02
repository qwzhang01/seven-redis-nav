import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  // 用户信息
  const user = ref({
    id: null,
    name: '张三',
    email: '',
    avatar: ''
  })
  
  // 是否登录
  const isLoggedIn = ref(false)
  
  // 模拟交易模式
  const isPaperTrading = ref(false)
  
  // 虚拟账户数据
  const virtualAccount = ref({
    balance: 10000.00,
    initialBalance: 10000.00,
    positions: [],
    trades: [],
    totalPnL: 0
  })
  
  // 登录
  const login = (userData) => {
    user.value = { ...user.value, ...userData }
    isLoggedIn.value = true
  }
  
  // 登出
  const logout = () => {
    user.value = { id: null, name: '', email: '', avatar: '' }
    isLoggedIn.value = false
  }
  
  // 切换交易模式
  const toggleTradeMode = () => {
    isPaperTrading.value = !isPaperTrading.value
    return isPaperTrading.value
  }
  
  // 用户名首字
  const avatarText = computed(() => {
    return user.value.name ? user.value.name.charAt(0) : 'U'
  })
  
  // 重置虚拟账户
  const resetVirtualAccount = () => {
    virtualAccount.value = {
      balance: 10000.00,
      initialBalance: 10000.00,
      positions: [],
      trades: [],
      totalPnL: 0
    }
  }
  
  return {
    user,
    isLoggedIn,
    isPaperTrading,
    virtualAccount,
    avatarText,
    login,
    logout,
    toggleTradeMode,
    resetVirtualAccount
  }
})
