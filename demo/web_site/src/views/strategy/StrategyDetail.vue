<template>
  <div class="min-h-screen bg-dark-900">
    <!-- Loading State -->
    <div v-if="loading" class="min-h-screen flex items-center justify-center">
      <div class="text-center">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mb-4"></div>
        <p class="text-dark-100">加载中...</p>
      </div>
    </div>
    
    <div class="page-container max-w-none" v-else-if="strategy">
      <!-- Breadcrumb -->
      <div class="flex items-center gap-2 text-sm text-dark-100 mb-8 px-8 pt-8">
        <router-link to="/system/strategies" class="hover:text-primary-500 transition-colors">系统策略</router-link>
        <ChevronRight :size="14" />
        <span class="text-white">{{ strategy.name }}</span>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 px-8 pb-8">
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
            <div class="flex items-center justify-between mb-6">
              <h3 class="text-lg font-bold text-white">启动策略</h3>
              <button 
                @click="isSimpleMode = !isSimpleMode"
                class="text-sm text-primary-400 hover:text-primary-300 transition-colors"
              >
                {{ isSimpleMode ? '切换为专业版' : '切换为简易版' }}
              </button>
            </div>
            
            <!-- Simple Mode -->
            <div v-if="isSimpleMode" class="space-y-5">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="text-sm text-dark-100 mb-1.5 block">开仓平台</label>
                  <t-select v-model="configValues.platform" size="medium">
                    <t-option v-for="platform in ['WEEX', 'Binance', 'OKX', 'Bybit', 'Gate.io']" :key="platform" :label="platform" :value="platform" />
                  </t-select>
                </div>
                <div>
                  <label class="text-sm text-dark-100 mb-1.5 block">开仓币种</label>
                  <t-select v-model="configValues.currencyPair" size="medium">
                    <t-option v-for="pair in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']" :key="pair" :label="pair" :value="pair" />
                  </t-select>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="text-sm text-dark-100 mb-1.5 block">开仓杠杆</label>
                  <t-input
                    v-model="configValues.leverage"
                    type="number"
                    size="medium"
                    placeholder="125"
                  />
                </div>
                <div>
                  <label class="text-sm text-dark-100 mb-1.5 block">初始金额(USDT)</label>
                  <t-input
                    v-model="configValues.investment"
                    type="number"
                    size="medium"
                    placeholder="100"
                  />
                </div>
              </div>
            </div>
            
            <!-- Professional Mode -->
            <div v-else class="space-y-6">
              <!-- Tabs Navigation -->
              <div class="flex border-b border-dark-700">
                <button 
                  v-for="tab in tabs" 
                  :key="tab.id"
                  @click="activeTab = tab.id"
                  class="px-4 py-2 text-sm font-medium transition-colors relative"
                  :class="activeTab === tab.id 
                    ? 'text-primary-400 border-b-2 border-primary-400' 
                    : 'text-dark-100 hover:text-white'"
                >
                  {{ tab.label }}
                </button>
              </div>
              
              <!-- Tab Content -->
              <div class="space-y-5">
                <!-- Strategy Configuration -->
                <div v-if="activeTab === 'strategy'" class="space-y-4">
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="text-sm text-dark-100 mb-1.5 block">开仓平台</label>
                      <t-select v-model="configValues.platform" size="medium">
                        <t-option v-for="platform in ['WEEX', 'Binance', 'OKX', 'Bybit', 'Gate.io']" :key="platform" :label="platform" :value="platform" />
                      </t-select>
                    </div>
                    <div>
                      <label class="text-sm text-dark-100 mb-1.5 block">开仓币种</label>
                      <t-select v-model="configValues.currencyPair" size="medium">
                        <t-option v-for="pair in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']" :key="pair" :label="pair" :value="pair" />
                      </t-select>
                    </div>
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="text-sm text-dark-100 mb-1.5 block">开仓K线周期</label>
                      <t-select v-model="configValues.timeframe" size="medium">
                        <t-option v-for="tf in ['1分钟', '5分钟', '15分钟', '1小时', '4小时', '1天']" :key="tf" :label="tf" :value="tf" />
                      </t-select>
                    </div>
                    <div>
                      <label class="text-sm text-dark-100 mb-1.5 block">开仓杠杆</label>
                      <t-input
                        v-model="configValues.leverage"
                        type="number"
                        size="medium"
                        placeholder="125"
                      />
                    </div>
                  </div>
                  <div>
                    <label class="text-sm text-dark-100 mb-1.5 block">开仓模式</label>
                    <t-select v-model="configValues.tradeMode" size="medium">
                      <t-option v-for="mode in ['多空双开', '只做多', '只做空']" :key="mode" :label="mode" :value="mode" />
                    </t-select>
                  </div>
                </div>
                
                <!-- Position Control -->
                <div v-if="activeTab === 'position'" class="space-y-4">
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="text-sm text-dark-100 mb-1.5 block">开仓数量</label>
                      <t-input
                        v-model="configValues.positionSize"
                        type="number"
                        size="medium"
                        placeholder="1"
                      />
                    </div>
                    <div>
                      <label class="text-sm text-dark-100 mb-1.5 block">止盈(%)</label>
                      <t-input
                        v-model="configValues.takeProfit"
                        type="number"
                        size="medium"
                        placeholder="100"
                      />
                    </div>
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="text-sm text-dark-100 mb-1.5 block">止损(%)</label>
                      <t-input
                        v-model="configValues.stopLoss"
                        type="number"
                        size="medium"
                        placeholder="300"
                      />
                    </div>
                    <div>
                      <label class="text-sm text-dark-100 mb-1.5 block">止盈止损模式</label>
                      <t-select v-model="configValues.stopMode" size="medium">
                        <t-option v-for="mode in ['两者都可触发', '仅止盈', '仅止损']" :key="mode" :label="mode" :value="mode" />
                      </t-select>
                    </div>
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="text-sm text-dark-100 mb-1.5 block">最大持仓张数</label>
                      <t-input
                        v-model="configValues.maxPositions"
                        type="number"
                        size="medium"
                        placeholder="100"
                      />
                    </div>
                    <div>
                      <label class="text-sm text-dark-100 mb-1.5 block">最大订单限制</label>
                      <t-input
                        v-model="configValues.maxOrders"
                        type="number"
                        size="medium"
                        placeholder="0"
                      />
                    </div>
                  </div>
                </div>
                
                <!-- Advanced Settings -->
                <div v-if="activeTab === 'advanced'" class="space-y-4">
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="text-sm text-dark-100 mb-1.5 block">最大连续亏损次数</label>
                      <t-input
                        v-model="configValues.maxLossStreak"
                        type="number"
                        size="medium"
                        placeholder="0"
                      />
                    </div>
                    <div>
                      <label class="text-sm text-dark-100 mb-1.5 block">是否自动撤销订单</label>
                      <t-select v-model="configValues.autoCancel" size="medium">
                        <t-option v-for="opt in ['是', '否']" :key="opt" :label="opt" :value="opt" />
                      </t-select>
                    </div>
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="text-sm text-dark-100 mb-1.5 block">是否自动平反向仓</label>
                      <t-select v-model="configValues.autoCloseReverse" size="medium">
                        <t-option v-for="opt in ['是', '否']" :key="opt" :label="opt" :value="opt" />
                      </t-select>
                    </div>
                    <div>
                      <label class="text-sm text-dark-100 mb-1.5 block">是否反向开仓</label>
                      <t-select v-model="configValues.reverseOpen" size="medium">
                        <t-option v-for="opt in ['是', '否']" :key="opt" :label="opt" :value="opt" />
                      </t-select>
                    </div>
                  </div>
                </div>
                
                <!-- Running Time -->
                <div v-if="activeTab === 'runtime'" class="space-y-4">
                  <div>
                    <label class="text-sm text-dark-100 mb-2 block">运行星期</label>
                    <div class="grid grid-cols-7 gap-2">
                      <div v-for="day in ['周一', '周二', '周三', '周四', '周五', '周六', '周日']" :key="day" class="flex items-center">
                        <input 
                          type="checkbox" 
                          :id="day" 
                          v-model="configValues.runDays" 
                          :value="day"
                          class="mr-2"
                        />
                        <label :for="day" class="text-xs text-dark-100">{{ day }}</label>
                      </div>
                    </div>
                  </div>
                  <div>
                    <label class="text-sm text-dark-100 mb-1.5 block">每日运行时间段</label>
                    <div class="flex items-center gap-2">
                      <t-input
                        v-model="configValues.startTime"
                        type="time"
                        size="medium"
                        placeholder="00:00"
                      />
                      <span class="text-dark-100">至</span>
                      <t-input
                        v-model="configValues.endTime"
                        type="time"
                        size="medium"
                        placeholder="23:59"
                      />
                    </div>
                  </div>
                  <p class="text-xs text-dark-200">策略仅在选定的星期和时间段内运行，默认全天候运行</p>
                </div>
                
                <!-- Filters -->
                <div v-if="activeTab === 'filters'" class="space-y-4">
                  <div>
                    <label class="text-sm text-dark-100 mb-2 block">已选择的筛选器</label>
                    <div class="space-y-2">
                      <div v-for="filter in selectedFilters" :key="filter.id" class="p-3 rounded-lg bg-dark-800/50 flex items-center justify-between">
                        <div>
                          <div class="text-sm text-white">{{ filter.name }}</div>
                          <div class="text-xs text-dark-100">{{ filter.type }}</div>
                        </div>
                        <button 
                          @click="removeFilter(filter.id)"
                          class="text-red-400 hover:text-red-300 text-sm"
                        >
                          移除
                        </button>
                      </div>
                    </div>
                  </div>
                  <div class="flex gap-2">
                    <button class="btn-outline text-sm flex-1">+ 添加筛选器</button>
                    <button class="btn-outline text-sm flex-1">编辑筛选器</button>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="flex gap-3 mt-6">
              <button
                class="btn-primary flex-1 !py-3 text-base rounded-xl flex items-center justify-center gap-2"
                :disabled="launching"
                @click="handleLaunch"
              >
                <Play :size="18" />
                {{ launching ? '启动中...' : '实盘交易' }}
              </button>
              <button
                class="flex-1 !py-3 text-base rounded-xl flex items-center justify-center gap-2 bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 border border-blue-500/30 transition-colors"
                :disabled="simLaunching"
                @click="handleSimLaunch"
              >
                <FlaskConical :size="18" />
                {{ simLaunching ? '启动中...' : '模拟交易' }}
              </button>
            </div>
            <p class="text-xs text-dark-200 text-center mt-3">实盘交易连接真实交易所，模拟交易使用虚拟资金</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Not Found -->
    <div v-else class="min-h-screen flex items-center justify-center bg-dark-900">
      <div class="text-center py-20">
        <p class="text-dark-100 text-lg">策略不存在</p>
        <router-link to="/system/strategies" class="btn-outline mt-4 inline-block">返回策略列表</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Zap, ChevronRight, BookOpen, Brain, Settings, AlertTriangle, Play, Building, TrendingUp, Clock, DollarSign, Shield, Cog, FlaskConical } from 'lucide-vue-next'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'
