<template>
  <div class="pt-24 pb-16">
    <div class="page-container">
      <!-- Header -->
      <div class="mb-10">
        <div class="flex items-center gap-4 mb-4">
          <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center">
            <UserIcon :size="32" class="text-primary-400" />
          </div>
          <div>
            <h1 class="text-2xl md:text-3xl font-extrabold text-white">账户管理</h1>
            <p class="text-dark-100">管理您的策略、信号跟单与API设置</p>
          </div>
        </div>
      </div>

      <!-- Stats Overview -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        <div v-for="stat in overviewStats" :key="stat.label" class="glass-card p-5">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-9 h-9 rounded-lg flex items-center justify-center" :class="stat.iconBg">
              <component :is="stat.icon" :size="18" :class="stat.iconColor" />
            </div>
            <span class="text-sm text-dark-100">{{ stat.label }}</span>
          </div>
          <div class="text-2xl font-bold" :class="stat.valueColor || 'text-white'">{{ stat.value }}</div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="glass-card p-1.5 mb-8 inline-flex gap-1">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          @click="activeTab = tab.value"
          class="px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
          :class="activeTab === tab.value ? 'bg-primary-500/15 text-primary-400' : 'text-dark-100 hover:text-white hover:bg-white/[0.04]'"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- My Strategies -->
      <div v-if="activeTab === 'strategies'" class="space-y-4">
        <div class="flex items-center gap-3 mb-4">
          <button
            v-for="status in ['all', 'running', 'ended'] as const"
            :key="status"
            @click="strategyFilter = status"
            class="text-sm px-3 py-1.5 rounded-lg transition-all"
            :class="strategyFilter === status ? 'bg-primary-500/10 text-primary-400' : 'text-dark-100 hover:text-white'"
          >
            {{ status === 'all' ? '全部' : status === 'running' ? '运行中' : '已结束' }}
          </button>
        </div>
        <div
          v-for="item in filteredUserStrategies" 
          :key="item.id"
          class="glass-card-hover p-6 flex items-center gap-6 cursor-pointer"
          @click="$router.push(`/system/running-strategies/${item.id}`)"
        >
          <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center shrink-0">
            <Zap :size="18" class="text-primary-400" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <h4 class="text-white font-semibold text-sm">{{ item.name }}</h4>
              <StatusDot :status="item.status" />
            </div>
            <div class="flex items-center gap-4 text-xs text-dark-100">
              <span>启动: {{ item.startTime }}</span>
              <span v-if="item.endTime">结束: {{ item.endTime }}</span>
            </div>
          </div>
          <div class="text-right">
            <div class="text-lg font-bold" :class="item.totalReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
              {{ item.totalReturn >= 0 ? '+' : '' }}{{ item.totalReturn.toFixed(2) }}%
            </div>
            <div class="text-xs text-dark-100">总收益</div>
          </div>
          <ChevronRight :size="16" class="text-dark-200 shrink-0" />
        </div>
        <div v-if="filteredUserStrategies.length === 0" class="text-center py-12 text-dark-100">
          暂无策略记录
        </div>
      </div>

      <!-- My Signals -->
      <div v-if="activeTab === 'signals'" class="space-y-4">
        <div class="flex items-center gap-3 mb-4">
          <button
            v-for="status in ['all', 'following', 'stopped'] as const"
            :key="status"
            @click="signalFilter = status"
            class="text-sm px-3 py-1.5 rounded-lg transition-all"
            :class="signalFilter === status ? 'bg-primary-500/10 text-primary-400' : 'text-dark-100 hover:text-white'"
          >
            {{ status === 'all' ? '全部' : status === 'following' ? '跟随中' : '已停止' }}
          </button>
        </div>
        <div
          v-for="item in filteredUserSignals"
          :key="item.id"
          class="glass-card-hover p-6 flex items-center gap-6 cursor-pointer"
          @click="$router.push(`/system/user/signal-follow/${item.id}`)"
        >
          <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-blue/20 to-accent-purple/20 flex items-center justify-center shrink-0">
            <Radio :size="18" class="text-blue-400" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <h4 class="text-white font-semibold text-sm">{{ item.signalName }}</h4>
              <StatusDot :status="item.status" />
            </div>
            <div class="flex items-center gap-4 text-xs text-dark-100">
              <span>跟单资金: {{ item.followAmount.toLocaleString() }} USDT</span>
              <span>比例: {{ (item.followRatio * 100).toFixed(0) }}%</span>
              <span v-if="item.exchange" class="text-xs px-1.5 py-0.5 rounded bg-dark-600 text-dark-200">{{ item.exchange }}</span>
            </div>
          </div>
          <div class="text-right">
            <div class="text-lg font-bold" :class="item.totalReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
              {{ item.totalReturn >= 0 ? '+' : '' }}{{ item.totalReturn.toFixed(2) }}%
            </div>
            <div class="text-xs text-dark-100">总收益</div>
          </div>
          <ChevronRight :size="16" class="text-dark-200 shrink-0" />
        </div>
        <!-- 加载中状态 -->
        <div v-if="signalLoading" class="text-center py-12">
          <Loader2 :size="24" class="text-primary-400 animate-spin mx-auto mb-2" />
          <span class="text-dark-100 text-sm">加载中...</span>
        </div>
        <div v-else-if="filteredUserSignals.length === 0" class="text-center py-12 text-dark-100">
          暂无跟单记录
        </div>
      </div>

      <!-- Profit Stats -->
      <div v-if="activeTab === 'profit'" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="glass-card p-6 text-center">
            <div class="text-3xl font-bold text-emerald-400">+24.56%</div>
            <div class="text-sm text-dark-100 mt-1">总收益率</div>
          </div>
          <div class="glass-card p-6 text-center">
            <div class="text-3xl font-bold text-white">$2,456.78</div>
            <div class="text-sm text-dark-100 mt-1">总收益 (USDT)</div>
          </div>
          <div class="glass-card p-6 text-center">
            <div class="text-3xl font-bold text-amber-400">8.32%</div>
            <div class="text-sm text-dark-100 mt-1">最大回撤</div>
          </div>
        </div>
        <div class="glass-card p-6">
          <h3 class="text-white font-bold mb-4">收益曲线</h3>
          <ReturnCurveChart :data="profitCurve" :labels="profitLabels" :height="300" color="#10b981" />
        </div>
      </div>

      <!-- API Management -->
      <div v-if="activeTab === 'api'" class="space-y-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-white font-bold">API 密钥管理</h3>
          <button class="btn-primary !py-2 !px-4 text-sm flex items-center gap-1.5" @click="showAddForm = !showAddForm">
            <Plus :size="14" /> {{ showAddForm ? '取消添加' : '添加密钥' }}
          </button>
        </div>
        
        <!-- Add API Key Form -->
        <div v-if="showAddForm" class="glass-card p-6 mb-6">
          <h4 class="text-white font-semibold mb-4">添加API密钥</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-sm text-dark-100 mb-2">交易所</label>
              <select v-model="formData.exchange_id" class="w-full bg-dark-600 border border-dark-500 rounded-lg px-3 py-2 text-white text-sm focus:border-primary-500 focus:outline-none">
                <option value="">选择交易所</option>
                <option value="1">Binance</option>
                <option value="2">OKX</option>
                <option value="3">Huobi</option>
              </select>
            </div>
            <div>
              <label class="block text-sm text-dark-100 mb-2">标签</label>
              <input v-model="formData.label" type="text" placeholder="请输入密钥标签" class="w-full bg-dark-600 border border-dark-500 rounded-lg px-3 py-2 text-white text-sm placeholder-dark-300 focus:border-primary-500 focus:outline-none">
            </div>
            <div class="md:col-span-2">
              <label class="block text-sm text-dark-100 mb-2">API Key</label>
              <input v-model="formData.api_key" type="text" placeholder="请输入API Key" class="w-full bg-dark-600 border border-dark-500 rounded-lg px-3 py-2 text-white text-sm placeholder-dark-300 focus:border-primary-500 focus:outline-none">
            </div>
            <div class="md:col-span-2">
              <label class="block text-sm text-dark-100 mb-2">Secret Key</label>
              <input v-model="formData.secret_key" type="password" placeholder="请输入Secret Key" class="w-full bg-dark-600 border border-dark-500 rounded-lg px-3 py-2 text-white text-sm placeholder-dark-300 focus:border-primary-500 focus:outline-none">
            </div>
            <div class="md:col-span-2">
              <label class="block text-sm text-dark-100 mb-2">密码短语（部分交易所需要）</label>
              <input v-model="formData.passphrase" type="password" placeholder="请输入密码短语" class="w-full bg-dark-600 border border-dark-500 rounded-lg px-3 py-2 text-white text-sm placeholder-dark-300 focus:border-primary-500 focus:outline-none">
            </div>
            <div class="md:col-span-2">
              <label class="block text-sm text-dark-100 mb-2">权限设置</label>
              <div class="flex flex-wrap gap-2">
                <label class="flex items-center gap-2 text-sm text-dark-100">
                  <input type="checkbox" v-model="formData.permissions" value="trade" class="rounded border-dark-500 bg-dark-600">
                  交易权限
                </label>
                <label class="flex items-center gap-2 text-sm text-dark-100">
                  <input type="checkbox" v-model="formData.permissions" value="read" class="rounded border-dark-500 bg-dark-600">
                  读取权限
                </label>
                <label class="flex items-center gap-2 text-sm text-dark-100">
                  <input type="checkbox" v-model="formData.permissions" value="withdraw" class="rounded border-dark-500 bg-dark-600">
                  提现权限
                </label>
              </div>
            </div>
          </div>
          <div class="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4 mb-4">
            <div class="flex items-start gap-3">
              <AlertTriangle :size="16" class="text-amber-400 mt-0.5 shrink-0" />
              <div class="text-sm">
                <p class="text-amber-400 font-medium mb-1">安全提示</p>
                <p class="text-amber-300">API密钥需要经过后台审核才能用于交易。请确保密钥权限设置正确，仅开启必要的交易权限。</p>
              </div>
            </div>
          </div>
          <button class="btn-primary w-full" :disabled="formLoading" @click="handleAddApiKey">
            <Loader2 v-if="formLoading" :size="16" class="text-white animate-spin mr-2" />
            提交审核
          </button>
        </div>

        <!-- API Keys List -->
        <div v-if="apiLoading" class="text-center py-12">
          <Loader2 :size="24" class="text-primary-400 animate-spin mx-auto mb-2" />
          <span class="text-dark-100 text-sm">加载中...</span>
        </div>
        <div v-else>
          <div
            v-for="key in apiKeys"
            :key="key.id"
            class="glass-card p-6 flex items-center gap-6 mb-4"
          >
            <div class="w-10 h-10 rounded-lg bg-dark-600 flex items-center justify-center shrink-0">
              <Key :size="18" class="text-primary-400" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <h4 class="text-white font-semibold text-sm">{{ key.label }}</h4>
                <span class="text-xs px-2 py-0.5 rounded bg-dark-600 text-dark-100">{{ key.exchange_id }}</span>
                <span
                  class="text-xs px-2 py-0.5 rounded font-medium"
                  :class="getReviewStatusClass(key.status)"
                >
                  {{ getReviewStatusText(key.status) }}
                </span>
              </div>
              <div class="text-xs text-dark-200 font-mono">{{ maskApiKey(key.api_key) }}</div>
              <div v-if="key.status !== 'pending' && key.review_reason" class="text-xs text-dark-100 mt-1">
                审核原因: {{ key.review_reason }}
              </div>
            </div>
            <div class="flex items-center gap-2">
              <StatusDot :status="key.status" />
              <button class="p-2 rounded-lg text-dark-100 hover:text-red-400 hover:bg-red-500/10 transition-all" @click="handleDeleteApiKey(key.id)">
                <Trash2 :size="14" />
              </button>
            </div>
          </div>
          <div v-if="apiKeys.length === 0" class="text-center py-12 text-dark-100">
            暂未绑定 API 密钥
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { User, Zap, Radio, ChevronRight, Plus, Key, Trash2, Edit, Eye, EyeOff, CheckCircle, XCircle, Clock, Settings, Bell, Shield, CreditCard, BarChart3, Users, Activity, TrendingUp, Star, HelpCircle, Mail, Phone, MapPin, Globe, Calendar, Download, Upload, Filter, Search, Menu, X, ChevronDown, ChevronUp, ArrowLeft, ArrowRight, Home, LogOut, User as UserIcon, Wallet } from 'lucide-vue-next'
import { MessagePlugin } from 'tdesign-vue-next'
import { useAuthStore } from '@/stores/auth'
import { getApiKeys, addApiKey, updateApiKey, deleteApiKey, getApiKeyById } from '@/utils/userApi'
import type { APIKeyResponse, CreateAPIKeyRequest, UpdateAPIKeyRequest } from '@/types/api/user'
import type { FollowListItem } from '@/types/api/signal'
import { getFollowList } from '@/utils/signalApi'

