/*
Package exchange Binance交易所实现

本文件实现了Binance交易所的完整对接，包括：
1. WebSocket实时数据流（Tick、K线、深度、行情）
2. REST API调用（历史数据、交易对信息）
3. 自动重连机制
4. 并发安全的数据分发

Binance API文档: https://binance-docs.github.io/apidocs/

【架构设计】
BinanceExchange实现了Exchange接口，采用策略模式：
- 对外暴露统一接口
- 内部处理Binance特有的协议格式
- 通过回调函数分发数据

【并发模型】
- 使用goroutine处理WebSocket消息
- 使用sync.RWMutex保护共享状态
- 回调函数异步执行，避免阻塞数据流
*/
package exchange

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/websocket" // WebSocket库：用于实时数据连接
	"github.com/shopspring/decimal" // 高精度小数：金融计算必备
	"go.uber.org/zap" // 日志库：高性能结构化日志

	"github.com/quant/go-market-service/internal/config"
	"github.com/quant/go-market-service/internal/model"
)

/*
BinanceExchange Binance交易所实现

【字段说明】
- cfg: 交易所配置（API地址、密钥、交易对列表等）
- log: 日志器，带有exchange=binance的固定字段
- wsConn: WebSocket连接实例
- httpClient: HTTP客户端，用于REST API调用
- mu: 读写锁，保护handlers和isConnected
- isConnected: 连接状态标志
- stopCh: 停止信号通道，用于优雅关闭goroutine
- xxxHandlers: 各类数据的回调处理器映射

【为什么用map存储handler？】
支持多个订阅者同时接收同一数据，key用于区分不同订阅
*/
type BinanceExchange struct {
	cfg         config.ExchangeConfig  // 交易所配置
	log         *zap.Logger            // 日志器（已绑定exchange字段）
	wsConn      *websocket.Conn        // WebSocket连接
	httpClient  *http.Client           // HTTP客户端（REST API）
	mu          sync.RWMutex           // 读写锁（保护共享状态）
	isConnected bool                   // 是否已连接
	stopCh      chan struct{}          // 停止信号（关闭时close）

	// 数据处理器映射
	// key: symbols的组合字符串
	// value: 回调函数
	tickHandlers      map[string]TickHandler      // Tick数据处理器
	klineHandlers     map[string]KlineHandler     // K线数据处理器
	orderBookHandlers map[string]OrderBookHandler // 订单簿处理器
	tickerHandlers    map[string]TickerHandler    // 行情处理器
}

// NewBinanceExchange 创建Binance交易所实例
func NewBinanceExchange(cfg config.ExchangeConfig, log *zap.Logger) *BinanceExchange {
	return &BinanceExchange{
		cfg:               cfg,
		log:               log.With(zap.String("exchange", "binance")),
		httpClient:        &http.Client{Timeout: 30 * time.Second},
		stopCh:            make(chan struct{}),
		tickHandlers:      make(map[string]TickHandler),
		klineHandlers:     make(map[string]KlineHandler),
		orderBookHandlers: make(map[string]OrderBookHandler),
		tickerHandlers:    make(map[string]TickerHandler),
	}
}

// Name 交易所名称
func (b *BinanceExchange) Name() model.Exchange {
	return model.ExchangeBinance
}

// Connect 连接交易所
func (b *BinanceExchange) Connect(ctx context.Context) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	if b.isConnected {
		return nil
	}

	b.log.Info("正在连接Binance WebSocket...")

	// 构建订阅流列表
	streams := b.buildStreams()
	if len(streams) == 0 {
		b.log.Warn("没有订阅任何流")
		return nil
	}

	// 组合流地址
	wsURL := fmt.Sprintf("%s/stream?streams=%s", b.cfg.WSEndpoint, strings.Join(streams, "/"))
	b.log.Debug("WebSocket URL", zap.String("url", wsURL))

	// 建立WebSocket连接
	dialer := websocket.Dialer{
		HandshakeTimeout: 10 * time.Second,
	}

	conn, _, err := dialer.DialContext(ctx, wsURL, nil)
	if err != nil {
		return fmt.Errorf("连接WebSocket失败: %w", err)
	}

	b.wsConn = conn
	b.isConnected = true

	// 启动消息处理协程
	go b.handleMessages()

	b.log.Info("Binance WebSocket连接成功")
	return nil
}

