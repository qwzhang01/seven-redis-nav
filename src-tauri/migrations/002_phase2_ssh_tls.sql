-- Phase 2: Add SSH/TLS connection configuration columns
ALTER TABLE connections ADD COLUMN connection_type TEXT NOT NULL DEFAULT 'tcp';
ALTER TABLE connections ADD COLUMN ssh_config      TEXT;  -- JSON blob: SshConfig
ALTER TABLE connections ADD COLUMN tls_config      TEXT;  -- JSON blob: TlsConfig
