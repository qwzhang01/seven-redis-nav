# 数据库初始化脚本
# 创建TimescaleDB超表和索引

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 创建K线表
CREATE TABLE IF NOT EXISTS klines (
    time TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(5) NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    quote_volume DOUBLE PRECISION,
    trade_count BIGINT,
    PRIMARY KEY (time, exchange, symbol, timeframe)
);

-- 转换为超表
SELECT create_hypertable('klines', 'time', if_not_exists => TRUE);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_klines_symbol ON klines (exchange, symbol, timeframe, time DESC);

-- 创建Tick表
CREATE TABLE IF NOT EXISTS ticks (
    time TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    trade_id VARCHAR(50),
    price DOUBLE PRECISION NOT NULL,
    quantity DOUBLE PRECISION NOT NULL,
    is_buyer BOOLEAN,
    PRIMARY KEY (time, exchange, symbol)
);

-- 转换为超表
SELECT create_hypertable('ticks', 'time', if_not_exists => TRUE);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_ticks_symbol ON ticks (exchange, symbol, time DESC);

-- 创建指标表
CREATE TABLE IF NOT EXISTS indicators (
    time TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(5) NOT NULL,
    name VARCHAR(30) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (time, exchange, symbol, timeframe, name)
);

-- 转换为超表
SELECT create_hypertable('indicators', 'time', if_not_exists => TRUE);

-- 创建交易对信息表
CREATE TABLE IF NOT EXISTS symbol_info (
    id SERIAL PRIMARY KEY,
    exchange VARCHAR(20) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    base_currency VARCHAR(10),
    quote_currency VARCHAR(10),
    price_precision INT,
    qty_precision INT,
    min_qty DOUBLE PRECISION,
    min_notional DOUBLE PRECISION,
    status VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (exchange, symbol)
);

-- 创建数据保留策略 (自动删除365天前的数据)
SELECT add_retention_policy('klines', INTERVAL '365 days', if_not_exists => TRUE);
SELECT add_retention_policy('ticks', INTERVAL '30 days', if_not_exists => TRUE);
SELECT add_retention_policy('indicators', INTERVAL '365 days', if_not_exists => TRUE);

-- 创建连续聚合视图 (可选，用于加速查询)
-- 1小时K线聚合
CREATE MATERIALIZED VIEW IF NOT EXISTS klines_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    exchange,
    symbol,
    first(open, time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, time) AS close,
    sum(volume) AS volume,
    sum(quote_volume) AS quote_volume,
    sum(trade_count) AS trade_count
FROM klines
WHERE timeframe = '1m'
GROUP BY bucket, exchange, symbol
WITH NO DATA;

-- 添加刷新策略
SELECT add_continuous_aggregate_policy('klines_1h',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);
