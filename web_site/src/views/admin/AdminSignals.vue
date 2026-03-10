<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold text-white">信号接入与验证</h2>
      <button class="btn-primary !py-2 !px-4 text-sm flex items-center gap-1.5">
        <Plus :size="14" /> 接入新信号
      </button>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="glass-card p-5 flex items-center gap-4">
        <div class="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
          <CheckCircle :size="20" class="text-emerald-400" />
        </div>
        <div>
          <div class="text-xl font-bold text-white">124</div>
          <div class="text-sm text-dark-100">已验证信号</div>
        </div>
      </div>
      <div class="glass-card p-5 flex items-center gap-4">
        <div class="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
          <Clock :size="20" class="text-amber-400" />
        </div>
        <div>
          <div class="text-xl font-bold text-white">32</div>
          <div class="text-sm text-dark-100">待审核</div>
        </div>
      </div>
      <div class="glass-card p-5 flex items-center gap-4">
        <div class="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
          <XCircle :size="20" class="text-red-400" />
        </div>
        <div>
          <div class="text-xl font-bold text-white">8</div>
          <div class="text-sm text-dark-100">已拒绝</div>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="glass-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-white/[0.06]">
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">信号名称</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">交易所</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">交易对</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">时间周期</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">平台</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">类型</th>
              <th class="text-right py-3.5 px-5 text-dark-100 font-medium">收益率</th>
              <th class="text-right py-3.5 px-5 text-dark-100 font-medium">最大回撤</th>
              <th class="text-right py-3.5 px-5 text-dark-100 font-medium">跟随人数</th>
              <th class="text-center py-3.5 px-5 text-dark-100 font-medium">状态</th>
              <th class="text-center py-3.5 px-5 text-dark-100 font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in signalList" :key="s.id" class="border-b border-white/[0.04] hover:bg-white/[0.02]">
              <td class="py-3.5 px-5 text-white font-medium">{{ s.name }}</td>
              <td class="py-3.5 px-5 text-dark-100">{{ s.exchange }}</td>
              <td class="py-3.5 px-5 text-dark-100">{{ s.tradingPair }}</td>
              <td class="py-3.5 px-5 text-dark-100">{{ s.timeframe }}</td>
              <td class="py-3.5 px-5 text-dark-100">{{ s.platform }}</td>
              <td class="py-3.5 px-5">
                <span class="text-xs px-2 py-0.5 rounded" :class="s.type === 'live' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-blue-500/10 text-blue-400'">
                  {{ s.type === 'live' ? '实盘' : '模拟' }}
                </span>
              </td>
              <td class="py-3.5 px-5 text-right font-medium" :class="s.cumulativeReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
                {{ s.cumulativeReturn >= 0 ? '+' : '' }}{{ s.cumulativeReturn.toFixed(2) }}%
              </td>
              <td class="py-3.5 px-5 text-right text-amber-400">{{ s.maxDrawdown.toFixed(2) }}%</td>
              <td class="py-3.5 px-5 text-right text-dark-100">{{ s.followers.toLocaleString() }}</td>
              <td class="py-3.5 px-5 text-center"><StatusDot :status="s.status" /></td>
              <td class="py-3.5 px-5 text-center">
                <div class="flex items-center justify-center gap-1">
                  <button class="p-1.5 rounded text-dark-100 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all"><CheckCircle :size="14" /></button>
                  <button class="p-1.5 rounded text-dark-100 hover:text-red-400 hover:bg-red-500/10 transition-all"><XCircle :size="14" /></button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Plus, CheckCircle, XCircle, Clock } from 'lucide-vue-next'
import StatusDot from '@/components/common/StatusDot.vue'
import { signals } from '@/utils/mockData'

const signalList = signals.slice(0, 15)
</script>