<template>
  <div class="script-list">
    <div v-if="loading" class="list-empty">加载中...</div>
    <div v-else-if="scripts.length === 0" class="list-empty">暂无历史脚本</div>
    <div
      v-for="script in scripts"
      :key="script.id"
      class="script-item"
      @click="$emit('select', script)"
    >
      <div class="script-name" @dblclick.stop="startRename(script)">
        <template v-if="renamingId === script.id">
          <input
            ref="renameInput"
            v-model="renameValue"
            class="rename-input"
            @keydown.enter="confirmRename(script.id)"
            @keydown.escape="cancelRename"
            @blur="confirmRename(script.id)"
            @click.stop
          />
        </template>
        <template v-else>{{ script.name || '未命名脚本' }}</template>
      </div>
      <div class="script-meta">{{ formatTime(script.last_used_at || script.created_at) }}</div>
      <button class="delete-btn" title="删除" @click.stop="$emit('delete', script.id)">
        <i class="ri-delete-bin-line" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import type { LuaScript } from '@/ipc/phase4'

defineProps<{ scripts: LuaScript[]; loading: boolean }>()
const emit = defineEmits<{
  select: [script: LuaScript]
  delete: [id: string]
  rename: [id: string, name: string]
}>()

const renamingId = ref<string | null>(null)
const renameValue = ref('')
const renameInput = ref<HTMLInputElement | null>(null)

function startRename(script: LuaScript) {
  renamingId.value = script.id
  renameValue.value = script.name || ''
  nextTick(() => renameInput.value?.focus())
}

function confirmRename(id: string) {
  if (renamingId.value === id && renameValue.value.trim()) {
    emit('rename', id, renameValue.value.trim())
  }
  renamingId.value = null
}

function cancelRename() {
  renamingId.value = null
}

function formatTime(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.script-list { flex: 1; overflow-y: auto; }
.list-empty { padding: 16px 12px; font-size: 12px; color: var(--text-secondary, #9ca3af); text-align: center; }
.script-item { position: relative; padding: 8px 12px; cursor: pointer; border-bottom: 1px solid var(--border-color, #f3f4f6); }
.script-item:hover { background: var(--hover-bg, #f9fafb); }
.script-item:hover .delete-btn { opacity: 1; }
.script-name { font-size: 12px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-right: 20px; }
.script-meta { font-size: 11px; color: var(--text-secondary, #9ca3af); margin-top: 2px; }
.delete-btn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; opacity: 0; color: var(--text-secondary, #9ca3af); padding: 2px; }
.delete-btn:hover { color: var(--danger, #ef4444); }
.rename-input { width: 100%; font-size: 12px; border: 1px solid var(--primary, #ef4444); border-radius: 2px; padding: 1px 4px; outline: none; }
</style>
