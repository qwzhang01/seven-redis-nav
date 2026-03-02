-- 量化交易系统数据库建表脚本
-- PostgreSQL + TimescaleDB
-- 创建时间: 2026-02-14

-- 创建数据库（如果不存在）
-- CREATE DATABASE quant_trading;

-- 连接到数据库
-- \c quant_trading;

-- 启用TimescaleDB扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 创建用户信息表
CREATE TABLE IF NOT EXISTS user_info (
    id BIGINT PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    nickname VARCHAR(128) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    phone VARCHAR(32),
    phone_verified BOOLEAN DEFAULT FALSE,
    avatar_url VARCHAR(512),
    user_type VARCHAR(32) DEFAULT 'customer', -- customer/admin
    registration_time TIMESTAMPTZ DEFAULT NOW(),
    last_login_time TIMESTAMPTZ,
    status VARCHAR(32) DEFAULT 'active', -- active/inactive/locked
    invitation_code VARCHAR(64) NOT NULL, -- 邀请码字段
    inviter_id BIGINT, -- 邀请人ID（不强制外键约束）
    create_by VARCHAR(64) DEFAULT 'system',
    create_time TIMESTAMPTZ DEFAULT NOW(),
    update_by VARCHAR(64),
    update_time TIMESTAMPTZ DEFAULT NOW(),
    enable_flag BOOLEAN DEFAULT TRUE
);

-- 创建交易所信息表
CREATE TABLE IF NOT EXISTS exchange_info (
    id BIGINT PRIMARY KEY,
    exchange_code VARCHAR(32) UNIQUE NOT NULL, -- binance/okx/huobi
    exchange_name VARCHAR(128) NOT NULL,
    exchange_type VARCHAR(32) DEFAULT 'spot', -- spot/futures/margin
    base_url VARCHAR(512) NOT NULL,
    api_doc_url VARCHAR(512),
    status VARCHAR(32) DEFAULT 'active', -- active/inactive
    supported_pairs JSONB,
    rate_limits JSONB,
    create_by VARCHAR(64) DEFAULT 'system',
    create_time TIMESTAMPTZ DEFAULT NOW(),
    update_by VARCHAR(64),
    update_time TIMESTAMPTZ DEFAULT NOW(),
    enable_flag BOOLEAN DEFAULT TRUE
);

-- 创建邀请码管理表
CREATE TABLE IF NOT EXISTS invitation_codes (
    id BIGINT PRIMARY KEY,
    code VARCHAR(64) UNIQUE NOT NULL, -- 邀请码（唯一）
    type VARCHAR(32) DEFAULT 'user', -- user/admin/system
    max_uses INTEGER DEFAULT 1, -- 最大使用次数
    used_count INTEGER DEFAULT 0, -- 已使用次数
    created_by BIGINT REFERENCES user_info(id), -- 创建者
    created_for BIGINT REFERENCES user_info(id), -- 指定给特定用户使用
    valid_from TIMESTAMPTZ DEFAULT NOW(), -- 生效时间
    valid_until TIMESTAMPTZ, -- 过期时间
    status VARCHAR(32) DEFAULT 'active', -- active/expired/disabled
    description TEXT, -- 描述信息
    create_by VARCHAR(64) DEFAULT 'system',
    create_time TIMESTAMPTZ DEFAULT NOW(),
    update_by VARCHAR(64),
    update_time TIMESTAMPTZ DEFAULT NOW(),
    enable_flag BOOLEAN DEFAULT TRUE
);

-- 创建用户交易所API表
CREATE TABLE IF NOT EXISTS user_exchange_api (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_info(id),
    exchange_id BIGINT NOT NULL REFERENCES exchange_info(id),
    label VARCHAR(128) NOT NULL,
    api_key VARCHAR(512) NOT NULL,
    secret_key VARCHAR(512) NOT NULL,
    passphrase VARCHAR(512), -- 部分交易所需要
    permissions JSONB, -- 权限配置
    status VARCHAR(32) DEFAULT 'pending', -- pending/approved/rejected/disabled
    review_reason TEXT, -- 审核原因
    approved_by VARCHAR(64),
    approved_time TIMESTAMPTZ,
    last_used_time TIMESTAMPTZ,
    create_by VARCHAR(64),
    create_time TIMESTAMPTZ DEFAULT NOW(),
    update_by VARCHAR(64),
    update_time TIMESTAMPTZ DEFAULT NOW(),
    enable_flag BOOLEAN DEFAULT TRUE
);

-- 创建K线数据表（时序表）
CREATE TABLE IF NOT EXISTS kline_data (
    id BIGINT,
    symbol VARCHAR(32) NOT NULL,
    exchange VARCHAR(32) NOT NULL,
    timeframe VARCHAR(8) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(20, 8) NOT NULL,
    high DECIMAL(20, 8) NOT NULL,
    low DECIMAL(20, 8) NOT NULL,
    close DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(30, 8) NOT NULL,
    turnover DECIMAL(30, 8),
    is_closed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, timestamp)
);

-- 为kline_data表字段添加注释
COMMENT ON TABLE kline_data IS 'K线数据表';
COMMENT ON COLUMN kline_data.id IS '主键';
COMMENT ON COLUMN kline_data.symbol IS '交易对符号';
COMMENT ON COLUMN kline_data.exchange IS '交易所名称';
COMMENT ON COLUMN kline_data.timeframe IS '时间框架';
COMMENT ON COLUMN kline_data.timestamp IS '时间戳';
COMMENT ON COLUMN kline_data.open IS '开盘价';
COMMENT ON COLUMN kline_data.high IS '最高价';
COMMENT ON COLUMN kline_data.low IS '最低价';
COMMENT ON COLUMN kline_data.close IS '收盘价';
COMMENT ON COLUMN kline_data.volume IS '成交量';
COMMENT ON COLUMN kline_data.turnover IS '成交额';
COMMENT ON COLUMN kline_data.is_closed IS 'K线是否已闭合';
COMMENT ON COLUMN kline_data.created_at IS '记录创建时间';

-- 添加唯一约束，防止相同时间戳、相同标的的重复数据
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'kline_data_unique_constraint'
    ) THEN
        ALTER TABLE kline_data ADD CONSTRAINT kline_data_unique_constraint
        UNIQUE (symbol, exchange, timeframe, timestamp);
    END IF;
END $$;

-- 将kline_data表转换为时序表
SELECT create_hypertable('kline_data', 'timestamp', if_not_exists => TRUE);

-- 创建实时行情数据表
CREATE TABLE IF NOT EXISTS tick_data (
    id BIGINT,
    symbol VARCHAR(32) NOT NULL,
    exchange VARCHAR(32) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(30, 8) NOT NULL,
    bid_price DECIMAL(20, 8),
    ask_price DECIMAL(20, 8),
    bid_size DECIMAL(30, 8),
    ask_size DECIMAL(30, 8),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, timestamp)
);

-- 为tick_data表字段添加注释
COMMENT ON TABLE tick_data IS '实时行情数据表';
COMMENT ON COLUMN tick_data.id IS '主键';
COMMENT ON COLUMN tick_data.symbol IS '交易对符号';
COMMENT ON COLUMN tick_data.exchange IS '交易所名称';
COMMENT ON COLUMN tick_data.timestamp IS '时间戳';
COMMENT ON COLUMN tick_data.price IS '最新价格';
COMMENT ON COLUMN tick_data.volume IS '成交量';
COMMENT ON COLUMN tick_data.bid_price IS '买一价';
COMMENT ON COLUMN tick_data.ask_price IS '卖一价';
COMMENT ON COLUMN tick_data.bid_size IS '买一数量';
COMMENT ON COLUMN tick_data.ask_size IS '卖一数量';
COMMENT ON COLUMN tick_data.created_at IS '记录创建时间';

-- 添加唯一约束，防止相同时间戳、相同标的的重复数据
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'tick_data_unique_constraint'
    ) THEN
        ALTER TABLE tick_data ADD CONSTRAINT tick_data_unique_constraint
        UNIQUE (symbol, exchange, timestamp);
    END IF;
END $$;

-- 将tick_data表转换为时序表
SELECT create_hypertable('tick_data', 'timestamp', if_not_exists => TRUE);

-- 创建深度数据表
CREATE TABLE IF NOT EXISTS depth_data (
    id BIGINT,
    symbol VARCHAR(32) NOT NULL,
    exchange VARCHAR(32) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    sequence BIGINT,
    bids JSONB NOT NULL,
    asks JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, timestamp)
);

-- 为depth_data表字段添加注释
COMMENT ON TABLE depth_data IS '深度数据表';
COMMENT ON COLUMN depth_data.id IS '主键';
COMMENT ON COLUMN depth_data.symbol IS '交易对符号';
COMMENT ON COLUMN depth_data.exchange IS '交易所名称';
COMMENT ON COLUMN depth_data.timestamp IS '时间戳';
COMMENT ON COLUMN depth_data.bids IS '买单深度';
COMMENT ON COLUMN depth_data.asks IS '卖单深度';
COMMENT ON COLUMN depth_data.sequence IS '序列号';
COMMENT ON COLUMN depth_data.created_at IS '记录创建时间';

-- 添加唯一约束，防止相同时间戳、相同标的的重复数据
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'depth_data_unique_constraint'
    ) THEN
        ALTER TABLE depth_data ADD CONSTRAINT depth_data_unique_constraint
        UNIQUE (symbol, exchange, timestamp);
    END IF;
END $$;

-- 将depth_data表转换为时序表
SELECT create_hypertable('depth_data', 'timestamp', if_not_exists => TRUE);