// buildStreams 构建订阅流列表
func (b *BinanceExchange) buildStreams() []string {
	var streams []string

	for _, symbol := range b.cfg.Symbols {
		lowerSymbol := strings.ToLower(symbol)
		// 逐笔成交流
		streams = append(streams, fmt.Sprintf("%s@trade", lowerSymbol))
		// K线流 (1分钟)
		streams = append(streams, fmt.Sprintf("%s@kline_1m", lowerSymbol))
		// 深度流
		streams = append(streams, fmt.Sprintf("%s@depth20@100ms", lowerSymbol))
		// 24h行情
		streams = append(streams, fmt.Sprintf("%s@ticker", lowerSymbol))
	}

	return streams
}

// handleMessages 处理WebSocket消息
func (b *BinanceExchange) handleMessages() {
	for {
		select {
		case <-b.stopCh:
			return
		default:
			_, message, err := b.wsConn.ReadMessage()
			if err != nil {
				if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
					b.log.Error("WebSocket读取错误", zap.Error(err))
				}
				b.handleReconnect()
				return
			}

			b.processMessage(message)
		}
	}
}

// processMessage 处理消息
func (b *BinanceExchange) processMessage(message []byte) {
	var wrapper struct {
		Stream string          `json:"stream"`
		Data   json.RawMessage `json:"data"`
	}

	if err := json.Unmarshal(message, &wrapper); err != nil {
		b.log.Error("解析消息失败", zap.Error(err))
		return
	}

	// 根据流类型分发消息
	parts := strings.Split(wrapper.Stream, "@")
	if len(parts) < 2 {
		return
	}

	symbol := strings.ToUpper(parts[0])
	streamType := parts[1]

	switch {
	case streamType == "trade":
		b.handleTradeMessage(symbol, wrapper.Data)
	case strings.HasPrefix(streamType, "kline"):
		b.handleKlineMessage(symbol, wrapper.Data)
	case strings.HasPrefix(streamType, "depth"):
		b.handleDepthMessage(symbol, wrapper.Data)
	case streamType == "ticker":
		b.handleTickerMessage(symbol, wrapper.Data)
	}
}

// handleTradeMessage 处理成交消息
func (b *BinanceExchange) handleTradeMessage(symbol string, data json.RawMessage) {
	var trade struct {
		EventType string `json:"e"`  // 事件类型
		EventTime int64  `json:"E"`  // 事件时间
		Symbol    string `json:"s"`  // 交易对
		TradeID   int64  `json:"t"`  // 成交ID
		Price     string `json:"p"`  // 价格
		Quantity  string `json:"q"`  // 数量
		BuyerID   int64  `json:"b"`  // 买方订单ID
		SellerID  int64  `json:"a"`  // 卖方订单ID
		TradeTime int64  `json:"T"`  // 成交时间
		IsBuyer   bool   `json:"m"`  // 是否买方
	}

	if err := json.Unmarshal(data, &trade); err != nil {
		b.log.Error("解析成交数据失败", zap.Error(err))
		return
	}

	price, _ := decimal.NewFromString(trade.Price)
	qty, _ := decimal.NewFromString(trade.Quantity)

	tick := &model.Tick{
		Exchange:  model.ExchangeBinance,
		Symbol:    symbol,
		TradeID:   strconv.FormatInt(trade.TradeID, 10),
		Price:     price,
		Quantity:  qty,
		Timestamp: time.UnixMilli(trade.TradeTime),
		IsBuyer:   trade.IsBuyer,
	}

	// 调用处理器
	b.mu.RLock()
	for _, handler := range b.tickHandlers {
		go handler(tick)
	}
	b.mu.RUnlock()
}

