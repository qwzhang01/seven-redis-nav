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
INSERT INTO user_info (
    id,
    username,
    nickname,
    password_hash,
    email,
    phone,
    invitation_code,
    inviter_id,
    user_type,
    registration_time,
    create_by,
    create_time,
    update_by,
    update_time,
    enable_flag
) VALUES (
    1000000000000000001, -- 使用固定的雪花ID，便于测试
    'test001',
    'test001',
    '$2b$12$eglYi6i.BJMp1Y/gLOhmxuY6PgjvKAK5u4mzUV61qyMKmMtyf2.S6', -- 哈希示例，密码:00000000
    'test001@example.com',
    NULL,
    'TEST001', -- 用户自己的邀请码
    0, -- 上级邀请人ID为0（系统用户）
    'customer',
    '2026-02-25 18:20:57+00',
    'system',
    '2026-02-25 18:20:57+00',
    'system',
    '2026-02-25 18:20:57+00',
    TRUE
) ON CONFLICT (id) DO NOTHING;

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
