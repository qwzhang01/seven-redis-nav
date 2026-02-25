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
            <label class="text-xs text-white-100 mb-1.5 block">市场类型</label>
            <t-select v-model="filters.market" placeholder="全部市场" clearable size="medium"
              :popup-props="{ overlayClassName: 'dark-select' }" class="text-white" @change="onFilterChange">
              <t-option v-for="m in markets" :key="m" :label="m" :value="m" />
            </t-select>
          </div>
          <div>
            <label class="text-xs text-white-100 mb-1.5 block">策略类型</label>
            <t-select v-model="filters.type" placeholder="全部类型" clearable size="medium" class="text-white" @change="onFilterChange">
              <t-option v-for="t in types" :key="t" :label="t" :value="t" />
            </t-select>
          </div>
          <div>
            <label class="text-xs text-white-100 mb-1.5 block">风险等级</label>
            <t-select v-model="filters.risk" placeholder="全部等级" clearable size="medium" class="text-white" @change="onFilterChange">
              <t-option label="低风险" value="low" />
              <t-option label="中风险" value="medium" />
              <t-option label="高风险" value="high" />
            </t-select>
          </div>
          <div class="flex items-end">
            <t-input v-model="filters.search" placeholder="搜索策略名称..." clearable size="medium" @change="onFilterChange">
              <template #prefix-icon>
                <Search :size="16" class="text-dark-100" />
              </template>
            </t-input>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-20">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
        <p class="text-dark-100 mt-4">加载中...</p>
      </div>

      <!-- Results Count -->
      <div v-else class="flex items-center justify-between mb-6">
        <span class="text-sm text-dark-100">共 {{ total }} 个策略</span>
        <div class="flex items-center gap-2">
          <button v-for="view in ['grid', 'list'] as const" :key="view" @click="viewMode = view"
            class="p-2 rounded-lg transition-all"
            :class="viewMode === view ? 'bg-primary-500/10 text-primary-500' : 'text-dark-100 hover:text-white'">
            <LayoutGrid v-if="view === 'grid'" :size="16" />
            <List v-else :size="16" />
          </button>
        </div>
      </div>

      <!-- Strategy Cards -->
      <div :class="viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'">
        <div v-for="strategy in paginatedStrategies" :key="strategy.id" class="glass-card-hover p-6 cursor-pointer"
          :class="viewMode === 'list' ? 'flex items-center gap-6' : ''"
          @click="$router.push(`/system/strategies/${strategy.id}`)">
          <!-- Grid View -->
          <template v-if="viewMode === 'grid'">
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-3">
                <div
                  class="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center">
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
            <div
              class="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center shrink-0">
              <Zap :size="18" class="text-primary-400" />
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="text-white font-semibold text-sm">{{ strategy.name }}</h3>
              <p class="text-xs text-dark-100 truncate">{{ strategy.description }}</p>
            </div>
            <div class="hidden sm:flex items-center gap-6">
              <div class="text-center">
                <div class="text-sm font-bold" :class="strategy.returnRate >= 0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ strategy.returnRate >= 0 ? '+' : '' }}{{ strategy.returnRate }}%</div>
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
      <div v-if="!loading && totalPages > 1" class="mt-10 flex justify-center">
        <t-pagination v-model:current="currentPage" :total="total" :page-size="pageSize"
          :show-page-size="false" theme="simple" @change="onPageChange" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Zap, Search, LayoutGrid, List, ArrowRight, SearchX } from 'lucide-vue-next'
import { MessagePlugin } from 'tdesign-vue-next'
import RiskBadge from '@/components/common/RiskBadge.vue'
import strategyApi, {
  getUserMarketType,
  getUserRiskLevel
} from '@/utils/strategyApi'
import systemApi from "@/utils/systemApi.ts";

const viewMode = ref<'grid' | 'list'>('grid')
const currentPage = ref(1)
const pageSize = 9
const loading = ref(false)
const strategies = ref<any[]>([])
const total = ref(0)

const filters = ref({
  market: '',
  type: '',
  risk: '',
  search: '',
})

const markets = ref<string[]>([])
const risks = ref<string[]>([])
const types = ref<string[]>([])

