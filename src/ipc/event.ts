import { listen } from '@tauri-apps/api/event';
import type { ConnectionStateEvent } from '@/types/connection';
import type { PubSubMessage, MonitorCommand, MetricsSnapshot } from '@/types/phase2';

/**
 * Listen to connection:state events from Tauri backend.
 * Returns an unlisten function to clean up the listener.
 */
export async function listenConnectionState(
  handler: (event: ConnectionStateEvent) => void,
): Promise<() => void> {
  const unlisten = await listen<ConnectionStateEvent>('connection:state', (e) => {
    handler(e.payload);
  });
  return unlisten;
}

/**
 * Listen to pubsub:message events from Tauri backend.
 * Returns an unlisten function to clean up the listener.
 */
export async function listenPubSubMessage(
  handler: (msg: PubSubMessage) => void,
): Promise<() => void> {
  const unlisten = await listen<PubSubMessage>('pubsub:message', (e) => {
    handler(e.payload);
  });
  return unlisten;
}

/**
 * Listen to monitor:command events from Tauri backend.
 * Returns an unlisten function to clean up the listener.
 */
export async function listenMonitorCommand(
  handler: (cmd: MonitorCommand) => void,
): Promise<() => void> {
  const unlisten = await listen<MonitorCommand>('monitor:command', (e) => {
    handler(e.payload);
  });
  return unlisten;
}

/**
 * Listen to monitor:metrics events from Tauri backend.
 * Returns an unlisten function to clean up the listener.
 */
export async function listenMetricsSnapshot(
  handler: (snapshot: MetricsSnapshot) => void,
): Promise<() => void> {
  const unlisten = await listen<MetricsSnapshot>('monitor:metrics', (e) => {
    handler(e.payload);
  });
  return unlisten;
}
