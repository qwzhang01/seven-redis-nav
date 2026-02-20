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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    create_by VARCHAR(64) DEFAULT 'system',
    create_time TIMESTAMPTZ DEFAULT NOW(),
    update_by VARCHAR(64),
    update_time TIMESTAMPTZ DEFAULT NOW(),
    enable_flag BOOLEAN DEFAULT TRUE
);

-- 创建交易所信息表
CREATE TABLE IF NOT EXISTS exchange_info (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

-- 创建用户交易所API表
CREATE TABLE IF NOT EXISTS user_exchange_api (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_info(id),
    exchange_id UUID NOT NULL REFERENCES exchange_info(id),
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
    id BIGSERIAL,
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

-- 将kline_data表转换为时序表
SELECT create_hypertable('kline_data', 'timestamp', if_not_exists => TRUE);

-- 创建实时行情数据表
CREATE TABLE IF NOT EXISTS tick_data (
    id BIGSERIAL,
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

-- 将tick_data表转换为时序表
SELECT create_hypertable('tick_data', 'timestamp', if_not_exists => TRUE);

-- 创建深度数据表
CREATE TABLE IF NOT EXISTS depth_data (
    id BIGSERIAL,
    symbol VARCHAR(32) NOT NULL,
    exchange VARCHAR(32) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
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
COMMENT ON COLUMN depth_data.bids IS '买盘深度';
COMMENT ON COLUMN depth_data.asks IS '卖盘深度';
COMMENT ON COLUMN depth_data.created_at IS '记录创建时间';

-- 将depth_data表转换为时序表
SELECT create_hypertable('depth_data', 'timestamp', if_not_exists => TRUE);

-- 创建回测结果表
CREATE TABLE IF NOT EXISTS backtest_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

-- 创建索引
-- 用户信息表索引
CREATE INDEX IF NOT EXISTS idx_user_info_username ON user_info (username);
CREATE INDEX IF NOT EXISTS idx_user_info_email ON user_info (email);
CREATE INDEX IF NOT EXISTS idx_user_info_status ON user_info (status);
CREATE INDEX IF NOT EXISTS idx_user_info_user_type ON user_info (user_type);

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

-- 插入示例数据
-- 插入示例交易所
INSERT INTO exchange_info (
    exchange_code, exchange_name, exchange_type, base_url, api_doc_url,
    supported_pairs, rate_limits
) VALUES
(
    'binance', '币安', 'spot', 'https://api.binance.com',
    'https://binance-docs.github.io/apidocs/',
    '["BTCUSDT", "ETHUSDT", "BNBUSDT"]'::JSONB,
    '{"requests_per_minute": 1200}'::JSONB
),
(
    'okx', '欧易', 'spot', 'https://www.okx.com',
    'https://www.okx.com/docs/',
    '["BTC-USDT", "ETH-USDT", "OKB-USDT"]'::JSONB,
    '{"requests_per_minute": 300}'::JSONB
),
(
    'huobi', '火币', 'spot', 'https://api.huobi.pro',
    'https://huobiapi.github.io/docs/',
    '["btcusdt", "ethusdt", "htusdt"]'::JSONB,
    '{"requests_per_minute": 100}'::JSONB
)
ON CONFLICT (exchange_code) DO NOTHING;

-- 插入示例用户（密码为password123的哈希值）
INSERT INTO user_info (
    username, nickname, password_hash, email, user_type
) VALUES
(
    'admin', '系统管理员',
    '$2b$12$LQv3c1yqBWV3pC7tb8H8CeZP3C3JZJQ9W8tYQYbY8YtY8YtY8YtY',
    'admin@quant.com', 'admin'
),
(
    'user1', '测试用户1',
    '$2b$12$LQv3c1yqBWV3pC7tb8H8CeZP3C3JZJQ9W8tYQYbY8YtY8YtY8YtY',
    'user1@quant.com', 'customer'
)
ON CONFLICT (username) DO NOTHING;

-- 查看表结构
\d user_info;
\d exchange_info;
\d user_exchange_api;

-- 查看示例数据
SELECT * FROM exchange_info;
SELECT username, nickname, email, user_type FROM user_info;
