<script setup lang="ts">
import { ref, computed } from 'vue';
import type { ConnectionConfig, ConnId } from '@/types/connection';

const props = defineProps<{
  connections: ConnectionConfig[];
  connectingId?: ConnId | null;
  errorId?: ConnId | null;
}>();

const emit = defineEmits<{
  (e: 'connect', connId: ConnId): void;
  (e: 'edit', config: ConnectionConfig): void;
  (e: 'delete', connId: ConnId): void;
}>();

// Group connections by group_name
const groupedConnections = computed(() => {
  const groups: Record<string, ConnectionConfig[]> = {};
  const ungrouped: ConnectionConfig[] = [];

  for (const conn of props.connections) {
    if (conn.group_name) {
      if (!groups[conn.group_name]) groups[conn.group_name] = [];
      groups[conn.group_name].push(conn);
    } else {
      ungrouped.push(conn);
    }
  }

  return { groups, ungrouped };
});

const collapsedGroups = ref<Set<string>>(new Set());

function toggleGroup(name: string) {
  if (collapsedGroups.value.has(name)) {
    collapsedGroups.value.delete(name);
  } else {
    collapsedGroups.value.add(name);
  }
}
</script>

<template>
  <div class="saved-connection-list">
    <h3 class="list-title">
      <i class="ri-bookmark-line" />
      已保存的连接
    </h3>

    <!-- Grouped connections -->
    <template v-for="(conns, groupName) in groupedConnections.groups" :key="groupName">
      <div class="group-header" @click="toggleGroup(groupName as string)">
        <i :class="collapsedGroups.has(groupName as string) ? 'ri-arrow-right-s-line' : 'ri-arrow-down-s-line'" />
        <span class="group-name">{{ groupName }}</span>
        <span class="group-count">{{ conns.length }}</span>
      </div>
      <Transition name="collapse">
        <div v-if="!collapsedGroups.has(groupName as string)" class="group-items">
          <div
            v-for="conn in conns"
            :key="conn.id"
            class="conn-item"
            :class="{ connecting: connectingId === conn.id, error: errorId === conn.id }"
            @click="emit('connect', conn.id)"
          >
            <div class="conn-status">
              <span class="status-dot" />
            </div>
            <div class="conn-info">
              <div class="conn-name">{{ conn.name }}</div>
              <div class="conn-host">
                {{ conn.host }}:{{ conn.port }}
                <i v-if="conn.has_password" class="ri-lock-line conn-lock" title="已设置密码" />
              </div>
            </div>
            <div class="conn-actions" @click.stop>
              <button class="action-btn" title="编辑" @click="emit('edit', conn)">
                <i class="ri-edit-line" />
              </button>
              <button class="action-btn action-btn-danger" title="删除" @click="emit('delete', conn.id)">
                <i class="ri-delete-bin-line" />
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </template>

    <!-- Ungrouped connections -->
    <div v-if="groupedConnections.ungrouped.length > 0" class="group-items">
      <div
        v-for="conn in groupedConnections.ungrouped"
        :key="conn.id"
        class="conn-item"
        :class="{ connecting: connectingId === conn.id, error: errorId === conn.id }"
        @click="emit('connect', conn.id)"
      >
        <div class="conn-status">
          <span class="status-dot" />
        </div>
        <div class="conn-info">
          <div class="conn-name">{{ conn.name }}</div>
          <div class="conn-host">{{ conn.host }}:{{ conn.port }}</div>
        </div>
        <div class="conn-actions" @click.stop>
          <button class="action-btn" title="编辑" @click="emit('edit', conn)">
            <i class="ri-edit-line" />
          </button>
          <button class="action-btn action-btn-danger" title="删除" @click="emit('delete', conn.id)">
            <i class="ri-delete-bin-line" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.saved-connection-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.list-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--srn-color-text-2);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  cursor: pointer;
  border-radius: var(--srn-radius-xs);
  font-size: 12px;
  color: var(--srn-color-text-2);
  user-select: none;
  transition: background var(--srn-motion-fast);
}
.group-header:hover { background: rgba(0, 0, 0, 0.03); }
.group-name { font-weight: 500; }
.group-count {
  margin-left: auto;
  font-size: 11px;
  color: var(--srn-color-text-3);
  background: var(--srn-color-surface-1);
  padding: 0 6px;
  border-radius: 8px;
}

.group-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.conn-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--srn-radius-sm);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all var(--srn-motion-fast);
  position: relative;
}
.conn-item:hover {
  background: var(--srn-color-surface-1);
  border-color: var(--srn-color-border);
}
.conn-item.connecting {
  border-color: var(--srn-color-info);
  background: rgba(0, 122, 255, 0.04);
}
.conn-item.error {
  border-color: var(--srn-color-error);
  background: rgba(255, 59, 48, 0.04);
  animation: shake 0.3s ease;
}

.conn-status { display: flex; align-items: center; }
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--srn-color-text-3);
  opacity: 0.4;
}
.conn-item.connecting .status-dot {
  background: var(--srn-color-info);
  opacity: 1;
  animation: pulse 1.5s infinite;
}
.conn-item.error .status-dot {
  background: var(--srn-color-error);
  opacity: 1;
}

.conn-info { flex: 1; min-width: 0; }
.conn-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--srn-color-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conn-host {
  font-size: 11px;
  color: var(--srn-color-text-3);
  font-family: var(--srn-font-mono);
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.conn-lock {
  font-size: 10px;
  opacity: 0.6;
}

.conn-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity var(--srn-motion-fast);
}
.conn-item:hover .conn-actions { opacity: 1; }

.action-btn {
  width: 26px;
  height: 26px;
  border: none;
  background: transparent;
  border-radius: var(--srn-radius-xs);
  color: var(--srn-color-text-3);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  transition: all var(--srn-motion-fast);
}
.action-btn:hover { background: rgba(0, 0, 0, 0.06); color: var(--srn-color-text-1); }
.action-btn-danger:hover { background: rgba(255, 59, 48, 0.08); color: var(--srn-color-error); }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-3px); }
  75% { transform: translateX(3px); }
}

.collapse-enter-active, .collapse-leave-active {
  transition: all var(--srn-motion-normal);
  overflow: hidden;
}
.collapse-enter-from, .collapse-leave-to {
  opacity: 0;
  max-height: 0;
}
.collapse-enter-to, .collapse-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>
