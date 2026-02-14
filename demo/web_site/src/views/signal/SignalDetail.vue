<template>
  <div class="pt-24 pb-16">
    <div class="page-container" v-if="signal">
      <!-- Breadcrumb -->
      <div class="flex items-center gap-2 text-sm text-dark-100 mb-8">
        <router-link to="/system/signals" class="hover:text-primary-500 transition-colors">信号广场</router-link>
        <ChevronRight :size="14" />
        <span class="text-white">{{ signal.name }}</span>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Main Content -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Signal Header -->
          <div class="glass-card p-8">
            <div class="flex items-start justify-between mb-6">
              <div class="flex items-center gap-4">
                <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-accent-blue/20 to-accent-purple/20 flex items-center justify-center">
                  <Radio :size="28" class="text-blue-400" />
                </div>
                <div>
                  <h1 class="text-2xl font-bold text-white">{{ signal.name }}</h1>
                  <div class="flex items-center gap-3 mt-1.5">
                    <span class="text-sm text-dark-100">{{ signal.platform }}</span>
                    <span class="text-xs px-2 py-0.5 rounded"
                          :class="signal.type === 'live' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-blue-500/10 text-blue-400'">
                      {{ signal.type === 'live' ? '实盘' : '模拟盘' }}
                    </span>
                    <StatusDot :status="signal.status" />
                  </div>
                </div>
              </div>
              <div class="text-right">
                <div class="text-xs text-dark-100 mb-1">跟随人数</div>
                <div class="text-lg font-bold text-white">{{ signal.followers.toLocaleString() }}</div>
              </div>
            </div>
            <p class="text-dark-100 leading-relaxed text-sm">{{ signal.description }}</p>
            
            <!-- 新增交易所和交易对信息 -->
            <div class="mt-6 pt-6 border-t border-dark-700">
              <div class="grid grid-cols-2 gap-4">
                <div class="flex items-center gap-3">
                  <Building :size="16" class="text-dark-200" />
                  <div>
                    <div class="text-xs text-dark-200">交易所</div>
                    <div class="text-sm text-white">{{ signal.exchange }}</div>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <TrendingUp :size="16" class="text-dark-200" />
                  <div>
                    <div class="text-xs text-dark-200">交易对</div>
                    <div class="text-sm text-white">{{ signal.tradingPair }}</div>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <Clock :size="16" class="text-dark-200" />
                  <div>
                    <div class="text-xs text-dark-200">时间周期</div>
                    <div class="text-sm text-white">{{ signal.timeframe }}</div>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <Activity :size="16" class="text-dark-200" />
                  <div>
                    <div class="text-xs text-dark-200">信号频率</div>
                    <div class="text-sm text-white">{{ signal.signalFrequency === 'high' ? '高频' : signal.signalFrequency === 'medium' ? '中频' : '低频' }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Risk Parameters -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Shield :size="18" class="text-amber-400" />
              风险参数
            </h2>
            <div class="grid grid-cols-2 gap-4">
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">最大仓位</div>
                <div class="text-white font-medium">{{ signal.riskParameters.maxPositionSize }}%</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">止损比例</div>
                <div class="text-white font-medium">{{ signal.riskParameters.stopLossPercentage }}%</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">止盈比例</div>
                <div class="text-white font-medium">{{ signal.riskParameters.takeProfitPercentage }}%</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">风险收益比</div>
                <div class="text-white font-medium">{{ signal.riskParameters.riskRewardRatio }}:1</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">波动率过滤</div>
                <div class="text-white font-medium">{{ signal.riskParameters.volatilityFilter ? '启用' : '禁用' }}</div>
              </div>
            </div>
          </div>

          <!-- Performance Metrics -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <BarChart3 :size="18" class="text-primary-400" />
              绩效指标
            </h2>
            <div class="grid grid-cols-2 gap-4">
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">夏普比率</div>
                <div class="text-white font-medium">{{ signal.performanceMetrics.sharpeRatio.toFixed(2) }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">胜率</div>
                <div class="text-white font-medium">{{ signal.performanceMetrics.winRate.toFixed(1) }}%</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">盈亏比</div>
                <div class="text-white font-medium">{{ signal.performanceMetrics.profitFactor.toFixed(2) }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">平均持仓</div>
                <div class="text-white font-medium">{{ signal.performanceMetrics.averageHoldingPeriod.toFixed(1) }}天</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">最大连亏</div>
                <div class="text-white font-medium">{{ signal.performanceMetrics.maxConsecutiveLosses }}次</div>
              </div>
            </div>
          </div>

          <!-- Notification Settings -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Bell :size="18" class="text-blue-400" />
              通知设置
            </h2>
            <div class="grid grid-cols-2 gap-4">
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">邮件提醒</div>
                <div class="text-white font-medium">{{ signal.notificationSettings.emailAlerts ? '启用' : '禁用' }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">推送通知</div>
                <div class="text-white font-medium">{{ signal.notificationSettings.pushNotifications ? '启用' : '禁用' }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">Telegram机器人</div>
                <div class="text-white font-medium">{{ signal.notificationSettings.telegramBot ? '启用' : '禁用' }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">Discord Webhook</div>
                <div class="text-white font-medium">{{ signal.notificationSettings.discordWebhook ? '启用' : '禁用' }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">提醒阈值</div>
                <div class="text-white font-medium">{{ signal.notificationSettings.alertThreshold }}%</div>
              </div>
            </div>
          </div>

          <!-- Performance -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <TrendingUp :size="18" class="text-primary-400" />
              收益表现
            </h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div class="p-4 rounded-xl bg-dark-800/50 text-center">
                <div class="text-2xl font-bold" :class="signal.cumulativeReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ signal.cumulativeReturn >= 0 ? '+' : '' }}{{ signal.cumulativeReturn.toFixed(2) }}%
                </div>
                <div class="text-xs text-dark-100 mt-1">累计收益率</div>
              </div>
              <div class="p-4 rounded-xl bg-dark-800/50 text-center">
                <div class="text-2xl font-bold text-amber-400">{{ signal.maxDrawdown.toFixed(2) }}%</div>
                <div class="text-xs text-dark-100 mt-1">最大回撤</div>
              </div>
              <div class="p-4 rounded-xl bg-dark-800/50 text-center">
                <div class="text-2xl font-bold text-white">{{ signal.runDays }}</div>
                <div class="text-xs text-dark-100 mt-1">运行天数</div>
              </div>
              <div class="p-4 rounded-xl bg-dark-800/50 text-center">
                <div class="text-2xl font-bold text-primary-400">{{ signal.followers.toLocaleString() }}</div>
                <div class="text-xs text-dark-100 mt-1">跟随人数</div>
              </div>
            </div>
            <div class="rounded-xl bg-dark-800/30 p-4">
              <h3 class="text-sm font-medium text-dark-100 mb-3">收益曲线</h3>
              <ReturnCurveChart
                v-if="signal.returnCurve?.length"
                :data="signal.returnCurve"
                :labels="signal.returnCurveLabels"
                :height="280"
                :color="signal.cumulativeReturn >= 0 ? '#10b981' : '#ef4444'"
              />
            </div>
          </div>

          <!-- Positions -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <Layers :size="18" class="text-primary-400" />
              当前持仓
              <span class="text-xs text-dark-100 font-normal ml-2">(只读)</span>
            </h2>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-white/[0.06]">
                    <th class="text-left py-3 px-4 text-dark-100 font-medium">交易对</th>
                    <th class="text-left py-3 px-4 text-dark-100 font-medium">方向</th>
                    <th class="text-right py-3 px-4 text-dark-100 font-medium">数量</th>
                    <th class="text-right py-3 px-4 text-dark-100 font-medium">开仓价</th>
                    <th class="text-right py-3 px-4 text-dark-100 font-medium">现价</th>
                    <th class="text-right py-3 px-4 text-dark-100 font-medium">盈亏</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="pos in signal.positions" :key="pos.symbol + pos.side" class="border-b border-white/[0.04] hover:bg-white/[0.02]">
                    <td class="py-3 px-4 text-white font-medium">{{ pos.symbol }}</td>
                    <td class="py-3 px-4">
                      <span class="text-xs px-2 py-0.5 rounded"
                            :class="pos.side === 'long' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'">
                        {{ pos.side === 'long' ? '做多' : '做空' }}
                      </span>
                    </td>
                    <td class="py-3 px-4 text-right text-dark-100">{{ pos.amount }}</td>
                    <td class="py-3 px-4 text-right text-dark-100">${{ pos.entryPrice.toLocaleString() }}</td>
                    <td class="py-3 px-4 text-right text-white">${{ pos.currentPrice.toLocaleString() }}</td>
                    <td class="py-3 px-4 text-right font-medium" :class="pos.pnlPercent >= 0 ? 'text-emerald-400' : 'text-red-400'">
                      {{ pos.pnlPercent >= 0 ? '+' : '' }}{{ pos.pnlPercent.toFixed(2) }}%
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-if="!signal.positions?.length" class="text-center py-8 text-dark-100 text-sm">暂无持仓数据</div>
          </div>
        </div>

        <!-- Sidebar: Follow Panel -->
        <div class="space-y-6">
          <div class="glass-card p-6 sticky top-24">
            <h3 class="text-lg font-bold text-white mb-6">跟单设置</h3>
            <div class="space-y-5">
              <div>
                <label class="text-sm text-dark-100 mb-1.5 block">跟单资金 (USDT)</label>
                <t-input v-model="followConfig.amount" type="number" placeholder="输入跟单金额" size="medium" />
              </div>
              <div>
                <label class="text-sm text-dark-100 mb-1.5 block">跟单比例</label>
                <t-select v-model="followConfig.ratio" size="medium">
                  <t-option label="100% 等比跟单" value="1" />
                  <t-option label="50% 跟单" value="0.5" />
                  <t-option label="25% 跟单" value="0.25" />
                  <t-option label="200% 放大跟单" value="2" />
                </t-select>
              </div>
              <div>
                <label class="text-sm text-dark-100 mb-1.5 block">止损设置</label>
                <t-input v-model="followConfig.stopLoss" type="number" placeholder="总亏损止损(%)" size="medium" suffix="%" />
              </div>
            </div>

            <div class="mt-6 p-4 rounded-xl bg-dark-800/50 space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-dark-100">跟单资金</span>
                <span class="text-white font-medium">{{ followConfig.amount || 0 }} USDT</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-dark-100">跟单比例</span>
                <span class="text-white font-medium">{{ Number(followConfig.ratio) * 100 }}%</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-dark-100">止损比例</span>
                <span class="text-white font-medium">{{ followConfig.stopLoss || '--' }}%</span>
              </div>
            </div>

            <button class="btn-primary w-full mt-6 !py-3 text-base rounded-xl flex items-center justify-center gap-2">
              <Copy :size="18" />
              启动跟单
            </button>
            <p class="text-xs text-dark-200 text-center mt-3">跟单有风险，请合理配置资金</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Not Found -->
    <div v-else class="page-container pt-24 text-center py-20">
      <p class="text-dark-100 text-lg">信号不存在</p>
      <router-link to="/system/signals" class="btn-outline mt-4 inline-block">返回信号广场</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Radio, ChevronRight, TrendingUp, Layers, Copy, Building, Clock, Activity, Shield, BarChart3, Bell } from 'lucide-vue-next'
import StatusDot from '@/components/common/StatusDot.vue'
import ReturnCurveChart from '@/components/charts/ReturnCurveChart.vue'
import { signals } from '@/utils/mockData'

const route = useRoute()
const signal = computed(() => signals.find((s) => s.id === route.params.id))

const followConfig = ref({
  amount: 1000,
  ratio: '1',
  stopLoss: 10,
})
</script>