const authStore = useAuthStore()
const route = useRoute()
const activeTab = ref('strategies')
const strategyFilter = ref('all')
const signalFilter = ref('all')

// API密钥管理相关状态
const apiKeys = ref<APIKeyResponse[]>([])
const apiLoading = ref(false)
const showAddForm = ref(false)
const formData = reactive({
  exchange_id: '',
  label: '',
  api_key: '',
  secret_key: '',
  passphrase: '',
  permissions: {
    spot_trading: false,
    margin_trading: false,
    futures_trading: false,
    withdraw: false
  }
})
const formLoading = ref(false)

// 收益统计相关数据
const profitCurve = ref<number[]>(Array.from({ length: 60 }, (_, i) => {
  return parseFloat((Math.sin(i / 10) * 5 + i * 0.4 + (Math.random() - 0.3) * 3).toFixed(2))
}))

const profitLabels = ref<string[]>(Array.from({ length: 60 }, (_, i) => {
  const date = new Date()
  date.setDate(date.getDate() - (59 - i))
  return date.toISOString().split('T')[0]
}))

// 根据URL参数设置默认标签页
if (route.query.tab === 'strategies') {
  activeTab.value = 'strategies'
}

const tabs = [
  { label: '我的策略', value: 'strategies' },
  { label: '信号跟单', value: 'signals' },
  { label: '收益统计', value: 'profit' },
  { label: 'API管理', value: 'api' },
]

