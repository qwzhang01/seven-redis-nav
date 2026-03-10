// Package service 数据输出服务
// 为回测和实盘提供统一的数据接口
package service

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/shopspring/decimal"
	"go.uber.org/zap"

	"github.com/quant/go-market-service/internal/indicator"
	"github.com/quant/go-market-service/internal/model"
)

// DataFeedMode 数据输出模式
type DataFeedMode string

const (
	// DataFeedModeBacktest 回测模式
	DataFeedModeBacktest DataFeedMode = "backtest"
	// DataFeedModeLive 实盘模式
	DataFeedModeLive DataFeedMode = "live"
)

// DataFeedConfig 数据输出配置
type DataFeedConfig struct {
	Mode       DataFeedMode    `json:"mode"`        // 模式
	Exchange   model.Exchange  `json:"exchange"`    // 交易所
	Symbols    []string        `json:"symbols"`     // 交易对
	Timeframes []model.Timeframe `json:"timeframes"` // 时间周期
	
	// 回测模式配置
	StartTime time.Time `json:"start_time,omitempty"` // 开始时间
	EndTime   time.Time `json:"end_time,omitempty"`   // 结束时间
	Speed     int       `json:"speed,omitempty"`      // 回放速度倍数
	
	// 指标配置
	EnableIndicators bool     `json:"enable_indicators"` // 是否计算指标
	Indicators       []string `json:"indicators"`        // 需要的指标列表
}

// DataPoint 数据点
type DataPoint struct {
	Timestamp  time.Time                    `json:"timestamp"`
	Exchange   model.Exchange               `json:"exchange"`
	Symbol     string                       `json:"symbol"`
	Timeframe  model.Timeframe              `json:"timeframe"`
	Kline      *model.Kline                 `json:"kline,omitempty"`
	Tick       *model.Tick                  `json:"tick,omitempty"`
	Ticker     *model.Ticker                `json:"ticker,omitempty"`
	Indicators map[string]decimal.Decimal   `json:"indicators,omitempty"`
}

// DataFeedHandler 数据处理函数
type DataFeedHandler func(dp *DataPoint)

// DataFeed 数据输出服务
type DataFeed struct {
	cfg     *DataFeedConfig
	svc     *Service
	log     *zap.Logger
	
	handlers []DataFeedHandler
	mu       sync.RWMutex
	stopCh   chan struct{}
	running  bool
}

// NewDataFeed 创建数据输出服务
func NewDataFeed(cfg *DataFeedConfig, svc *Service, log *zap.Logger) *DataFeed {
	return &DataFeed{
		cfg:    cfg,
		svc:    svc,
		log:    log.With(zap.String("component", "data_feed")),
		stopCh: make(chan struct{}),
	}
}

// Subscribe 订阅数据
func (f *DataFeed) Subscribe(handler DataFeedHandler) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.handlers = append(f.handlers, handler)
}

// Start 启动数据输出
func (f *DataFeed) Start(ctx context.Context) error {
	f.mu.Lock()
	if f.running {
		f.mu.Unlock()
		return fmt.Errorf("数据输出服务已在运行")
	}
	f.running = true
	f.mu.Unlock()

	switch f.cfg.Mode {
	case DataFeedModeBacktest:
		return f.startBacktest(ctx)
	case DataFeedModeLive:
		return f.startLive(ctx)
	default:
		return fmt.Errorf("不支持的模式: %s", f.cfg.Mode)
	}
}