import RiskBadge from '@/components/common/RiskBadge.vue'
import StatusDot from '@/components/common/StatusDot.vue'
import { useAuthStore } from '@/stores/auth'
import strategyApi from '@/utils/strategyApi'
import backtestApi from '@/utils/backtestApi'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const launching = ref(false)
const simLaunching = ref(false)
const loading = ref(false)

// 策略数据
const strategy = ref<any>(null)

// 加载策略详情（预设策略浏览页）
async function loadStrategyDetail() {
  loading.value = true
  try {
    const strategyId = route.params.id as string
    const response = await strategyApi.getPresetStrategyDetail(strategyId)
    // 兼容接口返回的各种字段名
    strategy.value = {
      ...response,
      id: response.id || response.strategy_id || (route.params.id as string),
      name: response.name || '',
      description: response.description || response.detail || '',
      market: response.symbols?.[0] || response.market || '',
      type: response.strategy_type || response.type || '',
      riskLevel: response.risk_level || response.riskLevel || 'medium',
      returnRate: response.total_return ?? response.returnRate ?? 0,
      maxDrawdown: response.max_drawdown ?? response.maxDrawdown ?? 0,
      runDays: response.running_days ?? response.runDays ?? 0,
      status: response.state || response.status || 'active',
      logic: response.logic_description || response.logic || '',
      riskTip: response.risk_warning || response.riskTip || '本策略存在市场风险，历史表现不代表未来收益。',
      exchange: response.exchange || 'Binance',
      tradingPair: response.symbols?.[0] || response.tradingPair || 'BTC/USDT',
      timeframe: response.timeframe || '1h',
      params: response.params_schema ? Object.entries(response.params_schema).map(([key, val]: [string, any]) => ({
        name: key,
        label: val.label || key,
        type: val.type || 'number',
        default: response.default_params?.[key] ?? val.default ?? '',
        description: val.description || '',
        required: val.required ?? false,
      })) : response.params || [],
      capitalAllocation: {
        initialCapital: response.initial_capital ?? response.capitalAllocation?.initialCapital ?? 10000,
        maxPositionSize: response.risk_params?.max_position_size ?? response.capitalAllocation?.maxPositionSize ?? 20,
        riskPerTrade: response.risk_params?.risk_per_trade ?? response.capitalAllocation?.riskPerTrade ?? 2,
        rebalancingFrequency: response.capitalAllocation?.rebalancingFrequency ?? 'daily',
      },
      riskManagement: {
        stopLoss: response.risk_params?.stop_loss ?? response.riskManagement?.stopLoss ?? 5,
        takeProfit: response.risk_params?.take_profit ?? response.riskManagement?.takeProfit ?? 10,
        trailingStop: response.risk_params?.trailing_stop ?? response.riskManagement?.trailingStop ?? false,
        maxConcurrentTrades: response.risk_params?.max_concurrent_trades ?? response.riskManagement?.maxConcurrentTrades ?? 5,
        dailyLossLimit: response.risk_params?.daily_loss_limit ?? response.riskManagement?.dailyLossLimit ?? 5,
        weeklyLossLimit: response.risk_params?.weekly_loss_limit ?? response.riskManagement?.weeklyLossLimit ?? 10,
      },
      advancedSettings: {
        slippageTolerance: response.advanced_params?.slippage_tolerance ?? response.advancedSettings?.slippageTolerance ?? 0.5,
        commissionRate: response.advanced_params?.commission_rate ?? response.advancedSettings?.commissionRate ?? 0.1,
        useMarketOrders: response.advanced_params?.use_market_orders ?? response.advancedSettings?.useMarketOrders ?? true,
        allowShortSelling: response.advanced_params?.allow_short_selling ?? response.advancedSettings?.allowShortSelling ?? false,
        enableHedging: response.advanced_params?.enable_hedging ?? response.advancedSettings?.enableHedging ?? false,
        backtestPeriod: response.advanced_params?.backtest_period ?? response.advancedSettings?.backtestPeriod ?? 90,
      },
    }
  } catch (error: any) {
    console.error('加载策略详情失败:', error)
    MessagePlugin.error(error.message || '加载策略详情失败')
  } finally {
    loading.value = false
  }
}