const overviewStats = [
  { label: '运行策略', value: '3', icon: Zap, iconBg: 'bg-primary-500/10', iconColor: 'text-primary-400' },
  { label: '跟单信号', value: '5', icon: Radio, iconBg: 'bg-blue-500/10', iconColor: 'text-blue-400' },
  { label: '总收益率', value: '+24.56%', icon: TrendingUp, iconBg: 'bg-emerald-500/10', iconColor: 'text-emerald-400', valueColor: 'text-emerald-400' },
  { label: '总资产', value: '$12,456', icon: Wallet, iconBg: 'bg-amber-500/10', iconColor: 'text-amber-400' },
]

const userStrategies = [
  { id: '1', name: '网格交易 BTC #1', status: 'running', startTime: '2025-11-01', endTime: null, totalReturn: 12.45 },
  { id: '2', name: '趋势跟踪 ETH #3', status: 'running', startTime: '2025-10-15', endTime: null, totalReturn: 8.32 },
  { id: '3', name: '均值回归 SOL #2', status: 'ended', startTime: '2025-08-01', endTime: '2025-10-01', totalReturn: -3.21 },
  { id: '4', name: '动量突破 BNB #5', status: 'running', startTime: '2025-12-01', endTime: null, totalReturn: 5.67 },
]

