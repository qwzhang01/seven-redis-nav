// Package model 数据库模型
package model

import (
	"time"
)

// KlineEntity K线数据库实体 (用于TimescaleDB)
type KlineEntity struct {
	Time        time.Time `gorm:"column:time;primaryKey"`          // 开盘时间
	Exchange    string    `gorm:"column:exchange;primaryKey;size:20"`
	Symbol      string    `gorm:"column:symbol;primaryKey;size:20"`
	Timeframe   string    `gorm:"column:timeframe;primaryKey;size:5"`
	Open        float64   `gorm:"column:open;type:double precision"`
	High        float64   `gorm:"column:high;type:double precision"`
	Low         float64   `gorm:"column:low;type:double precision"`
	Close       float64   `gorm:"column:close;type:double precision"`
	Volume      float64   `gorm:"column:volume;type:double precision"`
	QuoteVolume float64   `gorm:"column:quote_volume;type:double precision"`
	TradeCount  int64     `gorm:"column:trade_count"`
}

// TableName 表名
func (KlineEntity) TableName() string {
	return "klines"
}

// TickEntity Tick数据实体
type TickEntity struct {
	Time     time.Time `gorm:"column:time;primaryKey"`
	Exchange string    `gorm:"column:exchange;primaryKey;size:20"`
	Symbol   string    `gorm:"column:symbol;primaryKey;size:20"`
	TradeID  string    `gorm:"column:trade_id;size:50"`
	Price    float64   `gorm:"column:price;type:double precision"`
	Quantity float64   `gorm:"column:quantity;type:double precision"`
	IsBuyer  bool      `gorm:"column:is_buyer"`
}

// TableName 表名
func (TickEntity) TableName() string {
	return "ticks"
}

// IndicatorEntity 指标数据实体
type IndicatorEntity struct {
	Time      time.Time `gorm:"column:time;primaryKey"`
	Exchange  string    `gorm:"column:exchange;primaryKey;size:20"`
	Symbol    string    `gorm:"column:symbol;primaryKey;size:20"`
	Timeframe string    `gorm:"column:timeframe;primaryKey;size:5"`
	Name      string    `gorm:"column:name;primaryKey;size:30"` // 指标名称
	Value     float64   `gorm:"column:value;type:double precision"`
}

// TableName 表名
func (IndicatorEntity) TableName() string {
	return "indicators"
}

// SymbolInfo 交易对信息
type SymbolInfo struct {
	ID            uint      `gorm:"primaryKey"`
	Exchange      string    `gorm:"column:exchange;size:20;index:idx_symbol,unique"`
	Symbol        string    `gorm:"column:symbol;size:20;index:idx_symbol,unique"`
	BaseCurrency  string    `gorm:"column:base_currency;size:10"`
	QuoteCurrency string    `gorm:"column:quote_currency;size:10"`
	PricePrecision int      `gorm:"column:price_precision"`
	QtyPrecision   int      `gorm:"column:qty_precision"`
	MinQty        float64   `gorm:"column:min_qty;type:double precision"`
	MinNotional   float64   `gorm:"column:min_notional;type:double precision"`
	Status        string    `gorm:"column:status;size:20"` // TRADING, HALT
	CreatedAt     time.Time `gorm:"column:created_at"`
	UpdatedAt     time.Time `gorm:"column:updated_at"`
}

// TableName 表名
func (SymbolInfo) TableName() string {
	return "symbol_info"
}
