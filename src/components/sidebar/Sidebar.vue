<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useConnectionStore } from '@/stores/connection';
import { useKeyBrowserStore } from '@/stores/keyBrowser';
import ConnectionForm from '@/components/dialogs/ConnectionForm.vue';
import type { ConnectionConfig } from '@/types/connection';

const connStore = useConnectionStore();
const keyBrowserStore = useKeyBrowserStore();

const showForm = ref(false);
const editingConfig = ref<ConnectionConfig | null>(null);
const contextMenu = ref<{ visible: boolean; x: number; y: number; connId: string }>({
  visible: false, x: 0, y: 0, connId: '',
});

onMounted(async () => {
  await connStore.loadConnections();
  await connStore.startListening();
});

function openNewForm() {
  editingConfig.value = null;
  showForm.value = true;
}

function openEditForm(config: ConnectionConfig) {
  editingConfig.value = { ...config };
  showForm.value = true;
  contextMenu.value.visible = false;
}

async function handleConnect(connId: string) {
  try {
    await connStore.openConnection(connId);
    await keyBrowserStore.refresh();
  } catch (e) {
    console.error('Connection failed:', e);
  }
}

async function handleDisconnect(connId: string) {
  await connStore.closeConnection(connId);
  keyBrowserStore.reset();
  contextMenu.value.visible = false;
}

async function handleDelete(connId: string) {
  if (confirm('确定要删除此连接吗？')) {
    await connStore.deleteConnection(connId);
  }
  contextMenu.value.visible = false;
}

async function handleDbSelect(index: number) {
  await connStore.selectDb(index);
  await keyBrowserStore.refresh();
}

function showContextMenu(e: MouseEvent, connId: string) {
  e.preventDefault();
  contextMenu.value = { visible: true, x: e.clientX, y: e.clientY, connId };
}

function hideContextMenu() {
  contextMenu.value.visible = false;
}

function getConnStatus(connId: string) {
  const state = connStore.sessionStates[connId];
  if (state === 'connected') return 'online';
  if (state === 'reconnecting') return 'warning';
  return 'offline';
}
</script>

<template>
  <aside class="sidebar" @click="hideContextMenu">
    <!-- 连接列表 -->
    <div class="sidebar-section-header">
      <span>连接</span>
      <button class="sidebar-add" title="新建连接" @click.stop="openNewForm">
        <i class="ri-add-line" />
      </button>
    </div>
    <div class="conn-list">
      <div
        v-for="c in connStore.connections"
        :key="c.id"
        class="conn-item"
        :class="{ active: c.id === connStore.activeConnId }"
        @click="handleConnect(c.id)"
        @contextmenu.prevent="showContextMenu($event, c.id)"
      >
        <span class="conn-dot" :class="getConnStatus(c.id)" />
        <div class="conn-info">
          <div class="conn-name">{{ c.name }}</div>
          <div class="conn-host">{{ c.host }}:{{ c.port }}</div>
        </div>
        <span v-if="c.group_name" class="conn-badge">{{ c.group_name }}</span>
      </div>
      <div v-if="connStore.connections.length === 0" class="conn-empty">
        <i class="ri-plug-line" />
        <span>暂无连接，点击 + 新建</span>
      </div>
    </div>

    <!-- 数据库列表 -->
    <template v-if="connStore.isConnected">
      <div class="sidebar-section-header" style="margin-top: 12px;">
        <span>数据库 (DB)</span>
      </div>
      <div class="db-list">
        <div
          v-for="db in connStore.dbStats"
          :key="db.index"
          class="db-item"
          :class="{ active: db.index === connStore.currentDb }"
          @click="handleDbSelect(db.index)"
        >
          <i class="ri-database-line" />
          <span class="db-label">DB {{ db.index }}</span>
          <span class="db-count">{{ db.key_count.toLocaleString() }}</span>
        </div>
        <!-- Show DB 0-15 even if empty -->
        <template v-if="connStore.dbStats.length === 0">
          <div
            v-for="i in 16"
            :key="i - 1"
            class="db-item"
            :class="{ active: (i - 1) === connStore.currentDb }"
            @click="handleDbSelect(i - 1)"
          >
            <i class="ri-database-line" />
            <span class="db-label">DB {{ i - 1 }}</span>
            <span class="db-count">0</span>
          </div>
        </template>
      </div>
    </template>

    <!-- 用户信息 -->
    <div class="sidebar-footer">
      <div class="user-info">
        <div class="user-avatar">R</div>
        <div class="user-detail">
          <div class="user-name">Redis 管理员</div>
          <div class="user-dept">数据库运维组</div>
        </div>
        <button class="sidebar-add"><i class="ri-settings-3-line" /></button>
      </div>
    </div>

    <!-- Context Menu -->
    <div
      v-if="contextMenu.visible"
      class="context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
      @click.stop
    >
      <button @click="openEditForm(connStore.connections.find(c => c.id === contextMenu.connId)!)">
        <i class="ri-edit-line" /> 编辑
      </button>
      <button @click="handleDisconnect(contextMenu.connId)">
        <i class="ri-link-unlink" /> 断开
      </button>
      <div class="menu-divider" />
      <button class="danger" @click="handleDelete(contextMenu.connId)">
        <i class="ri-delete-bin-line" /> 删除
      </button>
    </div>
  </aside>

  <!-- Connection Form Dialog -->
  <ConnectionForm
    :visible="showForm"
    :edit-config="editingConfig"
    @close="showForm = false"
    @saved="showForm = false"
  />
