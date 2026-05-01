<template>
  <div class="result-panel">
    <div v-if="!result" class="result-empty">执行结果将显示在此处</div>
    <div v-else-if="result.is_error" class="result-error">
      <i class="ri-error-warning-line" />
      <pre>{{ result.output }}</pre>
    </div>
    <div v-else class="result-content">
      <div class="result-header">
        <span class="result-type-badge" :class="typeClass">{{ result.value_type }}</span>
        <span class="result-time">{{ result.elapsed_ms }}ms</span>
      </div>
      <pre class="result-value" :class="typeClass">{{ formatValue(result) }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { LuaEvalResult } from '@/ipc/phase4'

const props = defineProps<{ result: LuaEvalResult | null }>()

const typeClass = computed(() => {
  if (!props.result) return ''
  switch (props.result.value_type) {
    case 'integer': return 'type-integer'
    case 'bulk_string': return 'type-string'
    case 'array': return 'type-array'
    case 'error': return 'type-error'
    default: return 'type-nil'
  }
})

function formatValue(result: LuaEvalResult): string {
  if (result.value === null || result.value === undefined) return '(nil)'
  if (Array.isArray(result.value)) {
    return result.value.map((v: unknown, i: number) => `${i + 1}) ${JSON.stringify(v)}`).join('\n')
  }
  return String(result.value)
}
</script>

<style scoped>
.result-panel { flex: 0 0 120px; overflow-y: auto; padding: 8px 12px; background: var(--bg-secondary, #f9fafb); }
.result-empty { font-size: 12px; color: var(--text-secondary, #9ca3af); }
.result-error { display: flex; align-items: flex-start; gap: 6px; color: #ef4444; }
.result-error pre { font-size: 12px; margin: 0; white-space: pre-wrap; }
.result-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.result-type-badge { font-size: 10px; padding: 1px 6px; border-radius: 10px; font-weight: 600; }
.result-time { font-size: 11px; color: var(--text-secondary, #9ca3af); }
.result-value { font-size: 12px; font-family: monospace; margin: 0; white-space: pre-wrap; }
.type-integer { color: #f97316; background: #fff7ed; }
.type-string { color: #16a34a; background: #f0fdf4; }
.type-array { color: #2563eb; background: #eff6ff; }
.type-error { color: #ef4444; background: #fef2f2; }
.type-nil { color: #9ca3af; }
</style>
