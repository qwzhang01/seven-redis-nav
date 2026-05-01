<template>
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">大 Key 扫描</div>
      <div class="panel-actions">
        <label class="toggle-label">
          <input v-model="lowImpact" type="checkbox" />
          低影响模式
        </label>
        <button v-if="!store.isScanning" class="btn-primary" @click="startScan">开始扫描</button>
        <button v-else class="btn-danger" @click="store.stopScan">停止扫描</button>
        <button v-if="store.topKeys.length > 0" class="btn-secondary" @click="exportCsv">导出 CSV</button>
      </div>
    </div>

    <!-- Progress -->
    <div v-if="store.isScanning || store.progress" class="progress-bar-wrap">
      <div class="progress-info">
        <span>已扫描: {{ store.progress?.scanned ?? 0 }} 个键</span>
        <span v-if="store.scanAborted" class="aborted-badge">扫描已中止</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPct + '%' }" />
      </div>
    </div>

    <!-- Top Keys Table -->
    <div class="table-wrap">
      <table v-if="store.topKeys.length > 0" class="data-table">
        <thead>
          <tr>
            <th @click="sortBy('key')">键名 <i :class="sortIcon('key')" /></th>
            <th @click="sortBy('type')">类型 <i :class="sortIcon('type')" /></th>
            <th @click="sortBy('memory_bytes')">内存 <i :class="sortIcon('memory_bytes')" /></th>
            <th>编码</th>
            <th>元素数</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="k in sortedKeys" :key="k.key">
            <td class="key-cell" :title="k.key">
              <span class="key-link" @click="navigateToKey(k.key)">{{ k.key }}</span>
            </td>
            <td><span :class="['type-badge', `type-${k.key_type}`]">{{ k.key_type }}</span></td>
            <td>{{ formatBytes(k.memory_bytes) }}</td>
            <td>{{ k.encoding }}</td>
            <td>{{ k.element_count }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else-if="!store.isScanning" class="empty-tip">点击"开始扫描"分析大 Key 分布</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useKeyAnalyzerStore } from '@/stores/keyAnalyzer'
import { useConnectionStore } from '@/stores/connection'
import { useWorkspaceStore } from '@/stores/workspace'
import { useKeyBrowserStore } from '@/stores/keyBrowser'
import { listen } from '@tauri-apps/api/event'
import { onBeforeUnmount } from 'vue'
import type { ScanProgress } from '@/ipc/phase4'
import { keyScanMemoryExportCsv } from '@/ipc/phase4'
import { saveAs } from 'file-saver'

const store = useKeyAnalyzerStore()
const connStore = useConnectionStore()
const workspaceStore = useWorkspaceStore()
const keyBrowserStore = useKeyBrowserStore()
const lowImpact = ref(false)
const sortField = ref<string>('memory_bytes')
const sortDir = ref<'asc' | 'desc'>('desc')

let unlisten: (() => void) | null = null

onBeforeUnmount(() => unlisten?.())

function navigateToKey(key: string) {
  keyBrowserStore.selectKey(key)
  workspaceStore.setActiveTab('browser')
}

async function startScan() {
  if (!connStore.activeConnId) return
  // Clean up previous listener
  unlisten?.()
  unlisten = null

  const taskId = await store.startScan(connStore.activeConnId, lowImpact.value)
  if (!taskId) return

  // Listen on the task-specific event channel
  unlisten = await listen<ScanProgress>(`key_analyzer:progress:${taskId}`, (e) => {
    store.onProgress(e.payload)
    if (e.payload.is_done) {
      unlisten?.()
      unlisten = null
    }
  })
}

const progressPct = computed(() => {
  const p = store.progress
  if (!p || !p.total_estimate) return 0
  return Math.min(100, Math.round((p.scanned / p.total_estimate) * 100))
})

const sortedKeys = computed(() => {
  const keys = [...store.topKeys]
  keys.sort((a, b) => {
    const av = (a as Record<string, unknown>)[sortField.value]
    const bv = (b as Record<string, unknown>)[sortField.value]
    if (av === bv) return 0
    const cmp = av! < bv! ? -1 : 1
    return sortDir.value === 'asc' ? cmp : -cmp
  })
  return keys
})

function sortBy(field: string) {
  if (sortField.value === field) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDir.value = 'desc'
  }
}

function sortIcon(field: string) {
  if (sortField.value !== field) return 'ri-arrow-up-down-line'
  return sortDir.value === 'asc' ? 'ri-arrow-up-line' : 'ri-arrow-down-line'
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

async function exportCsv() {
  if (!store.taskId) return
  const csv = await keyScanMemoryExportCsv(store.taskId)
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  saveAs(blob, `redis-big-keys-${Date.now()}.csv`)
}
</script>

<style scoped>
.panel { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; border-bottom: 1px solid var(--border-color, #e5e7eb); flex-shrink: 0; }
.panel-title { font-size: 14px; font-weight: 600; }
.panel-actions { display: flex; align-items: center; gap: 8px; }
.toggle-label { display: flex; align-items: center; gap: 4px; font-size: 12px; color: var(--text-secondary, #6b7280); cursor: pointer; }
.btn-primary { padding: 5px 14px; background: var(--primary, #ef4444); color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-danger { padding: 5px 14px; background: #f97316; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-secondary { padding: 5px 12px; background: none; border: 1px solid var(--border-color, #e5e7eb); border-radius: 4px; cursor: pointer; font-size: 13px; }
.progress-bar-wrap { padding: 8px 16px; flex-shrink: 0; }
.progress-info { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-secondary, #6b7280); margin-bottom: 4px; }
.aborted-badge { color: #f97316; font-weight: 600; }
.progress-bar { height: 4px; background: var(--border-color, #e5e7eb); border-radius: 2px; }
.progress-fill { height: 100%; background: var(--primary, #ef4444); border-radius: 2px; transition: width 0.3s; }
.table-wrap { flex: 1; overflow: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.data-table th { padding: 6px 12px; text-align: left; background: var(--bg-secondary, #f9fafb); border-bottom: 1px solid var(--border-color, #e5e7eb); cursor: pointer; white-space: nowrap; }
.data-table td { padding: 5px 12px; border-bottom: 1px solid var(--border-color, #f3f4f6); }
.key-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: monospace; }
.key-link { cursor: pointer; color: var(--primary, #ef4444); text-decoration: underline; }
.key-link:hover { opacity: 0.8; }
.type-badge { font-size: 10px; padding: 1px 6px; border-radius: 10px; font-weight: 600; }
.type-string { background: #f0fdf4; color: #16a34a; }
.type-hash { background: #eff6ff; color: #2563eb; }
.type-list { background: #fef3c7; color: #d97706; }
.type-set { background: #fdf4ff; color: #9333ea; }
.type-zset { background: #fff7ed; color: #ea580c; }
.empty-tip { padding: 40px; text-align: center; color: var(--text-secondary, #9ca3af); font-size: 13px; }
</style>
