import { watch } from 'vue';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { useConnectionStore } from '@/stores/connection';

const APP_NAME = 'Seven Redis Nav';

/**
 * Composable that keeps the native window title in sync with connection state.
 * - Disconnected: "Seven Redis Nav"
 * - Connected: "Seven Redis Nav — <connection-name>"
 */
export function useWindowTitle() {
  const connStore = useConnectionStore();
  const appWindow = getCurrentWindow();

  function updateTitle() {
    if (connStore.isConnected && connStore.activeConnection) {
      const connName = connStore.activeConnection.name || connStore.activeConnId;
      appWindow.setTitle(`${APP_NAME} — ${connName}`);
    } else {
      appWindow.setTitle(APP_NAME);
    }
  }

  // Watch connection state changes
  watch(
    () => [connStore.isConnected, connStore.activeConnection?.name],
    () => updateTitle(),
    { immediate: true },
  );

  return { updateTitle };
}
