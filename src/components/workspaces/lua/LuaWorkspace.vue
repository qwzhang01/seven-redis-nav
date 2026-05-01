<template>
  <div class="lua-workspace">
    <!-- Left: Script History List -->
    <div class="lua-sidebar">
      <div class="sidebar-header">
        <span class="sidebar-title">脚本历史</span>
        <button class="btn-icon" title="新建脚本" @click="newScript">
          <i class="ri-add-line" />
        </button>
      </div>
      <LuaScriptList
        :scripts="luaStore.history"
        :loading="luaStore.isLoadingHistory"
        @select="luaStore.loadScript"
        @delete="luaStore.deleteScript"
        @rename="luaStore.renameScript"
      />
    </div>

    <!-- Right: Editor + Args + Result -->
    <div class="lua-main">
      <!-- Toolbar -->
      <div class="lua-toolbar">
        <div class="mode-toggle">
          <button :class="['mode-btn', { active: luaStore.evalMode === 'eval' }]" @click="luaStore.evalMode = 'eval'">EVAL</button>
          <button :class="['mode-btn', { active: luaStore.evalMode === 'evalsha' }]" @click="luaStore.evalMode = 'evalsha'">EVALSHA</button>
        </div>
        <span v-if="luaStore.currentSha" class="sha-badge">SHA: {{ luaStore.currentSha.slice(0, 12) }}...</span>
        <div class="toolbar-actions">
          <button class="btn-secondary" @click="loadScript" title="SCRIPT LOAD">加载脚本</button>
          <button
            class="btn-primary"
            :disabled="!luaStore.canExecute || luaStore.isExecuting"
            @click="execute"
            title="执行 (⌘+Enter)"
          >
            <i v-if="luaStore.isExecuting" class="ri-loader-4-line spin" />
            <span>{{ luaStore.isExecuting ? '执行中...' : '执行' }}</span>
          </button>
        </div>
      </div>

      <!-- Editor -->
      <LuaEditor v-model="luaStore.scriptContent" class="lua-editor-area" />

      <!-- Args Form -->
      <LuaArgsForm
        :keys="luaStore.keys"
        :argv="luaStore.argv"
        @add-key="luaStore.addKey"
        @remove-key="luaStore.removeKey"
        @add-argv="luaStore.addArgv"
        @remove-argv="luaStore.removeArgv"
        @update-key="(i, v) => luaStore.keys[i] = v"
        @update-argv="(i, v) => luaStore.argv[i] = v"
      />

      <!-- Result Panel -->
      <LuaResultPanel :result="luaStore.lastResult" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useLuaStore } from '@/stores/lua'
import { useConnectionStore } from '@/stores/connection'
import LuaScriptList from './LuaScriptList.vue'
import LuaEditor from './LuaEditor.vue'
import LuaArgsForm from './LuaArgsForm.vue'
import LuaResultPanel from './LuaResultPanel.vue'

const luaStore = useLuaStore()
const connStore = useConnectionStore()

onMounted(() => {
  luaStore.loadHistory()
  // ⌘+Enter to execute
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

function handleKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    e.preventDefault()
    execute()
  }
}

async function execute() {
  if (!connStore.activeConnId) return
  await luaStore.execute(connStore.activeConnId)
}

async function loadScript() {
  if (!connStore.activeConnId) return
  await luaStore.loadScriptToSha(connStore.activeConnId)
}

function newScript() {
  luaStore.scriptContent = `local key = KEYS[1]\nlocal val = redis.call('GET', key)\nreturn val`
  luaStore.keys = ['']
  luaStore.argv = []
  luaStore.lastResult = null
}
</script>

<style scoped>
.lua-workspace {
  display: flex;
  height: 100%;
  overflow: hidden;
}
.lua-sidebar {
  width: 200px;
  min-width: 160px;
  border-right: 1px solid var(--border-color, #e5e7eb);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary, #6b7280);
}
.lua-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.lua-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}
.mode-toggle { display: flex; border: 1px solid var(--border-color, #e5e7eb); border-radius: 4px; overflow: hidden; }
.mode-btn { padding: 4px 10px; font-size: 12px; background: none; border: none; cursor: pointer; color: var(--text-secondary, #6b7280); }
.mode-btn.active { background: var(--primary, #ef4444); color: #fff; }
.sha-badge { font-size: 11px; color: var(--text-secondary, #6b7280); font-family: monospace; }
.toolbar-actions { margin-left: auto; display: flex; gap: 8px; }
.btn-primary { padding: 5px 14px; background: var(--primary, #ef4444); color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; display: flex; align-items: center; gap: 4px; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { padding: 5px 12px; background: none; border: 1px solid var(--border-color, #e5e7eb); border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-icon { background: none; border: none; cursor: pointer; padding: 2px 4px; color: var(--text-secondary, #6b7280); }
.lua-editor-area { flex: 1; min-height: 0; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
