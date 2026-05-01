<script setup lang="ts">
import { ref, computed } from 'vue';
import { useWorkspaceStore } from '@/stores/workspace';
import { useShortcut } from '@/composables/useShortcut';
import { useWindowTitle } from '@/composables/useWindowTitle';
import Toolbar from '@/components/window/Toolbar.vue';
import Statusbar from '@/components/window/Statusbar.vue';
import Sidebar from '@/components/sidebar/Sidebar.vue';
import KeyPanel from '@/components/keypanel/KeyPanel.vue';
import WelcomePage from '@/views/WelcomePage.vue';
import ResizeSplitter from '@/components/common/ResizeSplitter.vue';

import BrowserWorkspace from '@/components/workspaces/browser/BrowserWorkspace.vue';
import CliWorkspace from '@/components/workspaces/cli/CliWorkspace.vue';
import MonitorWorkspace from '@/components/workspaces/monitor/MonitorWorkspace.vue';
import SlowlogWorkspace from '@/components/workspaces/slowlog/SlowlogWorkspace.vue';
import PubsubWorkspace from '@/components/workspaces/pubsub/PubsubWorkspace.vue';
import ServerConfigWorkspace from '@/components/workspaces/config/ServerConfigWorkspace.vue';
import LuaWorkspace from '@/components/workspaces/lua/LuaWorkspace.vue';
import ToolsWorkspace from '@/components/workspaces/tools/ToolsWorkspace.vue';

import SettingsModal from '@/components/settings/SettingsModal.vue';

// --- Constants ---
const SIDEBAR_DEFAULT = 240;
const SIDEBAR_MIN = 160;
const SIDEBAR_MAX = 400;
const KEYPANEL_DEFAULT = 320;
const KEYPANEL_MIN = 200;
const KEYPANEL_MAX = 500;
const STORAGE_KEY = 'srn-panel-widths';

// --- Helpers ---
function clampSidebar(v: number) {
  // Fix 2.11: secondary clamp against window width so the sidebar never
  // crowds out the keypanel + workspace to zero width.
  const maxAllowed = Math.min(SIDEBAR_MAX, window.innerWidth - KEYPANEL_MIN - 200);
  return Math.round(Math.min(maxAllowed, Math.max(SIDEBAR_MIN, v)));
}
function clampKeyPanel(v: number) {
  return Math.round(Math.min(KEYPANEL_MAX, Math.max(KEYPANEL_MIN, v)));
}

function loadWidths(): { sidebar: number; keyPanel: number } {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        sidebar: clampSidebar(parsed.sidebar ?? SIDEBAR_DEFAULT),
        keyPanel: clampKeyPanel(parsed.keyPanel ?? KEYPANEL_DEFAULT),
      };
    }
  } catch { /* ignore */ }
  return { sidebar: SIDEBAR_DEFAULT, keyPanel: KEYPANEL_DEFAULT };
}

function saveWidths(sidebar: number, keyPanel: number) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ sidebar, keyPanel }));
}

// --- Store ---
const store = useWorkspaceStore();

// Dynamic native window title
useWindowTitle();

// Panel visibility
const sidebarVisible = ref(true);
const keyPanelVisible = ref(true);

// Panel widths (persisted)
const initialWidths = loadWidths();
const sidebarWidth = ref(initialWidths.sidebar);
const keyPanelWidth = ref(initialWidths.keyPanel);

// Resizing state (disables transitions during drag)
const isResizing = ref(false);
// Track width at drag start
let sidebarStartWidth = 0;
let keyPanelStartWidth = 0;

// --- Sidebar splitter handlers ---
function onSidebarResizeStart() {
  isResizing.value = true;
  sidebarStartWidth = sidebarWidth.value;
}
function onSidebarResize(delta: number) {
  sidebarWidth.value = clampSidebar(sidebarStartWidth + delta);
}
function onSidebarResizeEnd() {
  isResizing.value = false;
  saveWidths(sidebarWidth.value, keyPanelWidth.value);
}
function onSidebarReset() {
  isResizing.value = false;
  sidebarWidth.value = SIDEBAR_DEFAULT;
  saveWidths(sidebarWidth.value, keyPanelWidth.value);
}

