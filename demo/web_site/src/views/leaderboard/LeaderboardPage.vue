<template>
  <div class="pt-24 pb-16">
    <div class="page-container">
      <!-- Header -->
      <div class="mb-10">
        <h1 class="text-3xl md:text-4xl font-extrabold text-white mb-3">收益排行榜</h1>
        <p class="text-dark-100 text-lg">透明公开的信号收益排行，发现最优秀的交易者</p>
      </div>

      <!-- Sort Tabs -->
      <div class="glass-card p-1.5 mb-8 inline-flex gap-1">
        <button
          v-for="tab in sortTabs"
          :key="tab.value"
          @click="sortBy = tab.value"
          class="px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
          :class="sortBy === tab.value ? 'bg-primary-500/15 text-primary-400' : 'text-dark-100 hover:text-white hover:bg-white/[0.04]'"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Top 3 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div
          v-for="(item, index) in top3"
          :key="item.id"
          class="glass-card p-6 relative overflow-hidden cursor-pointer group"
          :class="index === 0 ? 'ring-1 ring-amber-500/30 md:order-2' : index === 1 ? 'md:order-1' : 'md:order-3'"
          @click="$router.push(`/system/signals/${item.id}`)"
        >
          <!-- Rank Badge -->
          <div class="absolute top-0 right-0 w-16 h-16">
            <div class="absolute top-2 right-2 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                 :class="[
                   index === 0 ? 'bg-amber-500/20 text-amber-400' : index === 1 ? 'bg-gray-400/20 text-gray-300' : 'bg-orange-500/20 text-orange-400'
                 ]">
              {{ index + 1 }}
            </div>
          </div>

          <div class="flex items-center gap-3 mb-5">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br flex items-center justify-center"
                 :class="index === 0 ? 'from-amber-500/20 to-orange-500/20' : 'from-primary-500/20 to-accent-blue/20'">
              <Trophy v-if="index === 0" :size="22" class="text-amber-400" />
              <Medal v-else :size="22" class="text-primary-400" />
            </div>
            <div>
              <h3 class="text-white font-bold group-hover:text-primary-400 transition-colors">{{ item.name }}</h3>
              <span class="text-xs text-dark-100">{{ item.platform }}</span>
            </div>
          </div>

          <div class="text-center mb-4">
            <div class="text-3xl font-bold" :class="item.cumulativeReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
              {{ item.cumulativeReturn >= 0 ? '+' : '' }}{{ item.cumulativeReturn.toFixed(2) }}%
            </div>
            <div class="text-xs text-dark-100 mt-1">累计收益率</div>
          </div>

          <div class="grid grid-cols-3 gap-2 text-center">
            <div class="p-2 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-amber-400">{{ item.maxDrawdown.toFixed(1) }}%</div>
              <div class="text-[10px] text-dark-100">最大回撤</div>
            </div>
            <div class="p-2 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-white">{{ item.runDays }}天</div>
              <div class="text-[10px] text-dark-100">运行天数</div>
            </div>
            <div class="p-2 rounded-lg bg-dark-800/50">
              <div class="text-sm font-bold text-primary-400">{{ item.followers }}</div>
              <div class="text-[10px] text-dark-100">跟随人数</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Leaderboard Table -->
      <div class="glass-card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-white/[0.06]">
                <th class="text-left py-4 px-6 text-dark-100 font-medium w-16">排名</th>
                <th class="text-left py-4 px-6 text-dark-100 font-medium">信号名称</th>
                <th class="text-left py-4 px-6 text-dark-100 font-medium">来源平台</th>
                <th class="text-right py-4 px-6 text-dark-100 font-medium">累计收益率</th>
                <th class="text-right py-4 px-6 text-dark-100 font-medium">最大回撤</th>
                <th class="text-right py-4 px-6 text-dark-100 font-medium">运行天数</th>
                <th class="text-right py-4 px-6 text-dark-100 font-medium">跟随人数</th>
                <th class="text-center py-4 px-6 text-dark-100 font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, index) in tableItems"
                :key="item.id"
                class="border-b border-white/[0.04] hover:bg-white/[0.02] cursor-pointer transition-colors"
                @click="$router.push(`/system/signals/${item.id}`)"
              >
                <td class="py-4 px-6">
                  <span class="text-dark-100 font-mono">{{ index + 4 }}</span>
                </td>
                <td class="py-4 px-6">
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-lg bg-dark-600 flex items-center justify-center">
                      <Radio :size="14" class="text-primary-400" />
                    </div>
                    <span class="text-white font-medium">{{ item.name }}</span>
                  </div>
                </td>
                <td class="py-4 px-6 text-dark-100">{{ item.platform }}</td>
                <td class="py-4 px-6 text-right font-medium" :class="item.cumulativeReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ item.cumulativeReturn >= 0 ? '+' : '' }}{{ item.cumulativeReturn.toFixed(2) }}%
                </td>
                <td class="py-4 px-6 text-right text-amber-400">{{ item.maxDrawdown.toFixed(2) }}%</td>
                <td class="py-4 px-6 text-right text-dark-100">{{ item.runDays }}</td>
                <td class="py-4 px-6 text-right text-dark-100">{{ item.followers.toLocaleString() }}</td>
                <td class="py-4 px-6 text-center">
                  <button class="text-xs text-primary-500 hover:text-primary-400 font-medium transition-colors">
                    查看信号
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Trophy, Medal, Radio } from 'lucide-vue-next'
import { signals } from '@/utils/mockData'

const sortBy = ref('cumulativeReturn')

const sortTabs = [
  { label: '累计收益率', value: 'cumulativeReturn' },
  { label: '最大回撤', value: 'maxDrawdown' },
  { label: '运行天数', value: 'runDays' },
  { label: '跟随人数', value: 'followers' },
]

const sortedSignals = computed(() => {
  const list = [...signals].filter((s) => s.status === 'running')
  switch (sortBy.value) {
    case 'cumulativeReturn': list.sort((a, b) => b.cumulativeReturn - a.cumulativeReturn); break
    case 'maxDrawdown': list.sort((a, b) => a.maxDrawdown - b.maxDrawdown); break
    case 'runDays': list.sort((a, b) => b.runDays - a.runDays); break
    case 'followers': list.sort((a, b) => b.followers - a.followers); break
  }
  return list
})

const top3 = computed(() => sortedSignals.value.slice(0, 3))
const tableItems = computed(() => sortedSignals.value.slice(3, 23))
</script>