// startBacktest 启动回测模式
func (f *DataFeed) startBacktest(ctx context.Context) error {
	f.log.Info("启动回测数据输出",
		zap.Time("start", f.cfg.StartTime),
		zap.Time("end", f.cfg.EndTime),
		zap.Int("speed", f.cfg.Speed),
	)

	go func() {
		for _, symbol := range f.cfg.Symbols {
			for _, tf := range f.cfg.Timeframes {
				// 获取历史K线
				klines, err := f.svc.GetKlines(ctx, f.cfg.Exchange, symbol, tf, f.cfg.StartTime, f.cfg.EndTime)
				if err != nil {
					f.log.Error("获取历史K线失败", zap.Error(err))
					continue
				}

				// 按时间顺序回放
				for _, k := range klines {
					select {
					case <-ctx.Done():
						return
					case <-f.stopCh:
						return
					default:
						// 构建数据点
						dp := &DataPoint{
							Timestamp: k.OpenTime,
							Exchange:  f.cfg.Exchange,
							Symbol:    symbol,
							Timeframe: tf,
							Kline:     k,
						}

						// 计算指标
						if f.cfg.EnableIndicators {
							result := f.svc.GetIndicators(f.cfg.Exchange, symbol, tf)
							if result != nil {
								dp.Indicators = f.filterIndicators(result.Indicators)
							}
						}

						// 通知订阅者
						f.notify(dp)

						// 控制回放速度
						if f.cfg.Speed > 0 {
							time.Sleep(time.Duration(1000/f.cfg.Speed) * time.Millisecond)
						}
					}
				}
			}
		}

		f.log.Info("回测数据输出完成")
	}()

	return nil
}

// startLive 启动实盘模式
func (f *DataFeed) startLive(ctx context.Context) error {
	f.log.Info("启动实盘数据输出",
		zap.Strings("symbols", f.cfg.Symbols),
	)

	// 订阅实时K线
	f.svc.SubscribeKline(func(k *model.Kline) {
		// 检查是否是我们关注的交易对
		if k.Exchange != f.cfg.Exchange || !f.containsSymbol(k.Symbol) || !f.containsTimeframe(k.Timeframe) {
			return
		}

		dp := &DataPoint{
			Timestamp: time.Now(),
			Exchange:  k.Exchange,
			Symbol:    k.Symbol,
			Timeframe: k.Timeframe,
			Kline:     k,
		}

		// 计算指标
		if f.cfg.EnableIndicators && k.IsClosed {
			result := f.svc.GetIndicators(k.Exchange, k.Symbol, k.Timeframe)
			if result != nil {
				dp.Indicators = f.filterIndicators(result.Indicators)
			}
		}

		f.notify(dp)
	})

	// 订阅Tick
	f.svc.SubscribeTick(func(tick *model.Tick) {
		if tick.Exchange != f.cfg.Exchange || !f.containsSymbol(tick.Symbol) {
			return
		}

		dp := &DataPoint{
			Timestamp: tick.Timestamp,
			Exchange:  tick.Exchange,
			Symbol:    tick.Symbol,
			Tick:      tick,
		}

		f.notify(dp)
	})

	// 订阅行情
	f.svc.SubscribeTicker(func(ticker *model.Ticker) {
		if ticker.Exchange != f.cfg.Exchange || !f.containsSymbol(ticker.Symbol) {
			return
		}

		dp := &DataPoint{
			Timestamp: ticker.Timestamp,
			Exchange:  ticker.Exchange,
			Symbol:    ticker.Symbol,
			Ticker:    ticker,
		}

		f.notify(dp)
	})

	return nil
}

// notify 通知订阅者
func (f *DataFeed) notify(dp *DataPoint) {
	f.mu.RLock()
	handlers := f.handlers
	f.mu.RUnlock()

	for _, h := range handlers {
		go h(dp)
	}
}

// filterIndicators 过滤指标
func (f *DataFeed) filterIndicators(indicators map[string]decimal.Decimal) map[string]decimal.Decimal {
	if len(f.cfg.Indicators) == 0 {
		return indicators
	}

	filtered := make(map[string]decimal.Decimal)
	for _, name := range f.cfg.Indicators {
		if val, ok := indicators[name]; ok {
			filtered[name] = val
		}
	}
	return filtered
}

// containsSymbol 检查是否包含交易对
func (f *DataFeed) containsSymbol(symbol string) bool {
	for _, s := range f.cfg.Symbols {
		if s == symbol {
			return true
		}
	}
	return false
}

// containsTimeframe 检查是否包含时间周期
func (f *DataFeed) containsTimeframe(tf model.Timeframe) bool {
	for _, t := range f.cfg.Timeframes {
		if t == tf {
			return true
		}
	}
	return false
}

