<template>
  <div class="pt-24 pb-16">
    <div class="page-container max-w-none" v-if="followDetail">
      <!-- Breadcrumb -->
      <div class="flex items-center gap-2 text-sm text-dark-100 mb-8">
        <router-link to="/system/user" class="hover:text-primary-500 transition-colors">我的账户</router-link>
        <ChevronRight :size="14" />
        <span class="text-white">{{ followDetail.signalName }}</span>
      </div>

      <!-- Header -->
      <div class="glass-card p-8 mb-8">
        <div class="flex items-start justify-between mb-6">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-accent-blue/20 to-accent-purple/20 flex items-center justify-center">
              <Radio :size="28" class="text-blue-400" />
            </div>
            <div>
              <h1 class="text-2xl font-bold text-white">{{ followDetail.signalName }}</h1>
              <div class="flex items-center gap-3 mt-1.5">
                <span class="text-sm text-dark-100">{{ followDetail.exchange }}</span>
                <span class="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400">跟单中</span>
                <StatusDot :status="followDetail.status" />
              </div>
            </div>
          </div>
          <div class="flex items-center gap-4">
            <button class="btn-outline !py-2 !px-4 text-sm flex items-center gap-1.5">
              <Settings :size="14" /> 调整设置
            </button>
            <button class="btn-danger !py-2 !px-4 text-sm flex items-center gap-1.5">
              <StopCircle :size="14" /> 停止跟单
            </button>
          </div>
        </div>

        <!-- 关键指标 -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div class="p-4 rounded-xl bg-dark-800/50 text-center">
            <div class="text-2xl font-bold" :class="followDetail.totalReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
              {{ followDetail.totalReturn >= 0 ? '+' : '' }}{{ followDetail.totalReturn.toFixed(2) }}%
            </div>
            <div class="text-xs text-dark-100 mt-1">总收益率</div>
          </div>
          <div class="p-4 rounded-xl bg-dark-800/50 text-center">
            <div class="text-2xl font-bold text-white">{{ followDetail.followAmount.toLocaleString() }}</div>
            <div class="text-xs text-dark-100 mt-1">跟单资金 (USDT)</div>
          </div>
          <div class="p-4 rounded-xl bg-dark-800/50 text-center">
            <div class="text-2xl font-bold text-white">{{ followDetail.currentValue.toLocaleString() }}</div>
            <div class="text-xs text-dark-100 mt-1">当前净值 (USDT)</div>
          </div>
          <div class="p-4 rounded-xl bg-dark-800/50 text-center">
            <div class="text-2xl font-bold text-amber-400">{{ followDetail.maxDrawdown.toFixed(2) }}%</div>
            <div class="text-xs text-dark-100 mt-1">最大回撤</div>
          </div>
          <div class="p-4 rounded-xl bg-dark-800/50 text-center">
            <div class="text-2xl font-bold text-primary-400">{{ followDetail.followDays }}</div>
            <div class="text-xs text-dark-100 mt-1">跟单天数</div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Main Content -->
        <div class="lg:col-span-2 space-y-6">
          <!-- 行情与交易点 -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <TrendingUp :size="18" class="text-primary-400" />
              行情与交易点
            </h2>
            
            <!-- 当前价格信息 -->
            <div class="grid grid-cols-3 gap-4 mb-6">
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-xs text-dark-200 mb-1">当前价格</div>
                <div class="text-lg font-bold text-white">${{ followDetail.currentPrice.toLocaleString() }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-xs text-dark-200 mb-1">24h涨跌</div>
                <div class="text-lg font-bold" :class="followDetail.priceChange24h >= 0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ followDetail.priceChange24h >= 0 ? '+' : '' }}{{ followDetail.priceChange24h.toFixed(2) }}%
                </div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-xs text-dark-200 mb-1">24h成交量</div>
                <div class="text-lg font-bold text-white">{{ followDetail.volume24h }}</div>
              </div>
            </div>

            <!-- K线+指标+买卖点综合图表 -->
            <div class="rounded-xl bg-dark-800/30 p-4 mb-6">
              <div class="flex items-center justify-between mb-3">
                <h3 class="text-sm font-medium text-dark-100">K线行情</h3>
                <div class="flex items-center gap-3">
                  <div class="flex gap-1">
                    <button 
                      v-for="tf in timeframeOptions" 
                      :key="tf"
                      @click="selectedPeriod = tf"
                      class="px-2 py-1 text-xs rounded transition-colors"
                      :class="selectedPeriod === tf ? 'bg-primary-500 text-white' : 'text-dark-100 hover:text-white'"
                    >
                      {{ tf }}
                    </button>
                  </div>
                  <div class="flex gap-1">
                    <button 
                      v-for="ind in availableIndicators" 
                      :key="ind.key"
                      @click="toggleIndicator(ind.key)"
                      class="px-2 py-1 text-xs rounded transition-colors"
                      :class="activeIndicators.includes(ind.key) ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30' : 'bg-dark-800/50 text-dark-200 hover:text-white'"
                    >
                      {{ ind.label }}
                    </button>
                  </div>
                </div>
              </div>
              <TradingChart
                :kline-data="klineData"
                :indicators="chartIndicators"
                :trade-marks="followTradeMarks"
                :height="480"
                :show-volume="true"
              />
              <div class="flex items-center gap-6 mt-3 text-xs text-dark-200">
                <span class="flex items-center gap-1.5">
                  <span class="w-3 h-3 rounded-full bg-emerald-400 inline-block"></span>
                  买入
                </span>
                <span class="flex items-center gap-1.5">
                  <span class="w-3 h-3 rounded-full bg-red-400 inline-block"></span>
                  卖出
                </span>
                <span class="flex items-center gap-1.5">
                  <span class="w-3 h-0.5 bg-amber-400 inline-block"></span>
                  MA7
                </span>
                <span class="flex items-center gap-1.5">
                  <span class="w-3 h-0.5 bg-blue-400 inline-block"></span>
                  MA25
                </span>
              </div>
            </div>

            <!-- 交易点位标记 -->
            <div class="space-y-3">
              <h3 class="text-sm font-medium text-white flex items-center gap-2">
                <Target :size="16" class="text-amber-400" />
                最近交易点位
              </h3>
              <div class="space-y-2">
                <div 
                  v-for="point in followDetail.tradingPoints" 
                  :key="point.id"
                  class="p-3 rounded-lg bg-dark-800/50 flex items-center justify-between"
                >
                  <div class="flex items-center gap-3">
                    <div 
                      class="w-8 h-8 rounded-lg flex items-center justify-center"
                      :class="point.type === 'buy' ? 'bg-emerald-500/10' : 'bg-red-500/10'"
                    >
                      <component 
                        :is="point.type === 'buy' ? ArrowUpCircle : ArrowDownCircle" 
                        :size="16" 
                        :class="point.type === 'buy' ? 'text-emerald-400' : 'text-red-400'"
                      />
                    </div>
                    <div>
                      <div class="text-sm font-medium text-white">
                        {{ point.type === 'buy' ? '买入' : '卖出' }} {{ point.symbol }}
                      </div>
                      <div class="text-xs text-dark-100">{{ point.time }}</div>
                    </div>
                  </div>
                  <div class="text-right">
                    <div class="text-sm font-medium text-white">${{ point.price.toLocaleString() }}</div>
                    <div class="text-xs text-dark-100">{{ point.amount }} {{ point.symbol.split('/')[0] }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 收益曲线 -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <BarChart3 :size="18" class="text-primary-400" />
              收益曲线
            </h2>
            <div class="rounded-xl bg-dark-800/30 p-4">
              <ReturnCurveChart
                v-if="followDetail.returnCurve?.length"
                :data="followDetail.returnCurve"
                :labels="followDetail.returnCurveLabels"
                :height="280"
                :color="followDetail.totalReturn >= 0 ? '#10b981' : '#ef4444'"
              />
            </div>
            <div class="grid grid-cols-3 gap-4 mt-4">
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">累计收益</div>
                <div class="text-white font-medium" :class="followDetail.totalReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ followDetail.totalReturn >= 0 ? '+' : '' }}{{ followDetail.totalReturn.toFixed(2) }}%
                </div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">今日收益</div>
                <div class="text-white font-medium" :class="followDetail.todayReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ followDetail.todayReturn >= 0 ? '+' : '' }}{{ followDetail.todayReturn.toFixed(2) }}%
                </div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">胜率</div>
                <div class="text-white font-medium">{{ followDetail.winRate.toFixed(1) }}%</div>
              </div>
            </div>
          </div>

          <!-- 跟单 vs 信号源收益对比 -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <GitCompare :size="18" class="text-blue-400" />
              跟单 vs 信号源收益对比
            </h2>
            <div class="rounded-xl bg-dark-800/30 p-4">
              <DualReturnChart
                :data1="followReturnCurve"
                :data2="signalReturnCurve"
                :labels="followDetail.returnCurveLabels"
                :height="280"
                color1="#10b981"
                color2="#3b82f6"
                name1="我的跟单"
                name2="信号源"
              />
            </div>
            <div class="grid grid-cols-3 gap-4 mt-4">
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">收益差异</div>
                <div class="font-medium" :class="returnDiff >= 0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ returnDiff >= 0 ? '+' : '' }}{{ returnDiff.toFixed(2) }}%
                </div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">平均滑点</div>
                <div class="text-amber-400 font-medium">0.12%</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">跟单复制率</div>
                <div class="text-white font-medium">98.7%</div>
              </div>
            </div>
          </div>

          <!-- 当前持仓 -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <Layers :size="18" class="text-primary-400" />
              当前持仓
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
                    <th class="text-right py-3 px-4 text-dark-100 font-medium">盈亏率</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="pos in followDetail.positions" :key="pos.id" class="border-b border-white/[0.04] hover:bg-white/[0.02]">
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
                    <td class="py-3 px-4 text-right font-medium" :class="pos.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'">
                      {{ pos.pnl >= 0 ? '+' : '' }}${{ pos.pnl.toFixed(2) }}
                    </td>
                    <td class="py-3 px-4 text-right font-medium" :class="pos.pnlPercent >= 0 ? 'text-emerald-400' : 'text-red-400'">
                      {{ pos.pnlPercent >= 0 ? '+' : '' }}{{ pos.pnlPercent.toFixed(2) }}%
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-if="!followDetail.positions?.length" class="text-center py-8 text-dark-100 text-sm">暂无持仓</div>
          </div>

          <!-- 交易记录 -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <History :size="18" class="text-primary-400" />
              交易记录
            </h2>
            <div class="space-y-2">
              <div 
                v-for="trade in followDetail.tradeHistory" 
                :key="trade.id"
                class="p-4 rounded-lg bg-dark-800/50 hover:bg-dark-800/70 transition-colors"
              >
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-3">
                    <div 
                      class="w-8 h-8 rounded-lg flex items-center justify-center"
                      :class="trade.side === 'buy' ? 'bg-emerald-500/10' : 'bg-red-500/10'"
                    >
                      <component 
                        :is="trade.side === 'buy' ? ArrowUpCircle : ArrowDownCircle" 
                        :size="16" 
                        :class="trade.side === 'buy' ? 'text-emerald-400' : 'text-red-400'"
                      />
                    </div>
                    <div>
                      <div class="text-sm font-medium text-white">
                        {{ trade.side === 'buy' ? '买入' : '卖出' }} {{ trade.symbol }}
                      </div>
                      <div class="text-xs text-dark-100">{{ trade.time }}</div>
                    </div>
                  </div>
                  <div class="text-right">
                    <div class="text-sm font-medium text-white">${{ trade.price.toLocaleString() }}</div>
                    <div class="text-xs text-dark-100">{{ trade.amount }} {{ trade.symbol.split('/')[0] }}</div>
                  </div>
                </div>
                <div class="flex items-center justify-between text-xs">
                  <span class="text-dark-200">成交额: ${{ trade.total.toLocaleString() }}</span>
                  <span v-if="trade.pnl !== undefined" class="font-medium" :class="trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'">
                    盈亏: {{ trade.pnl >= 0 ? '+' : '' }}${{ trade.pnl.toFixed(2) }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 事件日志 -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <ScrollText :size="18" class="text-primary-400" />
              事件日志
            </h2>
            <div class="space-y-1">
              <div 
                v-for="event in eventLog" 
                :key="event.id"
                class="flex items-start gap-3 p-3 rounded-lg hover:bg-dark-800/30 transition-colors"
              >
                <div 
                  class="w-7 h-7 rounded-lg flex items-center justify-center mt-0.5 shrink-0"
                  :class="eventTypeStyle[event.type].bg"
                >
                  <component :is="eventTypeStyle[event.type].icon" :size="13" :class="eventTypeStyle[event.type].text" />
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-sm text-white">{{ event.message }}</div>
                  <div class="text-xs text-dark-200 mt-0.5">{{ event.time }}</div>
                </div>
                <span class="text-xs px-2 py-0.5 rounded shrink-0" :class="eventTypeStyle[event.type].badge">
                  {{ event.typeLabel }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Sidebar -->
        <div class="space-y-6">
          <!-- 跟单配置 -->
          <div class="glass-card p-6 sticky top-24">
            <h3 class="text-lg font-bold text-white mb-6">跟单配置</h3>
            <div class="space-y-4">
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">跟单资金</div>
                <div class="text-white font-medium">{{ followDetail.followAmount.toLocaleString() }} USDT</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">跟单比例</div>
                <div class="text-white font-medium">{{ followDetail.followRatio * 100 }}%</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">止损设置</div>
                <div class="text-white font-medium">{{ followDetail.stopLoss }}%</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">开始时间</div>
                <div class="text-white font-medium">{{ followDetail.startTime }}</div>
              </div>
            </div>
          </div>

          <!-- 资金使用率 / 仓位分布 -->
          <div class="glass-card p-6">
            <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <PieChart :size="18" class="text-primary-400" />
              仓位分布
            </h3>
            <PositionPieChart
              :data="positionDistribution"
              :height="220"
            />
            <div class="mt-3 p-3 rounded-lg bg-dark-800/50">
              <div class="flex justify-between text-sm">
                <span class="text-dark-200">资金使用率</span>
                <span class="text-white font-medium">{{ capitalUsageRate.toFixed(1) }}%</span>
              </div>
              <div class="w-full h-1.5 rounded-full bg-dark-700 mt-2 overflow-hidden">
                <div class="h-full rounded-full bg-primary-500" :style="{ width: capitalUsageRate + '%' }"></div>
              </div>
            </div>
          </div>

          <!-- 风险提示 -->
          <div class="glass-card p-6">
            <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Shield :size="18" class="text-amber-400" />
              风险提示
            </h3>
            <div class="space-y-3">
              <div class="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <div class="flex items-start gap-2">
                  <AlertTriangle :size="14" class="text-amber-400 mt-0.5 shrink-0" />
                  <div class="text-xs text-amber-300">
                    当前回撤: {{ followDetail.currentDrawdown.toFixed(2) }}%
                  </div>
                </div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-xs text-dark-200 mb-1">距离止损</div>
                <div class="text-sm font-medium text-white">
                  {{ (followDetail.stopLoss - Math.abs(followDetail.currentDrawdown)).toFixed(2) }}%
                </div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-xs text-dark-200 mb-1">持仓风险度</div>
                <div class="text-sm font-medium text-white">{{ followDetail.riskLevel }}</div>
              </div>
            </div>
          </div>

          <!-- 绩效统计 -->
          <div class="glass-card p-6">
            <h3 class="text-lg font-bold text-white mb-4">绩效统计</h3>
            <div class="space-y-3">
              <div class="flex justify-between text-sm">
                <span class="text-dark-200">总交易次数</span>
                <span class="text-white font-medium">{{ followDetail.totalTrades }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-dark-200">盈利次数</span>
                <span class="text-emerald-400 font-medium">{{ followDetail.winTrades }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-dark-200">亏损次数</span>
                <span class="text-red-400 font-medium">{{ followDetail.lossTrades }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-dark-200">胜率</span>
                <span class="text-white font-medium">{{ followDetail.winRate.toFixed(1) }}%</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-dark-200">平均盈利</span>
                <span class="text-emerald-400 font-medium">+${{ followDetail.avgWin.toFixed(2) }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-dark-200">平均亏损</span>
                <span class="text-red-400 font-medium">-${{ followDetail.avgLoss.toFixed(2) }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-dark-200">盈亏比</span>
                <span class="text-white font-medium">{{ followDetail.profitFactor.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Not Found -->
    <div v-else class="page-container max-w-none pt-24 text-center py-20">
      <p class="text-dark-100 text-lg">跟单记录不存在</p>
      <router-link to="/system/user" class="btn-outline mt-4 inline-block">返回我的账户</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  Radio, ChevronRight, TrendingUp, Layers, History, BarChart3, Shield, 
  Settings, StopCircle, Target, ArrowUpCircle, ArrowDownCircle, AlertTriangle,
  GitCompare, PieChart, ScrollText, Zap, ShieldAlert, CheckCircle, XCircle
} from 'lucide-vue-next'
import StatusDot from '@/components/common/StatusDot.vue'
import ReturnCurveChart from '@/components/charts/ReturnCurveChart.vue'
import TradingChart from '@/components/charts/TradingChart.vue'
import DualReturnChart from '@/components/charts/DualReturnChart.vue'
import PositionPieChart from '@/components/charts/PositionPieChart.vue'
import type { KlineDataPoint, IndicatorData, TradeMarkData } from '@/components/charts/TradingChart.vue'

const route = useRoute()
const selectedPeriod = ref('1D')
const timeframeOptions = ['15m', '1H', '4H', '1D', '1W']

const availableIndicators = [
  { key: 'ma', label: 'MA' },
  { key: 'macd', label: 'MACD' },
  { key: 'rsi', label: 'RSI' },
]
const activeIndicators = ref<string[]>(['ma'])

function toggleIndicator(key: string) {
  const idx = activeIndicators.value.indexOf(key)
  if (idx >= 0) {
    activeIndicators.value.splice(idx, 1)
  } else {
    activeIndicators.value.push(key)
  }
}

// 生成模拟K线数据
function generateMockKline(count = 200): KlineDataPoint[] {
  const data: KlineDataPoint[] = []
  const now = Math.floor(Date.now() / 1000)
  const interval = 3600
  let price = 89000 + Math.random() * 3000

  for (let i = 0; i < count; i++) {
    const time = now - (count - i) * interval
    const change = (Math.random() - 0.48) * price * 0.012
    const open = price
    const close = open + change
    const high = Math.max(open, close) + Math.random() * price * 0.004
    const low = Math.min(open, close) - Math.random() * price * 0.004
    const volume = Math.floor(30 + Math.random() * 400)
    data.push({ time, open, high, low, close, volume })
    price = close
  }
  return data
}

const klineData = ref<KlineDataPoint[]>(generateMockKline())

// MA计算
function calcMA(data: KlineDataPoint[], period: number): Array<{ time: number; value: number }> {
  const result: Array<{ time: number; value: number }> = []
  for (let i = period - 1; i < data.length; i++) {
    let sum = 0
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close
    }
    result.push({ time: data[i].time, value: sum / period })
  }
  return result
}

// EMA计算
function calcEMA(data: number[], period: number): number[] {
  const k = 2 / (period + 1)
  const result: number[] = [data[0]]
  for (let i = 1; i < data.length; i++) {
    result.push(data[i] * k + result[i - 1] * (1 - k))
  }
  return result
}

// MACD计算
function calcMACD(data: KlineDataPoint[]) {
  const closes = data.map(d => d.close)
  const ema12 = calcEMA(closes, 12)
  const ema26 = calcEMA(closes, 26)
  const dif: number[] = []
  for (let i = 0; i < closes.length; i++) {
    dif.push((ema12[i] || 0) - (ema26[i] || 0))
  }
  const dea = calcEMA(dif.slice(25), 9)
  const macdLine: Array<{ time: number; value: number }> = []
  const signalLine: Array<{ time: number; value: number }> = []
  const histogram: Array<{ time: number; value: number }> = []
  for (let i = 0; i < dea.length; i++) {
    const idx = i + 25 + 8
    if (idx < data.length) {
      macdLine.push({ time: data[idx].time, value: dif[idx] })
      signalLine.push({ time: data[idx].time, value: dea[i] })
      histogram.push({ time: data[idx].time, value: (dif[idx] - dea[i]) * 2 })
    }
  }
  return { macd: macdLine, signal: signalLine, histogram }
}

// RSI计算
function calcRSI(data: KlineDataPoint[], period = 14): Array<{ time: number; value: number }> {
  const result: Array<{ time: number; value: number }> = []
  const gains: number[] = []
  const losses: number[] = []
  for (let i = 1; i < data.length; i++) {
    const change = data[i].close - data[i - 1].close
    gains.push(change > 0 ? change : 0)
    losses.push(change < 0 ? -change : 0)
    if (i >= period) {
      const avgGain = gains.slice(i - period, i).reduce((a, b) => a + b, 0) / period
      const avgLoss = losses.slice(i - period, i).reduce((a, b) => a + b, 0) / period
      const rs = avgLoss === 0 ? 100 : avgGain / avgLoss
      result.push({ time: data[i].time, value: 100 - (100 / (1 + rs)) })
    }
  }
  return result
}

// 组合指标
const chartIndicators = computed<IndicatorData[]>(() => {
  const indicators: IndicatorData[] = []
  const data = klineData.value
  if (activeIndicators.value.includes('ma')) {
    indicators.push(
      { name: 'MA7', type: 'line', color: '#f59e0b', pane: 'main', data: calcMA(data, 7) },
      { name: 'MA25', type: 'line', color: '#3b82f6', pane: 'main', data: calcMA(data, 25) },
    )
  }
  if (activeIndicators.value.includes('macd')) {
    const macd = calcMACD(data)
    indicators.push(
      { name: 'MACD', type: 'line', color: '#3b82f6', pane: 'sub', data: macd.macd },
      { name: 'Signal', type: 'line', color: '#f59e0b', pane: 'sub', data: macd.signal },
      { name: 'Histogram', type: 'histogram', color: '#26a69a', pane: 'sub', data: macd.histogram },
    )
  }
  if (activeIndicators.value.includes('rsi')) {
    indicators.push(
      { name: 'RSI', type: 'line', color: '#ec4899', pane: 'sub2', data: calcRSI(data) },
    )
  }
  return indicators
})

// 将交易点位映射为K线图上的买卖标记
const followTradeMarks = computed<TradeMarkData[]>(() => {
  const data = klineData.value
  const marks: TradeMarkData[] = []
  let i = 25
  let isBuy = true
  while (i < data.length) {
    marks.push({
      time: data[i].time,
      position: isBuy ? 'belowBar' : 'aboveBar',
      color: isBuy ? '#10b981' : '#ef5350',
      shape: isBuy ? 'arrowUp' : 'arrowDown',
      text: isBuy ? '买入' : '卖出',
    })
    isBuy = !isBuy
    i += 18 + Math.floor(Math.random() * 15)
  }
  return marks
})

// Mock data - 实际应该从API获取
const followDetail = computed(() => {
  const id = route.params.id
  
  // 生成模拟数据
  return {
    id,
    signalName: 'Alpha Pro #1',
    exchange: 'Binance',
    status: 'following',
    totalReturn: 15.23,
    followAmount: 5000,
    currentValue: 5761.5,
    maxDrawdown: 8.45,
    followDays: 45,
    currentPrice: 91234.56,
    priceChange24h: 2.34,
    volume24h: '12.5B',
    todayReturn: 1.23,
    winRate: 68.5,
    followRatio: 1,
    stopLoss: 15,
    startTime: '2025-11-01 10:30:00',
    currentDrawdown: 3.21,
    riskLevel: '中等',
    totalTrades: 156,
    winTrades: 107,
    lossTrades: 49,
    avgWin: 125.50,
    avgLoss: 78.30,
    profitFactor: 1.60,
    
    // 价格历史数据
    priceHistory: Array.from({ length: 48 }, (_, i) => {
      return parseFloat((90000 + Math.sin(i / 5) * 2000 + i * 30 + (Math.random() - 0.5) * 500).toFixed(2))
    }),
    priceHistoryLabels: Array.from({ length: 48 }, (_, i) => {
      const date = new Date()
      date.setHours(date.getHours() - (47 - i))
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }),
    
    // 收益曲线
    returnCurve: Array.from({ length: 45 }, (_, i) => {
      return parseFloat((Math.sin(i / 8) * 3 + i * 0.35 + (Math.random() - 0.3) * 2).toFixed(2))
    }),
    returnCurveLabels: Array.from({ length: 45 }, (_, i) => {
      const date = new Date()
      date.setDate(date.getDate() - (44 - i))
      return date.toISOString().split('T')[0]
    }),
    
    // 交易点位
    tradingPoints: [
      { id: '1', type: 'buy', symbol: 'BTC/USDT', price: 89234.50, amount: 0.055, time: '2025-02-20 14:30:00' },
      { id: '2', type: 'sell', symbol: 'ETH/USDT', price: 3521.23, amount: 1.42, time: '2025-02-20 10:15:00' },
      { id: '3', type: 'buy', symbol: 'ETH/USDT', price: 3456.78, amount: 1.45, time: '2025-02-19 16:45:00' },
      { id: '4', type: 'sell', symbol: 'BTC/USDT', price: 90123.45, amount: 0.05, time: '2025-02-19 09:20:00' },
    ],
    
    // 当前持仓
    positions: [
      { 
        id: '1', 
        symbol: 'BTC/USDT', 
        side: 'long', 
        amount: 0.055, 
        entryPrice: 89234.50, 
        currentPrice: 91234.56, 
        pnl: 110.00,
        pnlPercent: 2.24 
      },
      { 
        id: '2', 
        symbol: 'ETH/USDT', 
        side: 'long', 
        amount: 1.42, 
        entryPrice: 3456.78, 
        currentPrice: 3521.23, 
        pnl: 91.52,
        pnlPercent: 1.86 
      },
    ],
    
    // 交易历史
    tradeHistory: [
      { 
        id: '1', 
        side: 'buy', 
        symbol: 'BTC/USDT', 
        price: 89234.50, 
        amount: 0.055, 
        total: 4907.90,
        time: '2025-02-20 14:30:00' 
      },
      { 
        id: '2', 
        side: 'sell', 
        symbol: 'ETH/USDT', 
        price: 3521.23, 
        amount: 1.42, 
        total: 5000.15,
        pnl: 91.52,
        time: '2025-02-20 10:15:00' 
      },
      { 
        id: '3', 
        side: 'buy', 
        symbol: 'ETH/USDT', 
        price: 3456.78, 
        amount: 1.45, 
        total: 5012.33,
        time: '2025-02-19 16:45:00' 
      },
      { 
        id: '4', 
        side: 'sell', 
        symbol: 'BTC/USDT', 
        price: 90123.45, 
        amount: 0.05, 
        total: 4506.17,
        pnl: 156.78,
        time: '2025-02-19 09:20:00' 
      },
      { 
        id: '5', 
        side: 'buy', 
        symbol: 'BTC/USDT', 
        price: 86993.80, 
        amount: 0.05, 
        total: 4349.69,
        time: '2025-02-18 11:20:00' 
      },
    ],
  }
})

// ==================== 跟单 vs 信号源 收益对比 ====================

const followReturnCurve = computed(() => followDetail.value?.returnCurve || [])
const signalReturnCurve = computed(() => {
  // 模拟信号源的收益曲线（通常比跟单稍高，因为没有滑点）
  return (followDetail.value?.returnCurve || []).map((v: number, i: number) => {
    return parseFloat((v + 0.5 + Math.sin(i / 6) * 0.8).toFixed(2))
  })
})
const returnDiff = computed(() => {
  const follow = followReturnCurve.value
  const signal = signalReturnCurve.value
  if (follow.length && signal.length) {
    return follow[follow.length - 1] - signal[signal.length - 1]
  }
  return 0
})

// ==================== 仓位分布 ====================

const positionDistribution = computed(() => {
  const positions = followDetail.value?.positions || []
  const totalValue = followDetail.value?.currentValue || 1
  const used = positions.reduce((sum: number, p: any) => sum + p.entryPrice * p.amount, 0)
  const free = totalValue - used

  const items = positions.map((p: any) => ({
    name: p.symbol,
    value: parseFloat((p.entryPrice * p.amount).toFixed(2)),
  }))
  items.push({ name: '可用资金', value: parseFloat(Math.max(0, free).toFixed(2)) })
  return items
})

const capitalUsageRate = computed(() => {
  const total = followDetail.value?.currentValue || 1
  const positions = followDetail.value?.positions || []
  const used = positions.reduce((sum: number, p: any) => sum + p.entryPrice * p.amount, 0)
  return Math.min(100, (used / total) * 100)
})

// ==================== 事件日志 ====================

const eventTypeStyle: Record<string, { bg: string; text: string; badge: string; icon: any }> = {
  trade: { bg: 'bg-primary-500/10', text: 'text-primary-400', badge: 'bg-primary-500/10 text-primary-400', icon: Zap },
  risk: { bg: 'bg-amber-500/10', text: 'text-amber-400', badge: 'bg-amber-500/10 text-amber-400', icon: ShieldAlert },
  success: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', badge: 'bg-emerald-500/10 text-emerald-400', icon: CheckCircle },
  error: { bg: 'bg-red-500/10', text: 'text-red-400', badge: 'bg-red-500/10 text-red-400', icon: XCircle },
  system: { bg: 'bg-blue-500/10', text: 'text-blue-400', badge: 'bg-blue-500/10 text-blue-400', icon: Settings },
}

const eventLog = [
  { id: '1', type: 'trade', typeLabel: '交易', message: '跟单买入 BTC/USDT 0.055个，成交价 $89,234.50', time: '2025-02-20 14:30:12' },
  { id: '2', type: 'success', typeLabel: '成交', message: '卖出 ETH/USDT 1.42个已成交，盈利 +$91.52', time: '2025-02-20 10:15:35' },
  { id: '3', type: 'risk', typeLabel: '风控', message: '当前回撤达到 3.21%，距离止损线还有 11.79%', time: '2025-02-20 08:00:00' },
  { id: '4', type: 'trade', typeLabel: '交易', message: '跟单买入 ETH/USDT 1.45个，成交价 $3,456.78', time: '2025-02-19 16:45:22' },
  { id: '5', type: 'success', typeLabel: '成交', message: '卖出 BTC/USDT 0.05个已成交，盈利 +$156.78', time: '2025-02-19 09:20:18' },
  { id: '6', type: 'system', typeLabel: '系统', message: '跟单参数更新：止损比例调整为 15%', time: '2025-02-18 20:00:00' },
  { id: '7', type: 'trade', typeLabel: '交易', message: '跟单买入 BTC/USDT 0.05个，成交价 $86,993.80', time: '2025-02-18 11:20:45' },
  { id: '8', type: 'risk', typeLabel: '风控', message: '信号源发出高风险预警，建议关注仓位', time: '2025-02-17 15:30:00' },
  { id: '9', type: 'error', typeLabel: '异常', message: '跟单延迟：ETH/USDT买入信号延迟 2.3s 执行，滑点 0.15%', time: '2025-02-16 09:12:33' },
  { id: '10', type: 'system', typeLabel: '系统', message: '跟单服务启动成功，初始资金 5,000 USDT', time: '2025-01-06 10:30:00' },
]
</script>
