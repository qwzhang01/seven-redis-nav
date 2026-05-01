-- Phase 4: Advanced Tools migration

-- Lua script history
CREATE TABLE IF NOT EXISTS lua_scripts (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name        TEXT NOT NULL DEFAULT '',
    script      TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    last_used_at TEXT NOT NULL
);

-- Custom shortcut bindings
CREATE TABLE IF NOT EXISTS shortcut_bindings (
    action      TEXT PRIMARY KEY,
    binding     TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- Data masking rules
CREATE TABLE IF NOT EXISTS masking_rules (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    pattern     TEXT NOT NULL,
    mask_char   TEXT NOT NULL DEFAULT '***',
    enabled     INTEGER NOT NULL DEFAULT 1,
    sort_order  INTEGER NOT NULL DEFAULT 0
);

-- Health check reports
CREATE TABLE IF NOT EXISTS health_reports (
    id            TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    connection_id TEXT NOT NULL DEFAULT '',
    score         INTEGER NOT NULL DEFAULT 0,
    report_json   TEXT NOT NULL,
    created_at    TEXT NOT NULL
);