// handleKlineMessage 处理K线消息
func (b *BinanceExchange) handleKlineMessage(symbol string, data json.RawMessage) {
	var klineMsg struct {
		EventType string `json:"e"` // 事件类型
		EventTime int64  `json:"E"` // 事件时间
		Symbol    string `json:"s"` // 交易对
		Kline     struct {
			StartTime    int64  `json:"t"` // K线开始时间
			CloseTime    int64  `json:"T"` // K线结束时间
			Symbol       string `json:"s"` // 交易对
			Interval     string `json:"i"` // 周期
			FirstTradeID int64  `json:"f"` // 第一笔成交ID
			LastTradeID  int64  `json:"L"` // 最后一笔成交ID
			Open         string `json:"o"` // 开盘价
			Close        string `json:"c"` // 收盘价
			High         string `json:"h"` // 最高价
			Low          string `json:"l"` // 最低价
			Volume       string `json:"v"` // 成交量
			TradeCount   int64  `json:"n"` // 成交笔数
			IsClosed     bool   `json:"x"` // 是否已收盘
			QuoteVolume  string `json:"q"` // 成交额
		} `json:"k"`
	}

	if err := json.Unmarshal(data, &klineMsg); err != nil {
		b.log.Error("解析K线数据失败", zap.Error(err))
		return
	}

	k := klineMsg.Kline
	open, _ := decimal.NewFromString(k.Open)
	high, _ := decimal.NewFromString(k.High)
	low, _ := decimal.NewFromString(k.Low)
	closePrice, _ := decimal.NewFromString(k.Close)
	volume, _ := decimal.NewFromString(k.Volume)
	quoteVolume, _ := decimal.NewFromString(k.QuoteVolume)

	kline := &model.Kline{
		Exchange:    model.ExchangeBinance,
		Symbol:      symbol,
		Timeframe:   model.Timeframe(k.Interval),
		OpenTime:    time.UnixMilli(k.StartTime),
		CloseTime:   time.UnixMilli(k.CloseTime),
		Open:        open,
		High:        high,
		Low:         low,
		Close:       closePrice,
		Volume:      volume,
		QuoteVolume: quoteVolume,
		TradeCount:  k.TradeCount,
		IsClosed:    k.IsClosed,
	}

	// 调用处理器
	b.mu.RLock()
	for _, handler := range b.klineHandlers {
		go handler(kline)
	}
	b.mu.RUnlock()
}

// handleDepthMessage 处理深度消息
func (b *BinanceExchange) handleDepthMessage(symbol string, data json.RawMessage) {
	var depth struct {
		LastUpdateID int64      `json:"lastUpdateId"`
		Bids         [][]string `json:"bids"`
		Asks         [][]string `json:"asks"`
	}

	if err := json.Unmarshal(data, &depth); err != nil {
		b.log.Error("解析深度数据失败", zap.Error(err))
		return
	}

	orderBook := &model.OrderBook{
		Exchange:  model.ExchangeBinance,
		Symbol:    symbol,
		Timestamp: time.Now(),
		Bids:      make([]model.PriceLevel, len(depth.Bids)),
		Asks:      make([]model.PriceLevel, len(depth.Asks)),
	}

	for i, bid := range depth.Bids {
		price, _ := decimal.NewFromString(bid[0])
		qty, _ := decimal.NewFromString(bid[1])
		orderBook.Bids[i] = model.PriceLevel{Price: price, Quantity: qty}
	}

	for i, ask := range depth.Asks {
		price, _ := decimal.NewFromString(ask[0])
		qty, _ := decimal.NewFromString(ask[1])
		orderBook.Asks[i] = model.PriceLevel{Price: price, Quantity: qty}
	}

	// 调用处理器
	b.mu.RLock()
	for _, handler := range b.orderBookHandlers {
		go handler(orderBook)
	}
	b.mu.RUnlock()
}

