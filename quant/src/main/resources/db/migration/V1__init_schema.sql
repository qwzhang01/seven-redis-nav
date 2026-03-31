-- =============================================
-- 加密货币量化交易系统 数据库初始化脚本
-- =============================================

-- K线数据表
CREATE TABLE IF NOT EXISTS t_kline (
    id              BIGSERIAL PRIMARY KEY,
    exchange        VARCHAR(20)     NOT NULL,               -- 交易所: BINANCE / OKX
    symbol          VARCHAR(30)     NOT NULL,               -- 交易对: BTC/USDT
    market_type     VARCHAR(10)     NOT NULL,               -- 市场类型: SPOT / FUTURES
    interval_val    VARCHAR(10)     NOT NULL,               -- K线周期: 1m,5m,15m,1h,4h,1d
    open_time       BIGINT          NOT NULL,               -- 开盘时间(ms timestamp)
    close_time      BIGINT          NOT NULL,               -- 收盘时间(ms timestamp)
    open_price      DECIMAL(30,10)  NOT NULL,               -- 开盘价
    high_price      DECIMAL(30,10)  NOT NULL,               -- 最高价
    low_price       DECIMAL(30,10)  NOT NULL,               -- 最低价
    close_price     DECIMAL(30,10)  NOT NULL,               -- 收盘价
    volume          DECIMAL(30,10)  NOT NULL DEFAULT 0,     -- 成交量
    quote_volume    DECIMAL(30,10)  NOT NULL DEFAULT 0,     -- 成交额
    trades_count    INTEGER         NOT NULL DEFAULT 0,     -- 成交笔数
    taker_buy_vol   DECIMAL(30,10)  DEFAULT 0,              -- 主动买入成交量
    taker_buy_quote DECIMAL(30,10)  DEFAULT 0,              -- 主动买入成交额
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_kline UNIQUE (exchange, symbol, market_type, interval_val, open_time)
);

CREATE INDEX idx_kline_query ON t_kline (exchange, symbol, market_type, interval_val, open_time DESC);

-- Tick行情数据表(最新成交)
CREATE TABLE IF NOT EXISTS t_tick (
    id              BIGSERIAL PRIMARY KEY,
    exchange        VARCHAR(20)     NOT NULL,
    symbol          VARCHAR(30)     NOT NULL,
    market_type     VARCHAR(10)     NOT NULL,
    last_price      DECIMAL(30,10)  NOT NULL,               -- 最新成交价
    best_bid_price  DECIMAL(30,10),                         -- 最优买一价
    best_bid_qty    DECIMAL(30,10),                         -- 最优买一量
    best_ask_price  DECIMAL(30,10),                         -- 最优卖一价
    best_ask_qty    DECIMAL(30,10),                         -- 最优卖一量
    volume_24h      DECIMAL(30,10)  DEFAULT 0,              -- 24h成交量
    quote_vol_24h   DECIMAL(30,10)  DEFAULT 0,              -- 24h成交额
    high_24h        DECIMAL(30,10),                         -- 24h最高价
    low_24h         DECIMAL(30,10),                         -- 24h最低价
    open_24h        DECIMAL(30,10),                         -- 24h开盘价
    price_change    DECIMAL(30,10),                         -- 24h价格变化
    price_change_pct DECIMAL(10,4),                         -- 24h价格变化百分比
    event_time      BIGINT          NOT NULL,               -- 事件时间(ms)
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_tick UNIQUE (exchange, symbol, market_type, event_time)
);

CREATE INDEX idx_tick_query ON t_tick (exchange, symbol, market_type, event_time DESC);