// 新增响应式数据
const isSimpleMode = ref(true)
const activeTab = ref('strategy')
const selectedFilters = ref([
  { id: 1, name: '超级趋势_14_3', type: 'WEEX | BTC/USDT | 5m' },
  { id: 2, name: '超级趋势_14_3', type: 'WEEX | BTC/USDT | 1m' },
  { id: 3, name: '超级趋势TV版_14_3', type: 'WEEX | BTC/USDT | 15m' }
])

const tabs = [
  { id: 'strategy', label: '策略配置' },
  { id: 'position', label: '仓位控制' },
  { id: 'advanced', label: '高级设置' },
  { id: 'runtime', label: '运行时间' },
  { id: 'filters', label: '筛选器' }
]

const configValues = ref({
  // 简易版配置
  platform: 'WEEX',
  currencyPair: 'BTC/USDT',
  leverage: 125,
  investment: 100,
  
  // 专业版配置
  timeframe: '5分钟',
  tradeMode: '多空双开',
  positionSize: 1,
  takeProfit: 100,
  stopLoss: 300,
  stopMode: '两者都可触发',
  maxPositions: 100,
  maxOrders: 0,
  maxLossStreak: 0,
  autoCancel: '否',
  autoCloseReverse: '否',
  reverseOpen: '否',
  runDays: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
  startTime: '00:00',
  endTime: '23:59'
})

