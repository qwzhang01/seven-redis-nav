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
      <t-select v-model="filterStatus" placeholder="状态" clearable size="medium" style="width: 140px">
        <t-option label="运行中" value="active" />
        <t-option label="已停止" value="stopped" />
      </t-select>
      <t-select v-model="filterRisk" placeholder="风险等级" clearable size="medium" style="width: 140px">
        <t-option label="低风险" value="low" />
        <t-option label="中风险" value="medium" />
        <t-option label="高风险" value="high" />
      </t-select>
    </div>

    <!-- Table -->
    <div class="glass-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-white/[0.06]">
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">策略名称</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">市场</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">类型</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">风险</th>
              <th class="text-right py-3.5 px-5 text-dark-100 font-medium">收益率</th>
              <th class="text-center py-3.5 px-5 text-dark-100 font-medium">状态</th>
              <th class="text-center py-3.5 px-5 text-dark-100 font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in filteredList" :key="s.id" class="border-b border-white/[0.04] hover:bg-white/[0.02]">
              <td class="py-3.5 px-5 text-white font-medium">{{ s.name }}</td>
              <td class="py-3.5 px-5 text-dark-100">{{ s.market }}</td>
              <td class="py-3.5 px-5 text-dark-100">{{ s.type }}</td>
              <td class="py-3.5 px-5"><RiskBadge :level="s.riskLevel" /></td>
              <td class="py-3.5 px-5 text-right font-medium" :class="s.returnRate >= 0 ? 'text-emerald-400' : 'text-red-400'">
                {{ s.returnRate >= 0 ? '+' : '' }}{{ s.returnRate }}%
              </td>
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

const filteredList = computed(() => {
  return strategies.filter((s) => {
    if (search.value && !s.name.toLowerCase().includes(search.value.toLowerCase())) return false
    if (filterStatus.value && s.status !== filterStatus.value) return false
    if (filterRisk.value && s.riskLevel !== filterRisk.value) return false
    return true
  })
})
</script>