// ==================== 信号跟单列表（对接 GET /api/v1/c/follows/list） ====================
const userSignals = ref<FollowListItem[]>([])
const signalLoading = ref(false)
const signalTotal = ref(0)
const signalPage = ref(1)
const signalPageSize = 20

/** 获取跟单列表 */
async function fetchFollowList() {
  signalLoading.value = true
  try {
    const statusParam = signalFilter.value === 'all' ? undefined : signalFilter.value as 'following' | 'stopped'
    const res = await getFollowList({
      page: signalPage.value,
      pageSize: signalPageSize,
      status: statusParam,
    })
    userSignals.value = res.records || []
    signalTotal.value = res.total || 0
  } catch (e) {
    console.error('获取跟单列表失败', e)
    userSignals.value = []
  } finally {
    signalLoading.value = false
  }
}

// ==================== API密钥管理 ====================

/** 获取API密钥列表 */
async function fetchApiKeys() {
  apiLoading.value = true
  try {
    const response = await getApiKeys()
    apiKeys.value = response.items || []
  } catch (e) {
    console.error('获取API密钥列表失败', e)
    apiKeys.value = []
  } finally {
    apiLoading.value = false
  }
}

/** 添加API密钥 */
async function handleAddApiKey() {
  formLoading.value = true
  try {
    const request: CreateAPIKeyRequest = {
      exchange_id: formData.exchange_id,
      label: formData.label,
      api_key: formData.api_key,
      secret_key: formData.secret_key,
      passphrase: formData.passphrase || undefined,
      permissions: Object.values(formData.permissions).some(v => v) ? formData.permissions : undefined
    }
    
    await addApiKey(request)
    
    // 重置表单
    Object.assign(formData, {
      exchange_id: '',
      label: '',
      api_key: '',
      secret_key: '',
      passphrase: '',
      permissions: {
        spot_trading: false,
        margin_trading: false,
        futures_trading: false,
        withdraw: false
      }
    })
    showAddForm.value = false
    
    // 重新获取列表
    await fetchApiKeys()
  } catch (e) {
    console.error('添加API密钥失败', e)
  } finally {
    formLoading.value = false
  }
}