// Stop 停止数据输出
func (f *DataFeed) Stop() {
	f.mu.Lock()
	defer f.mu.Unlock()

	if !f.running {
		return
	}

	close(f.stopCh)
	f.running = false
	f.log.Info("数据输出服务已停止")
}

// BacktestDataProvider 回测数据提供者
// 提供更灵活的回测数据访问方式
type BacktestDataProvider struct {
	svc *Service
	log *zap.Logger
}

// NewBacktestDataProvider 创建回测数据提供者
func NewBacktestDataProvider(svc *Service, log *zap.Logger) *BacktestDataProvider {
	return &BacktestDataProvider{
		svc: svc,
		log: log.With(zap.String("component", "backtest_provider")),
	}
}

// GetKlinesWithIndicators 获取带指标的K线数据
func (p *BacktestDataProvider) GetKlinesWithIndicators(
	ctx context.Context,
	exchange model.Exchange,
	symbol string,
	tf model.Timeframe,
	start, end time.Time,
	indicatorNames []string,
) ([]*model.KlineWithIndicators, error) {
	// 获取K线
	klines, err := p.svc.GetKlines(ctx, exchange, symbol, tf, start, end)
	if err != nil {
		return nil, err
	}

	result := make([]*model.KlineWithIndicators, len(klines))

	// 计算指标
	for i, k := range klines {
		kwi := &model.KlineWithIndicators{
			Kline:      *k,
			Indicators: make(map[string]decimal.Decimal),
		}

		// 获取指标
		indResult := p.svc.GetIndicators(exchange, symbol, tf)
		if indResult != nil {
			for _, name := range indicatorNames {
				if val, ok := indResult.Indicators[name]; ok {
					kwi.Indicators[name] = val
				}
			}
		}

		result[i] = kwi
	}

	return result, nil
}

// ExportCSV 导出CSV格式数据
func (p *BacktestDataProvider) ExportCSV(
	ctx context.Context,
	exchange model.Exchange,
	symbol string,
	tf model.Timeframe,
	start, end time.Time,
) ([]byte, error) {
	klines, err := p.svc.GetKlines(ctx, exchange, symbol, tf, start, end)
	if err != nil {
		return nil, err
	}

	// CSV头
	csv := "timestamp,open,high,low,close,volume,quote_volume,trade_count\n"

	for _, k := range klines {
		csv += fmt.Sprintf("%s,%s,%s,%s,%s,%s,%s,%d\n",
			k.OpenTime.Format(time.RFC3339),
			k.Open.String(),
			k.High.String(),
			k.Low.String(),
			k.Close.String(),
			k.Volume.String(),
			k.QuoteVolume.String(),
			k.TradeCount,
		)
	}

	return []byte(csv), nil
}

// ExportJSON 导出JSON格式数据
func (p *BacktestDataProvider) ExportJSON(
	ctx context.Context,
	exchange model.Exchange,
	symbol string,
	tf model.Timeframe,
	start, end time.Time,
) ([]byte, error) {
	klines, err := p.svc.GetKlines(ctx, exchange, symbol, tf, start, end)
	if err != nil {
		return nil, err
	}

	return json.Marshal(klines)
}

// StreamToChannel 流式输出到channel
func (p *BacktestDataProvider) StreamToChannel(
	ctx context.Context,
	exchange model.Exchange,
	symbol string,
	tf model.Timeframe,
	start, end time.Time,
) (<-chan *model.Kline, <-chan error) {
	klineCh := make(chan *model.Kline, 100)
	errCh := make(chan error, 1)

	go func() {
		defer close(klineCh)
		defer close(errCh)

		klines, err := p.svc.GetKlines(ctx, exchange, symbol, tf, start, end)
		if err != nil {
			errCh <- err
			return
		}

		for _, k := range klines {
			select {
			case <-ctx.Done():
				return
			case klineCh <- k:
			}
		}
	}()

	return klineCh, errCh
}
