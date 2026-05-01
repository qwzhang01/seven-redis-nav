<template>
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">健康检查报告</div>
      <div class="panel-actions">
        <button class="btn-secondary" @click="showHistory = true">历史报告</button>
        <button v-if="store.currentReport" class="btn-secondary" @click="exportMd">导出报告</button>
        <button class="btn-primary" :disabled="store.isGenerating" @click="generate">
          <i v-if="store.isGenerating" class="ri-loader-4-line spin" />
          {{ store.isGenerating ? '生成中...' : '生成健康报告' }}
        </button>
      </div>
    </div>

    <div v-if="store.currentReport" class="content">
      <!-- Score -->
      <div class="score-section">
        <div class="score-circle" :class="scoreClass">{{ store.currentReport.score }}</div>
        <div class="score-label">总体健康分</div>
        <div class="score-time">生成于 {{ formatTime(store.currentReport.created_at) }}</div>
      </div>

      <!-- Indicators -->
      <div class="indicators-table">
        <div v-for="ind in store.currentReport.indicators" :key="ind.name" class="indicator-row" :class="levelClass(ind.level)">
          <div class="ind-name">{{ ind.name }}</div>
          <div class="ind-value">{{ ind.value }}</div>
          <div class="ind-level">
            <span :class="['level-badge', levelClass(ind.level)]">{{ levelLabel(ind.level) }}</span>
          </div>
          <div class="ind-suggestion">{{ ind.suggestion || '-' }}</div>
        </div>
      </div>
    </div>

    <div v-else class="empty-tip">点击"生成健康报告"开始检查</div>

    <!-- History Dialog -->
    <div v-if="showHistory" class="dialog-overlay" @click.self="showHistory = false">
      <div class="dialog">
        <div class="dialog-header">
          <span>历史报告</span>
          <button class="close-btn" @click="showHistory = false"><i class="ri-close-line" /></button>
        </div>
        <div class="dialog-body">
          <div v-if="store.historyList.length === 0" class="empty-tip">暂无历史报告</div>
          <div
            v-for="r in store.historyList"
            :key="r.id"
            class="history-item"
            @click="loadHistory(r.id)"
          >
            <span class="history-score" :class="r.score >= 80 ? 'score-good' : r.score >= 60 ? 'score-warn' : 'score-bad'">{{ r.score }}</span>
            <span class="history-time">{{ formatTime(r.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useHealthCheckStore } from '@/stores/healthCheck'
import { useConnectionStore } from '@/stores/connection'
import { saveAs } from 'file-saver'

const store = useHealthCheckStore()
const connStore = useConnectionStore()
const showHistory = ref(false)

onMounted(() => store.loadHistory())

async function generate() {
  if (!connStore.activeConnId) return
  await store.generate(connStore.activeConnId)
}

async function exportMd() {
  if (!connStore.activeConnId) return
  const md = await store.exportMarkdown(connStore.activeConnId)
  const host = connStore.activeConnection?.host ?? 'redis'
  const date = new Date().toISOString().slice(0, 10)
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8;' })
  saveAs(blob, `redis-health-report-${host}-${date}.md`)
}

async function loadHistory(id: string) {
  await store.loadHistoryItem(id)
  showHistory.value = false
}

const scoreClass = computed(() => {
  const s = store.currentReport?.score ?? 0
  return s >= 80 ? 'score-good' : s >= 60 ? 'score-warn' : 'score-bad'
})

function levelClass(level: string) {
  return level === 'Normal' ? 'level-normal' : level === 'Warning' ? 'level-warning' : 'level-danger'
}

function levelLabel(level: string) {
  return level === 'Normal' ? '✅ 正常' : level === 'Warning' ? '⚠️ 警告' : '🔴 危险'
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN')
}
</script>

<style scoped>
.panel { display: flex; flex-direction: column; height: 100%; overflow: hidden; position: relative; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; border-bottom: 1px solid var(--border-color, #e5e7eb); flex-shrink: 0; }
.panel-title { font-size: 14px; font-weight: 600; }
.panel-actions { display: flex; gap: 8px; }
.btn-primary { padding: 5px 14px; background: var(--primary, #ef4444); color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; display: flex; align-items: center; gap: 4px; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { padding: 5px 12px; background: none; border: 1px solid var(--border-color, #e5e7eb); border-radius: 4px; cursor: pointer; font-size: 13px; }
.content { flex: 1; overflow-y: auto; padding: 16px; }
.score-section { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.score-circle { width: 64px; height: 64px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 700; color: #fff; }
.score-good { background: #22c55e; }
.score-warn { background: #f97316; }
.score-bad { background: #ef4444; }
.score-label { font-size: 14px; font-weight: 600; }
.score-time { font-size: 12px; color: var(--text-secondary, #6b7280); }
.indicators-table { display: flex; flex-direction: column; gap: 0; border: 1px solid var(--border-color, #e5e7eb); border-radius: 6px; overflow: hidden; }
.indicator-row { display: grid; grid-template-columns: 140px 1fr 90px 1fr; gap: 12px; padding: 8px 12px; border-bottom: 1px solid var(--border-color, #f3f4f6); font-size: 12px; align-items: center; }
.indicator-row:last-child { border-bottom: none; }
.indicator-row.level-danger { background: #fef2f2; }
.indicator-row.level-warning { background: #fffbeb; }
.ind-name { font-weight: 600; }
.ind-value { font-family: monospace; }
.level-badge { font-size: 11px; padding: 1px 6px; border-radius: 10px; }
.level-normal { background: #f0fdf4; color: #16a34a; }
.level-warning { background: #fffbeb; color: #d97706; }
.level-danger { background: #fef2f2; color: #ef4444; }
.ind-suggestion { color: var(--text-secondary, #6b7280); font-size: 11px; }
.empty-tip { padding: 40px; text-align: center; color: var(--text-secondary, #9ca3af); font-size: 13px; }
.dialog-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog { background: #fff; border-radius: 8px; width: 400px; max-height: 400px; display: flex; flex-direction: column; }
.dialog-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid var(--border-color, #e5e7eb); font-weight: 600; }
.close-btn { background: none; border: none; cursor: pointer; font-size: 16px; }
.dialog-body { flex: 1; overflow-y: auto; padding: 8px; }
.history-item { display: flex; align-items: center; gap: 12px; padding: 8px 12px; cursor: pointer; border-radius: 4px; }
.history-item:hover { background: var(--hover-bg, #f9fafb); }
.history-score { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; color: #fff; }
.history-time { font-size: 12px; color: var(--text-secondary, #6b7280); }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
