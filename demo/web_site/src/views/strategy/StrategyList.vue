<template>
  <div class="pt-24 pb-16">
    <div class="page-container">
      <!-- Header -->
      <div class="mb-10">
        <h1 class="text-3xl md:text-4xl font-extrabold text-white mb-3">系统策略</h1>
        <p class="text-dark-100 text-lg">精选量化交易策略，助力您的投资决策</p>
      </div>

      <!-- Filters -->
      <div class="glass-card p-5 mb-8">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label class="text-xs text-dark-100 mb-1.5 block">市场类型</label>
            <t-select v-model="filters.market" placeholder="全部市场" clearable size="medium" :popup-props="{ overlayClassName: 'dark-select' }">
              <t-option v-for="m in markets" :key="m" :label="m" :value="m" />
            </t-select>
          </div>
          <div>
            <label class="text-xs text-dark-100 mb-1.5 block">策略类型</label>
            <t-select v-model="filters.type" placeholder="全部类型" clearable size="medium">
              <t-option v-for="t in types" :key="t" :label="t" :value="t" />
            </t-select>
          </div>
          <div>
            <label class="text-xs text-dark-100 mb-1.5 block">风险等级</label>
            <t-select v-model="filters.risk" placeholder="全部等级" clearable size="medium">
              <t-option label="低风险" value="low" />
              <t-option label="中风险" value="medium" />
              <t-option label="高风险" value="high" />
            </t-select>
          </div>
          <div class="flex items-end">
            <t-input v-model="filters.search" placeholder="搜索策略名称..." clearable size="medium">
              <template #prefix-icon><Search :size="16" class="text-dark-100" /></template>
            </t-input>
          </div>
        </div>
      </div>

      <!-- Results Count -->
      <div class="flex items-center justify-between mb-6">
        <span class="text-sm text-dark-100">共 {{ filteredStrategies.length }} 个策略</span>
        <div class="flex items-center gap-2">
          <button
            v-for="view in ['grid', 'list'] as const"
            :key="view"
            @click="viewMode = view"
            class="p-2 rounded-lg transition-all"
            :class="viewMode === view ? 'bg-primary-500/10 text-primary-500' : 'text-dark-100 hover:text-white'"
          >
            <LayoutGrid v-if="view === 'grid'" :size="16" />
            <List v-else :size="16" />
          </button>
        </div>
      </div>

      <!-- Strategy Cards -->
      <div :class="viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'">
        <div
          v-for="strategy in paginatedStrategies"
          :key="strategy.id"
          class="glass-card-hover p-6 cursor-pointer"
          :class="viewMode === 'list' ? 'flex items-center gap-6' : ''"
          @click="$router.push(`/system/strategies/${strategy.id}`)"
        >
          <!-- Grid View -->
          <template v-if="viewMode === 'grid'">
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center">
                  <Zap :size="18" class="text-primary-400" />
                </div>
                <div>
                  <h3 class="text-white font-semibold text-sm">{{ strategy.name }}</h3>
                  <span class="text-xs text-dark-100">{{ strategy.market }}</span>
                </div>
              </div>
              <RiskBadge :level="strategy.riskLevel" />
            </div>
            <p class="text-sm text-dark-100 mb-4 line-clamp-2">{{ strategy.description }}</p>
            <div class="grid grid-cols-3 gap-3 mb-4">
              <div class="text-center p-2.5 rounded-lg bg-dark-800/50">
                <div class="text-sm font-bold" :class="strategy.returnRate >= 0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ strategy.returnRate >= 0 ? '+' : '' }}{{ strategy.returnRate }}%
                </div>
                <div class="text-[10px] text-dark-100 mt-0.5">收益率</div>
              </div>
              <div class="text-center p-2.5 rounded-lg bg-dark-800/50">
                <div class="text-sm font-bold text-amber-400">{{ strategy.maxDrawdown }}%</div>
                <div class="text-[10px] text-dark-100 mt-0.5">最大回撤</div>
              </div>
              <div class="text-center p-2.5 rounded-lg bg-dark-800/50">
                <div class="text-sm font-bold text-white">{{ strategy.runDays }}天</div>
                <div class="text-[10px] text-dark-100 mt-0.5">运行时间</div>
              </div>
            </div>
            <div class="flex items-center justify-between pt-3 border-t border-white/[0.06]">
              <span class="text-xs text-dark-100">{{ strategy.type }}</span>
              <span class="text-xs text-primary-500 font-medium">查看详情 →</span>
            </div>
          </template>

          <!-- List View -->
          <template v-else>
            <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center shrink-0">
              <Zap :size="18" class="text-primary-400" />
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="text-white font-semibold text-sm">{{ strategy.name }}</h3>
              <p class="text-xs text-dark-100 truncate">{{ strategy.description }}</p>
            </div>
            <div class="hidden sm:flex items-center gap-6">
              <div class="text-center">
                <div class="text-sm font-bold" :class="strategy.returnRate >= 0 ? 'text-emerald-400' : 'text-red-400'">{{ strategy.returnRate >= 0 ? '+' : '' }}{{ strategy.returnRate }}%</div>
                <div class="text-[10px] text-dark-100">收益率</div>
              </div>
              <div class="text-center">
                <div class="text-sm font-bold text-amber-400">{{ strategy.maxDrawdown }}%</div>
                <div class="text-[10px] text-dark-100">回撤</div>
              </div>
            </div>
            <RiskBadge :level="strategy.riskLevel" />
            <ArrowRight :size="16" class="text-dark-100 shrink-0" />
          </template>
        </div>
      </div>

      <!-- Empty -->
      <div v-if="filteredStrategies.length === 0" class="text-center py-20">
        <SearchX :size="48" class="text-dark-300 mx-auto mb-4" />
        <p class="text-dark-100">未找到匹配的策略</p>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="mt-10 flex justify-center">
        <t-pagination
          v-model:current="currentPage"
          :total="filteredStrategies.length"
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
import { Zap, Search, LayoutGrid, List, ArrowRight, SearchX } from 'lucide-vue-next'
import RiskBadge from '@/components/common/RiskBadge.vue'
import { strategies } from '@/utils/mockData'

const viewMode = ref<'grid' | 'list'>('grid')
const currentPage = ref(1)
const pageSize = 9

const filters = ref({
  market: '',
  type: '',
  risk: '',
  search: '',
})

const markets = [...new Set(strategies.map((s) => s.market))]
const types = [...new Set(strategies.map((s) => s.type))]

const filteredStrategies = computed(() => {
  return strategies.filter((s) => {
    if (filters.value.market && s.market !== filters.value.market) return false
    if (filters.value.type && s.type !== filters.value.type) return false
    if (filters.value.risk && s.riskLevel !== filters.value.risk) return false
    if (filters.value.search && !s.name.toLowerCase().includes(filters.value.search.toLowerCase())) return false
    return true
  })
})

const totalPages = computed(() => Math.ceil(filteredStrategies.value.length / pageSize))
const paginatedStrategies = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredStrategies.value.slice(start, start + pageSize)
})
</script>