// handleTickerMessage 处理行情消息
func (b *BinanceExchange) handleTickerMessage(symbol string, data json.RawMessage) {
	var t struct {
		EventType      string `json:"e"`  // 事件类型
		EventTime      int64  `json:"E"`  // 事件时间
		Symbol         string `json:"s"`  // 交易对
		PriceChange    string `json:"p"`  // 价格变化
		PriceChangePct string `json:"P"`  // 价格变化百分比
		LastPrice      string `json:"c"`  // 最新价
		BidPrice       string `json:"b"`  // 最优买价
		AskPrice       string `json:"a"`  // 最优卖价
		OpenPrice      string `json:"o"`  // 开盘价
		HighPrice      string `json:"h"`  // 最高价
		LowPrice       string `json:"l"`  // 最低价
		Volume         string `json:"v"`  // 成交量
		QuoteVolume    string `json:"q"`  // 成交额
	}

	if err := json.Unmarshal(data, &t); err != nil {
		b.log.Error("解析行情数据失败", zap.Error(err))
		return
	}

	lastPrice, _ := decimal.NewFromString(t.LastPrice)
	bidPrice, _ := decimal.NewFromString(t.BidPrice)
	askPrice, _ := decimal.NewFromString(t.AskPrice)
	volume, _ := decimal.NewFromString(t.Volume)
	priceChange, _ := decimal.NewFromString(t.PriceChange)
	priceChangePct, _ := decimal.NewFromString(t.PriceChangePct)
	highPrice, _ := decimal.NewFromString(t.HighPrice)
	lowPrice, _ := decimal.NewFromString(t.LowPrice)

	ticker := &model.Ticker{
		Exchange:       model.ExchangeBinance,
		Symbol:         symbol,
		LastPrice:      lastPrice,
		BidPrice:       bidPrice,
		AskPrice:       askPrice,
		Volume24h:      volume,
		PriceChange:    priceChange,
		PriceChangePct: priceChangePct,
		High24h:        highPrice,
		Low24h:         lowPrice,
		Timestamp:      time.UnixMilli(t.EventTime),
	}

	// 调用处理器
	b.mu.RLock()
	for _, handler := range b.tickerHandlers {
		go handler(ticker)
	}
	b.mu.RUnlock()
}

// handleReconnect 处理重连
func (b *BinanceExchange) handleReconnect() {
	b.mu.Lock()
	b.isConnected = false
	b.mu.Unlock()

	b.log.Info("尝试重新连接...")

	// 指数退避重连
	backoff := time.Second
	maxBackoff := time.Minute

	for {
		select {
		case <-b.stopCh:
			return
		case <-time.After(backoff):
			if err := b.Connect(context.Background()); err != nil {
				b.log.Error("重连失败", zap.Error(err), zap.Duration("next_retry", backoff))
				backoff *= 2
				if backoff > maxBackoff {
					backoff = maxBackoff
				}
				continue
			}
			b.log.Info("重连成功")
			return
		}
	}
}

// Disconnect 断开连接
func (b *BinanceExchange) Disconnect() error {
	b.mu.Lock()
	defer b.mu.Unlock()

	close(b.stopCh)

	if b.wsConn != nil {
		if err := b.wsConn.Close(); err != nil {
			return fmt.Errorf("关闭WebSocket失败: %w", err)
		}
	}

	b.isConnected = false
	b.log.Info("已断开连接")
	return nil
}

// SubscribeTick 订阅逐笔成交
func (b *BinanceExchange) SubscribeTick(ctx context.Context, symbols []string, handler TickHandler) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	key := strings.Join(symbols, ",")
	b.tickHandlers[key] = handler
	return nil
}

// SubscribeKline 订阅K线
func (b *BinanceExchange) SubscribeKline(ctx context.Context, symbols []string, timeframe model.Timeframe, handler KlineHandler) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	key := fmt.Sprintf("%s_%s", strings.Join(symbols, ","), timeframe)
	b.klineHandlers[key] = handler
	return nil
}

// SubscribeOrderBook 订阅订单簿
func (b *BinanceExchange) SubscribeOrderBook(ctx context.Context, symbols []string, handler OrderBookHandler) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	key := strings.Join(symbols, ",")
	b.orderBookHandlers[key] = handler
	return nil
}

// SubscribeTicker 订阅行情快照
func (b *BinanceExchange) SubscribeTicker(ctx context.Context, symbols []string, handler TickerHandler) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	key := strings.Join(symbols, ",")
	b.tickerHandlers[key] = handler
	return nil
}

