// Package exchange 交易所接口定义
package exchange

import (
	"context"
	"time"

	"github.com/quant/go-market-service/internal/model"
)

// Exchange 交易所接口
type Exchange interface {
	// Name 交易所名称
	Name() model.Exchange

	// Connect 连接交易所
	Connect(ctx context.Context) error

	// Disconnect 断开连接
	Disconnect() error

	// SubscribeTick 订阅逐笔成交
	SubscribeTick(ctx context.Context, symbols []string, handler TickHandler) error

	// SubscribeKline 订阅K线
	SubscribeKline(ctx context.Context, symbols []string, timeframe model.Timeframe, handler KlineHandler) error

	// SubscribeOrderBook 订阅订单簿
	SubscribeOrderBook(ctx context.Context, symbols []string, handler OrderBookHandler) error

	// SubscribeTicker 订阅行情快照
	SubscribeTicker(ctx context.Context, symbols []string, handler TickerHandler) error

	// GetHistoricalKlines 获取历史K线
	GetHistoricalKlines(ctx context.Context, symbol string, timeframe model.Timeframe, start, end time.Time, limit int) ([]model.Kline, error)

	// GetTicker 获取当前行情
	GetTicker(ctx context.Context, symbol string) (*model.Ticker, error)

	// GetOrderBook 获取订单簿
	GetOrderBook(ctx context.Context, symbol string, limit int) (*model.OrderBook, error)

	// GetSymbols 获取交易对列表
	GetSymbols(ctx context.Context) ([]model.SymbolInfo, error)

	// Ping 检查连接
	Ping(ctx context.Context) error
}

// TickHandler Tick数据处理器
type TickHandler func(tick *model.Tick)

// KlineHandler K线数据处理器
type KlineHandler func(kline *model.Kline)

// OrderBookHandler 订单簿处理器
type OrderBookHandler func(ob *model.OrderBook)

// TickerHandler 行情处理器
type TickerHandler func(ticker *model.Ticker)

// ErrorHandler 错误处理器
type ErrorHandler func(err error)
