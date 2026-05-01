-- Phase 2: Add Sentinel/Cluster connection configuration columns
ALTER TABLE connections ADD COLUMN sentinel_nodes TEXT;  -- JSON blob: Vec<String> (host:port list)
ALTER TABLE connections ADD COLUMN master_name    TEXT;  -- Sentinel master name
ALTER TABLE connections ADD COLUMN cluster_nodes  TEXT;  -- JSON blob: Vec<String> (host:port list)
