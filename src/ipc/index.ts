import { invoke as tauriInvoke } from '@tauri-apps/api/core';
import type { IpcError, IpcErrorKind } from '@/types/ipc';

/**
 * User-friendly messages for IpcError kinds (fix 2.4).
 * Sensitive details (stack traces, internal Redis errors) are not shown to users.
 */
const FRIENDLY_MESSAGES: Record<IpcErrorKind, string> = {
  redis: 'Redis 命令执行失败',
  connection_refused: '无法连接到 Redis 服务器',
  timeout: '连接超时',
  invalid_argument: '参数无效',
  internal: '内部错误',
  auth_failed: '认证失败：密码错误或权限不足',
  auth_cancelled: '认证已取消',
  not_found: '未找到指定资源',
  dangerous_command: '危险命令需要确认',
};

/**
 * Truncate a message string to avoid exposing internal details.
 * Keeps the first 120 chars + ellipsis if longer.
 */
function truncateMessage(msg: string | undefined): string | undefined {
  if (!msg) return undefined;
  if (msg.length <= 120) return msg;
  return msg.substring(0, 120) + '…';
}

/**
 * Unified IPC invoke wrapper.
 * All ipc/*.ts modules must use this function; components must not import @tauri-apps/api directly.
 */
export async function invoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  try {
    return await tauriInvoke<T>(cmd, args);
  } catch (e: unknown) {
    // Case 1: Tauri v2 在某些情况下直接抛出对象（已经是 IpcError 结构）
    if (e !== null && typeof e === 'object' && 'kind' in e) {
      const ipcErr = e as IpcError;
      throw {
        ...ipcErr,
        message: truncateMessage(ipcErr.message),
      } as IpcError;
    }
    // Case 2: Tauri 返回的错误是 JSON 字符串
    if (typeof e === 'string') {
      try {
        const parsed = JSON.parse(e);
        throw {
          ...parsed,
          message: truncateMessage(parsed.message),
        } as IpcError;
      } catch (parseErr) {
        if ((parseErr as IpcError).kind) throw parseErr;
        throw { kind: 'internal', message: truncateMessage(String(e)) } as IpcError;
      }
    }
    // Case 3: 其他未知错误
    const msg = e instanceof Error ? e.message : String(e);
    throw { kind: 'internal', message: truncateMessage(msg) } as IpcError;
  }
}

/**
 * Get a user-friendly display message for an IpcError.
 * Returns a short, localized message based on the error kind,
 * with the original message appended in parentheses (truncated).
 */
export function getFriendlyMessage(err: IpcError): string {
  const base = FRIENDLY_MESSAGES[err.kind] ?? '操作失败';
  const detail = truncateMessage(err.message);
  return detail ? `${base}（${detail}）` : base;
}
