// Package exchange 交易所工厂
package exchange

import (
	"fmt"

	"go.uber.org/zap"

	"github.com/quant/go-market-service/internal/config"
	"github.com/quant/go-market-service/internal/model"
)

// Factory 交易所工厂
type Factory struct {
	log *zap.Logger
}

// NewFactory 创建工厂
func NewFactory(log *zap.Logger) *Factory {
	return &Factory{log: log}
}

// Create 创建交易所实例
func (f *Factory) Create(cfg config.ExchangeConfig) (Exchange, error) {
	switch model.Exchange(cfg.Name) {
	case model.ExchangeBinance:
		return NewBinanceExchange(cfg, f.log), nil
	case model.ExchangeOKX:
		return NewOKXExchange(cfg, f.log), nil
	default:
		return nil, fmt.Errorf("不支持的交易所: %s", cfg.Name)
	}
}
