<template>
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">TTL 分布分析</div>
      <button class="btn-primary" :disabled="store.isAnalyzingTtl" @click="analyze">
        <i v-if="store.isAnalyzingTtl" class="ri-loader-4-line spin" />
        {{ store.isAnalyzingTtl ? '分析中...' : '分析 TTL 分布' }}
      </button>
    </div>

    <div v-if="store.ttlDistribution" class="content">
      <!-- Warning -->
      <div v-if="expiringWarning" class="warning-banner">
        <i class="ri-alarm-warning-line" />
        有 {{ store.ttlDistribution?.expiring_soon_count }} 个键即将过期，请注意
      </div>

      <!-- Stats cards -->
      <div class="stats-grid">
        <div v-for="stat in stats" :key="stat.label" class="stat-card">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>

      <!-- Bar chart (simple CSS-based) -->
      <div class="chart-area">
        <div v-for="bar in chartBars" :key="bar.label" class="bar-row">
          <div class="bar-label">{{ bar.label }}</div>
          <div class="bar-track">
            <div class="bar-fill" :style="{ width: bar.pct + '%', background: bar.color }" />
          </div>
          <div class="bar-count">{{ bar.count }}</div>
          <div class="bar-pct">{{ bar.pct.toFixed(1) }}%</div>
        </div>
      </div>
    </div>

    <div v-else class="empty-tip">点击"分析 TTL 分布"查看键的过期时间分布</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useKeyAnalyzerStore } from '@/stores/keyAnalyzer'
import { useConnectionStore } from '@/stores/connection'

const store = useKeyAnalyzerStore()
const connStore = useConnectionStore()

async function analyze() {
  if (!connStore.activeConnId) return
  await store.analyzeTtl(connStore.activeConnId)
}

const expiringWarning = computed(() => {
  const d = store.ttlDistribution
  if (!d) return false
  return d.expiring_soon_warning
})

const stats = computed(() => {
  const d = store.ttlDistribution
  if (!d) return []
  return [
    { label: '采样总数', value: d.total_sampled },
    { label: '即将过期', value: d.expiring_soon_count },
  ]
})

const chartBars = computed(() => {
  const d = store.ttlDistribution
  if (!d) return []
  const colors = ['#6b7280', '#ef4444', '#f97316', '#eab308', '#22c55e']
  return d.buckets.map((b, i) => ({
    label: b.label,
    count: b.count,
    pct: b.percentage,
    color: colors[i % colors.length],
  }))
})
</script>

<style scoped>
.panel { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; border-bottom: 1px solid var(--border-color, #e5e7eb); flex-shrink: 0; }
.panel-title { font-size: 14px; font-weight: 600; }
.btn-primary { padding: 5px 14px; background: var(--primary, #ef4444); color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; display: flex; align-items: center; gap: 4px; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.content { flex: 1; overflow-y: auto; padding: 16px; }
.warning-banner { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #fff7ed; border: 1px solid #fed7aa; border-radius: 6px; color: #ea580c; font-size: 13px; margin-bottom: 16px; }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.stat-card { background: var(--bg-secondary, #f9fafb); border-radius: 8px; padding: 12px; text-align: center; }
.stat-value { font-size: 20px; font-weight: 700; color: var(--text-primary, #111827); }
.stat-label { font-size: 11px; color: var(--text-secondary, #6b7280); margin-top: 2px; }
.chart-area { display: flex; flex-direction: column; gap: 10px; }
.bar-row { display: flex; align-items: center; gap: 10px; }
.bar-label { width: 50px; font-size: 12px; color: var(--text-secondary, #6b7280); text-align: right; }
.bar-track { flex: 1; height: 16px; background: var(--border-color, #e5e7eb); border-radius: 8px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 8px; transition: width 0.5s; }
.bar-count { width: 50px; font-size: 12px; text-align: right; }
.bar-pct { width: 45px; font-size: 12px; color: var(--text-secondary, #6b7280); }
.empty-tip { padding: 40px; text-align: center; color: var(--text-secondary, #9ca3af); font-size: 13px; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
