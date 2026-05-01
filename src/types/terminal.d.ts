export interface CliReply {
  output: string;
  is_error: boolean;
}

export interface CliHistoryEntry {
  id: number;
  command: string;
  created_at: string;
}
