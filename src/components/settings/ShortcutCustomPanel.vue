<template>
  <div class="shortcut-panel">
    <div class="panel-header">
      <div class="panel-title">快捷键自定义</div>
      <button class="btn-danger-outline" @click="resetAll">重置全部</button>
    </div>

    <div class="panel-desc">
      点击快捷键区域进入录制模式，按下新的组合键完成绑定。双击可恢复默认值。
    </div>

    <div class="shortcuts-list">
      <div v-for="group in shortcutGroups" :key="group.label" class="shortcut-group">
        <div class="group-label">{{ group.label }}</div>
        <div v-for="item in group.items" :key="item.action" class="shortcut-row">
          <div class="shortcut-name">{{ item.label }}</div>
          <div class="shortcut-binding-area">
            <div
              :class="['binding-display', { recording: recordingAction === item.action, conflict: conflictAction === item.action }]"
              @click="startRecording(item.action)"
              @dblclick="resetSingle(item.action)"
              :title="recordingAction === item.action ? '按下组合键...' : '点击录制，双击恢复默认'"
            >
              <template v-if="recordingAction === item.action">
                <span class="recording-hint">{{ recordingPreview || '按下组合键...' }}</span>
              </template>
              <template v-else>
                <kbd v-for="key in formatBinding(getBinding(item.action)).split('+')" :key="key" class="key-badge">{{ key }}</kbd>
              </template>
            </div>
            <span v-if="conflictAction === item.action" class="conflict-hint">⚠️ 与其他绑定冲突</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as ipc from '@/ipc/phase4'
import type { ShortcutBinding } from '@/ipc/phase4'

// Default bindings
const DEFAULT_BINDINGS: Record<string, string> = {
  'cli.new_tab': 'Meta+t',
  'cli.close_tab': 'Meta+w',
  'cli.clear': 'Meta+l',
  'lua.execute': 'Meta+Enter',
  'browser.refresh': 'Meta+r',
  'browser.search': 'Meta+f',
  'app.settings': 'Meta+,',
}

const shortcutGroups = [
  {
    label: 'CLI 终端',
    items: [
      { action: 'cli.new_tab', label: '新建 Tab' },
      { action: 'cli.close_tab', label: '关闭 Tab' },
      { action: 'cli.clear', label: '清屏' },
    ],
  },
  {
    label: 'Lua 编辑器',
    items: [
      { action: 'lua.execute', label: '执行脚本' },
    ],
  },
  {
    label: '键浏览器',
    items: [
      { action: 'browser.refresh', label: '刷新' },
      { action: 'browser.search', label: '搜索' },
    ],
  },
  {
    label: '应用',
    items: [
      { action: 'app.settings', label: '打开设置' },
    ],
  },
]

const customBindings = ref<Record<string, string>>({})
const recordingAction = ref<string | null>(null)
const recordingPreview = ref('')
const conflictAction = ref<string | null>(null)

onMounted(async () => {
  const list = await ipc.shortcutBindingList()
  list.forEach((b: ShortcutBinding) => {
    customBindings.value[b.action] = b.binding
  })
})

function getBinding(action: string): string {
  return customBindings.value[action] ?? DEFAULT_BINDINGS[action] ?? ''
}

function formatBinding(binding: string): string {
  return binding
    .replace('Meta', '⌘')
    .replace('Ctrl', 'Ctrl')
    .replace('Alt', '⌥')
    .replace('Shift', '⇧')
}

function startRecording(action: string) {
  recordingAction.value = action
  recordingPreview.value = ''
  conflictAction.value = null
  window.addEventListener('keydown', handleRecordKeydown)
}

function handleRecordKeydown(e: KeyboardEvent) {
  e.preventDefault()
  e.stopPropagation()

  if (e.key === 'Escape') {
    stopRecording()
    return
  }

  const parts: string[] = []
  if (e.metaKey) parts.push('Meta')
  if (e.ctrlKey) parts.push('Ctrl')
  if (e.altKey) parts.push('Alt')
  if (e.shiftKey) parts.push('Shift')

  const key = e.key
  if (!['Meta', 'Control', 'Alt', 'Shift'].includes(key)) {
    parts.push(key)
  }

  const binding = parts.join('+')
  recordingPreview.value = formatBinding(binding)

  if (parts.length > 1 && !['Meta', 'Control', 'Alt', 'Shift'].includes(key)) {
    // Check conflict
    const conflict = checkConflict(recordingAction.value!, binding)
    if (conflict) {
      conflictAction.value = recordingAction.value
    } else {
      conflictAction.value = null
      saveBinding(recordingAction.value!, binding)
    }
    stopRecording()
  }
}

function checkConflict(action: string, binding: string): boolean {
  for (const [a, b] of Object.entries({ ...DEFAULT_BINDINGS, ...customBindings.value })) {
    if (a !== action && b === binding) return true
  }
  return false
}

async function saveBinding(action: string, binding: string) {
  customBindings.value[action] = binding
  await ipc.shortcutBindingSave(action, binding)
}

function stopRecording() {
  recordingAction.value = null
  recordingPreview.value = ''
  window.removeEventListener('keydown', handleRecordKeydown)
}

async function resetSingle(action: string) {
  delete customBindings.value[action]
  await ipc.shortcutBindingDelete(action)
}

async function resetAll() {
  customBindings.value = {}
  await ipc.shortcutBindingResetAll()
}

onUnmounted(() => {
  window.removeEventListener('keydown', handleRecordKeydown)
})
</script>

<style scoped>
.shortcut-panel { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid var(--border-color, #e5e7eb); flex-shrink: 0; }
.panel-title { font-size: 14px; font-weight: 600; }
.panel-desc { padding: 8px 16px; font-size: 12px; color: var(--text-secondary, #6b7280); background: var(--bg-secondary, #f9fafb); border-bottom: 1px solid var(--border-color, #e5e7eb); }
.btn-danger-outline { padding: 5px 12px; background: none; border: 1px solid #ef4444; color: #ef4444; border-radius: 4px; cursor: pointer; font-size: 13px; }
.shortcuts-list { flex: 1; overflow-y: auto; padding: 12px 16px; display: flex; flex-direction: column; gap: 16px; }
.shortcut-group { }
.group-label { font-size: 11px; font-weight: 700; color: var(--text-secondary, #6b7280); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.shortcut-row { display: flex; align-items: center; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border-color, #f3f4f6); }
.shortcut-name { font-size: 13px; color: var(--text-primary, #111827); }
.shortcut-binding-area { display: flex; align-items: center; gap: 8px; }
.binding-display { display: flex; align-items: center; gap: 3px; padding: 4px 8px; border: 1px solid var(--border-color, #e5e7eb); border-radius: 4px; cursor: pointer; min-width: 100px; justify-content: center; }
.binding-display:hover { border-color: var(--primary, #ef4444); }
.binding-display.recording { border-color: var(--primary, #ef4444); background: #fef2f2; animation: pulse 1s infinite; }
.binding-display.conflict { border-color: #f97316; background: #fff7ed; }
.recording-hint { font-size: 12px; color: var(--primary, #ef4444); }
.key-badge { display: inline-block; padding: 1px 5px; background: var(--bg-secondary, #f3f4f6); border: 1px solid var(--border-color, #d1d5db); border-radius: 3px; font-size: 11px; font-family: monospace; }
.conflict-hint { font-size: 11px; color: #f97316; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
</style>