/** 删除API密钥 */
async function handleDeleteApiKey(keyId: string) {
  if (!confirm('确定要删除这个API密钥吗？此操作不可撤销。')) {
    return
  }
  
  try {
    await deleteApiKey(keyId)
    MessagePlugin.success('API密钥删除成功')
    await fetchApiKeys()
  } catch (error) {
    console.error('删除API密钥失败', error)
    MessagePlugin.error('删除失败，请重试')
  }
}

// 筛选状态变化时重新请求（因为接口支持 status 筛选，直接走接口过滤）
watch(signalFilter, () => {
  signalPage.value = 1
  fetchFollowList()
})

// 监听API标签页激活，自动加载数据
watch(activeTab, (newTab) => {
  if (newTab === 'api') {
    fetchApiKeys()
  }
})

const filteredUserStrategies = computed(() => {
  if (strategyFilter.value === 'all') return userStrategies
  return userStrategies.filter((s) => s.status === strategyFilter.value)
})

// 跟单列表已由接口按 status 筛选，直接使用
const filteredUserSignals = computed(() => userSignals.value)

const getReviewStatusClass = (status: string) => {
  switch (status) {
    case 'pending': return 'bg-amber-500/20 text-amber-400'
    case 'approved': return 'bg-emerald-500/20 text-emerald-400'
    case 'rejected': return 'bg-red-500/20 text-red-400'
    default: return 'bg-dark-600 text-dark-100'
  }
}

const getReviewStatusText = (status: string) => {
  switch (status) {
    case 'pending': return '审核中'
    case 'approved': return '已通过'
    case 'rejected': return '已拒绝'
    default: return status
  }
}

const maskApiKey = (key: string) => {
  if (key.length <= 8) return key
  return key.substring(0, 6) + '*'.repeat(key.length - 10) + key.substring(key.length - 4)
}

// Initialize data
onMounted(async () => {
  await fetchFollowList()
})
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
}

.glass-card-hover {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  transition: all 0.2s;
}

.glass-card-hover:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #2563eb, #1e40af);
  transform: translateY(-1px);
}
</style>