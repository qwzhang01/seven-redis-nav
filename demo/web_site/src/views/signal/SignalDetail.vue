<template>
  <div class="pt-24 pb-16">
    <div class="page-container max-w-none" v-if="signal">
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

          <!-- K线行情 + 指标 + 买卖点综合图表 -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <BarChart3 :size="18" class="text-primary-400" />
              K线行情与交易信号
            </h2>
            <div class="flex items-center gap-3 mb-4">
              <div class="flex gap-1">
                <button 
                  v-for="tf in timeframeOptions" 
                  :key="tf"
                  @click="selectedTimeframe = tf"
                  class="px-3 py-1.5 text-xs rounded-lg transition-colors"
                  :class="selectedTimeframe === tf ? 'bg-primary-500 text-white' : 'bg-dark-800/50 text-dark-100 hover:text-white'"
                >
                  {{ tf }}
                </button>
              </div>
              <div class="flex items-center gap-2 ml-auto">
                <span class="text-xs text-dark-200">指标:</span>
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
            <div class="rounded-xl bg-dark-800/30 overflow-hidden">
              <TradingChart
                :kline-data="klineData"
                :indicators="chartIndicators"
                :trade-marks="tradeMarks"
                :height="520"
                :show-volume="true"
              />
            </div>
            <div class="flex items-center gap-6 mt-3 text-xs text-dark-200">
              <span class="flex items-center gap-1.5">
                <span class="w-3 h-3 rounded-full bg-emerald-400 inline-block"></span>
                买入信号
              </span>
              <span class="flex items-center gap-1.5">
                <span class="w-3 h-3 rounded-full bg-red-400 inline-block"></span>
                卖出信号
              </span>
              <span class="flex items-center gap-1.5">
                <span class="w-3 h-0.5 bg-amber-400 inline-block"></span>
                MA7
              </span>
              <span class="flex items-center gap-1.5">
                <span class="w-3 h-0.5 bg-blue-400 inline-block"></span>
                MA25
              </span>
              <span class="flex items-center gap-1.5">
                <span class="w-3 h-0.5 bg-purple-400 inline-block"></span>
                MA99
              </span>
            </div>
          </div>

          <!-- 最近信号记录 -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <Activity :size="18" class="text-primary-400" />
              最近信号记录
            </h2>
            <div class="space-y-2">
              <div 
                v-for="record in signalHistory" 
                :key="record.id"
                class="p-4 rounded-lg bg-dark-800/50 hover:bg-dark-800/70 transition-colors"
              >
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-3">
                    <div 
                      class="w-8 h-8 rounded-lg flex items-center justify-center"
                      :class="record.action === 'buy' ? 'bg-emerald-500/10' : 'bg-red-500/10'"
                    >
                      <component 
                        :is="record.action === 'buy' ? ArrowUpCircle : ArrowDownCircle" 
                        :size="16" 
                        :class="record.action === 'buy' ? 'text-emerald-400' : 'text-red-400'"
                      />
                    </div>
                    <div>
                      <div class="text-sm font-medium text-white">
                        {{ record.action === 'buy' ? '买入' : '卖出' }} {{ record.symbol }}
                      </div>
                      <div class="text-xs text-dark-100">{{ record.time }}</div>
                    </div>
                  </div>
                  <div class="text-right">
                    <div class="text-sm font-medium text-white">${{ record.price.toLocaleString() }}</div>
                    <div class="text-xs text-dark-100">{{ record.amount }} {{ record.symbol.split('/')[0] }}</div>
                  </div>
                </div>
                <div class="flex items-center justify-between text-xs">
                  <span class="text-dark-200">信号强度: {{ record.strength }}</span>
                  <span v-if="record.pnl !== undefined" class="font-medium" :class="record.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'">
                    盈亏: {{ record.pnl >= 0 ? '+' : '' }}${{ record.pnl.toFixed(2) }}
                  </span>
                  <span v-else class="text-dark-200">持仓中</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 信号提供者信息 -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <User :size="18" class="text-primary-400" />
              信号提供者
            </h2>
            <div class="flex items-start gap-5">
              <div class="w-16 h-16 rounded-full bg-gradient-to-br from-primary-500/20 to-accent-purple/20 flex items-center justify-center shrink-0">
                <span class="text-2xl font-bold text-primary-400">{{ signalProvider.name.charAt(0) }}</span>
              </div>
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-2">
                  <span class="text-lg font-bold text-white">{{ signalProvider.name }}</span>
                  <span v-if="signalProvider.verified" class="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                    <Award :size="12" /> 认证交易员
                  </span>
                </div>
                <p class="text-sm text-dark-100 mb-3">{{ signalProvider.bio }}</p>
                <div class="grid grid-cols-4 gap-3">
                  <div class="text-center p-2 rounded-lg bg-dark-800/50">
                    <div class="text-sm font-bold text-white">{{ signalProvider.totalSignals }}</div>
                    <div class="text-xs text-dark-200">信号数</div>
                  </div>
                  <div class="text-center p-2 rounded-lg bg-dark-800/50">
                    <div class="text-sm font-bold text-emerald-400">{{ signalProvider.avgReturn }}%</div>
                    <div class="text-xs text-dark-200">平均收益</div>
                  </div>
                  <div class="text-center p-2 rounded-lg bg-dark-800/50">
                    <div class="text-sm font-bold text-white">{{ signalProvider.totalFollowers.toLocaleString() }}</div>
                    <div class="text-xs text-dark-200">总粉丝</div>
                  </div>
                  <div class="text-center p-2 rounded-lg bg-dark-800/50">
                    <div class="text-sm font-bold text-amber-400 flex items-center justify-center gap-1">
                      <Star :size="12" /> {{ signalProvider.rating }}
                    </div>
                    <div class="text-xs text-dark-200">评分</div>
                  </div>
                </div>
                <div class="flex items-center gap-4 mt-3 text-xs text-dark-200">
                  <span class="flex items-center gap-1"><Calendar :size="12" /> 入驻 {{ signalProvider.joinDate }}</span>
                  <span>交易经验: {{ signalProvider.experience }}</span>
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

          <!-- 月度收益分布 -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Calendar :size="18" class="text-primary-400" />
              月度收益分布
            </h2>
            <div class="rounded-xl bg-dark-800/30 p-4">
              <MonthlyReturnChart
                :data="monthlyReturnData"
                :labels="monthlyReturnLabels"
                :height="220"
              />
            </div>
            <div class="grid grid-cols-3 gap-3 mt-4">
              <div class="p-3 rounded-lg bg-dark-800/50 text-center">
                <div class="text-sm font-bold text-emerald-400">{{ monthlyStats.profitMonths }}</div>
                <div class="text-xs text-dark-200">盈利月份</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50 text-center">
                <div class="text-sm font-bold text-red-400">{{ monthlyStats.lossMonths }}</div>
                <div class="text-xs text-dark-200">亏损月份</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50 text-center">
                <div class="text-sm font-bold text-white">{{ monthlyStats.bestMonth }}%</div>
                <div class="text-xs text-dark-200">最佳月份</div>
              </div>
            </div>
          </div>

          <!-- 回撤分析 -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <TrendingDown :size="18" class="text-red-400" />
              回撤分析
            </h2>
            <div class="rounded-xl bg-dark-800/30 p-4">
              <DrawdownChart
                :data="drawdownData"
                :labels="drawdownLabels"
                :height="200"
              />
            </div>
            <div class="grid grid-cols-3 gap-3 mt-4">
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">当前回撤</div>
                <div class="text-red-400 font-medium">{{ drawdownStats.current.toFixed(2) }}%</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">最大回撤</div>
                <div class="text-red-400 font-medium">{{ drawdownStats.max.toFixed(2) }}%</div>
              </div>
              <div class="p-3 rounded-lg bg-dark-800/50">
                <div class="text-sm text-dark-200">平均回撤</div>
                <div class="text-amber-400 font-medium">{{ drawdownStats.avg.toFixed(2) }}%</div>
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

          <!-- 用户评价 -->
          <div class="glass-card p-8">
            <h2 class="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <MessageSquare :size="18" class="text-primary-400" />
              用户评价
              <span class="text-xs text-dark-100 font-normal ml-2">({{ userReviews.length }}条评价)</span>
            </h2>

            <!-- 评分概览 -->
            <div class="flex items-center gap-6 mb-6 p-4 rounded-xl bg-dark-800/50">
              <div class="text-center">
                <div class="text-3xl font-bold text-amber-400">4.6</div>
                <div class="flex items-center gap-0.5 mt-1">
                  <Star v-for="s in 5" :key="s" :size="12" :class="s <= 4 ? 'text-amber-400 fill-amber-400' : 'text-dark-300'" />
                </div>
                <div class="text-xs text-dark-200 mt-1">{{ userReviews.length }}条评价</div>
              </div>
              <div class="flex-1 space-y-1.5">
                <div v-for="star in [5,4,3,2,1]" :key="star" class="flex items-center gap-2">
                  <span class="text-xs text-dark-200 w-3">{{ star }}</span>
                  <Star :size="10" class="text-amber-400" />
                  <div class="flex-1 h-1.5 rounded-full bg-dark-700 overflow-hidden">
                    <div class="h-full rounded-full bg-amber-400" :style="{ width: ratingDistribution[star] + '%' }"></div>
                  </div>
                  <span class="text-xs text-dark-200 w-8 text-right">{{ ratingDistribution[star] }}%</span>
                </div>
              </div>
            </div>

            <!-- 评价列表 -->
            <div class="space-y-4">
              <div 
                v-for="review in userReviews" 
                :key="review.id"
                class="p-4 rounded-lg bg-dark-800/50"
              >
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500/30 to-accent-purple/30 flex items-center justify-center">
                      <span class="text-xs font-bold text-primary-400">{{ review.user.charAt(0) }}</span>
                    </div>
                    <div>
                      <div class="text-sm font-medium text-white">{{ review.user }}</div>
                      <div class="text-xs text-dark-200">{{ review.date }}</div>
                    </div>
                  </div>
                  <div class="flex items-center gap-0.5">
                    <Star v-for="s in 5" :key="s" :size="10" :class="s <= review.rating ? 'text-amber-400 fill-amber-400' : 'text-dark-300'" />
                  </div>
                </div>
                <p class="text-sm text-dark-100 leading-relaxed">{{ review.content }}</p>
                <div class="flex items-center gap-3 mt-2">
                  <button class="flex items-center gap-1 text-xs text-dark-200 hover:text-primary-400 transition-colors">
                    <ThumbsUp :size="12" /> {{ review.likes }}
                  </button>
                </div>
              </div>
            </div>
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
    <div v-else class="page-container max-w-none pt-24 text-center py-20">
      <p class="text-dark-100 text-lg">信号不存在</p>
      <router-link to="/system/signals" class="btn-outline mt-4 inline-block">返回信号广场</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Radio, ChevronRight, TrendingUp, Layers, Copy, Building, Clock, Activity, Shield, BarChart3, Bell, ArrowUpCircle, ArrowDownCircle, User, Star, MessageSquare, ThumbsUp, Calendar, Award, TrendingDown } from 'lucide-vue-next'
