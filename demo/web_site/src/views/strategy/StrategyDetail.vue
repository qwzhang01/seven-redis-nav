<template>
  <div class="pt-24 pb-16">
    <div class="page-container" v-if="strategy">
      <!-- Breadcrumb -->
      <div class="flex items-center gap-2 text-sm text-dark-100 mb-8">
        <router-link to="/system/strategies" class="hover:text-primary-500 transition-colors">系统策略</router-link>
        <ChevronRight :size="14" />
        <span class="text-white">{{ strategy.name }}</span>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Main Content -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Strategy Header -->
          <div class="glass-card p-8">
            <div class="flex items-start justify-between mb-6">
              <div class="flex items-center gap-4">
                <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center">
                  <Zap :size="28" class="text-primary-400" />
                </div>
                <div>
                  <h1 class="text-2xl font-bold text-white">{{ strategy.name }}</h1>
                  <div class="flex items-center gap-3 mt-1.5">
                    <span class="text-sm text-dark-100">{{ strategy.market }}</span>
                    <span class="text-dark-300">·</span>
                    <span class="text-sm text-dark-100">{{ strategy.type }}</span>
                    <RiskBadge :level="strategy.riskLevel" />
                  </div>
                </div>
              </div>
              <StatusDot :status="strategy.status" />
            </div>
            <div class="grid grid-cols-3 gap-4">
              <div class="p-4 rounded-xl bg-dark-800/50 text-center">
                <div class="text-2xl font-bold" :class="strategy.returnRate >= 0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ strategy.returnRate >= 0 ? '+' : '' }}{{ strategy.returnRate }}%
                </div>
                <div class="text-xs text-dark-100 mt-1">累计收益率</div>
              </div>
              <div class="p-4 rounded-xl bg-dark-800/50 text-center">
                <div class="text-2xl font-bold text-amber-400">{{ strategy.maxDrawdown }}%</div>
                <div class="text-xs text-dark-100 mt-1">最大回撤</div>
              </div>
              <div class="p-4 rounded-xl bg-dark-800/50 text-center">
                <div class="text-2xl font-bold text-white">{{ strategy.runDays }}天</div>
                <div class="text-xs text-dark-100 mt-1">运行天数</div>
              </div>
            </div>
            <!-- 新增交易所和交易对信息 -->
            <div class="mt-6 pt-6 border-t border-dark-700">
              <div class="grid grid-cols-2 gap-4">
                <div class="flex items-center gap-3">
                  <Building :size="16" class="text-dark-200" />
                  <div>
                    <div class="text-xs text-dark-200">交易所</div>
                    <div class="text-sm text-white">{{ strategy.exchange }}</div>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <TrendingUp :size="16" class="text-dark-200" />
                  <div>
                    <div class="text-xs text-dark-200">交易对</div>
                    <div class="text-sm text-white">{{ strategy.tradingPair }}</div>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <Clock :size="16" class="text-dark-200" />
                  <div>
                    <div class="text-xs text-dark-200">时间周期</div>
                    <div class="text-sm text-white">{{ strategy.timeframe }}</div>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <DollarSign :size="16" class="text-dark-200" />
                  <div>
                    <div class="text-xs text-dark-200">初始资金</div>
                    <div class="text-sm text-white">{{ strategy.capitalAllocation.initialCapital }} USDT</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Strategy Description -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <BookOpen :size="18" class="text-primary-400" />
              策略介绍
            </h2>
            <p class="text-dark-100 leading-relaxed">{{ strategy.description }}</p>
          </div>

          <!-- Strategy Logic -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Brain :size="18" class="text-primary-400" />
              策略逻辑
            </h2>
            <p class="text-dark-100 leading-relaxed">{{ strategy.logic }}</p>
          </div>

          <!-- Parameters -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Settings :size="18" class="text-primary-400" />
              参数说明
            </h2>
            <div class="space-y-4">
              <div v-for="param in strategy.params" :key="param.name" class="p-4 rounded-xl bg-dark-800/50">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-white font-medium text-sm">{{ param.label }}</span>
                  <span class="text-xs text-dark-100">默认值: {{ param.default }}</span>
                </div>
                <p class="text-xs text-dark-100">{{ param.description }}</p>
              </div>
            </div>
          </div>

          <!-- Risk Management -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Shield :size="18" class="text-amber-400" />
              风险管理
            </h2>
            <div class="grid grid-cols-2 gap-4">
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">止损比例</div>
                <div class="text-white font-medium">{{ strategy.riskManagement.stopLoss }}%</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">止盈比例</div>
                <div class="text-white font-medium">{{ strategy.riskManagement.takeProfit }}%</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">移动止损</div>
                <div class="text-white font-medium">{{ strategy.riskManagement.trailingStop ? '启用' : '禁用' }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">最大并发交易</div>
                <div class="text-white font-medium">{{ strategy.riskManagement.maxConcurrentTrades }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">日亏损限制</div>
                <div class="text-white font-medium">{{ strategy.riskManagement.dailyLossLimit }}%</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">周亏损限制</div>
                <div class="text-white font-medium">{{ strategy.riskManagement.weeklyLossLimit }}%</div>
              </div>
            </div>
          </div>

          <!-- Advanced Settings -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Cog :size="18" class="text-primary-400" />
              高级设置
            </h2>
            <div class="grid grid-cols-2 gap-4">
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">滑点容忍度</div>
                <div class="text-white font-medium">{{ strategy.advancedSettings.slippageTolerance }}%</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">手续费率</div>
                <div class="text-white font-medium">{{ strategy.advancedSettings.commissionRate }}%</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">市价单</div>
                <div class="text-white font-medium">{{ strategy.advancedSettings.useMarketOrders ? '是' : '否' }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">允许做空</div>
                <div class="text-white font-medium">{{ strategy.advancedSettings.allowShortSelling ? '是' : '否' }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">对冲功能</div>
                <div class="text-white font-medium">{{ strategy.advancedSettings.enableHedging ? '启用' : '禁用' }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">回测周期</div>
                <div class="text-white font-medium">{{ strategy.advancedSettings.backtestPeriod }}天</div>
              </div>
            </div>
          </div>

          <!-- Risk Warning -->
          <div class="glass-card p-8 border-amber-500/20">
            <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <AlertTriangle :size="18" class="text-amber-400" />
              风险提示
            </h2>
            <p class="text-dark-100 leading-relaxed">{{ strategy.riskTip }}</p>
          </div>
        </div>

        <!-- Sidebar: Config Panel -->
        <div class="space-y-6">
          <div class="glass-card p-6 sticky top-24">
            <h3 class="text-lg font-bold text-white mb-6">启动策略</h3>
            <div class="space-y-5">
              <div v-for="param in strategy.params" :key="param.name">
                <label class="text-sm text-dark-100 mb-1.5 block">{{ param.label }}</label>
                <t-select
                  v-if="param.type === 'select'"
                  v-model="configValues[param.name]"
                  size="medium"
                >
                  <t-option v-for="opt in param.options" :key="opt" :label="opt" :value="opt" />
                </t-select>
                <t-input
                  v-else
                  v-model="configValues[param.name]"
                  :type="param.type === 'number' ? 'number' : 'text'"
                  size="medium"
                />
              </div>
            </div>
            <button
              class="btn-primary w-full mt-6 !py-3 text-base rounded-xl flex items-center justify-center gap-2"
              :disabled="launching"
              @click="handleLaunch"
            >
              <Play :size="18" />
              {{ launching ? '启动中...' : '启动策略' }}
            </button>
            <p class="text-xs text-dark-200 text-center mt-3">启动前请确认参数配置并了解相关风险</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Not Found -->
    <div v-else class="page-container pt-24 text-center py-20">
      <p class="text-dark-100 text-lg">策略不存在</p>
      <router-link to="/system/strategies" class="btn-outline mt-4 inline-block">返回策略列表</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Zap, ChevronRight, BookOpen, Brain, Settings, AlertTriangle, Play, Building, TrendingUp, Clock, DollarSign, Shield, Cog } from 'lucide-vue-next'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'
import RiskBadge from '@/components/common/RiskBadge.vue'
import StatusDot from '@/components/common/StatusDot.vue'
import { useAuthStore } from '@/stores/auth'
import { strategies } from '@/utils/mockData'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const launching = ref(false)

const strategy = computed(() => strategies.find((s) => s.id === route.params.id))

const configValues = ref<Record<string, string | number>>({})

function initConfig() {
  const vals: Record<string, string | number> = {}
  strategy.value?.params?.forEach((p) => {
    vals[p.name] = p.default
  })
  configValues.value = vals
}

watch(() => route.params.id, initConfig, { immediate: true })

async function handleLaunch() {
  if (!authStore.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  const dlg = DialogPlugin.confirm({
    header: '确认启动策略',
    body: `即将启动「${strategy.value?.name}」，投入资金 ${configValues.value.investment || 1000} USDT。确认启动？`,
    theme: 'warning',
    confirmBtn: '确认启动',
    cancelBtn: '取消',
    onConfirm: async () => {
      dlg.hide()
      launching.value = true
      await new Promise((r) => setTimeout(r, 1200))
      launching.value = false
      MessagePlugin.success('策略已成功启动！可在「我的」页面查看运行状态。')
    },
    onCancel: () => dlg.hide(),
  })
}
</script>