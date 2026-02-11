<template>
  <div class="pt-24 pb-16">
    <div class="page-container">
      <!-- Header -->
      <div class="mb-10">
        <h1 class="text-3xl md:text-4xl font-extrabold text-white mb-3">信号广场</h1>
        <p class="text-dark-100 text-lg">发现并跟随优质交易信号，一键复制顶级交易者策略</p>
      </div>

      <!-- Filters -->
      <div class="glass-card p-5 mb-8">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label class="text-xs text-dark-100 mb-1.5 block">来源平台</label>
            <t-select v-model="filters.platform" placeholder="全部平台" clearable size="medium">
              <t-option v-for="p in platforms" :key="p" :label="p" :value="p" />
            </t-select>
          </div>
          <div>
            <label class="text-xs text-dark-100 mb-1.5 block">信号类型</label>
            <t-select v-model="filters.type" placeholder="全部类型" clearable size="medium">
              <t-option label="实盘" value="live" />
              <t-option label="模拟盘" value="simulated" />
            </t-select>
          </div>
          <div>
            <label class="text-xs text-dark-100 mb-1.5 block">运行天数</label>
            <t-select v-model="filters.minDays" placeholder="不限" clearable size="medium">
              <t-option label="≥ 7天" :value="7" />
              <t-option label="≥ 30天" :value="30" />
              <t-option label="≥ 90天" :value="90" />
              <t-option label="≥ 180天" :value="180" />
            </t-select>
          </div>
          <div>
            <label class="text-xs text-dark-100 mb-1.5 block">排序方式</label>
            <t-select v-model="sortBy" size="medium">
              <t-option label="收益率(高→低)" value="returnDesc" />
              <t-option label="收益率(低→高)" value="returnAsc" />
              <t-option label="回撤(低→高)" value="drawdownAsc" />
              <t-option label="跟随人数" value="followers" />
            </t-select>
          </div>
          <div class="flex items-end">
            <t-input v-model="filters.search" placeholder="搜索信号..." clearable size="medium">
              <template #prefix-icon><Search :size="16" class="text-dark-100" /></template>
            </t-input>
          </div>
        </div>
      </div>

      <!-- Results -->
      <div class="flex items-center justify-between mb-6">
        <span class="text-sm text-dark-100">共 {{ filteredSignals.length }} 个信号</span>
      </div>

      <!-- Signal Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="signal in paginatedSignals"
          :key="signal.id"
          class="glass-card-hover p-6 cursor-pointer group"
          @click="$router.push(`/signals/${signal.id}`)"
        >
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-blue/20 to-accent-purple/20 flex items-center justify-center">
                <Radio :size="18" class="text-blue-400" />
              </div>
              <div>
                <h4 class="text-white font-semibold text-sm group-hover:text-primary-400 transition-colors">{{ signal.name }}</h4>
                <div class="flex items-center gap-2">
                  <span class="text-xs text-dark-100">{{ signal.platform }}</span>
                  <span class="text-[10px] px-1.5 py-0.5 rounded"
                        :class="signal.type === 'live' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-blue-500/10 text-blue-400'">
                    {{ signal.type === 'live' ? '实盘' : '模拟' }}
                  </span>
                </div>
              </div>
            </div>
            <StatusDot :status="signal.status" />
          </div>

          <div class="grid grid-cols-2 gap-3 mb-4">
            <div class="p-3 rounded-lg bg-dark-800/50 text-center">
              <div class="text-lg font-bold" :class="signal.cumulativeReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
                {{ signal.cumulativeReturn >= 0 ? '+' : '' }}{{ signal.cumulativeReturn.toFixed(2) }}%
              </div>
              <div class="text-[10px] text-dark-100 mt-0.5">累计收益率</div>
            </div>
            <div class="p-3 rounded-lg bg-dark-800/50 text-center">
              <div class="text-lg font-bold text-amber-400">{{ signal.maxDrawdown.toFixed(2) }}%</div>
              <div class="text-[10px] text-dark-100 mt-0.5">最大回撤</div>
            </div>
          </div>

          <ReturnCurveChart
            v-if="signal.returnCurve?.length"
            :data="signal.returnCurve"
            :height="90"
            :color="signal.cumulativeReturn >= 0 ? '#10b981' : '#ef4444'"
          />

          <div class="flex items-center justify-between mt-4 pt-3 border-t border-white/[0.06]">
            <div class="flex items-center gap-4">
              <span class="text-xs text-dark-100"><Users :size="12" class="inline mr-1" />{{ signal.followers }}</span>
              <span class="text-xs text-dark-100"><Clock :size="12" class="inline mr-1" />{{ signal.runDays }}天</span>
            </div>
            <span class="text-xs text-primary-500 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
              查看详情 →
            </span>
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div v-if="filteredSignals.length === 0" class="text-center py-20">
        <SearchX :size="48" class="text-dark-300 mx-auto mb-4" />
        <p class="text-dark-100">未找到匹配的信号</p>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="mt-10 flex justify-center">
        <t-pagination
          v-model:current="currentPage"
          :total="filteredSignals.length"
          :page-size="pageSize"
          :show-page-size="false"
          theme="simple"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Radio, Search, Users, Clock, SearchX } from 'lucide-vue-next'
import StatusDot from '@/components/common/StatusDot.vue'
import ReturnCurveChart from '@/components/charts/ReturnCurveChart.vue'
import { signals } from '@/utils/mockData'

const currentPage = ref(1)
const pageSize = 9
const sortBy = ref('returnDesc')

const filters = ref({
  platform: '',
  type: '',
  minDays: null as number | null,
  search: '',
})

const platforms = [...new Set(signals.map((s) => s.platform))]

const filteredSignals = computed(() => {
  let result = signals.filter((s) => {
    if (filters.value.platform && s.platform !== filters.value.platform) return false
    if (filters.value.type && s.type !== filters.value.type) return false
    if (filters.value.minDays && s.runDays < filters.value.minDays) return false
    if (filters.value.search && !s.name.toLowerCase().includes(filters.value.search.toLowerCase())) return false
    return true
  })

  switch (sortBy.value) {
    case 'returnDesc': result.sort((a, b) => b.cumulativeReturn - a.cumulativeReturn); break
    case 'returnAsc': result.sort((a, b) => a.cumulativeReturn - b.cumulativeReturn); break
    case 'drawdownAsc': result.sort((a, b) => a.maxDrawdown - b.maxDrawdown); break
    case 'followers': result.sort((a, b) => b.followers - a.followers); break
  }
  return result
})

const totalPages = computed(() => Math.ceil(filteredSignals.value.length / pageSize))
const paginatedSignals = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredSignals.value.slice(start, start + pageSize)
})
</script>