import StatusDot from '@/components/common/StatusDot.vue'
import ReturnCurveChart from '@/components/charts/ReturnCurveChart.vue'
import TradingChart from '@/components/charts/TradingChart.vue'
import MonthlyReturnChart from '@/components/charts/MonthlyReturnChart.vue'
import DrawdownChart from '@/components/charts/DrawdownChart.vue'
import type { KlineDataPoint, IndicatorData, TradeMarkData } from '@/components/charts/TradingChart.vue'
import { signals } from '@/utils/mockData'

const route = useRoute()
const signal = computed(() => signals.find((s) => s.id === route.params.id))

const followConfig = ref({
  amount: 1000,
  ratio: '1',
  stopLoss: 10,
})

// ==================== K线图表相关 ====================

const selectedTimeframe = ref('1H')
const timeframeOptions = ['15m', '1H', '4H', '1D', '1W']

const availableIndicators = [
  { key: 'ma', label: 'MA' },
  { key: 'macd', label: 'MACD' },
  { key: 'rsi', label: 'RSI' },
]
const activeIndicators = ref<string[]>(['ma', 'macd'])

function toggleIndicator(key: string) {
  const idx = activeIndicators.value.indexOf(key)
  if (idx >= 0) {
    activeIndicators.value.splice(idx, 1)
  } else {
    activeIndicators.value.push(key)
  }
}

