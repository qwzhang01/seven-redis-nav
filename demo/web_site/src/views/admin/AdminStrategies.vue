<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold text-white">策略管理</h2>
      <button class="btn-primary !py-2 !px-4 text-sm flex items-center gap-1.5">
        <Plus :size="14" /> 新增策略
      </button>
    </div>

    <!-- Filters -->
    <div class="glass-card p-4 flex flex-wrap items-center gap-4">
      <t-input v-model="search" placeholder="搜索策略..." clearable size="medium" style="width: 240px">
        <template #prefix-icon><Search :size="16" class="text-dark-100" /></template>
      </t-input>
      <t-select v-model="filterStatus" placeholder="状态" clearable size="medium" style="width: 140px; color: white !important;" class="text-white">
        <t-option label="运行中" value="active" />
        <t-option label="已停止" value="stopped" />
      </t-select>
      <t-select v-model="filterRisk" placeholder="风险等级" clearable size="medium" style="width: 140px; color: white !important;" class="text-white">
        <t-option label="低风险" value="low" />
        <t-option label="中风险" value="medium" />
        <t-option label="高风险" value="high" />
      </t-select>
      <t-select v-model="filterExchange" placeholder="交易所" clearable size="medium" style="width: 160px; color: white !important;" class="text-white">
        <t-option label="Binance" value="Binance" />
        <t-option label="OKX" value="OKX" />
        <t-option label="Bybit" value="Bybit" />
        <t-option label="Bitget" value="Bitget" />
        <t-option label="Gate.io" value="Gate.io" />
        <t-option label="Huobi" value="Huobi" />
        <t-option label="Kraken" value="Kraken" />
        <t-option label="Coinbase" value="Coinbase" />
      </t-select>
      <t-select v-model="filterTimeframe" placeholder="时间周期" clearable size="medium" style="width: 140px; color: white !important;" class="text-white">
        <t-option label="1分钟" value="1m" />
        <t-option label="5分钟" value="5m" />
        <t-option label="15分钟" value="15m" />
        <t-option label="1小时" value="1h" />
        <t-option label="4小时" value="4h" />
        <t-option label="日线" value="1d" />
        <t-option label="周线" value="1w" />
      </t-select>
    </div>

    <!-- Table -->
    <div class="glass-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-white/[0.06]">
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">策略名称</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">交易所</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">交易对</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">时间周期</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">类型</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">风险</th>
              <th class="text-right py-3.5 px-5 text-dark-100 font-medium">收益率</th>
              <th class="text-right py-3.5 px-5 text-dark-100 font-medium">最大回撤</th>
              <th class="text-center py-3.5 px-5 text-dark-100 font-medium">状态</th>
              <th class="text-center py-3.5 px-5 text-dark-100 font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in filteredList" :key="s.id" class="border-b border-white/[0.04] hover:bg-white/[0.02]">
              <td class="py-3.5 px-5 text-white font-medium">{{ s.name }}</td>
              <td class="py-3.5 px-5 text-dark-100">{{ s.exchange }}</td>
              <td class="py-3.5 px-5 text-dark-100">{{ s.tradingPair }}</td>
              <td class="py-3.5 px-5 text-dark-100">{{ s.timeframe }}</td>
              <td class="py-3.5 px-5 text-dark-100">{{ s.type }}</td>
              <td class="py-3.5 px-5"><RiskBadge :level="s.riskLevel" /></td>
              <td class="py-3.5 px-5 text-right font-medium" :class="s.returnRate >= 0 ? 'text-emerald-400' : 'text-red-400'">
                {{ s.returnRate >= 0 ? '+' : '' }}{{ s.returnRate }}%
              </td>
              <td class="py-3.5 px-5 text-right text-amber-400">{{ s.maxDrawdown }}%</td>
              <td class="py-3.5 px-5 text-center"><StatusDot :status="s.status" /></td>
              <td class="py-3.5 px-5 text-center">
                <div class="flex items-center justify-center gap-1">
                  <button class="p-1.5 rounded text-dark-100 hover:text-primary-500 hover:bg-primary-500/10 transition-all"><Pencil :size="14" /></button>
                  <button class="p-1.5 rounded text-dark-100 hover:text-red-400 hover:bg-red-500/10 transition-all"><Trash2 :size="14" /></button>
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
import { ref, computed } from 'vue'
import { Plus, Search, Pencil, Trash2 } from 'lucide-vue-next'
import RiskBadge from '@/components/common/RiskBadge.vue'
import StatusDot from '@/components/common/StatusDot.vue'
import { strategies } from '@/utils/mockData'

const search = ref('')
const filterStatus = ref('')
const filterRisk = ref('')
const filterExchange = ref('')
const filterTimeframe = ref('')

const filteredList = computed(() => {
  return strategies.filter((s) => {
    if (search.value && !s.name.toLowerCase().includes(search.value.toLowerCase())) return false
    if (filterStatus.value && s.status !== filterStatus.value) return false
    if (filterRisk.value && s.riskLevel !== filterRisk.value) return false
    if (filterExchange.value && s.exchange !== filterExchange.value) return false
    if (filterTimeframe.value && s.timeframe !== filterTimeframe.value) return false
    return true
  })
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