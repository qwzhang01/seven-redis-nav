<template>
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">数据导入导出</div>
    </div>

    <div class="content">
      <!-- Export Section -->
      <div class="section">
        <div class="section-title"><i class="ri-upload-2-line" /> 导出</div>
        <div class="section-body">
          <button class="action-btn" :disabled="exporting" @click="exportDb">
            <i :class="exporting ? 'ri-loader-4-line spin' : 'ri-database-2-line'" />
            <div>
              <div class="action-name">导出整个 DB</div>
              <div class="action-desc">将当前 DB 所有键导出为 JSON 文件</div>
            </div>
          </button>
        </div>
      </div>

      <!-- Import Section -->
      <div class="section">
        <div class="section-title"><i class="ri-download-2-line" /> 导入</div>
        <div class="section-body">
          <button class="action-btn" :disabled="importing" @click="importJson">
            <i :class="importing ? 'ri-loader-4-line spin' : 'ri-file-code-line'" />
            <div>
              <div class="action-name">从 JSON 导入</div>
              <div class="action-desc">从 Seven Redis Nav 导出的 JSON 文件导入键值对</div>
            </div>
          </button>
          <button class="action-btn" :disabled="importing" @click="openRdb">
            <i class="ri-file-zip-line" />
            <div>
              <div class="action-name">打开 RDB 文件</div>
              <div class="action-desc">只读解析 RDB 文件，以只读模式浏览键值</div>
            </div>
          </button>
        </div>
      </div>

      <!-- Progress / Result -->
      <div v-if="status" class="status-bar" :class="status.type">
        <i :class="status.icon" />
        <span>{{ status.message }}</span>
        <!-- Show saved file path for export success -->
        <span v-if="status.savedPath" class="saved-path" :title="status.savedPath">
          → {{ status.savedPath }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { useConnectionStore } from '@/stores/connection'
import * as ipc from '@/ipc/phase4'

const connStore = useConnectionStore()

interface Status {
  type: 'info' | 'success' | 'error'
  icon: string
  message: string
  savedPath?: string
}
const status = ref<Status | null>(null)
const exporting = ref(false)
const importing = ref(false)

function setStatus(type: Status['type'], message: string, savedPath?: string) {
  const icons = {
    info: 'ri-loader-4-line spin',
    success: 'ri-checkbox-circle-line',
    error: 'ri-error-warning-line',
  }
  status.value = { type, icon: icons[type], message, savedPath }
}

async function exportDb() {
  if (!connStore.activeConnId) return
  exporting.value = true
  setStatus('info', '正在导出数据...')
  try {
    const data = await ipc.exportDbJson(connStore.activeConnId)

    // Ask user where to save
    const host = connStore.activeConnection?.host ?? 'redis'
    const defaultName = `redis-export-${host}-${Date.now()}.json`
    const savePath = await invoke<string | null>('dialog_save_file', {
      defaultName,
      filters: [{ name: 'JSON', extensions: ['json'] }],
    })
    if (!savePath) {
      status.value = null
      return
    }

    const json = JSON.stringify(data, null, 2)
    await invoke('fs_write_text_file', { path: savePath, content: json })
    setStatus('success', `导出成功，共 ${data.keys.length} 个键`, savePath)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : (e as { message?: string })?.message ?? String(e)
    setStatus('error', `导出失败：${msg}`)
  } finally {
    exporting.value = false
  }
}

async function importJson() {
  if (!connStore.activeConnId) return
  importing.value = true
  setStatus('info', '请选择 JSON 文件...')
  try {
    const path = await invoke<string | null>('dialog_open_file', {
      filters: [{ name: 'JSON', extensions: ['json'] }],
    })
    if (!path) {
      status.value = null
      return
    }

    setStatus('info', '读取文件中...')
    const content = await invoke<string>('fs_read_text_file', { path })

    let data: ipc.RedisExport
    try {
      data = JSON.parse(content)
    } catch {
      throw new Error('JSON 解析失败，请确认文件格式正确')
    }
    if (!data.version || !Array.isArray(data.keys)) {
      throw new Error('文件格式不正确，请选择由 Seven Redis Nav 导出的 JSON 文件')
    }

    setStatus('info', `正在导入 ${data.keys.length} 个键...`)
    const result = await ipc.importKeysJson(connStore.activeConnId, data, false)
    setStatus(
      result.failed > 0 ? 'error' : 'success',
      `导入完成：成功 ${result.success}，跳过 ${result.skipped}，失败 ${result.failed}${result.errors.length ? '（' + result.errors[0] + '）' : ''}`,
    )
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : (e as { message?: string })?.message ?? String(e)
    setStatus('error', `导入失败：${msg}`)
  } finally {
    importing.value = false
  }
}

async function openRdb() {
  importing.value = true
  setStatus('info', '请选择 RDB 文件...')
  try {
    const path = await invoke<string | null>('dialog_open_file', {
      filters: [{ name: 'RDB', extensions: ['rdb'] }],
    })
    if (!path) {
      status.value = null
      return
    }
    setStatus('info', '解析 RDB 文件中...')
    await ipc.rdbParseFile(path)
    setStatus('success', 'RDB 文件解析完成，已在只读模式下加载')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : (e as { message?: string })?.message ?? String(e)
    setStatus('error', `解析失败：${msg}`)
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.panel { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.panel-header { padding: 10px 16px; border-bottom: 1px solid var(--border-color, #e5e7eb); flex-shrink: 0; }
.panel-title { font-size: 14px; font-weight: 600; }
.content { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 20px; }
.section-title { font-size: 13px; font-weight: 600; color: var(--text-secondary, #6b7280); margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }
.section-body { display: flex; flex-direction: column; gap: 8px; }
.action-btn { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border: 1px solid var(--border-color, #e5e7eb); border-radius: 8px; background: none; cursor: pointer; text-align: left; width: 100%; transition: background 0.15s; }
.action-btn:hover:not(:disabled) { background: var(--hover-bg, #f9fafb); border-color: var(--primary, #ef4444); }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.action-btn > i { font-size: 20px; color: var(--primary, #ef4444); flex-shrink: 0; }
.action-name { font-size: 13px; font-weight: 600; }
.action-desc { font-size: 12px; color: var(--text-secondary, #6b7280); margin-top: 2px; }
.status-bar { display: flex; align-items: flex-start; gap: 8px; padding: 10px 14px; border-radius: 6px; font-size: 13px; flex-wrap: wrap; }
.status-bar.info { background: #eff6ff; color: #2563eb; }
.status-bar.success { background: #f0fdf4; color: #16a34a; }
.status-bar.error { background: #fef2f2; color: #ef4444; }
.saved-path { font-size: 12px; opacity: 0.8; word-break: break-all; width: 100%; margin-top: 2px; padding-left: 20px; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
