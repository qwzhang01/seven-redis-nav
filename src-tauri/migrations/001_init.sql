-- connections table: stores connection config metadata (password stored in Keychain)
CREATE TABLE IF NOT EXISTS connections (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    group_name   TEXT NOT NULL DEFAULT '',
    host         TEXT NOT NULL,
    port         INTEGER NOT NULL DEFAULT 6379,
    auth_db      INTEGER NOT NULL DEFAULT 0,
    timeout_ms   INTEGER NOT NULL DEFAULT 5000,
    keychain_key TEXT,
    sort_order   INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

-- cli_history table: stores CLI command history (keep latest 200)
CREATE TABLE IF NOT EXISTS cli_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    command    TEXT NOT NULL,
    created_at TEXT NOT NULL
);