// 生成模拟K线数据 (200根K线)
function generateMockKline(count = 200): KlineDataPoint[] {
  const data: KlineDataPoint[] = []
  const now = Math.floor(Date.now() / 1000)
  const interval = 3600 // 1小时
  let price = 91000 + Math.random() * 2000

  for (let i = 0; i < count; i++) {
    const time = now - (count - i) * interval
    const change = (Math.random() - 0.48) * price * 0.015
    const open = price
    const close = open + change
    const high = Math.max(open, close) + Math.random() * price * 0.005
    const low = Math.min(open, close) - Math.random() * price * 0.005
    const volume = Math.floor(50 + Math.random() * 500)
    data.push({ time, open, high, low, close, volume })
    price = close
  }
  return data
}

const klineData = ref<KlineDataPoint[]>(generateMockKline())

// 计算MA指标
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

// 计算MACD指标
function calcMACD(data: KlineDataPoint[]): { macd: Array<{ time: number; value: number }>; signal: Array<{ time: number; value: number }>; histogram: Array<{ time: number; value: number }> } {
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

function calcEMA(data: number[], period: number): number[] {
  const k = 2 / (period + 1)
  const result: number[] = [data[0]]
  for (let i = 1; i < data.length; i++) {
    result.push(data[i] * k + result[i - 1] * (1 - k))
  }
  return result
}

// 计算RSI
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
      const rsi = 100 - (100 / (1 + rs))
      result.push({ time: data[i].time, value: rsi })
    }
  }
  return result
}

