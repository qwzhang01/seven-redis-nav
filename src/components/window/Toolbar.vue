<script setup lang="ts">
import { useWorkspaceStore, type WorkspaceTab } from '@/stores/workspace';

const store = useWorkspaceStore();
const emit = defineEmits<{ openSettings: [] }>();

const tabs: { id: WorkspaceTab; icon: string; label: string }[] = [
  { id: 'browser', icon: 'ri-file-list-3-line', label: '浏览器' },
  { id: 'cli', icon: 'ri-terminal-box-line', label: '命令行' },
  { id: 'monitor', icon: 'ri-pulse-line', label: '监控' },
  { id: 'slowlog', icon: 'ri-timer-flash-line', label: '慢查询' },
  { id: 'pubsub', icon: 'ri-broadcast-line', label: '发布订阅' },
  { id: 'config', icon: 'ri-settings-3-line', label: '配置' },
  { id: 'lua', icon: 'ri-code-s-slash-line', label: 'Lua' },
  { id: 'tools', icon: 'ri-tools-line', label: '工具' },
];
</script>

<template>
  <div class="toolbar">
    <div class="toolbar-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tool-btn"
        :class="{ active: store.activeTab === tab.id }"
        :data-tab="tab.id"
        @click="store.setActiveTab(tab.id)"
      >
        <i :class="tab.icon" />
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <div class="toolbar-search">
      <i class="ri-search-line" />
      <input id="globalSearch" type="text" placeholder="搜索键、命令或设置..." />
      <span class="kbd">⌘K</span>
    </div>

    <div class="toolbar-right">
      <div class="status-chip">
        <span class="status-dot" />
        已连接
      </div>
      <button class="tool-btn-icon" title="刷新">
        <i class="ri-refresh-line" />
      </button>
      <button class="tool-btn-icon" title="分享">
        <i class="ri-share-line" />
      </button>
      <button class="tool-btn-icon" title="设置" @click="emit('openSettings')">
        <i class="ri-settings-3-line" />
      </button>
      <button class="tool-btn-icon" title="新建连接">
        <i class="ri-add-line" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  height: var(--srn-toolbar-h);
  background: var(--srn-color-toolbar);
  border-bottom: 1px solid var(--srn-color-border);
  display: flex;
  align-items: center;
  padding: 0 12px;
  gap: 8px;
}

.toolbar-tabs { display: flex; gap: 4px; }

.tool-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: var(--srn-radius-sm);
  color: var(--srn-color-text-2);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--srn-motion-fast);
  white-space: nowrap;
}
.tool-btn i { font-size: 14px; }
.tool-btn:hover { background: rgba(0, 0, 0, 0.04); }
.tool-btn.active {
  background: #fff;
  color: var(--srn-color-primary);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  font-weight: 500;
}

.toolbar-search {
  flex: 1;
  max-width: 360px;
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 0 10px;
  height: 32px;
  gap: 6px;
  transition: border-color var(--srn-motion-fast), box-shadow var(--srn-motion-fast);
}
.toolbar-search:focus-within {
  border-color: var(--srn-color-info);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.12);
}
.toolbar-search i { color: var(--srn-color-text-3); font-size: 14px; }
.toolbar-search input {
  border: none;
  outline: none;
  flex: 1;
  font-size: 12px;
  background: transparent;
  color: var(--srn-color-text-1);
}
.kbd {
  font-size: 10px;
  color: var(--srn-color-text-3);
  background: var(--srn-color-surface-1);
  padding: 1px 5px;
  border-radius: 3px;
  border: 1px solid var(--srn-color-border);
}

.toolbar-right { display: flex; align-items: center; gap: 8px; margin-left: auto; }

.status-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--srn-color-success);
  font-weight: 500;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--srn-color-success);
  animation: pulse 2s infinite;
}

.tool-btn-icon {
  width: 32px;
  height: 32px;
  border: 1px solid var(--srn-color-border);
  background: #fff;
  border-radius: var(--srn-radius-sm);
  color: var(--srn-color-text-2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: background var(--srn-motion-fast);
}
.tool-btn-icon:hover { background: var(--srn-color-surface-1); }
</style>
