<template>
  <div class="space-y-6">
    <h2 class="text-xl font-bold text-white">排行榜规则配置</h2>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Ranking Rules -->
      <div class="glass-card p-6">
        <h3 class="text-white font-bold mb-5">排序规则</h3>
        <div class="space-y-4">
          <div v-for="rule in rules" :key="rule.field" class="p-4 rounded-xl bg-dark-800/50 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-dark-600 flex items-center justify-center text-sm font-bold text-primary-400">
                {{ rule.priority }}
              </div>
              <div>
                <div class="text-white text-sm font-medium">{{ rule.label }}</div>
                <div class="text-xs text-dark-100">{{ rule.description }}</div>
              </div>
            </div>
            <t-switch v-model="rule.enabled" />
          </div>
        </div>
      </div>

      <!-- Display Settings -->
      <div class="glass-card p-6">
        <h3 class="text-white font-bold mb-5">展示设置</h3>
        <div class="space-y-5">
          <div>
            <label class="text-sm text-dark-100 mb-1.5 block">排行榜显示数量</label>
            <t-input v-model="displayCount" type="number" size="medium" placeholder="默认 20" />
          </div>
          <div>
            <label class="text-sm text-dark-100 mb-1.5 block">最低运行天数</label>
            <t-input v-model="minRunDays" type="number" size="medium" placeholder="默认 7" />
          </div>
          <div>
            <label class="text-sm text-dark-100 mb-1.5 block">最低跟随人数</label>
            <t-input v-model="minFollowers" type="number" size="medium" placeholder="默认 10" />
          </div>
          <div>
            <label class="text-sm text-dark-100 mb-1.5 block">更新频率</label>
            <t-select v-model="updateFrequency" size="medium" class="text-white" style="color: white !important;">
              <t-option label="实时" value="realtime" />
              <t-option label="每小时" value="hourly" />
              <t-option label="每日" value="daily" />
            </t-select>
          </div>
        </div>
        <button class="btn-primary w-full mt-6 !py-2.5 text-sm">保存设置</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'

const displayCount = ref(20)
const minRunDays = ref(7)
const minFollowers = ref(10)
const updateFrequency = ref('hourly')

const rules = reactive([
  { priority: 1, field: 'cumulativeReturn', label: '累计收益率', description: '按总收益率排序', enabled: true },
  { priority: 2, field: 'maxDrawdown', label: '最大回撤', description: '回撤越低排名越高', enabled: true },
  { priority: 3, field: 'runDays', label: '运行天数', description: '运行时间越长权重越高', enabled: true },
  { priority: 4, field: 'followers', label: '跟随人数', description: '跟随者越多排名越高', enabled: false },
  { priority: 5, field: 'sharpeRatio', label: '夏普比率', description: '风险调整后收益', enabled: false },
])
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
</style>