// 加载策略列表（系统预设策略）
async function loadStrategies() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize,
    }
    if (filters.value.search) params.keyword = filters.value.search
    if (filters.value.market) params.market_type = filters.value.market === '现货' ? 'spot' : filters.value.market === '合约' ? 'futures' : filters.value.market
    if (filters.value.type) params.strategy_type = filters.value.type
    if (filters.value.risk) params.risk_level = filters.value.risk

    const response = await strategyApi.getPresetStrategyList(params)
    strategies.value = (response.strategies || []).map((item: any) => ({
      ...item,
      id: item.id || item.strategy_id,
      market: item.symbols?.[0] || item.market || '',
      type: item.strategy_type || item.type || '',
      riskLevel: item.risk_level || item.riskLevel || 'medium',
      returnRate: item.total_return ?? item.returnRate ?? 0,
      maxDrawdown: item.max_drawdown ?? item.maxDrawdown ?? 0,
      runDays: item.running_days ?? item.runDays ?? 0,
      status: item.state || item.status || 'active',
    }))
    total.value = response.total || 0
  } catch (error) {
    console.error('加载策略失败:', error)
    MessagePlugin.error('加载策略失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 加载策略类型
async function loadStrategyTypes() {
  try {
    const response = await systemApi.getEnumByName("StrategyType")
    if (response?.items) {
      types.value = response.items.map((t: any) => t.label || t.value || t.name)
    }
  } catch (error) {
    console.error('加载策略类型失败:', error)
  }
}

async function loadRiskLevel() {
  try {
    const response = await systemApi.getEnumByName("RiskLevel")
    if (response?.items) {
      risks.value = response.items.map((t: any) => t.label || t.value || t.name)
    }
  } catch (error) {
    console.error('加载策略类型失败:', error)
  }
}

async function loadMarketType() {
  try {
    const response = await systemApi.getEnumByName("MarketType")
    if (response?.items) {
      markets.value = response.items.map((t: any) => t.label || t.value || t.name)
    }
  } catch (error) {
    console.error('加载策略类型失败:', error)
  }
}

const filteredStrategies = computed(() => {
  return strategies.value.filter((s) => {
    if (filters.value.market && s.market !== filters.value.market) return false
    if (filters.value.type && s.type !== filters.value.type) return false
    if (filters.value.risk && s.riskLevel !== filters.value.risk) return false
    if (filters.value.search && !s.name.toLowerCase().includes(filters.value.search.toLowerCase())) return false
    return true
  })
})

const totalPages = computed(() => Math.ceil(total.value / pageSize))
const paginatedStrategies = computed(() => {
  return filteredStrategies.value
})

// 填充市场类型下拉数据
const defaultMarkets = ['现货', '合约']
if (markets.value.length === 0) {
  markets.value = defaultMarkets
}

// 监听筛选条件变化
function onFilterChange() {
  currentPage.value = 1
  loadStrategies()
}

// 监听分页变化
function onPageChange(page: number) {
  currentPage.value = page
  loadStrategies()
}

// 页面加载时获取数据
onMounted(() => {
  loadStrategies()
  loadStrategyTypes()
  loadMarketType()
  loadRiskLevel()
})
</script>

<style scoped>
/* 确保下拉框占位符文本颜色为白色 */
:deep(.t-select .t-select__single-input),
:deep(.t-select .t-select__placeholder),
:deep(.t-select.t-is-empty .t-select__single-input),
:deep(.t-select.t-is-empty .t-select__placeholder) {
  color: #ffffff !important;
}

:deep(.t-select .t-select__single-input::placeholder),
:deep(.t-select .t-select__placeholder::placeholder) {
  color: #ffffff !important;
}

:deep(.t-select .t-select__single-input::-webkit-input-placeholder),
:deep(.t-select .t-select__placeholder::-webkit-input-placeholder) {
  color: #ffffff !important;
}

:deep(.t-select .t-select__single-input::-moz-placeholder),
:deep(.t-select .t-select__placeholder::-moz-placeholder) {
  color: #ffffff !important;
}

:deep(.t-select .t-select__single-input:-ms-input-placeholder),
:deep(.t-select .t-select__placeholder:-ms-input-placeholder) {
  color: #ffffff !important;
}

/* 针对实际DOM结构的下拉选项样式 */
:deep(.t-popup__content .t-select-option),
:deep(.t-select__dropdown-inner .t-select-option),
:deep(.t-select__list .t-select-option),
:deep(.t-select-option) {
  color: #ffffff !important;
}

:deep(.t-popup__content .t-select-option:hover),
:deep(.t-select__dropdown-inner .t-select-option:hover),
:deep(.t-select__list .t-select-option:hover),
:deep(.t-select-option:hover) {
  color: #ffffff !important;
}

/* 选中状态下的文本颜色改为黑色 */
:deep(.t-popup__content .t-select-option.t-is-selected),
:deep(.t-select__dropdown-inner .t-select-option.t-is-selected),
:deep(.t-select__list .t-select-option.t-is-selected),
:deep(.t-select-option.t-is-selected) {
  color: #000000 !important;
}

/* 确保下拉选项内的span元素也应用颜色 */
:deep(.t-select-option span),
:deep(.t-select-option.t-is-selected span) {
  color: inherit !important;
}

/* 针对下拉列表中的所有文本 */
:deep(.t-popup__content),
:deep(.t-popup__content *),
:deep(.t-select__dropdown-inner),
:deep(.t-select__dropdown-inner *),
:deep(.t-select__list),
:deep(.t-select__list *) {
  color: #ffffff !important;
}

:deep(.t-popup__content .t-select-option.t-is-selected),
:deep(.t-popup__content .t-select-option.t-is-selected *),
:deep(.t-select__dropdown-inner .t-select-option.t-is-selected),
:deep(.t-select__dropdown-inner .t-select-option.t-is-selected *),
:deep(.t-select__list .t-select-option.t-is-selected),
:deep(.t-select__list .t-select-option.t-is-selected *) {
  color: #000000 !important;
}
</style>
