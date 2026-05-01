-- Add tab_id column to cli_history for multi-tab CLI history persistence.
-- NULL tab_id means single-tab (legacy) history; non-NULL means multi-tab history.
ALTER TABLE cli_history ADD COLUMN tab_id TEXT;
ALTER TABLE cli_history ADD COLUMN conn_id TEXT;
