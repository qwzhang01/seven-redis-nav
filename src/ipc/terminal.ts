import { invoke } from './index';
import type { ConnId } from '@/types/connection';
import type { CliReply, CliHistoryEntry } from '@/types/terminal';

export async function cliExec(
  connId: ConnId,
  command: string,
  confirmToken?: string,
): Promise<CliReply> {
  return invoke<CliReply>('cli_exec', { connId, command, confirmToken });
}

export async function cliHistoryGet(): Promise<CliHistoryEntry[]> {
  return invoke<CliHistoryEntry[]>('cli_history_get');
}
