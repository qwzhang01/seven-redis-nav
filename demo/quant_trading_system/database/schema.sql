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
    id BIGSERIAL PRIMARY KEY,
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
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 将kline_data表转换为时序表
SELECT create_hypertable('kline_data', 'timestamp', if_not_exists => TRUE);

-- 创建实时行情数据表
CREATE TABLE IF NOT EXISTS tick_data (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    exchange VARCHAR(32) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(30, 8) NOT NULL,
    bid_price DECIMAL(20, 8),
    ask_price DECIMAL(20, 8),
    bid_size DECIMAL(30, 8),
    ask_size DECIMAL(30, 8),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 将tick_data表转换为时序表
SELECT create_hypertable('tick_data', 'timestamp', if_not_exists => TRUE);

-- 创建深度数据表
CREATE TABLE IF NOT EXISTS depth_data (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    exchange VARCHAR(32) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    bids JSONB NOT NULL,
    asks JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

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
