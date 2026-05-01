import { onMounted, onUnmounted } from 'vue';
import { useWorkspaceStore } from '@/stores/workspace';
import { useTerminalStore } from '@/stores/terminal';
import { shortcutBindingList } from '@/ipc/phase4';

// Runtime custom bindings (loaded from SQLite on app start)
const customBindings: Record<string, string> = {};

/** Load custom shortcut bindings from SQLite. Called once on app init. */
export async function loadCustomShortcuts() {
  try {
    const list = await shortcutBindingList();
    list.forEach((b) => { customBindings[b.action] = b.binding; });
  } catch { /* ignore if DB not ready */ }
}

export interface ShortcutHandlers {
  onNewConnection?: () => void;
  onFocusSearch?: () => void;
  onFocusKeySearch?: () => void;
  onToggleSidebar?: () => void;
  onToggleKeyPanel?: () => void;
  onRefresh?: () => void;
}

/**
 * Global keyboard shortcut system.
 * ⌘K → focus global search
 * ⌘N → new connection
 * ⌘F → focus key search
 * ⌘1 → toggle sidebar
 * ⌘2 → toggle key panel
 * ⌘L → clear CLI (only in CLI tab)
 * ⌘+Enter → save edit (handled by individual components)
 * ⌘+Shift+R → refresh current data
 */
export function useShortcut(handlers: ShortcutHandlers = {}) {
  const workspaceStore = useWorkspaceStore();
  const terminalStore = useTerminalStore();

  function handleKeydown(e: KeyboardEvent) {
    const isMeta = e.metaKey || e.ctrlKey;
    if (!isMeta) return;

    // Build a normalized key combo string, e.g. "meta+shift+r"
    const parts: string[] = ['meta'];
    if (e.shiftKey) parts.push('shift');
    if (e.altKey) parts.push('alt');
    parts.push(e.key.toLowerCase());
    const combo = parts.join('+');

    // Helper: resolve which action matches the current combo,
    // checking custom bindings first, then falling back to defaults.
    const resolveAction = (): string | null => {
      // Check custom bindings (stored as "action → combo")
      for (const [action, customCombo] of Object.entries(customBindings)) {
        if (customCombo === combo) return action;
      }
      // Fall back to default bindings
      if (e.key === 'n' && !e.shiftKey && !e.altKey) return 'new_connection';
      if (e.key === 'k' && !e.shiftKey && !e.altKey) return 'focus_search';
      if (e.key === 'f' && !e.shiftKey && !e.altKey) return 'focus_key_search';
      if (e.key === '1' && !e.shiftKey && !e.altKey) return 'toggle_sidebar';
      if (e.key === '2' && !e.shiftKey && !e.altKey) return 'toggle_key_panel';
      if (e.key === 'l' && !e.shiftKey && !e.altKey) return 'clear_cli';
      if (e.key === 'r' && e.shiftKey && !e.altKey) return 'refresh';
      return null;
    };

    const action = resolveAction();
    if (!action) return;

    e.preventDefault();
    switch (action) {
      case 'new_connection':
        handlers.onNewConnection?.();
        break;
      case 'focus_search':
        handlers.onFocusSearch?.();
        break;
      case 'focus_key_search':
        handlers.onFocusKeySearch?.();
        break;
      case 'toggle_sidebar':
        handlers.onToggleSidebar?.();
        break;
      case 'toggle_key_panel':
        handlers.onToggleKeyPanel?.();
        break;
      case 'clear_cli':
        if (workspaceStore.activeTab === 'cli') {
          terminalStore.clearOutput();
        }
        break;
      case 'refresh':
        handlers.onRefresh?.();
        break;
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeydown);
  });

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown);
  });
}