-- 深度数据表
CREATE TABLE IF NOT EXISTS t_depth (
    id              BIGSERIAL PRIMARY KEY,
    exchange        VARCHAR(20)     NOT NULL,
    symbol          VARCHAR(30)     NOT NULL,
    market_type     VARCHAR(10)     NOT NULL,
    bids            TEXT            NOT NULL,               -- 买单JSON: [[price,qty],...]
    asks            TEXT            NOT NULL,               -- 卖单JSON: [[price,qty],...]
    last_update_id  BIGINT,                                -- 最后更新ID
    event_time      BIGINT          NOT NULL,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_depth_query ON t_depth (exchange, symbol, market_type, event_time DESC);

-- 技术指标计算结果表
CREATE TABLE IF NOT EXISTS t_indicator (
    id              BIGSERIAL PRIMARY KEY,
    exchange        VARCHAR(20)     NOT NULL,
    symbol          VARCHAR(30)     NOT NULL,
    market_type     VARCHAR(10)     NOT NULL,
    interval_val    VARCHAR(10)     NOT NULL,
    calc_time       BIGINT          NOT NULL,               -- 计算时间
    -- 移动平均
    ma5             DECIMAL(30,10),
    ma10            DECIMAL(30,10),
    ma20            DECIMAL(30,10),
    ma60            DECIMAL(30,10),
    ema12           DECIMAL(30,10),
    ema26           DECIMAL(30,10),
    -- MACD
    macd_line       DECIMAL(30,10),
    macd_signal     DECIMAL(30,10),
    macd_histogram  DECIMAL(30,10),
    -- RSI
    rsi6            DECIMAL(10,4),
    rsi14           DECIMAL(10,4),
    rsi24           DECIMAL(10,4),
    -- 布林带
    boll_upper      DECIMAL(30,10),
    boll_middle     DECIMAL(30,10),
    boll_lower      DECIMAL(30,10),
    -- KDJ
    kdj_k           DECIMAL(10,4),
    kdj_d           DECIMAL(10,4),
    kdj_j           DECIMAL(10,4),
    -- 成交量指标
    vol_ma5         DECIMAL(30,10),
    vol_ma10        DECIMAL(30,10),
    -- ATR
    atr14           DECIMAL(30,10),
    -- VWAP
    vwap            DECIMAL(30,10),
    -- OBV
    obv             DECIMAL(30,10),
    -- 额外指标JSON
    extra_indicators TEXT,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_indicator UNIQUE (exchange, symbol, market_type, interval_val, calc_time)
);

CREATE INDEX idx_indicator_query ON t_indicator (exchange, symbol, market_type, interval_val, calc_time DESC);

-- AI分析结果表
CREATE TABLE IF NOT EXISTS t_ai_analysis (
    id              BIGSERIAL PRIMARY KEY,
    exchange        VARCHAR(20)     NOT NULL,
    symbol          VARCHAR(30)     NOT NULL,
    market_type     VARCHAR(10)     NOT NULL,
    analysis_time   BIGINT          NOT NULL,
    -- AI分析内容
    trend_direction VARCHAR(10)     NOT NULL,               -- BULLISH / BEARISH / NEUTRAL
    confidence      DECIMAL(5,2)    NOT NULL,               -- 置信度 0-100
    signal_type     VARCHAR(20)     NOT NULL,               -- BUY / SELL / HOLD / PARTIAL_CLOSE
    suggested_action VARCHAR(20)    NOT NULL,               -- OPEN_LONG / OPEN_SHORT / CLOSE_LONG / CLOSE_SHORT / PARTIAL_CLOSE / HOLD
    entry_price     DECIMAL(30,10),                         -- 建议入场价
    stop_loss       DECIMAL(30,10),                         -- 止损价
    take_profit     DECIMAL(30,10),                         -- 止盈价
    position_pct    DECIMAL(5,2),                           -- 建议仓位百分比
    risk_level      VARCHAR(10),                            -- LOW / MEDIUM / HIGH
    time_horizon    VARCHAR(20),                            -- SHORT_TERM / MEDIUM_TERM / LONG_TERM
    analysis_summary TEXT           NOT NULL,               -- 分析摘要
    detailed_analysis TEXT,                                 -- 详细分析
    indicators_used TEXT,                                   -- 使用的指标JSON
    model_name      VARCHAR(50),                            -- 使用的AI模型
    raw_response    TEXT,                                   -- AI原始响应
    executed        BOOLEAN         NOT NULL DEFAULT FALSE, -- 是否已执行
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ai_analysis_query ON t_ai_analysis (exchange, symbol, market_type, analysis_time DESC);
CREATE INDEX idx_ai_analysis_unexecuted ON t_ai_analysis (executed, created_at DESC) WHERE executed = FALSE;

-- 订单表
CREATE TABLE IF NOT EXISTS t_order (
    id              BIGSERIAL PRIMARY KEY,
    exchange        VARCHAR(20)     NOT NULL,
    symbol          VARCHAR(30)     NOT NULL,
    market_type     VARCHAR(10)     NOT NULL,
    order_id        VARCHAR(100),                           -- 交易所订单ID
    client_order_id VARCHAR(100),                           -- 客户端订单ID
    analysis_id     BIGINT,                                 -- 关联的AI分析ID
    side            VARCHAR(10)     NOT NULL,               -- BUY / SELL
    position_side   VARCHAR(10),                            -- LONG / SHORT (合约)
    order_type      VARCHAR(20)     NOT NULL,               -- MARKET / LIMIT / STOP_MARKET / TAKE_PROFIT_MARKET
    action_type     VARCHAR(20)     NOT NULL,               -- OPEN_LONG / OPEN_SHORT / CLOSE_LONG / CLOSE_SHORT / PARTIAL_CLOSE
    price           DECIMAL(30,10),                         -- 委托价格
    quantity        DECIMAL(30,10)  NOT NULL,               -- 委托数量
    filled_qty      DECIMAL(30,10)  DEFAULT 0,              -- 已成交数量
    avg_price       DECIMAL(30,10),                         -- 成交均价
    stop_loss       DECIMAL(30,10),                         -- 止损价
    take_profit     DECIMAL(30,10),                         -- 止盈价
    status          VARCHAR(20)     NOT NULL DEFAULT 'CREATED', -- CREATED/SUBMITTED/PARTIALLY_FILLED/FILLED/CANCELLED/REJECTED/EXPIRED
    fee             DECIMAL(30,10)  DEFAULT 0,              -- 手续费
    fee_asset       VARCHAR(10),                            -- 手续费币种
    pnl             DECIMAL(30,10),                         -- 盈亏
    error_msg       TEXT,                                   -- 错误信息
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_order_query ON t_order (exchange, symbol, market_type, created_at DESC);
CREATE INDEX idx_order_status ON t_order (status, created_at DESC);

-- 持仓表
CREATE TABLE IF NOT EXISTS t_position (
    id              BIGSERIAL PRIMARY KEY,
    exchange        VARCHAR(20)     NOT NULL,
    symbol          VARCHAR(30)     NOT NULL,
    market_type     VARCHAR(10)     NOT NULL,
    position_side   VARCHAR(10)     NOT NULL,               -- LONG / SHORT
    entry_price     DECIMAL(30,10)  NOT NULL,               -- 开仓均价
    quantity        DECIMAL(30,10)  NOT NULL,               -- 持仓数量
    unrealized_pnl  DECIMAL(30,10)  DEFAULT 0,              -- 未实现盈亏
    realized_pnl    DECIMAL(30,10)  DEFAULT 0,              -- 已实现盈亏
    leverage        INTEGER         DEFAULT 1,              -- 杠杆倍数
    margin          DECIMAL(30,10),                         -- 保证金
    stop_loss       DECIMAL(30,10),                         -- 止损价
    take_profit     DECIMAL(30,10),                         -- 止盈价
    status          VARCHAR(10)     NOT NULL DEFAULT 'OPEN',-- OPEN / CLOSED
    opened_at       TIMESTAMP       NOT NULL DEFAULT NOW(),
    closed_at       TIMESTAMP,
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_position UNIQUE (exchange, symbol, market_type, position_side, status)
);

CREATE INDEX idx_position_open ON t_position (status, exchange, symbol);