// 组合指标数据
const chartIndicators = computed<IndicatorData[]>(() => {
  const indicators: IndicatorData[] = []
  const data = klineData.value
  
  if (activeIndicators.value.includes('ma')) {
    indicators.push(
      { name: 'MA7', type: 'line', color: '#f59e0b', pane: 'main', data: calcMA(data, 7) },
      { name: 'MA25', type: 'line', color: '#3b82f6', pane: 'main', data: calcMA(data, 25) },
      { name: 'MA99', type: 'line', color: '#a855f7', pane: 'main', data: calcMA(data, 99) },
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

// 生成模拟买卖点标记
const tradeMarks = computed<TradeMarkData[]>(() => {
  const data = klineData.value
  const marks: TradeMarkData[] = []
  // 在K线数据中每隔15-30根选一些作为买卖信号
  let i = 20
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
    i += 15 + Math.floor(Math.random() * 20)
  }
  return marks
})

// ==================== 信号历史记录 ====================

const signalHistory = computed(() => {
  const pair = signal.value?.tradingPair || 'BTC/USDT'
  return [
    { id: '1', action: 'buy', symbol: pair, price: 89234.50, amount: 0.055, time: '2025-02-25 14:30:00', strength: '强', pnl: undefined },
    { id: '2', action: 'sell', symbol: 'ETH/USDT', price: 3521.23, amount: 1.42, time: '2025-02-24 10:15:00', strength: '中', pnl: 91.52 },
    { id: '3', action: 'buy', symbol: 'ETH/USDT', price: 3456.78, amount: 1.45, time: '2025-02-23 16:45:00', strength: '强', pnl: 64.45 },
    { id: '4', action: 'sell', symbol: pair, price: 90123.45, amount: 0.05, time: '2025-02-22 09:20:00', strength: '强', pnl: 156.78 },
    { id: '5', action: 'buy', symbol: pair, price: 86993.80, amount: 0.05, time: '2025-02-21 11:20:00', strength: '中', pnl: 312.50 },
    { id: '6', action: 'sell', symbol: 'SOL/USDT', price: 178.55, amount: 12.5, time: '2025-02-20 08:45:00', strength: '弱', pnl: -45.30 },
    { id: '7', action: 'buy', symbol: 'SOL/USDT', price: 182.10, amount: 12.5, time: '2025-02-19 15:30:00', strength: '中', pnl: -44.38 },
    { id: '8', action: 'sell', symbol: pair, price: 88650.00, amount: 0.06, time: '2025-02-18 12:00:00', strength: '强', pnl: 225.60 },
  ]
})

// ==================== 信号提供者信息 ====================

const signalProvider = {
  name: 'CryptoMaster',
  verified: true,
  bio: '8年加密货币交易经验，擅长趋势跟踪和量化分析。前对冲基金量化研究员，专注于BTC/ETH主流币种交易。',
  totalSignals: 12,
  avgReturn: 23.5,
  totalFollowers: 8420,
  rating: 4.6,
  joinDate: '2023-06-15',
  experience: '8年',
}

// ==================== 月度收益分布 ====================

const monthlyReturnData = [5.2, -1.8, 8.3, 3.1, -4.5, 12.6, 7.8, -2.3, 6.4, 9.1, -0.8, 4.7]
const monthlyReturnLabels = ['2024-03', '2024-04', '2024-05', '2024-06', '2024-07', '2024-08', '2024-09', '2024-10', '2024-11', '2024-12', '2025-01', '2025-02']

const monthlyStats = computed(() => {
  const profitMonths = monthlyReturnData.filter(v => v >= 0).length
  const lossMonths = monthlyReturnData.filter(v => v < 0).length
  const bestMonth = Math.max(...monthlyReturnData).toFixed(1)
  return { profitMonths, lossMonths, bestMonth }
})

// ==================== 回撤分析 ====================

const drawdownLabels = computed(() => signal.value?.returnCurveLabels || [])
const drawdownData = computed(() => {
  // 从收益曲线计算回撤
  const curve = signal.value?.returnCurve || []
  const dd: number[] = []
  let peak = -Infinity
  for (const val of curve) {
    if (val > peak) peak = val
    dd.push(peak > 0 ? Math.min(0, val - peak) : 0)
  }
  return dd
})

const drawdownStats = computed(() => {
  const data = drawdownData.value
  const max = data.length ? Math.min(...data) : 0
  const avg = data.length ? data.reduce((a, b) => a + b, 0) / data.length : 0
  const current = data.length ? data[data.length - 1] : 0
  return { max, avg, current }
})

// ==================== 用户评价 ====================

const ratingDistribution: Record<number, number> = { 5: 45, 4: 30, 3: 15, 2: 7, 1: 3 }

const userReviews = [
  { id: '1', user: 'Trader_John', date: '2025-02-20', rating: 5, content: '信号质量很高，跟单两个月了收益很稳定。止损设置合理，回撤控制得很好。强烈推荐！', likes: 24 },
  { id: '2', user: 'CryptoFan88', date: '2025-02-18', rating: 4, content: '整体不错，信号准确率很高。偶尔有延迟，希望能优化一下推送速度。', likes: 15 },
  { id: '3', user: 'InvestorPro', date: '2025-02-15', rating: 5, content: '已跟单3个月，累计收益超过20%，非常满意。信号频率适中，不会过度交易。', likes: 31 },
  { id: '4', user: 'NewbieTD', date: '2025-02-12', rating: 4, content: '作为新手来说很友好，信号说明清晰，风险控制也很到位。扣一星是因为有时候信号来的时候价格已经变了。', likes: 12 },
  { id: '5', user: 'WhaleHunter', date: '2025-02-08', rating: 3, content: '信号不错但近期表现一般，希望后续能恢复之前的水平。', likes: 8 },
]
</script>