// --- KeyPanel splitter handlers ---
function onKeyPanelResizeStart() {
  isResizing.value = true;
  keyPanelStartWidth = keyPanelWidth.value;
}
function onKeyPanelResize(delta: number) {
  keyPanelWidth.value = clampKeyPanel(keyPanelStartWidth + delta);
}
function onKeyPanelResizeEnd() {
  isResizing.value = false;
  saveWidths(sidebarWidth.value, keyPanelWidth.value);
}
function onKeyPanelReset() {
  isResizing.value = false;
  keyPanelWidth.value = KEYPANEL_DEFAULT;
  saveWidths(sidebarWidth.value, keyPanelWidth.value);
}

// Shortcut handlers
useShortcut({
  onToggleSidebar: () => { sidebarVisible.value = !sidebarVisible.value; },
  onToggleKeyPanel: () => { keyPanelVisible.value = !keyPanelVisible.value; },
  onRefresh: () => { /* handled by individual components */ },
});

const workspaceComponent = computed(() => {
  const map = {
    browser: BrowserWorkspace,
    cli: CliWorkspace,
    monitor: MonitorWorkspace,
    slowlog: SlowlogWorkspace,
    pubsub: PubsubWorkspace,
    config: ServerConfigWorkspace,
    lua: LuaWorkspace,
    tools: ToolsWorkspace,
  } as const;
  return map[store.activeTab];
});

// Settings modal
const showSettings = ref(false);
</script>

<template>
  <div class="mac-window">
    <!-- Toolbar: only shown when connected -->
    <Toolbar v-if="store.connected" @open-settings="showSettings = true" />
    <!-- Row 3: Main body -->
    <div
      class="window-body"
      :class="{ resizing: isResizing }"
      :style="{
        '--srn-sidebar-w': sidebarWidth + 'px',
        '--srn-keypanel-w': keyPanelWidth + 'px',
      }"
    >
      <template v-if="store.connected">
        <Transition name="slide-sidebar">
          <Sidebar v-if="sidebarVisible" />
        </Transition>
        <ResizeSplitter
          v-if="sidebarVisible"
          @resize-start="onSidebarResizeStart"
          @resize="onSidebarResize"
          @resize-end="onSidebarResizeEnd"
          @reset="onSidebarReset"
        />
        <Transition name="slide-keypanel">
          <KeyPanel v-if="keyPanelVisible" />
        </Transition>
        <ResizeSplitter
          v-if="keyPanelVisible"
          @resize-start="onKeyPanelResizeStart"
          @resize="onKeyPanelResize"
          @resize-end="onKeyPanelResizeEnd"
          @reset="onKeyPanelReset"
        />
        <main class="workspace">
          <component :is="workspaceComponent" />
        </main>
      </template>
      <template v-else>
        <main class="workspace workspace-full">
          <WelcomePage />
        </main>
      </template>
    </div>
    <!-- Row 4: Statusbar -->
    <Statusbar />
    <!-- Settings Modal -->
    <SettingsModal :visible="showSettings" @close="showSettings = false" />
  </div>
</template>

<style scoped>
.mac-window {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--srn-color-surface-2);
  overflow: hidden;
  transition: all var(--srn-motion-normal) ease;
}

.window-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

/* Disable width transitions during drag for smooth performance */
.window-body.resizing :deep(.sidebar),
.window-body.resizing :deep(.key-panel) {
  transition: none !important;
}

.workspace {
  flex: 1;
  min-width: 0;
  background: var(--srn-color-surface-1);
  overflow: auto;
}

.workspace-full {
  flex: 1;
}

/* Sidebar slide animation */
.slide-sidebar-enter-active,
.slide-sidebar-leave-active {
  transition: all var(--srn-motion-normal) ease;
  overflow: hidden;
}
.slide-sidebar-enter-from,
.slide-sidebar-leave-to {
  width: 0 !important;
  opacity: 0;
}

/* KeyPanel slide animation */
.slide-keypanel-enter-active,
.slide-keypanel-leave-active {
  transition: all var(--srn-motion-normal) ease;
  overflow: hidden;
}
.slide-keypanel-enter-from,
.slide-keypanel-leave-to {
  width: 0 !important;
  opacity: 0;
}
</style>