function removeFilter(filterId: number) {
  selectedFilters.value = selectedFilters.value.filter(f => f.id !== filterId)
}

function initConfig() {
  if (strategy.value?.params) {
    const vals: Record<string, string | number | string[] | boolean> = {}
    strategy.value.params.forEach((p: any) => {
      vals[p.name] = p.default
    })
    configValues.value = { ...configValues.value, ...vals }
  }
}

watch(() => route.params.id, () => {
  loadStrategyDetail()
}, { immediate: true })

watch(() => strategy.value, () => {
  if (strategy.value) {
    initConfig()
  }
})

async function handleLaunch() {
  if (!authStore.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  
  const dlg = DialogPlugin.confirm({
    header: '确认启动策略',
    body: `即将启动「${strategy.value?.name}」，投入资金 ${configValues.value.investment || 1000} USDT。${
      isSimpleMode.value ? '（简易版模式）' : '（专业版模式）'
    }确认启动？`,
    theme: 'warning',
    confirmBtn: '确认启动',
    cancelBtn: '取消',
    onConfirm: async () => {
      dlg.hide()
      launching.value = true
      try {
        // 创建策略实例
        const response = await strategyApi.createUserStrategy({
          name: `${strategy.value.name}_${Date.now()}`,
          strategy_type: strategy.value.type,
          symbols: [configValues.value.currencyPair],
          params: configValues.value
        })
        
        MessagePlugin.success('策略已成功启动！正在跳转到策略运行详情...')
        const runningStrategyId = response?.strategy_id || strategy.value.id || (route.params.id as string)
        router.push(`/system/running-strategies/${runningStrategyId}`)
      } catch (error: any) {
        console.error('启动策略失败:', error)
        MessagePlugin.error(error.message || '启动策略失败')
      } finally {
        launching.value = false
      }
    },
    onCancel: () => dlg.hide(),
  })
}

async function handleSimLaunch() {
  if (!authStore.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  
  const dlg = DialogPlugin.confirm({
    header: '确认启动模拟交易',
    body: `即将以模拟模式启动「${strategy.value?.name}」，初始模拟资金 ${configValues.value.investment || 10000} USDT。模拟交易不会连接真实交易所，使用虚拟资金进行策略验证。确认启动？`,
    theme: 'info',
    confirmBtn: '确认启动模拟',
    cancelBtn: '取消',
    onConfirm: async () => {
      dlg.hide()
      simLaunching.value = true
      try {
        const response = await strategyApi.createSimulateStrategy({
          strategy_id: strategy.value.id,
          strategy_type: strategy.value.type,
          symbols: [configValues.value.currencyPair],
          params: configValues.value,
          initial_capital: Number(configValues.value.investment) || 10000,
        })
        
        MessagePlugin.success('模拟交易已成功启动！正在跳转到模拟交易页面...')
        const simStrategyId = response?.strategy_id || strategy.value.id || (route.params.id as string)
        router.push(`/system/simulation/${simStrategyId}`)
      } catch (error: any) {
        console.error('启动模拟交易失败:', error)
        MessagePlugin.error(error.message || '启动模拟交易失败')
      } finally {
        simLaunching.value = false
      }
    },
    onCancel: () => dlg.hide(),
  })
}

// 页面加载时获取数据
onMounted(() => {
  loadStrategyDetail()
})
</script>