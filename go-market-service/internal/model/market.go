// Package model 数据模型定义
package model

import (
	"time"

	"github.com/shopspring/decimal"
)

// Exchange 交易所枚举
type Exchange string

const (
	ExchangeBinance Exchange = "binance"
	ExchangeOKX     Exchange = "okx"
	ExchangeBybit   Exchange = "bybit"
)

// Timeframe K线周期枚举
type Timeframe string

const (
	Timeframe1m  Timeframe = "1m"
	Timeframe5m  Timeframe = "5m"
	Timeframe15m Timeframe = "15m"
	Timeframe30m Timeframe = "30m"
	Timeframe1h  Timeframe = "1h"
	Timeframe4h  Timeframe = "4h"
	Timeframe1d  Timeframe = "1d"
	Timeframe1w  Timeframe = "1w"
)

// TimeframeDuration 返回周期对应的时间长度
func (t Timeframe) Duration() time.Duration {
	switch t {
	case Timeframe1m:
		return time.Minute
	case Timeframe5m:
		return 5 * time.Minute
	case Timeframe15m:
		return 15 * time.Minute
	case Timeframe30m:
		return 30 * time.Minute
	case Timeframe1h:
		return time.Hour
	case Timeframe4h:
		return 4 * time.Hour
	case Timeframe1d:
		return 24 * time.Hour
	case Timeframe1w:
		return 7 * 24 * time.Hour
	default:
		return time.Minute
	}
}

// Tick 逐笔成交数据
type Tick struct {
	Exchange  Exchange        `json:"exchange"`   // 交易所
	Symbol    string          `json:"symbol"`     // 交易对
	TradeID   string          `json:"trade_id"`   // 成交ID
	Price     decimal.Decimal `json:"price"`      // 成交价
	Quantity  decimal.Decimal `json:"quantity"`   // 成交量
	Timestamp time.Time       `json:"timestamp"`  // 成交时间
	IsBuyer   bool            `json:"is_buyer"`   // 是否买方主动
}

// OrderBook 订单簿
type OrderBook struct {
	Exchange  Exchange          `json:"exchange"`   // 交易所
	Symbol    string            `json:"symbol"`     // 交易对
	Bids      []PriceLevel      `json:"bids"`       // 买单列表
	Asks      []PriceLevel      `json:"asks"`       // 卖单列表
	Timestamp time.Time         `json:"timestamp"`  // 更新时间
}

// PriceLevel 价格档位
type PriceLevel struct {
	Price    decimal.Decimal `json:"price"`    // 价格
	Quantity decimal.Decimal `json:"quantity"` // 数量
}

// Kline K线/OHLCV数据
type Kline struct {
	Exchange   Exchange        `json:"exchange"`    // 交易所
	Symbol     string          `json:"symbol"`      // 交易对
	Timeframe  Timeframe       `json:"timeframe"`   // 周期
	OpenTime   time.Time       `json:"open_time"`   // 开盘时间
	CloseTime  time.Time       `json:"close_time"`  // 收盘时间
	Open       decimal.Decimal `json:"open"`        // 开盘价
	High       decimal.Decimal `json:"high"`        // 最高价
	Low        decimal.Decimal `json:"low"`         // 最低价
	Close      decimal.Decimal `json:"close"`       // 收盘价
	Volume     decimal.Decimal `json:"volume"`      // 成交量
	QuoteVolume decimal.Decimal `json:"quote_volume"` // 成交额
	TradeCount int64           `json:"trade_count"` // 成交笔数
	IsClosed   bool            `json:"is_closed"`   // 是否已收盘
}

// KlineWithIndicators K线+技术指标
type KlineWithIndicators struct {
	Kline
	Indicators map[string]decimal.Decimal `json:"indicators"` // 技术指标
}

// MarketDepth 市场深度
type MarketDepth struct {
	Exchange  Exchange        `json:"exchange"`
	Symbol    string          `json:"symbol"`
	BidDepth  decimal.Decimal `json:"bid_depth"`  // 买方深度
	AskDepth  decimal.Decimal `json:"ask_depth"`  // 卖方深度
	Spread    decimal.Decimal `json:"spread"`     // 买卖价差
	SpreadPct decimal.Decimal `json:"spread_pct"` // 价差百分比
	Timestamp time.Time       `json:"timestamp"`
}

// Ticker 行情快照
type Ticker struct {
	Exchange     Exchange        `json:"exchange"`
	Symbol       string          `json:"symbol"`
	LastPrice    decimal.Decimal `json:"last_price"`    // 最新价
	BidPrice     decimal.Decimal `json:"bid_price"`     // 最优买价
	AskPrice     decimal.Decimal `json:"ask_price"`     // 最优卖价
	Volume24h    decimal.Decimal `json:"volume_24h"`    // 24h成交量
	PriceChange  decimal.Decimal `json:"price_change"`  // 24h价格变化
	PriceChangePct decimal.Decimal `json:"price_change_pct"` // 24h价格变化率
	High24h      decimal.Decimal `json:"high_24h"`      // 24h最高价
	Low24h       decimal.Decimal `json:"low_24h"`       // 24h最低价
	Timestamp    time.Time       `json:"timestamp"`
}

// SubscribeRequest 订阅请求
type SubscribeRequest struct {
	Exchange  Exchange   `json:"exchange"`
	Symbol    string     `json:"symbol"`
	Channels  []string   `json:"channels"` // tick, kline, orderbook, ticker
	Timeframe Timeframe  `json:"timeframe,omitempty"`
}

// DataFeed 数据推送
type DataFeed struct {
	Type      string      `json:"type"` // tick, kline, orderbook, ticker
	Data      interface{} `json:"data"`
	Timestamp time.Time   `json:"timestamp"`
}