-- 创建回测结果表
CREATE TABLE IF NOT EXISTS backtest_results (
    id BIGINT PRIMARY KEY,
    strategy_name VARCHAR(128) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    initial_capital DECIMAL(20, 2) NOT NULL,
    final_capital DECIMAL(20, 2) NOT NULL,
    total_return DECIMAL(10, 6) NOT NULL,
    annual_return DECIMAL(10, 6),
    max_drawdown DECIMAL(10, 6),
    sharpe_ratio DECIMAL(10, 6),
    total_trades INTEGER NOT NULL,
    win_rate DECIMAL(10, 6),
    total_commission DECIMAL(20, 2),
    total_slippage DECIMAL(20, 2),
    equity_curve JSONB,
    trades JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建订阅配置表
CREATE TABLE IF NOT EXISTS subscriptions (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    market_type VARCHAR(20) DEFAULT 'spot',
    data_type VARCHAR(20) NOT NULL,
    symbols JSONB NOT NULL,
    interval VARCHAR(10),
    status VARCHAR(20) DEFAULT 'stopped', -- stopped/running/paused
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_sync_time TIMESTAMPTZ,
    total_records BIGINT DEFAULT 0,
    error_count INT DEFAULT 0,
    last_error TEXT,
    config JSONB
);

COMMENT ON TABLE subscriptions IS '行情订阅配置表';
COMMENT ON COLUMN subscriptions.id IS '订阅ID';
COMMENT ON COLUMN subscriptions.name IS '订阅名称';
COMMENT ON COLUMN subscriptions.exchange IS '交易所名称';
COMMENT ON COLUMN subscriptions.market_type IS '市场类型：spot/futures/margin';
COMMENT ON COLUMN subscriptions.data_type IS '数据类型：kline/ticker/depth/trade/orderbook';
COMMENT ON COLUMN subscriptions.symbols IS '交易对列表（JSON数组）';
COMMENT ON COLUMN subscriptions.interval IS 'K线周期（仅data_type为kline时有效）';
COMMENT ON COLUMN subscriptions.status IS '订阅状态：stopped/running/paused';
COMMENT ON COLUMN subscriptions.last_sync_time IS '最后同步时间';
COMMENT ON COLUMN subscriptions.total_records IS '累计同步记录数';
COMMENT ON COLUMN subscriptions.error_count IS '累计错误次数';
COMMENT ON COLUMN subscriptions.last_error IS '最后一次错误信息';
COMMENT ON COLUMN subscriptions.config IS '高级配置（auto_restart/max_retries/batch_size/sync_interval）';

-- 创建同步任务表
CREATE TABLE IF NOT EXISTS sync_tasks (
    id VARCHAR(50) PRIMARY KEY,
    subscription_id VARCHAR(50) NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending/running/completed/failed/cancelled
    progress INT DEFAULT 0,
    total_records BIGINT DEFAULT 0,
    synced_records BIGINT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

COMMENT ON TABLE sync_tasks IS '手动同步任务表';
COMMENT ON COLUMN sync_tasks.id IS '任务ID';
COMMENT ON COLUMN sync_tasks.subscription_id IS '关联订阅ID（级联删除）';
COMMENT ON COLUMN sync_tasks.start_time IS '同步数据起始时间';
COMMENT ON COLUMN sync_tasks.end_time IS '同步数据结束时间';
COMMENT ON COLUMN sync_tasks.status IS '任务状态：pending/running/completed/failed/cancelled';
COMMENT ON COLUMN sync_tasks.progress IS '同步进度（0-100）';
COMMENT ON COLUMN sync_tasks.total_records IS '预计总记录数';
COMMENT ON COLUMN sync_tasks.synced_records IS '已同步记录数';
COMMENT ON COLUMN sync_tasks.error_message IS '错误信息';
COMMENT ON COLUMN sync_tasks.completed_at IS '任务完成时间';

-- 创建历史数据同步任务表（独立于订阅）
CREATE TABLE IF NOT EXISTS historical_sync_tasks (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    data_type VARCHAR(20) NOT NULL,
    symbols JSONB NOT NULL,
    interval VARCHAR(10),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    batch_size INTEGER DEFAULT 1000,
    status VARCHAR(20) DEFAULT 'pending', -- pending/running/completed/failed/cancelled
    progress INTEGER DEFAULT 0,
    total_records BIGINT DEFAULT 0,
    synced_records BIGINT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

COMMENT ON TABLE historical_sync_tasks IS '历史数据同步任务表（独立于订阅）';
COMMENT ON COLUMN historical_sync_tasks.id IS '任务ID';
COMMENT ON COLUMN historical_sync_tasks.name IS '任务名称';
COMMENT ON COLUMN historical_sync_tasks.exchange IS '交易所名称';
COMMENT ON COLUMN historical_sync_tasks.data_type IS '数据类型：kline/ticker/depth/trade/orderbook';
COMMENT ON COLUMN historical_sync_tasks.symbols IS '交易对列表（JSON数组）';
COMMENT ON COLUMN historical_sync_tasks.interval IS 'K线周期（仅data_type为kline时有效）';
COMMENT ON COLUMN historical_sync_tasks.start_time IS '同步数据起始时间';
COMMENT ON COLUMN historical_sync_tasks.end_time IS '同步数据结束时间';
COMMENT ON COLUMN historical_sync_tasks.batch_size IS '批量同步记录数';
COMMENT ON COLUMN historical_sync_tasks.status IS '任务状态：pending/running/completed/failed/cancelled';
COMMENT ON COLUMN historical_sync_tasks.progress IS '同步进度（0-100）';
COMMENT ON COLUMN historical_sync_tasks.total_records IS '预计总记录数';
COMMENT ON COLUMN historical_sync_tasks.synced_records IS '已同步记录数';
COMMENT ON COLUMN historical_sync_tasks.error_message IS '错误信息';
COMMENT ON COLUMN historical_sync_tasks.completed_at IS '任务完成时间';

-- 创建索引
-- 用户信息表索引
CREATE INDEX IF NOT EXISTS idx_user_info_username ON user_info (username);
CREATE INDEX IF NOT EXISTS idx_user_info_email ON user_info (email);
CREATE INDEX IF NOT EXISTS idx_user_info_invitation_code ON user_info (invitation_code);
CREATE INDEX IF NOT EXISTS idx_user_info_inviter_id ON user_info (inviter_id);
CREATE INDEX IF NOT EXISTS idx_user_info_status ON user_info (status);
CREATE INDEX IF NOT EXISTS idx_user_info_user_type ON user_info (user_type);

-- 邀请码表索引
CREATE INDEX IF NOT EXISTS idx_invitation_codes_code ON invitation_codes (code);
CREATE INDEX IF NOT EXISTS idx_invitation_codes_status ON invitation_codes (status);
CREATE INDEX IF NOT EXISTS idx_invitation_codes_type ON invitation_codes (type);
CREATE INDEX IF NOT EXISTS idx_invitation_codes_valid_until ON invitation_codes (valid_until);
CREATE INDEX IF NOT EXISTS idx_invitation_codes_created_by ON invitation_codes (created_by);
CREATE INDEX IF NOT EXISTS idx_invitation_codes_created_for ON invitation_codes (created_for);
CREATE INDEX IF NOT EXISTS idx_invitation_codes_valid_from ON invitation_codes (valid_from);
CREATE INDEX IF NOT EXISTS idx_invitation_codes_max_uses ON invitation_codes (max_uses);
CREATE INDEX IF NOT EXISTS idx_invitation_codes_used_count ON invitation_codes (used_count);

-- 为invitation_code字段添加唯一性约束
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'user_info_invitation_code_unique'
    ) THEN
        ALTER TABLE user_info ADD CONSTRAINT user_info_invitation_code_unique
        UNIQUE (invitation_code);
    END IF;
END $$;

-- 交易所信息表索引
CREATE INDEX IF NOT EXISTS idx_exchange_info_code ON exchange_info (exchange_code);
CREATE INDEX IF NOT EXISTS idx_exchange_info_type ON exchange_info (exchange_type);
CREATE INDEX IF NOT EXISTS idx_exchange_info_status ON exchange_info (status);

-- 用户交易所API表索引
CREATE INDEX IF NOT EXISTS idx_user_exchange_api_user_id ON user_exchange_api (user_id);
CREATE INDEX IF NOT EXISTS idx_user_exchange_api_exchange_id ON user_exchange_api (exchange_id);
CREATE INDEX IF NOT EXISTS idx_user_exchange_api_status ON user_exchange_api (status);
CREATE INDEX IF NOT EXISTS idx_user_exchange_api_label ON user_exchange_api (label);

-- K线数据表索引
CREATE INDEX IF NOT EXISTS idx_kline_symbol_timeframe ON kline_data (symbol, timeframe, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_kline_timestamp ON kline_data (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_kline_exchange_symbol ON kline_data (exchange, symbol);

-- Tick数据表索引
CREATE INDEX IF NOT EXISTS idx_tick_symbol ON tick_data (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tick_timestamp ON tick_data (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tick_exchange_symbol ON tick_data (exchange, symbol);

-- 深度数据表索引
CREATE INDEX IF NOT EXISTS idx_depth_symbol ON depth_data (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_depth_timestamp ON depth_data (timestamp DESC);

-- 回测结果表索引
CREATE INDEX IF NOT EXISTS idx_backtest_strategy_name ON backtest_results (strategy_name);
CREATE INDEX IF NOT EXISTS idx_backtest_time_range ON backtest_results (start_time, end_time);

-- 订阅配置表索引
CREATE INDEX IF NOT EXISTS idx_subscriptions_exchange ON subscriptions (exchange);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions (status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_data_type ON subscriptions (data_type);
CREATE INDEX IF NOT EXISTS idx_subscriptions_created_at ON subscriptions (created_at DESC);

-- 同步任务表索引
CREATE INDEX IF NOT EXISTS idx_sync_tasks_subscription_id ON sync_tasks (subscription_id);
CREATE INDEX IF NOT EXISTS idx_sync_tasks_status ON sync_tasks (status);
CREATE INDEX IF NOT EXISTS idx_sync_tasks_created_at ON sync_tasks (created_at DESC);

-- 历史数据同步任务表索引
CREATE INDEX IF NOT EXISTS idx_historical_sync_tasks_status ON historical_sync_tasks (status);
CREATE INDEX IF NOT EXISTS idx_historical_sync_tasks_exchange ON historical_sync_tasks (exchange);
CREATE INDEX IF NOT EXISTS idx_historical_sync_tasks_data_type ON historical_sync_tasks (data_type);
CREATE INDEX IF NOT EXISTS idx_historical_sync_tasks_created_at ON historical_sync_tasks (created_at DESC);

-- 创建信号记录表（策略产生的交易信号）
CREATE TABLE IF NOT EXISTS signal_records (
    id BIGINT PRIMARY KEY,
    strategy_id VARCHAR(128) NOT NULL,
    strategy_name VARCHAR(128),
    symbol VARCHAR(32) NOT NULL,
    exchange VARCHAR(32) DEFAULT 'binance',
    signal_type VARCHAR(16) NOT NULL,          -- buy/sell/close
    price DECIMAL(20, 8) NOT NULL,
    quantity DECIMAL(20, 8),
    confidence DECIMAL(5, 4),                  -- 置信度 0~1
    timeframe VARCHAR(8),
    reason TEXT,
    indicators JSONB,                          -- 触发时的指标值快照
    status VARCHAR(16) DEFAULT 'pending',      -- pending/executed/ignored/expired
    executed_order_id VARCHAR(128),
    executed_price DECIMAL(20, 8),
    executed_at TIMESTAMPTZ,
    is_public BOOLEAN DEFAULT FALSE,
    subscriber_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE signal_records IS '策略信号记录表';
COMMENT ON COLUMN signal_records.signal_type IS '信号类型: buy/sell/close';
COMMENT ON COLUMN signal_records.confidence IS '信号置信度 0.0~1.0';
COMMENT ON COLUMN signal_records.indicators IS '触发时的技术指标快照（JSON）';
COMMENT ON COLUMN signal_records.status IS '信号状态: pending/executed/ignored/expired';
COMMENT ON COLUMN signal_records.is_public IS '是否在信号广场公开展示';

CREATE INDEX IF NOT EXISTS idx_signal_strategy_id ON signal_records (strategy_id);
CREATE INDEX IF NOT EXISTS idx_signal_symbol ON signal_records (symbol);
CREATE INDEX IF NOT EXISTS idx_signal_type ON signal_records (signal_type);
CREATE INDEX IF NOT EXISTS idx_signal_status ON signal_records (status);
CREATE INDEX IF NOT EXISTS idx_signal_is_public ON signal_records (is_public);
CREATE INDEX IF NOT EXISTS idx_signal_created_at ON signal_records (created_at DESC);

-- 创建信号订阅表
CREATE TABLE IF NOT EXISTS signal_subscriptions (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_info(id) ON DELETE CASCADE,
    strategy_id VARCHAR(128) NOT NULL,
    notify_type VARCHAR(32) DEFAULT 'realtime', -- realtime/daily/weekly
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, strategy_id)
);

CREATE INDEX IF NOT EXISTS idx_signal_sub_user_id ON signal_subscriptions (user_id);
CREATE INDEX IF NOT EXISTS idx_signal_sub_strategy_id ON signal_subscriptions (strategy_id);

-- 创建排行榜快照表（定时计算并存储）
CREATE TABLE IF NOT EXISTS leaderboard_snapshots (
    id BIGINT PRIMARY KEY,
    rank_type VARCHAR(32) NOT NULL,            -- strategy/signal/user
    period VARCHAR(16) NOT NULL,               -- daily/weekly/monthly/all_time
    rank_position INTEGER NOT NULL,
    entity_id VARCHAR(128) NOT NULL,
    entity_name VARCHAR(256),
    entity_type VARCHAR(64),
    owner_id BIGINT REFERENCES user_info(id),
    owner_name VARCHAR(128),
    total_return DECIMAL(10, 6),
    annual_return DECIMAL(10, 6),
    max_drawdown DECIMAL(10, 6),
    sharpe_ratio DECIMAL(10, 6),
    win_rate DECIMAL(10, 6),
    total_trades INTEGER DEFAULT 0,
    profit_factor DECIMAL(10, 4),
    stat_start_time TIMESTAMPTZ,
    stat_end_time TIMESTAMPTZ,
    snapshot_time TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE leaderboard_snapshots IS '排行榜快照表，定时计算存储';
COMMENT ON COLUMN leaderboard_snapshots.rank_type IS '排行类型: strategy/signal/user';
COMMENT ON COLUMN leaderboard_snapshots.period IS '统计周期: daily/weekly/monthly/all_time';

CREATE INDEX IF NOT EXISTS idx_leaderboard_type_period ON leaderboard_snapshots (rank_type, period, rank_position);
CREATE INDEX IF NOT EXISTS idx_leaderboard_snapshot_time ON leaderboard_snapshots (snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_leaderboard_entity_id ON leaderboard_snapshots (entity_id);

-- 创建系统统计快照表（定时采集）
CREATE TABLE IF NOT EXISTS system_stats_snapshots (
    id BIGINT,
    snapshot_time TIMESTAMPTZ NOT NULL,
    total_users INTEGER DEFAULT 0,
    active_users_today INTEGER DEFAULT 0,
    new_users_today INTEGER DEFAULT 0,
    total_strategies INTEGER DEFAULT 0,
    running_strategies INTEGER DEFAULT 0,
    total_orders_today INTEGER DEFAULT 0,
    total_trades_today INTEGER DEFAULT 0,
    total_volume_today DECIMAL(30, 8) DEFAULT 0,
    cpu_usage DECIMAL(5, 2),
    memory_usage DECIMAL(5, 2),
    disk_usage DECIMAL(5, 2),
    subscribed_symbols INTEGER DEFAULT 0,
    kline_records_total BIGINT DEFAULT 0,
    extra_metrics JSONB,
    PRIMARY KEY (id, snapshot_time)
);

SELECT create_hypertable('system_stats_snapshots', 'snapshot_time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_stats_snapshot_time ON system_stats_snapshots (snapshot_time DESC);

-- 创建审计日志表（记录所有重要操作）
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT,
    log_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    log_level VARCHAR(16) NOT NULL DEFAULT 'INFO', -- DEBUG/INFO/WARNING/ERROR/CRITICAL
    log_category VARCHAR(32) NOT NULL,              -- system/trading/strategy/user/risk/market
    user_id BIGINT REFERENCES user_info(id),
    username VARCHAR(64),
    action VARCHAR(128) NOT NULL,
    resource_type VARCHAR(64),
    resource_id VARCHAR(128),
    request_ip VARCHAR(64),
    request_path VARCHAR(512),
    request_method VARCHAR(16),
    request_body JSONB,
    response_status INTEGER,
    duration_ms INTEGER,
    message TEXT,
    extra_data JSONB,
    PRIMARY KEY (id, log_time)
);

SELECT create_hypertable('audit_logs', 'log_time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_audit_log_time ON audit_logs (log_time DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_level ON audit_logs (log_level);
CREATE INDEX IF NOT EXISTS idx_audit_log_category ON audit_logs (log_category);
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs (action);

-- 创建风控告警表
CREATE TABLE IF NOT EXISTS risk_alerts (
    id BIGINT PRIMARY KEY,
    alert_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    alert_type VARCHAR(32) NOT NULL,           -- drawdown/position_limit/loss_limit/volatility
    severity VARCHAR(16) NOT NULL DEFAULT 'warning', -- info/warning/critical
    strategy_id VARCHAR(128),
    symbol VARCHAR(32),
    user_id BIGINT REFERENCES user_info(id),
    title VARCHAR(256) NOT NULL,
    message TEXT NOT NULL,
    trigger_value DECIMAL(20, 8),
    threshold_value DECIMAL(20, 8),
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(64),
    extra_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE risk_alerts IS '风控告警记录表';
COMMENT ON COLUMN risk_alerts.alert_type IS '告警类型: drawdown/position_limit/loss_limit/volatility';
COMMENT ON COLUMN risk_alerts.severity IS '严重程度: info/warning/critical';

CREATE INDEX IF NOT EXISTS idx_risk_alert_time ON risk_alerts (alert_time DESC);
CREATE INDEX IF NOT EXISTS idx_risk_alert_type ON risk_alerts (alert_type);
CREATE INDEX IF NOT EXISTS idx_risk_alert_severity ON risk_alerts (severity);
CREATE INDEX IF NOT EXISTS idx_risk_alert_strategy ON risk_alerts (strategy_id);
CREATE INDEX IF NOT EXISTS idx_risk_alert_resolved ON risk_alerts (is_resolved);

-- 创建信号跟单订单表（用户跟单记录主表）
CREATE TABLE IF NOT EXISTS signal_follow_orders (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_info(id) ON DELETE CASCADE,
    strategy_id VARCHAR(128) NOT NULL,              -- 跟单的策略ID
    signal_name VARCHAR(256) NOT NULL,              -- 信号/策略名称
    exchange VARCHAR(32) NOT NULL DEFAULT 'binance',-- 交易所
    follow_amount DECIMAL(20, 2) NOT NULL,          -- 跟单资金（USDT）
    current_value DECIMAL(20, 2),                   -- 当前净值（USDT）
    follow_ratio DECIMAL(5, 4) DEFAULT 1.0,         -- 跟单比例（0~1）
    stop_loss DECIMAL(5, 4),                        -- 止损比例（0~1）
    total_return DECIMAL(10, 6) DEFAULT 0,          -- 总收益率
    max_drawdown DECIMAL(10, 6) DEFAULT 0,          -- 最大回撤
    current_drawdown DECIMAL(10, 6) DEFAULT 0,      -- 当前回撤
    today_return DECIMAL(10, 6) DEFAULT 0,          -- 今日收益率
    win_rate DECIMAL(10, 6) DEFAULT 0,              -- 胜率
    total_trades INTEGER DEFAULT 0,                 -- 总交易次数
    win_trades INTEGER DEFAULT 0,                   -- 盈利次数
    loss_trades INTEGER DEFAULT 0,                  -- 亏损次数
    avg_win DECIMAL(20, 8) DEFAULT 0,               -- 平均盈利（USDT）
    avg_loss DECIMAL(20, 8) DEFAULT 0,              -- 平均亏损（USDT）
    profit_factor DECIMAL(10, 4) DEFAULT 0,         -- 盈亏比
    risk_level VARCHAR(16) DEFAULT 'low',           -- 风险等级: low/medium/high
    status VARCHAR(16) DEFAULT 'following',         -- following/stopped/paused
    start_time TIMESTAMPTZ DEFAULT NOW(),           -- 跟单开始时间
    stop_time TIMESTAMPTZ,                          -- 跟单停止时间
    return_curve JSONB,                             -- 收益曲线数据（JSON数组）
    return_curve_labels JSONB,                      -- 收益曲线时间标签（JSON数组）
    create_by VARCHAR(64),
    create_time TIMESTAMPTZ DEFAULT NOW(),
    update_time TIMESTAMPTZ DEFAULT NOW(),
    enable_flag BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE signal_follow_orders IS '信号跟单订单主表';
COMMENT ON COLUMN signal_follow_orders.follow_amount IS '跟单资金（USDT）';
COMMENT ON COLUMN signal_follow_orders.current_value IS '当前净值（USDT）';
COMMENT ON COLUMN signal_follow_orders.follow_ratio IS '跟单比例 0.0~1.0';
COMMENT ON COLUMN signal_follow_orders.stop_loss IS '止损比例 0.0~1.0';
COMMENT ON COLUMN signal_follow_orders.total_return IS '总收益率（小数，如0.1523表示15.23%）';
COMMENT ON COLUMN signal_follow_orders.max_drawdown IS '最大回撤（小数）';
COMMENT ON COLUMN signal_follow_orders.current_drawdown IS '当前回撤（小数）';
COMMENT ON COLUMN signal_follow_orders.risk_level IS '风险等级: low/medium/high';
COMMENT ON COLUMN signal_follow_orders.status IS '跟单状态: following/stopped/paused';
COMMENT ON COLUMN signal_follow_orders.return_curve IS '收益曲线数据（JSON数组）';
COMMENT ON COLUMN signal_follow_orders.return_curve_labels IS '收益曲线时间标签（JSON数组）';

CREATE INDEX IF NOT EXISTS idx_follow_orders_user_id ON signal_follow_orders (user_id);
CREATE INDEX IF NOT EXISTS idx_follow_orders_strategy_id ON signal_follow_orders (strategy_id);
CREATE INDEX IF NOT EXISTS idx_follow_orders_status ON signal_follow_orders (status);
CREATE INDEX IF NOT EXISTS idx_follow_orders_create_time ON signal_follow_orders (create_time DESC);

-- 创建信号跟单持仓表（当前持仓快照）
CREATE TABLE IF NOT EXISTS signal_follow_positions (
    id BIGINT PRIMARY KEY,
    follow_order_id BIGINT NOT NULL REFERENCES signal_follow_orders(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES user_info(id) ON DELETE CASCADE,
    symbol VARCHAR(32) NOT NULL,                    -- 交易对
    side VARCHAR(8) NOT NULL,                       -- long/short
    amount DECIMAL(20, 8) NOT NULL,                 -- 持仓数量
    entry_price DECIMAL(20, 8) NOT NULL,            -- 开仓价格
    current_price DECIMAL(20, 8),                   -- 当前价格
    pnl DECIMAL(20, 8) DEFAULT 0,                   -- 盈亏金额（USDT）
    pnl_percent DECIMAL(10, 6) DEFAULT 0,           -- 盈亏率
    status VARCHAR(16) DEFAULT 'open',              -- open/closed
    open_time TIMESTAMPTZ DEFAULT NOW(),            -- 开仓时间
    close_time TIMESTAMPTZ,                         -- 平仓时间
    create_time TIMESTAMPTZ DEFAULT NOW(),
    update_time TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE signal_follow_positions IS '信号跟单持仓表';
COMMENT ON COLUMN signal_follow_positions.side IS '持仓方向: long/short';
COMMENT ON COLUMN signal_follow_positions.pnl IS '盈亏金额（USDT）';
COMMENT ON COLUMN signal_follow_positions.pnl_percent IS '盈亏率（小数）';
COMMENT ON COLUMN signal_follow_positions.status IS '持仓状态: open/closed';

CREATE INDEX IF NOT EXISTS idx_follow_positions_order_id ON signal_follow_positions (follow_order_id);
CREATE INDEX IF NOT EXISTS idx_follow_positions_user_id ON signal_follow_positions (user_id);
CREATE INDEX IF NOT EXISTS idx_follow_positions_symbol ON signal_follow_positions (symbol);
CREATE INDEX IF NOT EXISTS idx_follow_positions_status ON signal_follow_positions (status);

-- 创建信号跟单交易记录表（历史成交记录）
CREATE TABLE IF NOT EXISTS signal_follow_trades (
    id BIGINT PRIMARY KEY,
    follow_order_id BIGINT NOT NULL REFERENCES signal_follow_orders(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES user_info(id) ON DELETE CASCADE,
    position_id BIGINT REFERENCES signal_follow_positions(id),
    symbol VARCHAR(32) NOT NULL,                    -- 交易对
    side VARCHAR(8) NOT NULL,                       -- buy/sell
    price DECIMAL(20, 8) NOT NULL,                  -- 成交价格
    amount DECIMAL(20, 8) NOT NULL,                 -- 成交数量
    total DECIMAL(20, 8) NOT NULL,                  -- 成交额（USDT）
    pnl DECIMAL(20, 8),                             -- 盈亏金额（已平仓时有值）
    fee DECIMAL(20, 8) DEFAULT 0,                   -- 手续费
    signal_record_id BIGINT REFERENCES signal_records(id), -- 关联的信号记录
    trade_time TIMESTAMPTZ DEFAULT NOW(),           -- 成交时间
    create_time TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE signal_follow_trades IS '信号跟单交易记录表';
COMMENT ON COLUMN signal_follow_trades.side IS '交易方向: buy/sell';
COMMENT ON COLUMN signal_follow_trades.pnl IS '盈亏金额（已平仓时有值，USDT）';
COMMENT ON COLUMN signal_follow_trades.fee IS '手续费（USDT）';
COMMENT ON COLUMN signal_follow_trades.signal_record_id IS '触发此交易的信号记录ID';

CREATE INDEX IF NOT EXISTS idx_follow_trades_order_id ON signal_follow_trades (follow_order_id);
CREATE INDEX IF NOT EXISTS idx_follow_trades_user_id ON signal_follow_trades (user_id);
CREATE INDEX IF NOT EXISTS idx_follow_trades_symbol ON signal_follow_trades (symbol);
CREATE INDEX IF NOT EXISTS idx_follow_trades_trade_time ON signal_follow_trades (trade_time DESC);

-- ============================================================
-- 新增表：系统预设策略、用户策略实例、模拟交易记录、模拟持仓、模拟日志
-- ============================================================

-- 创建系统预设策略表
CREATE TABLE IF NOT EXISTS preset_strategies (
    id BIGINT PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    detail TEXT,
    strategy_type VARCHAR(32) NOT NULL,         -- grid/trend/mean_reversion/momentum/arbitrage/martingale/dca/swing
    market_type VARCHAR(16) NOT NULL DEFAULT 'spot', -- spot/futures/margin
    risk_level VARCHAR(16) NOT NULL DEFAULT 'medium', -- low/medium/high
    exchange VARCHAR(32) DEFAULT 'binance',
    symbols JSONB,
    timeframe VARCHAR(8) DEFAULT '1h',
    logic_description TEXT,
    params_schema JSONB,
    default_params JSONB,
    risk_params JSONB,
    advanced_params JSONB,
    risk_warning TEXT,
    total_return DECIMAL(10, 6),
    max_drawdown DECIMAL(10, 6),
    sharpe_ratio DECIMAL(10, 6),
    win_rate DECIMAL(10, 6),
    running_days INTEGER DEFAULT 0,
    status VARCHAR(16) DEFAULT 'draft',         -- draft/testing/running/paused/stopped/error
    is_published BOOLEAN DEFAULT FALSE,
    is_featured BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    create_by VARCHAR(64) DEFAULT 'system',
    create_time TIMESTAMPTZ DEFAULT NOW(),
    update_by VARCHAR(64),
    update_time TIMESTAMPTZ DEFAULT NOW(),
    enable_flag BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE preset_strategies IS '系统预设策略表';
COMMENT ON COLUMN preset_strategies.name IS '策略名称';
COMMENT ON COLUMN preset_strategies.strategy_type IS '策略类型: grid/trend/mean_reversion/momentum/arbitrage/martingale/dca/swing';
COMMENT ON COLUMN preset_strategies.market_type IS '市场类型: spot/futures/margin';
COMMENT ON COLUMN preset_strategies.risk_level IS '风险等级: low/medium/high';
COMMENT ON COLUMN preset_strategies.status IS '策略状态: draft/testing/running/paused/stopped/error';
COMMENT ON COLUMN preset_strategies.is_published IS '是否已上架（对C端可见）';
COMMENT ON COLUMN preset_strategies.is_featured IS '是否推荐（首页展示）';
COMMENT ON COLUMN preset_strategies.params_schema IS '可配置参数schema（JSON Schema格式）';

CREATE INDEX IF NOT EXISTS idx_preset_strategies_type ON preset_strategies (strategy_type);
CREATE INDEX IF NOT EXISTS idx_preset_strategies_market ON preset_strategies (market_type);
CREATE INDEX IF NOT EXISTS idx_preset_strategies_risk ON preset_strategies (risk_level);
CREATE INDEX IF NOT EXISTS idx_preset_strategies_status ON preset_strategies (status);
CREATE INDEX IF NOT EXISTS idx_preset_strategies_published ON preset_strategies (is_published);
CREATE INDEX IF NOT EXISTS idx_preset_strategies_featured ON preset_strategies (is_featured);
CREATE INDEX IF NOT EXISTS idx_preset_strategies_create_time ON preset_strategies (create_time DESC);

-- 创建用户策略实例表
CREATE TABLE IF NOT EXISTS user_strategies (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    preset_strategy_id BIGINT NOT NULL,
    name VARCHAR(128) NOT NULL,
    mode VARCHAR(16) NOT NULL DEFAULT 'live',   -- live/simulate
    exchange VARCHAR(32) DEFAULT 'binance',
    symbols JSONB,
    timeframe VARCHAR(8) DEFAULT '1h',
    leverage INTEGER DEFAULT 1,
    initial_capital DECIMAL(20, 2) DEFAULT 10000,
    params JSONB,
    trade_mode VARCHAR(16) DEFAULT 'both',      -- both/long_only/short_only
    take_profit DECIMAL(10, 6),
    stop_loss DECIMAL(10, 6),
    stop_mode VARCHAR(16) DEFAULT 'both',       -- both/tp_only/sl_only
    max_positions INTEGER DEFAULT 10,
    max_orders INTEGER DEFAULT 50,
    max_consecutive_losses INTEGER,
    auto_cancel_orders BOOLEAN DEFAULT FALSE,
    auto_close_reverse BOOLEAN DEFAULT FALSE,
    reverse_open BOOLEAN DEFAULT FALSE,
    running_days JSONB,
    running_time_start VARCHAR(8),
    running_time_end VARCHAR(8),
    filters JSONB,
    status VARCHAR(16) DEFAULT 'stopped',       -- draft/running/paused/stopped/error
    current_value DECIMAL(20, 2),
    total_return DECIMAL(10, 6) DEFAULT 0,
    today_return DECIMAL(10, 6) DEFAULT 0,
    max_drawdown DECIMAL(10, 6) DEFAULT 0,
    sharpe_ratio DECIMAL(10, 6),
    calmar_ratio DECIMAL(10, 6),
    sortino_ratio DECIMAL(10, 6),
    win_rate DECIMAL(10, 6) DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    signal_count INTEGER DEFAULT 0,
    var_value DECIMAL(10, 6),
    volatility DECIMAL(10, 6),
    started_at TIMESTAMPTZ,
    stopped_at TIMESTAMPTZ,
    create_by VARCHAR(64),
    create_time TIMESTAMPTZ DEFAULT NOW(),
    update_by VARCHAR(64),
    update_time TIMESTAMPTZ DEFAULT NOW(),
    enable_flag BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE user_strategies IS '用户策略实例表';
COMMENT ON COLUMN user_strategies.user_id IS '用户ID';
COMMENT ON COLUMN user_strategies.preset_strategy_id IS '关联的预设策略ID';
COMMENT ON COLUMN user_strategies.mode IS '运行模式: live(实盘)/simulate(模拟)';
COMMENT ON COLUMN user_strategies.trade_mode IS '开仓模式: both/long_only/short_only';
COMMENT ON COLUMN user_strategies.stop_mode IS '止盈止损模式: both/tp_only/sl_only';
COMMENT ON COLUMN user_strategies.status IS '策略状态: draft/running/paused/stopped/error';

CREATE INDEX IF NOT EXISTS idx_user_strategies_user_id ON user_strategies (user_id);
CREATE INDEX IF NOT EXISTS idx_user_strategies_preset_id ON user_strategies (preset_strategy_id);
CREATE INDEX IF NOT EXISTS idx_user_strategies_mode ON user_strategies (mode);
CREATE INDEX IF NOT EXISTS idx_user_strategies_status ON user_strategies (status);
CREATE INDEX IF NOT EXISTS idx_user_strategies_create_time ON user_strategies (create_time DESC);

-- 创建模拟交易记录表
CREATE TABLE IF NOT EXISTS simulation_trades (
    id BIGINT PRIMARY KEY,
    user_strategy_id BIGINT NOT NULL,
    symbol VARCHAR(32) NOT NULL,
    side VARCHAR(16) NOT NULL,                  -- buy/sell
    price DECIMAL(20, 8) NOT NULL,
    amount DECIMAL(20, 8) NOT NULL,
    value DECIMAL(20, 8),
    fee DECIMAL(20, 8) DEFAULT 0,
    pnl DECIMAL(20, 8),
    trade_time TIMESTAMPTZ DEFAULT NOW(),
    create_time TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE simulation_trades IS '模拟交易记录表';
COMMENT ON COLUMN simulation_trades.user_strategy_id IS '关联的用户策略ID';
COMMENT ON COLUMN simulation_trades.side IS '交易方向: buy/sell';
COMMENT ON COLUMN simulation_trades.pnl IS '盈亏金额(USDT)';

CREATE INDEX IF NOT EXISTS idx_sim_trades_strategy_id ON simulation_trades (user_strategy_id);
CREATE INDEX IF NOT EXISTS idx_sim_trades_symbol ON simulation_trades (symbol);
CREATE INDEX IF NOT EXISTS idx_sim_trades_trade_time ON simulation_trades (trade_time DESC);

-- 创建模拟持仓表
CREATE TABLE IF NOT EXISTS simulation_positions (
    id BIGINT PRIMARY KEY,
    user_strategy_id BIGINT NOT NULL,
    symbol VARCHAR(32) NOT NULL,
    direction VARCHAR(8) NOT NULL,              -- long/short
    amount DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    current_price DECIMAL(20, 8),
    pnl DECIMAL(20, 8) DEFAULT 0,
    pnl_ratio DECIMAL(10, 6) DEFAULT 0,
    status VARCHAR(16) DEFAULT 'open',          -- open/closed
    open_time TIMESTAMPTZ DEFAULT NOW(),
    close_time TIMESTAMPTZ,
    create_time TIMESTAMPTZ DEFAULT NOW(),
    update_time TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE simulation_positions IS '模拟持仓表';
COMMENT ON COLUMN simulation_positions.direction IS '持仓方向: long/short';
COMMENT ON COLUMN simulation_positions.status IS '持仓状态: open/closed';

CREATE INDEX IF NOT EXISTS idx_sim_positions_strategy_id ON simulation_positions (user_strategy_id);
CREATE INDEX IF NOT EXISTS idx_sim_positions_status ON simulation_positions (status);
CREATE INDEX IF NOT EXISTS idx_sim_positions_symbol ON simulation_positions (symbol);

-- 创建模拟运行日志表
CREATE TABLE IF NOT EXISTS simulation_logs (
    id BIGINT PRIMARY KEY,
    user_strategy_id BIGINT NOT NULL,
    level VARCHAR(16) DEFAULT 'info',           -- info/warn/error/trade
    message TEXT NOT NULL,
    log_time TIMESTAMPTZ DEFAULT NOW(),
    create_time TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE simulation_logs IS '模拟运行日志表';
COMMENT ON COLUMN simulation_logs.level IS '日志级别: info/warn/error/trade';

CREATE INDEX IF NOT EXISTS idx_sim_logs_strategy_id ON simulation_logs (user_strategy_id);
CREATE INDEX IF NOT EXISTS idx_sim_logs_level ON simulation_logs (level);
CREATE INDEX IF NOT EXISTS idx_sim_logs_log_time ON simulation_logs (log_time DESC);

-- 查看表结构
\d user_info;
\d exchange_info;
\d user_exchange_api;

-- 查看示例数据
SELECT * FROM exchange_info;
SELECT username, nickname, email, user_type FROM user_info;


-- 量化交易系统 - 初始用户插入脚本
-- 用户名: test001, 密码: 00000000, 上级邀请人: 0
-- 创建时间: 2026-02-25

-- 1. 插入初始用户 test001
INSERT INTO public.user_info (id,username,nickname,password_hash,email,email_verified,phone,phone_verified,avatar_url,user_type,registration_time,last_login_time,status,invitation_code,inviter_id,create_by,create_time,update_by,update_time,enable_flag) VALUES
	 (1000000000000000001,'test001','test001','$2b$12$eglYi6i.BJMp1Y/gLOhmxuY6PgjvKAK5u4mzUV61qyMKmMtyf2.S6','test001@example.com',false,NULL,false,NULL,'admin','2026-02-26 02:20:57.000',NULL,'active','WEALTH',0,'system','2026-02-26 02:20:57.000','system','2026-02-26 02:20:57.000',true)
 ON CONFLICT (id) DO NOTHING;

-- 2. 插入邀请码记录（用于test001用户邀请其他人）
INSERT INTO invitation_codes (
    id,
    code,
    type,
    max_uses,
    used_count,
    created_by,
    created_for,
    valid_from,
    valid_until,
    status,
    description,
    create_by,
    create_time,
    update_by,
    update_time,
    enable_flag
) VALUES (
    1000000000000000002, -- 邀请码ID
    'TEST001', -- 邀请码
    'user', -- 类型
    10, -- 最大使用次数
    0, -- 已使用次数
    1000000000000000001, -- 创建者（test001用户）
    1000000000000000001, -- 指定给test001用户使用
    '2026-02-25 18:20:57+00', -- 生效时间
    '2027-02-25 18:20:57+00', -- 过期时间（1年后）
    'active', -- 状态
    'test001用户的邀请码，用于邀请新用户注册', -- 描述
    'system',
    '2026-02-25 18:20:57+00',
    'system',
    '2026-02-25 18:20:57+00',
    TRUE
) ON CONFLICT (id) DO NOTHING;


-- 预设策略数据插入脚本

-- 布林带策略
INSERT INTO public.preset_strategies (id,"name",description,detail,strategy_type,market_type,risk_level,exchange,symbols,timeframe,logic_description,params_schema,default_params,risk_params,advanced_params,risk_warning,total_return,max_drawdown,sharpe_ratio,win_rate,running_days,status,is_published,is_featured,sort_order,create_by,create_time,update_by,update_time,enable_flag) VALUES
	 (152410378779754497,'布林带策略','布林带策略','价格触及下轨买入，触及上轨卖出','trend','spot','medium','binance','["BTCUSDT"]','1h','本策略基于布林带指标进行交易决策：
1. 布林带计算：使用20周期移动平均线和2倍标准差构建上下轨
2. 买入信号：当价格触及或跌破布林带下轨时，视为超卖状态，产生买入信号
3. 卖出信号：当价格触及或突破布林带上轨时，视为超买状态，产生卖出信号
4. 风险控制：通过布林带的自然波动范围自动调整止损止盈位置
5. 趋势过滤：在明显的单边趋势中，布林带会扩张，策略会自动适应市场波动性变化','{"period": {"type": "int", "default":
20, "min": 5, "max": 100}, "std_dev": {"type": "float", "default": 2.0, "min": 1.0, "max": 3.0}}','{"period": 20, "std_dev": 2.0}','{}','{}','本策略在震荡市中表现较好，但在单边趋势行情中可能出现连续亏损。布林带指标对市场波动性敏感，在低波动期可能产生较多假信号。价格触及上下轨后可能继续沿趋势方向运行，导致过早入场或过早离场。建议结合其他趋势指标进行过滤，并严格控制单笔交易风险。',35.000000,42.000000,8.500000,45.000000,286,'running',true,false,1,'admin','2026-02-25 13:44:25.953',NULL,'2026-02-25 13:44:25.953',true) ON CONFLICT (id) DO NOTHING;

-- 双均线策略
INSERT INTO public.preset_strategies (id,"name",description,detail,strategy_type,market_type,risk_level,exchange,symbols,timeframe,logic_description,params_schema,default_params,risk_params,advanced_params,risk_warning,total_return,max_drawdown,sharpe_ratio,win_rate,running_days,status,is_published,is_featured,sort_order,create_by,create_time,update_by,update_time,enable_flag) VALUES
	 (152410378779754498,'双均线交叉','双均线交叉策略','当快线上穿慢线时买入，下穿时卖出','trend','spot','medium','binance','["BTCUSDT"]','15m','本策略基于双均线交叉原理进行交易：
1. 均线配置：使用5周期快线和20周期慢线，快线反映短期趋势，慢线反映长期趋势
2. 金叉信号：当快线上穿慢线时，视为短期趋势转强，产生买入信号
3. 死叉信号：当快线下穿慢线时，视为短期趋势转弱，产生卖出信号
4. 趋势确认：均线排列方向确认当前市场的主要趋势方向
5. 过滤机制：避免在震荡市中频繁交易，只在明确的趋势信号出现时入场','{"fast_period": {"type": "int", "default":
5, "min": 3, "max": 10}, "slow_period": {"type": "int", "default": 20, "min": 10, "max": 30}}','{"fast_period": 5, "slow_period": 20}','{}','{}','双均线策略在趋势明显的市场中表现优异，但在震荡市中可能产生较多假信号。均线交叉存在滞后性，可能导致入场时机较晚。建议结合成交量或其他动量指标进行确认，减少假信号干扰。在横盘整理期间应降低交易频率或暂停策略运行。',28.000000,35.000000,6.200000,38.000000,312,'running',true,false,2,'admin','2026-02-25 13:44:25.953',NULL,'2026-02-25 13:44:25.953',true) ON CONFLICT (id) DO NOTHING;

-- MACD策略
INSERT INTO public.preset_strategies (id,"name",description,detail,strategy_type,market_type,risk_level,exchange,symbols,timeframe,logic_description,params_schema,default_params,risk_params,advanced_params,risk_warning,total_return,max_drawdown,sharpe_ratio,win_rate,running_days,status,is_published,is_featured,sort_order,create_by,create_time,update_by,update_time,enable_flag) VALUES
	 (152410378779754499,'MACD交叉','MACD交叉策略','基于MACD金叉死叉的交易策略','trend','spot','medium','binance','["BTCUSDT"]','1h','本策略基于MACD指标的交叉信号进行交易：
1. MACD计算：使用12周期快线、26周期慢线和9周期信号线
2. 金叉信号：当MACD线上穿信号线时，视为多头信号，产生买入指令
3. 死叉信号：当MACD线下穿信号线时，视为空头信号，产生卖出指令
4. 柱状图分析：MACD柱状图的正负和大小反映趋势的强度和动量
5. 背离检测：价格与MACD指标的背离可作为趋势反转的预警信号','{"fast_period": {"type": "int", "default": 12, "min": 8, "max": 20}, "slow_period": {"type": "int", "default": 26, "min": 20, "max": 30}, "signal_period": {"type": "int", "default": 9, "min": 5, "max": 15}}','{"fast_period": 12, "slow_period": 26, "signal_period": 9}','{}','{}','MACD策略在趋势行情中表现稳定，但对市场噪音较为敏感，在震荡市中可能产生较多假信号。MACD指标的滞后性可能导致入场时机偏晚，错过部分趋势利润。建议结合价格行为分析或波动率过滤来优化信号质量。极端行情下MACD可能出现钝化现象，需要额外风险控制措施。',41.000000,48.000000,9.800000,52.000000,298,'running',true,true,3,'admin','2026-02-25 13:44:25.953',NULL,'2026-02-25 13:44:25.953',true)ON CONFLICT (id) DO NOTHING;

-- 多时间框架均线突破策略（已存在示例）
INSERT INTO public.preset_strategies (id,"name",description,detail,strategy_type,market_type,risk_level,exchange,symbols,timeframe,logic_description,params_schema,default_params,risk_params,advanced_params,risk_warning,total_return,max_drawdown,sharpe_ratio,win_rate,running_days,status,is_published,is_featured,sort_order,create_by,create_time,update_by,update_time,enable_flag) VALUES
	 (152410378779754496,'多周期趋势','多周期趋势+MA11回调突破+固定盈亏比交易策略','大周期定趋势方向，小周期等MA11回调，突破后顺势进场，结构止损，固定盈亏比止盈，只做顺势单，不逆市','trend','spot','medium','binance','["BTCUSDT", "ETHUSDT"]','1h','本策略采用多周期共振+均线回调突破的交易框架，核心思路为"大周期定方向，小周期找入场"：
1. 大周期趋势判断： 在4H或日线级别，通过EMA50与EMA200的排列关系判断主趋势方向。EMA50位于EMA200上方视为多头趋势，反之为空头趋势。仅在趋势明确时参与交易，震荡市自动过滤。
2. 小周期回调等待： 确认大周期趋势后，切换至15分钟或1小时级别，等待价格回调至MA11（11周期移动平均线）附近。回调的定义为价格从趋势方向的极值回撤并触及或穿越MA11。
3. 突破进场信号： 当价格在MA11附近企稳并重新突破MA11（多头趋势中向上突破，空头趋势中向下突破），确认回调结束，顺势开仓。突破需伴随K线实体收盘确认，避免假突破。
4. 结构止损设置： 止损设置在回调波段的结构低点（做多）或结构高点（做空）外侧，通常为最近一次回调的极值价格±一定缓冲点数，确保止损具有市场结构支撑。
5. 固定盈亏比止盈： 采用固定盈亏比（默认1:2）进行止盈，即止盈距离为止损距离的2
倍。不设移动止损，触及止盈或止损即平仓。严格遵守"只做顺势单，不逆市操作"的原则。','{"ma_period": {"type": "int", "default": 11, "min": 2, "max": 200, "description": "移动平均线周期"}, "risk_reward_ratio": {"type": "float", "default": 2.0, "min": 0.5, "max": 10.0, "description": "盈亏比（止盈 = 风险 × 该值）"}, "min_pullback_bars": {"type": "int", "default": 3, "min": 1, "max": 20, "description": "回调结构最少K线根数（收盘在MA另一侧）"}, "max_pullback_bars": {"type": "int", "default": 5, "min": 2, "max": 50, "description": "回调结构最多K线根数（收盘在MA另一侧）"}}','{"ma_period": 11, "risk_reward_ratio": 2.0, "min_pullback_bars": 3, "max_pullback_bars": 5}','{"max_position_size": 0.02, "max_daily_loss": 0.05, "max_consecutive_losses": 5, "stop_loss_mode": "structure", "take_profit_mode": "fixed_ratio"}','{"timeframe_mapping": {"M15": "H1", "M30": "H4", "H1": "H4", "H4": "D1"}, "trend_confirmation": true, "pullback_validation": true, "signal_quality_filter": 0.7}','本策略基于趋势跟踪逻辑，在单边趋势行情中表现较优，但在横盘震荡市中可能产生连续止损。大小周期的趋势判断存在滞后性，极端行情（如插针、闪崩）可能导致止损滑点超出预期。固定盈亏比止盈方式在强趋势中可能过早离场，无法捕获全部利润。历史回测收益不代表未来实际表现，加密货币市场波动剧烈，杠杆交易会放大风险与收益。请根据自身风险承受能力合理配置资金，建议单笔交易风险不超过总资金的2%，并确保充分了解策略逻辑后再投入使用。',43.000000,58.000000,12.000000,26.000000,354,'running',true,true,0,'admin','2026-02-25 13:44:25.953',NULL,'2026-02-25 13:44:25.953',true) ON CONFLICT (id) DO NOTHING;

-- RSI策略
INSERT INTO public.preset_strategies (id,"name",description,detail,strategy_type,market_type,risk_level,exchange,symbols,timeframe,logic_description,params_schema,default_params,risk_params,advanced_params,risk_warning,total_return,max_drawdown,sharpe_ratio,win_rate,running_days,status,is_published,is_featured,sort_order,create_by,create_time,update_by,update_time,enable_flag) VALUES
	 (152410378779754500,'RSI超买超卖','RSI超买超卖策略','RSI低于超卖线买入，高于超买线卖出','momentum','spot','medium','binance','["BTCUSDT"]','4h','本策略基于RSI指标的超买超卖现象进行交易：
1. RSI计算：使用14周期RSI指标，衡量价格变化的幅度和速度
2. 超卖买入：当RSI低于30时，视为市场处于超卖状态，价格可能反弹，产生买入信号
3. 超买卖出：当RSI高于70时，视为市场处于超买状态，价格可能回调，产生卖出信号
4. 背离确认：结合价格与RSI的背离现象，提高信号的可靠性
5. 趋势过滤：在强势趋势中，RSI可能长时间停留在超买或超卖区域，需要结合趋势判断','{"period": {"type": "int", "default": 14, "min": 10, "max": 20}, "overbought": {"type": "float", "default": 70.0, "min": 60.0, "max": 80.0}, "oversold": {"type": "float", "default": 30.0, "min": 20.0, "max": 40.0}}','{"period": 14, "overbought": 70.0, "oversold": 30.0}','{}','{}','RSI策略在区间震荡市场中表现良好，但在强势趋势行情中可能出现连续亏损。RSI指标的超买超卖阈值需要根据市场特性进行调整，不同品种和周期可能需要不同的参数设置。在极端行情中，RSI可能出现钝化现象，失去参考价值。建议结合趋势分析和成交量确认，避免在单边市中逆势操作。',32.000000,39.000000,7.500000,42.000000,275,'running',true,false,4,'admin','2026-02-25 13:44:25.953',NULL,'2026-02-25 13:44:25.953',true)ON CONFLICT (id) DO NOTHING;


-- ============================================================
-- 新增表：信号跟单核心扩展表
-- ============================================================

-- 信号提供者表（信号源的创建者/交易员信息）
CREATE TABLE IF NOT EXISTS signal_providers (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_info(id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,                    -- 提供者昵称
    avatar VARCHAR(512),                           -- 头像URL
    verified BOOLEAN DEFAULT FALSE,                -- 是否认证交易员
    bio TEXT,                                      -- 个人简介
    total_signals INTEGER DEFAULT 0,               -- 发布的信号总数
    avg_return DECIMAL(10, 6) DEFAULT 0,           -- 平均收益率
    total_followers INTEGER DEFAULT 0,             -- 总粉丝数
    rating DECIMAL(3, 2) DEFAULT 0,                -- 评分 1.00~5.00
    experience VARCHAR(64),                        -- 交易经验描述
    badges JSONB DEFAULT '[]',                     -- 徽章列表
    create_time TIMESTAMPTZ DEFAULT NOW(),
    update_time TIMESTAMPTZ DEFAULT NOW(),
    enable_flag BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE signal_providers IS '信号提供者表';
COMMENT ON COLUMN signal_providers.user_id IS '关联用户ID';
COMMENT ON COLUMN signal_providers.verified IS '是否认证交易员';
COMMENT ON COLUMN signal_providers.avg_return IS '平均收益率（小数）';
COMMENT ON COLUMN signal_providers.rating IS '评分 1.00~5.00';
COMMENT ON COLUMN signal_providers.badges IS '徽章列表（JSON数组）';

CREATE INDEX IF NOT EXISTS idx_signal_providers_user_id ON signal_providers (user_id);
CREATE INDEX IF NOT EXISTS idx_signal_providers_rating ON signal_providers (rating DESC);

-- 用户评价表（信号评论与评分）
CREATE TABLE IF NOT EXISTS signal_reviews (
    id BIGINT PRIMARY KEY,
    signal_id BIGINT NOT NULL REFERENCES signal_records(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES user_info(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),   -- 评分 1~5
    content TEXT NOT NULL,                                          -- 评价内容
    likes INTEGER DEFAULT 0,                                        -- 点赞数
    status VARCHAR(16) DEFAULT 'active',                            -- active/hidden/deleted
    create_time TIMESTAMPTZ DEFAULT NOW(),
    update_time TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE signal_reviews IS '用户评价表';
COMMENT ON COLUMN signal_reviews.rating IS '评分 1~5';
COMMENT ON COLUMN signal_reviews.likes IS '点赞数';
COMMENT ON COLUMN signal_reviews.status IS '评价状态: active/hidden/deleted';

CREATE INDEX IF NOT EXISTS idx_signal_reviews_signal_id ON signal_reviews (signal_id);
CREATE INDEX IF NOT EXISTS idx_signal_reviews_user_id ON signal_reviews (user_id);
CREATE INDEX IF NOT EXISTS idx_signal_reviews_create_time ON signal_reviews (create_time DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_signal_reviews_unique ON signal_reviews (signal_id, user_id);

-- 评价点赞表
CREATE TABLE IF NOT EXISTS signal_review_likes (
    id BIGINT PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES signal_reviews(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES user_info(id) ON DELETE CASCADE,
    create_time TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE signal_review_likes IS '评价点赞表';

CREATE UNIQUE INDEX IF NOT EXISTS idx_review_likes_unique ON signal_review_likes (review_id, user_id);
CREATE INDEX IF NOT EXISTS idx_review_likes_review_id ON signal_review_likes (review_id);

-- 信号跟单事件日志表（完整的跟单操作日志）
CREATE TABLE IF NOT EXISTS signal_follow_events (
    id BIGINT PRIMARY KEY,
    follow_order_id BIGINT NOT NULL REFERENCES signal_follow_orders(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES user_info(id) ON DELETE CASCADE,
    event_type VARCHAR(16) NOT NULL,               -- trade/success/risk/error/system
    type_label VARCHAR(32) NOT NULL,               -- 类型中文标签
    message TEXT NOT NULL,                          -- 事件描述文本
    event_meta JSONB,                               -- 事件附加数据
    event_time TIMESTAMPTZ DEFAULT NOW(),
    create_time TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE signal_follow_events IS '信号跟单事件日志表';
COMMENT ON COLUMN signal_follow_events.event_type IS '事件类型: trade/success/risk/error/system';
COMMENT ON COLUMN signal_follow_events.type_label IS '类型中文标签';
COMMENT ON COLUMN signal_follow_events.event_meta IS '事件附加数据（JSON）';

CREATE INDEX IF NOT EXISTS idx_follow_events_order_id ON signal_follow_events (follow_order_id);
CREATE INDEX IF NOT EXISTS idx_follow_events_user_id ON signal_follow_events (user_id);
CREATE INDEX IF NOT EXISTS idx_follow_events_type ON signal_follow_events (event_type);
CREATE INDEX IF NOT EXISTS idx_follow_events_time ON signal_follow_events (event_time DESC);

-- 交易所跟单账户表（用于跟踪交易所真实账户的跟单）
CREATE TABLE IF NOT EXISTS exchange_copy_accounts (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_info(id) ON DELETE CASCADE,
    exchange VARCHAR(32) NOT NULL DEFAULT 'binance',    -- 交易所
    account_type VARCHAR(16) NOT NULL DEFAULT 'spot',   -- spot/futures
    target_account_id VARCHAR(256) NOT NULL,             -- 被跟单的交易所账户ID/交易员UID
    target_account_name VARCHAR(256),                    -- 被跟单账户名称
    api_key_id BIGINT REFERENCES user_exchange_api(id),  -- 用户自己的API Key
    follow_order_id BIGINT REFERENCES signal_follow_orders(id), -- 关联的跟单记录
    sync_interval INTEGER DEFAULT 5,                     -- 同步间隔（秒）
    last_sync_time TIMESTAMPTZ,                          -- 最后同步时间
    last_sync_order_id VARCHAR(256),                     -- 最后同步的订单ID（用于增量同步）
    status VARCHAR(16) DEFAULT 'active',                 -- active/paused/stopped
    error_count INTEGER DEFAULT 0,                       -- 连续错误次数
    last_error TEXT,                                      -- 最近错误信息
    config JSONB DEFAULT '{}',                           -- 额外配置（跟单比例、过滤规则等）
    create_time TIMESTAMPTZ DEFAULT NOW(),
    update_time TIMESTAMPTZ DEFAULT NOW(),
    enable_flag BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE exchange_copy_accounts IS '交易所跟单账户表';
COMMENT ON COLUMN exchange_copy_accounts.target_account_id IS '被跟单的交易所账户ID/交易员UID';
COMMENT ON COLUMN exchange_copy_accounts.account_type IS '账户类型: spot/futures';
COMMENT ON COLUMN exchange_copy_accounts.sync_interval IS '订单同步间隔（秒）';
COMMENT ON COLUMN exchange_copy_accounts.last_sync_order_id IS '最后同步的订单ID（增量同步标记）';
COMMENT ON COLUMN exchange_copy_accounts.status IS '状态: active/paused/stopped';
COMMENT ON COLUMN exchange_copy_accounts.config IS '额外配置（跟单比例、交易对过滤等）';

CREATE INDEX IF NOT EXISTS idx_copy_accounts_user_id ON exchange_copy_accounts (user_id);
CREATE INDEX IF NOT EXISTS idx_copy_accounts_target ON exchange_copy_accounts (target_account_id);
CREATE INDEX IF NOT EXISTS idx_copy_accounts_status ON exchange_copy_accounts (status);
CREATE INDEX IF NOT EXISTS idx_copy_accounts_follow_order ON exchange_copy_accounts (follow_order_id);

-- 为signal_records表新增provider_id字段（如果不存在则添加）
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'signal_records' AND column_name = 'provider_id') THEN
        ALTER TABLE signal_records ADD COLUMN provider_id BIGINT REFERENCES signal_providers(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'signal_records' AND column_name = 'signal_source') THEN
        ALTER TABLE signal_records ADD COLUMN signal_source VARCHAR(32) DEFAULT 'internal';
        COMMENT ON COLUMN signal_records.signal_source IS '信号来源: internal(内部研究)/exchange_copy(交易所跟单)';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'signal_records' AND column_name = 'trading_pair') THEN
        ALTER TABLE signal_records ADD COLUMN trading_pair VARCHAR(32);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'signal_records' AND column_name = 'signal_strength') THEN
        ALTER TABLE signal_records ADD COLUMN signal_strength VARCHAR(16) DEFAULT 'medium';
        COMMENT ON COLUMN signal_records.signal_strength IS '信号强度: strong/medium/weak';
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_signal_provider_id ON signal_records (provider_id);
CREATE INDEX IF NOT EXISTS idx_signal_source ON signal_records (signal_source);

-- 为signal_follow_orders表新增signal_time字段（交叉跟单需记录信号原始时间）
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'signal_follow_trades' AND column_name = 'signal_time') THEN
        ALTER TABLE signal_follow_trades ADD COLUMN signal_time TIMESTAMPTZ;
        COMMENT ON COLUMN signal_follow_trades.signal_time IS '信号源发出时间';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'signal_follow_trades' AND column_name = 'slippage') THEN
        ALTER TABLE signal_follow_trades ADD COLUMN slippage DECIMAL(10, 6) DEFAULT 0;
        COMMENT ON COLUMN signal_follow_trades.slippage IS '滑点百分比';
    END IF;
END $$;


-- ============================================================
-- 新增表：信号广场核心表（信号主表及关联的参数/绩效/通知/时序数据表）
-- ============================================================

-- 信号主表（信号广场展示的信号源核心信息）
CREATE TABLE IF NOT EXISTS signal (
    id                  BIGINT PRIMARY KEY,
    name                VARCHAR(128) NOT NULL,                          -- 信号名称，如 "Alpha Pro #1"
    platform            VARCHAR(64) NOT NULL DEFAULT 'Binance',         -- 来源平台，如 Binance、OKX
    type                VARCHAR(16) NOT NULL DEFAULT 'live',            -- 信号类型：live(实盘) / simulated(模拟盘)
    signal_source       VARCHAR(16) NOT NULL DEFAULT 'strategy',        -- 信号来源：strategy(策略信号) / subscribe(订阅大佬账户)
    status              VARCHAR(16) NOT NULL DEFAULT 'running',         -- 信号状态：running / paused / stopped
    exchange            VARCHAR(64),                                    -- 交易所
    account_type        VARCHAR(16) DEFAULT 'spot',                     -- 账户类型：spot / futures
    trading_pair        VARCHAR(32),                                    -- 交易对，如 BTC/USDT
    timeframe           VARCHAR(16),                                    -- 时间周期，如 15m、1H、4H、1D
    signal_frequency    VARCHAR(16),                                    -- 信号频率：high / medium / low
    description         TEXT,                                           -- 信号描述
    provider_id         BIGINT REFERENCES signal_providers(id),         -- 信号提供者ID
    strategy_id         VARCHAR(128),                                   -- 关联的策略ID（可选，如果信号由策略生成）

    -- 订阅大佬账户时的 API 授权信息（signal_source='subscribe' 时必填）
    target_api_key      VARCHAR(512),                                   -- 目标账户 API Key
    target_api_secret   VARCHAR(512),                                   -- 目标账户 API Secret
    target_passphrase   VARCHAR(512),                                   -- 目标账户 Passphrase（部分交易所需要）
    target_account_name VARCHAR(256),                                   -- 目标账户别名（便于识别）
    testnet             BOOLEAN DEFAULT FALSE,                          -- 是否使用测试网

    -- WebSocket 监听配置
    auto_start_stream   BOOLEAN DEFAULT TRUE,                           -- 系统启动时是否自动开始监听
    watch_symbols       JSONB,                                          -- 限定监听的交易对列表（为空则全部）
    sync_history        BOOLEAN DEFAULT FALSE,                          -- 是否同步历史订单

    -- 统计字段
    followers_count     INTEGER NOT NULL DEFAULT 0,                     -- 跟随人数（冗余计数，定期同步）
    run_days            INTEGER NOT NULL DEFAULT 0,                     -- 运行天数
    cumulative_return   DECIMAL(12, 4) NOT NULL DEFAULT 0,              -- 累计收益率(%)
    max_drawdown        DECIMAL(12, 4) NOT NULL DEFAULT 0,              -- 最大回撤(%)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    enable_flag         BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE signal IS '信号广场主表 — 存储信号源的核心元数据信息，分为 strategy(策略信号) 和 subscribe(订阅大佬账户) 两类';
COMMENT ON COLUMN signal.name IS '信号名称，如 "Alpha Pro #1"';
COMMENT ON COLUMN signal.platform IS '来源平台，如 Binance、OKX';
COMMENT ON COLUMN signal.type IS '信号类型：live(实盘) / simulated(模拟盘)';
COMMENT ON COLUMN signal.signal_source IS '信号来源：strategy(交易所跟单信号) / subscribe(订阅大佬账户)';
COMMENT ON COLUMN signal.status IS '信号状态：running / paused / stopped';
COMMENT ON COLUMN signal.account_type IS '账户类型：spot(现货) / futures(合约)';
COMMENT ON COLUMN signal.provider_id IS '关联的信号提供者ID';
COMMENT ON COLUMN signal.strategy_id IS '关联的策略ID（策略生成的信号可通过此关联）';
COMMENT ON COLUMN signal.target_api_key IS '目标账户 API Key（subscribe 类型必填）';
COMMENT ON COLUMN signal.target_api_secret IS '目标账户 API Secret（subscribe 类型必填）';
COMMENT ON COLUMN signal.target_passphrase IS '目标账户 Passphrase（部分交易所需要）';
COMMENT ON COLUMN signal.target_account_name IS '目标账户别名，便于用户识别';
COMMENT ON COLUMN signal.testnet IS '是否使用测试网';
COMMENT ON COLUMN signal.auto_start_stream IS '系统启动时是否自动开始 WebSocket 监听';
COMMENT ON COLUMN signal.watch_symbols IS '限定监听的交易对列表，为空则监听全部';
COMMENT ON COLUMN signal.sync_history IS '是否同步历史订单到 signal_records';
COMMENT ON COLUMN signal.followers_count IS '跟随人数（冗余计数）';
COMMENT ON COLUMN signal.cumulative_return IS '累计收益率(%)';
COMMENT ON COLUMN signal.max_drawdown IS '最大回撤(%)';

CREATE INDEX IF NOT EXISTS idx_signal_platform ON signal (platform);
CREATE INDEX IF NOT EXISTS idx_signal_type ON signal (type);
CREATE INDEX IF NOT EXISTS idx_signal_source ON signal (signal_source);
CREATE INDEX IF NOT EXISTS idx_signal_status ON signal (status);
CREATE INDEX IF NOT EXISTS idx_signal_provider ON signal (provider_id);
CREATE INDEX IF NOT EXISTS idx_signal_strategy ON signal (strategy_id);
CREATE INDEX IF NOT EXISTS idx_signal_cumulative_return ON signal (cumulative_return DESC);
CREATE INDEX IF NOT EXISTS idx_signal_followers ON signal (followers_count DESC);
CREATE INDEX IF NOT EXISTS idx_signal_enable ON signal (enable_flag);
CREATE INDEX IF NOT EXISTS idx_signal_auto_start ON signal (auto_start_stream) WHERE status = 'running' AND enable_flag = TRUE;

-- 信号风险参数表（一对一关联signal表）
CREATE TABLE IF NOT EXISTS signal_risk_parameters (
    id                      BIGINT PRIMARY KEY,
    signal_id               BIGINT NOT NULL UNIQUE REFERENCES signal(id) ON DELETE CASCADE,
    max_position_size       DECIMAL(8, 2),          -- 最大仓位(%)
    stop_loss_percentage    DECIMAL(8, 2),           -- 止损比例(%)
    take_profit_percentage  DECIMAL(8, 2),           -- 止盈比例(%)
    risk_reward_ratio       DECIMAL(8, 2),           -- 风险收益比
    volatility_filter       BOOLEAN DEFAULT FALSE,   -- 波动率过滤开关
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE signal_risk_parameters IS '信号风险参数表';
COMMENT ON COLUMN signal_risk_parameters.max_position_size IS '最大仓位百分比(%)';
COMMENT ON COLUMN signal_risk_parameters.stop_loss_percentage IS '止损比例(%)';
COMMENT ON COLUMN signal_risk_parameters.take_profit_percentage IS '止盈比例(%)';
COMMENT ON COLUMN signal_risk_parameters.risk_reward_ratio IS '风险收益比';
COMMENT ON COLUMN signal_risk_parameters.volatility_filter IS '是否启用波动率过滤';

-- 信号绩效指标表（一对一关联signal表）
CREATE TABLE IF NOT EXISTS signal_performance_metrics (
    id                          BIGINT PRIMARY KEY,
    signal_id                   BIGINT NOT NULL UNIQUE REFERENCES signal(id) ON DELETE CASCADE,
    sharpe_ratio                DECIMAL(8, 4),          -- 夏普比率
    win_rate                    DECIMAL(8, 4),           -- 胜率(%)
    profit_factor               DECIMAL(8, 4),           -- 盈亏比
    average_holding_period      DECIMAL(8, 2),           -- 平均持仓天数
    max_consecutive_losses      INTEGER,                 -- 最大连亏次数
    total_trades                INTEGER DEFAULT 0,       -- 总交易次数
    win_trades                  INTEGER DEFAULT 0,       -- 盈利次数
    loss_trades                 INTEGER DEFAULT 0,       -- 亏损次数
    avg_win                     DECIMAL(14, 4),          -- 平均盈利金额
    avg_loss                    DECIMAL(14, 4),          -- 平均亏损金额
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE signal_performance_metrics IS '信号绩效指标表';
COMMENT ON COLUMN signal_performance_metrics.sharpe_ratio IS '夏普比率';
COMMENT ON COLUMN signal_performance_metrics.win_rate IS '胜率(%)';
COMMENT ON COLUMN signal_performance_metrics.profit_factor IS '盈亏比';
COMMENT ON COLUMN signal_performance_metrics.total_trades IS '总交易次数';

-- 信号通知设置表（一对一关联signal表）
CREATE TABLE IF NOT EXISTS signal_notification_settings (
    id                  BIGINT PRIMARY KEY,
    signal_id           BIGINT NOT NULL UNIQUE REFERENCES signal(id) ON DELETE CASCADE,
    email_alerts        BOOLEAN DEFAULT TRUE,           -- 邮件提醒
    push_notifications  BOOLEAN DEFAULT TRUE,           -- 推送通知
    telegram_bot        BOOLEAN DEFAULT FALSE,          -- Telegram 机器人
    discord_webhook     BOOLEAN DEFAULT FALSE,          -- Discord Webhook
    alert_threshold     DECIMAL(8, 2),                  -- 提醒阈值(%)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE signal_notification_settings IS '信号通知设置表';
COMMENT ON COLUMN signal_notification_settings.email_alerts IS '是否启用邮件提醒';
COMMENT ON COLUMN signal_notification_settings.push_notifications IS '是否启用推送通知';
COMMENT ON COLUMN signal_notification_settings.telegram_bot IS '是否启用Telegram机器人';
COMMENT ON COLUMN signal_notification_settings.discord_webhook IS '是否启用Discord Webhook';
COMMENT ON COLUMN signal_notification_settings.alert_threshold IS '提醒阈值百分比(%)';

-- 信号收益曲线时序表（TimescaleDB超表）
CREATE TABLE IF NOT EXISTS signal_return_curve (
    signal_id       BIGINT NOT NULL REFERENCES signal(id) ON DELETE CASCADE,
    time            TIMESTAMPTZ NOT NULL,               -- 日期
    return_value    DECIMAL(12, 4) NOT NULL,             -- 当日累计收益率(%)
    drawdown        DECIMAL(12, 4),                      -- 当日回撤(%)
    PRIMARY KEY (signal_id, time)
);

COMMENT ON TABLE signal_return_curve IS '信号收益曲线时序表';
COMMENT ON COLUMN signal_return_curve.return_value IS '当日累计收益率(%)';
COMMENT ON COLUMN signal_return_curve.drawdown IS '当日回撤(%)';

SELECT create_hypertable('signal_return_curve', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_signal_return_curve_signal ON signal_return_curve (signal_id, time DESC);

-- 信号月度收益表
CREATE TABLE IF NOT EXISTS signal_monthly_return (
    signal_id       BIGINT NOT NULL REFERENCES signal(id) ON DELETE CASCADE,
    month           DATE NOT NULL,                      -- 月份（取当月1日）
    return_value    DECIMAL(12, 4) NOT NULL,             -- 月度收益率(%)
    PRIMARY KEY (signal_id, month)
);

COMMENT ON TABLE signal_monthly_return IS '信号月度收益表';
COMMENT ON COLUMN signal_monthly_return.month IS '月份（取当月1日）';
COMMENT ON COLUMN signal_monthly_return.return_value IS '月度收益率(%)';

CREATE INDEX IF NOT EXISTS idx_signal_monthly_return ON signal_monthly_return (signal_id, month DESC);

-- 信号当前持仓表
CREATE TABLE IF NOT EXISTS signal_position (
    id              BIGINT PRIMARY KEY,
    signal_id       BIGINT NOT NULL REFERENCES signal(id) ON DELETE CASCADE,
    symbol          VARCHAR(32) NOT NULL,               -- 交易对
    side            VARCHAR(8) NOT NULL,                 -- 方向：long / short
    amount          DECIMAL(18, 8) NOT NULL,             -- 数量
    entry_price     DECIMAL(18, 8) NOT NULL,             -- 开仓价
    current_price   DECIMAL(18, 8),                      -- 当前价格（实时更新）
    pnl             DECIMAL(14, 4),                      -- 盈亏金额
    pnl_percent     DECIMAL(10, 4),                      -- 盈亏百分比(%)
    opened_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE signal_position IS '信号当前持仓表';
COMMENT ON COLUMN signal_position.side IS '方向：long(做多) / short(做空)';
COMMENT ON COLUMN signal_position.pnl IS '盈亏金额';
COMMENT ON COLUMN signal_position.pnl_percent IS '盈亏百分比(%)';

CREATE INDEX IF NOT EXISTS idx_signal_position_signal ON signal_position (signal_id);

-- 信号交易记录表（信号历史信号/交易记录）
CREATE TABLE IF NOT EXISTS signal_trade_record (
    id              BIGINT PRIMARY KEY,
    signal_id       BIGINT NOT NULL REFERENCES signal(id) ON DELETE CASCADE,
    action          VARCHAR(8) NOT NULL,                 -- buy / sell
    symbol          VARCHAR(32) NOT NULL,                -- 交易对
    price           DECIMAL(18, 8) NOT NULL,             -- 成交价格
    amount          DECIMAL(18, 8) NOT NULL,             -- 成交数量
    total           DECIMAL(18, 4),                      -- 成交额
    strength        VARCHAR(8),                          -- 信号强度：strong / medium / weak
    pnl             DECIMAL(14, 4),                      -- 盈亏金额（卖出时有值）
    traded_at       TIMESTAMPTZ NOT NULL,                -- 成交时间
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE signal_trade_record IS '信号交易记录表';
COMMENT ON COLUMN signal_trade_record.action IS '交易方向: buy/sell';
COMMENT ON COLUMN signal_trade_record.strength IS '信号强度: strong/medium/weak';
COMMENT ON COLUMN signal_trade_record.pnl IS '盈亏金额（卖出时有值）';

CREATE INDEX IF NOT EXISTS idx_signal_trade_signal ON signal_trade_record (signal_id, traded_at DESC);

-- 跟单收益曲线时序表（TimescaleDB超表，替代JSONB存储，便于大数据量查询）
CREATE TABLE IF NOT EXISTS signal_follow_return_curve (
    follow_id       BIGINT NOT NULL REFERENCES signal_follow_orders(id) ON DELETE CASCADE,
    time            TIMESTAMPTZ NOT NULL,                -- 日期
    return_value    DECIMAL(12, 4) NOT NULL,              -- 跟单累计收益率(%)
    signal_return   DECIMAL(12, 4),                       -- 对应信号源的收益率(%)（用于收益对比）
    PRIMARY KEY (follow_id, time)
);

COMMENT ON TABLE signal_follow_return_curve IS '跟单收益曲线时序表';
COMMENT ON COLUMN signal_follow_return_curve.return_value IS '跟单累计收益率(%)';
COMMENT ON COLUMN signal_follow_return_curve.signal_return IS '对应信号源的收益率(%)';

SELECT create_hypertable('signal_follow_return_curve', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_follow_return_curve ON signal_follow_return_curve (follow_id, time DESC);

-- 为signal_follow_orders表新增signal_id字段（直接关联signal主表）
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'signal_follow_orders' AND column_name = 'signal_id') THEN
        ALTER TABLE signal_follow_orders ADD COLUMN signal_id BIGINT REFERENCES signal(id);
        COMMENT ON COLUMN signal_follow_orders.signal_id IS '关联的信号广场主表ID';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'signal_follow_orders' AND column_name = 'follow_days') THEN
        ALTER TABLE signal_follow_orders ADD COLUMN follow_days INTEGER DEFAULT 0;
        COMMENT ON COLUMN signal_follow_orders.follow_days IS '跟单天数';
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_follow_orders_signal_id ON signal_follow_orders (signal_id);

-- TimescaleDB 数据保留策略
SELECT add_retention_policy('signal_return_curve', INTERVAL '2 years', if_not_exists => TRUE);
SELECT add_retention_policy('signal_follow_return_curve', INTERVAL '2 years', if_not_exists => TRUE);