// GetHistoricalKlines 获取历史K线
func (b *BinanceExchange) GetHistoricalKlines(ctx context.Context, symbol string, timeframe model.Timeframe, start, end time.Time, limit int) ([]model.Kline, error) {
	url := fmt.Sprintf("%s/api/v3/klines?symbol=%s&interval=%s&startTime=%d&endTime=%d&limit=%d",
		b.cfg.RESTEndpoint, symbol, timeframe, start.UnixMilli(), end.UnixMilli(), limit)

	resp, err := b.doRequest(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var rawKlines [][]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&rawKlines); err != nil {
		return nil, fmt.Errorf("解析K线数据失败: %w", err)
	}

	klines := make([]model.Kline, len(rawKlines))
	for i, raw := range rawKlines {
		openTime := int64(raw[0].(float64))
		closeTime := int64(raw[6].(float64))

		open, _ := decimal.NewFromString(raw[1].(string))
		high, _ := decimal.NewFromString(raw[2].(string))
		low, _ := decimal.NewFromString(raw[3].(string))
		closePrice, _ := decimal.NewFromString(raw[4].(string))
		volume, _ := decimal.NewFromString(raw[5].(string))
		quoteVolume, _ := decimal.NewFromString(raw[7].(string))
		tradeCount := int64(raw[8].(float64))

		klines[i] = model.Kline{
			Exchange:    model.ExchangeBinance,
			Symbol:      symbol,
			Timeframe:   timeframe,
			OpenTime:    time.UnixMilli(openTime),
			CloseTime:   time.UnixMilli(closeTime),
			Open:        open,
			High:        high,
			Low:         low,
			Close:       closePrice,
			Volume:      volume,
			QuoteVolume: quoteVolume,
			TradeCount:  tradeCount,
			IsClosed:    true,
		}
	}

	return klines, nil
}

