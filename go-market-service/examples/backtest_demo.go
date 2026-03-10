// 回测数据使用示例
package main

import (
	"context"
	"fmt"
	"time"

	"github.com/shopspring/decimal"

	"github.com/quant/go-market-service/internal/model"
	"github.com/quant/go-market-service/internal/service"
)

// 简单的策略示例
type SimpleStrategy struct {
	symbol    string
	position  decimal.Decimal // 持仓数量
	entryPrice decimal.Decimal // 入场价格
	
	// 策略参数
	shortPeriod int
	longPeriod  int
}

func (s *SimpleStrategy) OnData(dp *service.DataPoint) {
	if dp.Kline == nil || !dp.Kline.IsClosed {
		return
	}

	// 获取指标
	shortMA, okShort := dp.Indicators["ema_12"]
	longMA, okLong := dp.Indicators["ema_26"]
	rsi, _ := dp.Indicators["rsi"]
	
	if !okShort || !okLong {
		return
	}

	price := dp.Kline.Close

	// 金叉买入
	if shortMA.GreaterThan(longMA) && s.position.IsZero() {
		// RSI不能太高
		if rsi.LessThan(decimal.NewFromInt(70)) {
			s.position = decimal.NewFromInt(1)
			s.entryPrice = price
			fmt.Printf("[%s] 买入 %s @ %s, RSI: %s\n", 
				dp.Timestamp.Format("2006-01-02 15:04"),
				s.symbol, price.String(), rsi.String())
		}
	}

	// 死叉卖出
	if shortMA.LessThan(longMA) && s.position.GreaterThan(decimal.Zero) {
		profit := price.Sub(s.entryPrice).Div(s.entryPrice).Mul(decimal.NewFromInt(100))
		fmt.Printf("[%s] 卖出 %s @ %s, 收益: %s%%\n",
			dp.Timestamp.Format("2006-01-02 15:04"),
			s.symbol, price.String(), profit.StringFixed(2))
		
		s.position = decimal.Zero
		s.entryPrice = decimal.Zero
	}
}

func main() {
	fmt.Println("=== Go行情处理系统 - 回测示例 ===")
	
	// 这是示例代码，需要完整初始化服务才能运行
	// 以下展示如何使用DataFeed进行回测

	/*
	// 1. 初始化配置和服务
	cfg, _ := config.Load("configs/config.yaml")
	log := logger.New(cfg.Log)
	store, _ := storage.New(cfg.Storage, log)
	svc := service.New(cfg, store, log)

	// 2. 配置回测数据源
	feedCfg := &service.DataFeedConfig{
		Mode:       service.DataFeedModeBacktest,
		Exchange:   model.ExchangeBinance,
		Symbols:    []string{"BTCUSDT"},
		Timeframes: []model.Timeframe{model.Timeframe1h},
		StartTime:  time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
		EndTime:    time.Date(2024, 6, 1, 0, 0, 0, 0, time.UTC),
		Speed:      100, // 100倍速回放
		EnableIndicators: true,
		Indicators: []string{"ema_12", "ema_26", "rsi", "macd", "macd_signal"},
	}

	// 3. 创建数据源
	feed := service.NewDataFeed(feedCfg, svc, log)

	// 4. 创建策略
	strategy := &SimpleStrategy{
		symbol:      "BTCUSDT",
		shortPeriod: 12,
		longPeriod:  26,
	}

	// 5. 订阅数据
	feed.Subscribe(strategy.OnData)

	// 6. 启动回测
	ctx := context.Background()
	feed.Start(ctx)

	// 等待回测完成
	time.Sleep(time.Hour)
	*/

	fmt.Println("\n=== 使用方法 ===")
	fmt.Println("1. 确保PostgreSQL/TimescaleDB和Redis已启动")
	fmt.Println("2. 修改configs/config.yaml中的数据库配置")
	fmt.Println("3. 运行: go run cmd/server/main.go")
	fmt.Println("4. 访问: http://localhost:8080/health")
	fmt.Println("")
	fmt.Println("=== API接口 ===")
	fmt.Println("GET /api/v1/klines?exchange=binance&symbol=BTCUSDT&timeframe=1h")
	fmt.Println("GET /api/v1/indicators?exchange=binance&symbol=BTCUSDT&timeframe=1h")
	fmt.Println("GET /api/v1/ticker?exchange=binance&symbol=BTCUSDT")
	fmt.Println("WS  /ws - 实时数据推送")
}