</template>

<style scoped>
.sidebar {
  width: var(--srn-sidebar-w);
  background: var(--srn-color-sidebar);
  border-right: 1px solid var(--srn-color-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.sidebar-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px 4px;
  font-size: 10px;
  font-weight: 600;
  color: var(--srn-color-text-3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.sidebar-add {
  border: none;
  background: transparent;
  color: var(--srn-color-text-3);
  cursor: pointer;
  font-size: 14px;
  padding: 2px;
}
.sidebar-add:hover { color: var(--srn-color-text-1); }

.conn-list { flex: 0 0 auto; overflow-y: auto; max-height: 210px; padding: 0 6px; }
.conn-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: var(--srn-radius-sm);
  cursor: pointer;
  transition: background var(--srn-motion-fast);
}
.conn-item:hover { background: rgba(0, 0, 0, 0.04); }
.conn-item.active {
  background: var(--srn-color-primary);
  color: #fff;
}
.conn-item.active .conn-host,
.conn-item.active .conn-badge { color: rgba(255,255,255,0.8); }

.conn-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.conn-dot.online { background: var(--srn-color-success); }
.conn-dot.warning { background: var(--srn-color-warning); }
.conn-dot.offline { background: var(--srn-color-text-3); }

.conn-info { flex: 1; min-width: 0; }
.conn-name { font-size: 12px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.conn-host { font-size: 10px; color: var(--srn-color-text-3); font-family: var(--srn-font-mono); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.conn-badge { font-size: 9px; background: var(--srn-color-primary); color: #fff; padding: 1px 5px; border-radius: 3px; font-weight: 600; flex-shrink: 0; }
.conn-item.active .conn-badge { background: rgba(255,255,255,0.25); }

.conn-empty { display: flex; align-items: center; gap: 6px; padding: 12px 8px; font-size: 11px; color: var(--srn-color-text-3); }

.db-list { flex: 1; overflow-y: auto; padding: 0 6px; }
.db-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-radius: var(--srn-radius-xs);
  font-size: 12px;
  cursor: pointer;
  transition: background var(--srn-motion-fast);
}
.db-item:hover { background: rgba(0, 0, 0, 0.04); }
.db-item.active { background: rgba(220, 56, 45, 0.08); color: var(--srn-color-primary); font-weight: 500; }
.db-item i { color: var(--srn-color-text-3); font-size: 13px; }
.db-label { flex: 1; }
.db-count { font-family: var(--srn-font-mono); font-size: 11px; color: var(--srn-color-text-3); }

.sidebar-footer {
  margin-top: auto;
  border-top: 1px solid var(--srn-color-border);
  padding: 8px 12px;
}
.user-info { display: flex; align-items: center; gap: 8px; }
.user-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, #ef4444, #f97316);
  color: #fff; font-weight: 700; font-size: 13px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.user-detail { flex: 1; min-width: 0; }
.user-name { font-size: 11px; font-weight: 500; color: var(--srn-color-text-1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-dept { font-size: 10px; color: var(--srn-color-text-3); }

/* Context Menu */
.context-menu {
  position: fixed;
  background: var(--srn-color-surface-2);
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  z-index: 2000;
  min-width: 140px;
  padding: 4px;
}
.context-menu button {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 12px;
  border: none;
  background: transparent;
  font-size: 12px;
  color: var(--srn-color-text-1);
  cursor: pointer;
  border-radius: var(--srn-radius-xs);
  text-align: left;
}
.context-menu button:hover { background: rgba(0,0,0,0.05); }
.context-menu button.danger { color: var(--srn-color-primary); }
.menu-divider { height: 1px; background: var(--srn-color-border); margin: 4px 0; }
</style>