// GetTicker 获取当前行情
func (b *BinanceExchange) GetTicker(ctx context.Context, symbol string) (*model.Ticker, error) {
	url := fmt.Sprintf("%s/api/v3/ticker/24hr?symbol=%s", b.cfg.RESTEndpoint, symbol)

	resp, err := b.doRequest(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var t struct {
		Symbol         string `json:"symbol"`
		PriceChange    string `json:"priceChange"`
		PriceChangePct string `json:"priceChangePercent"`
		LastPrice      string `json:"lastPrice"`
		BidPrice       string `json:"bidPrice"`
		AskPrice       string `json:"askPrice"`
		HighPrice      string `json:"highPrice"`
		LowPrice       string `json:"lowPrice"`
		Volume         string `json:"volume"`
		QuoteVolume    string `json:"quoteVolume"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&t); err != nil {
		return nil, fmt.Errorf("解析行情数据失败: %w", err)
	}

	lastPrice, _ := decimal.NewFromString(t.LastPrice)
	bidPrice, _ := decimal.NewFromString(t.BidPrice)
	askPrice, _ := decimal.NewFromString(t.AskPrice)
	volume, _ := decimal.NewFromString(t.Volume)
	priceChange, _ := decimal.NewFromString(t.PriceChange)
	priceChangePct, _ := decimal.NewFromString(t.PriceChangePct)
	highPrice, _ := decimal.NewFromString(t.HighPrice)
	lowPrice, _ := decimal.NewFromString(t.LowPrice)

	return &model.Ticker{
		Exchange:       model.ExchangeBinance,
		Symbol:         symbol,
		LastPrice:      lastPrice,
		BidPrice:       bidPrice,
		AskPrice:       askPrice,
		Volume24h:      volume,
		PriceChange:    priceChange,
		PriceChangePct: priceChangePct,
		High24h:        highPrice,
		Low24h:         lowPrice,
		Timestamp:      time.Now(),
	}, nil
}

// GetOrderBook 获取订单簿
func (b *BinanceExchange) GetOrderBook(ctx context.Context, symbol string, limit int) (*model.OrderBook, error) {
	url := fmt.Sprintf("%s/api/v3/depth?symbol=%s&limit=%d", b.cfg.RESTEndpoint, symbol, limit)

	resp, err := b.doRequest(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var depth struct {
		LastUpdateID int64      `json:"lastUpdateId"`
		Bids         [][]string `json:"bids"`
		Asks         [][]string `json:"asks"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&depth); err != nil {
		return nil, fmt.Errorf("解析订单簿数据失败: %w", err)
	}

	orderBook := &model.OrderBook{
		Exchange:  model.ExchangeBinance,
		Symbol:    symbol,
		Timestamp: time.Now(),
		Bids:      make([]model.PriceLevel, len(depth.Bids)),
		Asks:      make([]model.PriceLevel, len(depth.Asks)),
	}

	for i, bid := range depth.Bids {
		price, _ := decimal.NewFromString(bid[0])
		qty, _ := decimal.NewFromString(bid[1])
		orderBook.Bids[i] = model.PriceLevel{Price: price, Quantity: qty}
	}

	for i, ask := range depth.Asks {
		price, _ := decimal.NewFromString(ask[0])
		qty, _ := decimal.NewFromString(ask[1])
		orderBook.Asks[i] = model.PriceLevel{Price: price, Quantity: qty}
	}

	return orderBook, nil
}

// GetSymbols 获取交易对列表
func (b *BinanceExchange) GetSymbols(ctx context.Context) ([]model.SymbolInfo, error) {
	url := fmt.Sprintf("%s/api/v3/exchangeInfo", b.cfg.RESTEndpoint)

	resp, err := b.doRequest(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var exchangeInfo struct {
		Symbols []struct {
			Symbol             string `json:"symbol"`
			Status             string `json:"status"`
			BaseAsset          string `json:"baseAsset"`
			QuoteAsset         string `json:"quoteAsset"`
			BaseAssetPrecision int    `json:"baseAssetPrecision"`
			QuotePrecision     int    `json:"quotePrecision"`
			Filters            []struct {
				FilterType string `json:"filterType"`
				MinQty     string `json:"minQty,omitempty"`
				MinNotional string `json:"minNotional,omitempty"`
			} `json:"filters"`
		} `json:"symbols"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&exchangeInfo); err != nil {
		return nil, fmt.Errorf("解析交易所信息失败: %w", err)
	}

	symbols := make([]model.SymbolInfo, len(exchangeInfo.Symbols))
	for i, s := range exchangeInfo.Symbols {
		var minQty, minNotional float64
		for _, f := range s.Filters {
			switch f.FilterType {
			case "LOT_SIZE":
				minQty, _ = strconv.ParseFloat(f.MinQty, 64)
			case "MIN_NOTIONAL":
				minNotional, _ = strconv.ParseFloat(f.MinNotional, 64)
			}
		}

		symbols[i] = model.SymbolInfo{
			Exchange:       string(model.ExchangeBinance),
			Symbol:         s.Symbol,
			BaseCurrency:   s.BaseAsset,
			QuoteCurrency:  s.QuoteAsset,
			PricePrecision: s.QuotePrecision,
			QtyPrecision:   s.BaseAssetPrecision,
			MinQty:         minQty,
			MinNotional:    minNotional,
			Status:         s.Status,
		}
	}

	return symbols, nil
}

// Ping 检查连接
func (b *BinanceExchange) Ping(ctx context.Context) error {
	url := fmt.Sprintf("%s/api/v3/ping", b.cfg.RESTEndpoint)
	resp, err := b.doRequest(ctx, "GET", url, nil)
	if err != nil {
		return err
	}
	resp.Body.Close()
	return nil
}

// doRequest 执行HTTP请求
func (b *BinanceExchange) doRequest(ctx context.Context, method, url string, body io.Reader) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, method, url, body)
	if err != nil {
		return nil, fmt.Errorf("创建请求失败: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := b.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("请求失败: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		return nil, fmt.Errorf("API返回错误: status=%d, body=%s", resp.StatusCode, string(body))
	}

	return resp, nil
}
