// 实盘交易数据订阅示例
package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/shopspring/decimal"

	"github.com/quant/go-market-service/internal/model"
	"github.com/quant/go-market-service/internal/service"
)

// LiveTradingStrategy 实盘交易策略
type LiveTradingStrategy struct {
	symbol string
	
	// 状态
	position  decimal.Decimal
	lastPrice decimal.Decimal
	
	// 统计
	tickCount  int64
	klineCount int64
}

// OnTick 处理Tick数据
func (s *LiveTradingStrategy) OnTick(tick *model.Tick) {
	s.tickCount++
	s.lastPrice = tick.Price
	
	// 每1000个Tick打印一次
	if s.tickCount%1000 == 0 {
		fmt.Printf("[Tick] %s: Price=%s, Qty=%s, IsBuyer=%v\n",
			tick.Symbol, tick.Price.String(), tick.Quantity.String(), tick.IsBuyer)
	}
}

// OnKline 处理K线数据
func (s *LiveTradingStrategy) OnKline(k *model.Kline) {
	s.klineCount++
	
	// K线完成时打印
	if k.IsClosed {
		fmt.Printf("[Kline] %s %s: O=%s H=%s L=%s C=%s V=%s\n",
			k.Symbol, k.Timeframe,
			k.Open.String(), k.High.String(), k.Low.String(), k.Close.String(),
			k.Volume.String())
	}
}

// OnTicker 处理行情快照
func (s *LiveTradingStrategy) OnTicker(ticker *model.Ticker) {
	fmt.Printf("[Ticker] %s: Last=%s, Bid=%s, Ask=%s, Change=%s%%\n",
		ticker.Symbol,
		ticker.LastPrice.String(),
		ticker.BidPrice.String(),
		ticker.AskPrice.String(),
		ticker.PriceChangePct.String())
}

// OnDataPoint 处理DataFeed数据点
func (s *LiveTradingStrategy) OnDataPoint(dp *service.DataPoint) {
	if dp.Kline != nil && dp.Kline.IsClosed {
		// 检查指标
		if rsi, ok := dp.Indicators["rsi"]; ok {
			fmt.Printf("[Signal] %s RSI: %s", dp.Symbol, rsi.StringFixed(2))
			
			if rsi.LessThan(decimal.NewFromInt(30)) {
				fmt.Println(" - 超卖，考虑买入")
			} else if rsi.GreaterThan(decimal.NewFromInt(70)) {
				fmt.Println(" - 超买，考虑卖出")
			} else {
				fmt.Println()
			}
		}
	}
}

func main() {
	fmt.Println("=== Go行情处理系统 - 实盘数据订阅示例 ===")
	
	/*
	// 完整初始化代码
	cfg, _ := config.Load("configs/config.yaml")
	log := logger.New(cfg.Log)
	store, _ := storage.New(cfg.Storage, log)
	svc := service.New(cfg, store, log)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// 启动服务
	svc.Start(ctx)

	// 创建策略
	strategy := &LiveTradingStrategy{
		symbol: "BTCUSDT",
	}

	// 方式1: 直接订阅原始数据
	svc.SubscribeTick(strategy.OnTick)
	svc.SubscribeKline(strategy.OnKline)
	svc.SubscribeTicker(strategy.OnTicker)

	// 方式2: 使用DataFeed (带指标计算)
	feedCfg := &service.DataFeedConfig{
		Mode:       service.DataFeedModeLive,
		Exchange:   model.ExchangeBinance,
		Symbols:    []string{"BTCUSDT", "ETHUSDT"},
		Timeframes: []model.Timeframe{model.Timeframe1m, model.Timeframe5m},
		EnableIndicators: true,
		Indicators: []string{"rsi", "macd", "ema_12", "ema_26"},
	}

	feed := service.NewDataFeed(feedCfg, svc, log)
	feed.Subscribe(strategy.OnDataPoint)
	feed.Start(ctx)
	*/

	fmt.Println("\n=== 实盘数据订阅方式 ===")
	fmt.Println("")
	fmt.Println("方式1: 直接订阅原始数据")
	fmt.Println("  svc.SubscribeTick(handler)   // 订阅逐笔成交")
	fmt.Println("  svc.SubscribeKline(handler)  // 订阅K线")
	fmt.Println("  svc.SubscribeTicker(handler) // 订阅行情快照")
	fmt.Println("")
	fmt.Println("方式2: 使用DataFeed (带指标计算)")
	fmt.Println("  feed := service.NewDataFeed(cfg, svc, log)")
	fmt.Println("  feed.Subscribe(handler)")
	fmt.Println("  feed.Start(ctx)")
	fmt.Println("")
	fmt.Println("方式3: WebSocket实时推送")
	fmt.Println("  连接 ws://localhost:8080/ws")
	fmt.Println("  接收 {\"type\":\"kline\",\"data\":{...}}")
	fmt.Println("")
	
	// 模拟等待退出信号
	fmt.Println("按 Ctrl+C 退出...")
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	
	fmt.Println("程序已退出")
}
