<template>
  <div class="tab-bar">
    <div
      v-for="tab in store.tabList"
      :key="tab.tabId"
      :class="['tab-item', { active: store.activeTabId === tab.tabId }]"
      @click="store.switchTab(tab.tabId)"
    >
      <span v-if="renamingId !== tab.tabId" class="tab-name" @dblclick.stop="startRename(tab)">
        {{ tab.name }}
      </span>
      <input
        v-else
        ref="renameInput"
        v-model="renameValue"
        class="tab-rename-input"
        @keydown.enter="confirmRename(tab.tabId)"
        @keydown.escape="cancelRename"
        @blur="confirmRename(tab.tabId)"
        @click.stop
      />
      <button
        v-if="store.tabList.length > 1"
        class="tab-close"
        title="关闭 (⌘W)"
        @click.stop="store.closeTab(tab.tabId)"
      >
        <i class="ri-close-line" />
      </button>
    </div>
    <button
      class="tab-add"
      :disabled="!store.canAddTab"
      :title="store.canAddTab ? '新建终端 (⌘T)' : '最多支持 8 个终端标签页'"
      @click="addTab"
    >
      <i class="ri-add-line" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { useTerminalStore } from '@/stores/terminal'
import { useConnectionStore } from '@/stores/connection'
import type { CliTabState } from '@/stores/terminal'

const store = useTerminalStore()
const connStore = useConnectionStore()

const renamingId = ref<string | null>(null)
const renameValue = ref('')
const renameInput = ref<HTMLInputElement | null>(null)

async function addTab() {
  if (!connStore.activeConnId) return
  await store.createTab(connStore.activeConnId)
}

function startRename(tab: CliTabState) {
  renamingId.value = tab.tabId
  renameValue.value = tab.name
  nextTick(() => renameInput.value?.focus())
}

function confirmRename(tabId: string) {
  if (renamingId.value === tabId && renameValue.value.trim()) {
    store.renameTab(tabId, renameValue.value.trim())
  }
  renamingId.value = null
}

function cancelRename() {
  renamingId.value = null
}
</script>

<style scoped>
.tab-bar { display: flex; align-items: center; border-bottom: 1px solid var(--border-color, #e5e7eb); background: var(--bg-secondary, #f9fafb); overflow-x: auto; flex-shrink: 0; }
.tab-item { display: flex; align-items: center; gap: 4px; padding: 6px 12px; cursor: pointer; border-right: 1px solid var(--border-color, #e5e7eb); white-space: nowrap; min-width: 80px; max-width: 160px; }
.tab-item.active { background: #fff; border-bottom: 2px solid var(--primary, #ef4444); }
.tab-name { font-size: 12px; flex: 1; overflow: hidden; text-overflow: ellipsis; }
.tab-rename-input { font-size: 12px; border: 1px solid var(--primary, #ef4444); border-radius: 2px; padding: 0 4px; width: 80px; outline: none; }
.tab-close { background: none; border: none; cursor: pointer; padding: 1px; color: var(--text-secondary, #9ca3af); opacity: 0; font-size: 12px; }
.tab-item:hover .tab-close { opacity: 1; }
.tab-close:hover { color: var(--danger, #ef4444); }
.tab-add { background: none; border: none; cursor: pointer; padding: 6px 10px; color: var(--text-secondary, #6b7280); font-size: 14px; }
.tab-add:disabled { opacity: 0.4; cursor: not-allowed; }
.tab-add:not(:disabled):hover { color: var(--primary, #ef4444); }
</style>
