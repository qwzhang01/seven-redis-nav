export type IpcErrorKind =
  | 'redis'
  | 'connection_refused'
  | 'timeout'
  | 'invalid_argument'
  | 'internal'
  | 'auth_failed'
  | 'auth_cancelled'
  | 'not_found'
  | 'dangerous_command';

export interface IpcError {
  kind: IpcErrorKind;
  message?: string;
  target?: string;
  ms?: number;
  field?: string;
  reason?: string;
  key?: string;
  command?: string;
  confirm_token?: string;
}
