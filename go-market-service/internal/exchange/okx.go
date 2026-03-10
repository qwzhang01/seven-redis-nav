/*
Package exchange OKX交易所实现

本文件实现了OKX交易所的完整对接，包括：
1. WebSocket实时数据流（成交、K线、深度、行情）
2. REST API调用（历史数据、交易对信息）
3. 自动重连机制
4. 并发安全的数据分发

========== OKX交易所API特点 ==========

与Binance不同，OKX的API有以下特点：

1. WebSocket订阅格式：
   - 使用统一的订阅消息格式：{"op": "subscribe", "args": [...]}
   - 每个订阅参数包含 channel 和 instId（交易对）

2. 心跳机制：
   - 发送 "ping"，接收 "pong"
   - 默认25秒间隔

3. 数据格式：
   - K线数据返回数组格式：[时间戳, 开, 高, 低, 收, 成交量, ...]
   - 确认字段用于标识K线是否已完成

4. 交易对命名：
   - 使用 "BTC-USDT" 格式（连字符分隔）

========== 设计模式 ==========

1. 观察者模式：通过 Handler Map 实现数据分发
2. 并发安全：使用 sync.RWMutex 保护共享状态
3. 自动重连：指数退避策略，最大60秒

========== 使用示例 ==========

	cfg := config.ExchangeConfig{
	    Name:         "okx",
	    Enabled:      true,
	    WSEndpoint:   "wss://ws.okx.com:8443/ws/v5/public",
	    RESTEndpoint: "https://www.okx.com",
	    Symbols:      []string{"BTC-USDT", "ETH-USDT"},
	}

	ex := NewOKXExchange(cfg, logger)
	err := ex.Connect(ctx)

========== 参考资料 ==========

- OKX API文档：https://www.okx.com/docs-v5/
- WebSocket Public Channels: https://www.okx.com/docs-v5/en/#websocket-api-public-channel
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

	"github.com/gorilla/websocket"
	"github.com/shopspring/decimal"
	"go.uber.org/zap"

	"github.com/quant/go-market-service/internal/config"
	"github.com/quant/go-market-service/internal/model"
)

/*
OKXExchange OKX交易所实现

实现了 Exchange 接口，提供OKX交易所的完整功能：
- WebSocket实时数据订阅
- REST API调用
- 多种数据类型支持（Tick、K线、深度、行情）

字段说明：
- cfg: 交易所配置（API端点、交易对列表等）
- log: 日志记录器，带有 exchange=okx 标签
- wsConn: WebSocket连接实例
- httpClient: HTTP客户端，用于REST API调用
- mu: 读写锁，保护并发访问
- isConnected: 连接状态标志
- stopCh: 停止信号通道，用于优雅关闭
- xxxHandlers: 各类型数据的回调处理器映射

线程安全：
所有公开方法都是线程安全的，内部使用 sync.RWMutex 保护共享状态
*/
type OKXExchange struct {
	// ========== 基础配置 ==========

	// cfg 交易所配置
	// 包含WebSocket端点、REST端点、交易对列表等
	cfg config.ExchangeConfig

	// log 日志记录器
	// 已注入 exchange=okx 标签，便于日志过滤
	log *zap.Logger

	// ========== 网络连接 ==========

	// wsConn WebSocket连接
	// 用于接收实时市场数据流
	wsConn *websocket.Conn

	// httpClient HTTP客户端
	// 用于REST API调用，超时设置30秒
	httpClient *http.Client

	// ========== 并发控制 ==========

	// mu 读写锁
	// 保护 wsConn、isConnected 和各 handlers 的并发访问
	mu sync.RWMutex

	// isConnected 连接状态
	// true表示WebSocket已连接且正常工作
	isConnected bool

	// stopCh 停止信号通道
	// 用于通知goroutine退出（心跳、消息处理）
	stopCh chan struct{}

	// ========== 数据处理器 ==========
	// 使用 map 存储处理器，key为订阅标识
	// 支持多个处理器同时订阅同一数据流

	// tickHandlers 逐笔成交处理器
	// key: 以逗号分隔的交易对列表
	tickHandlers map[string]TickHandler

	// klineHandlers K线处理器
	// key: "交易对列表_周期"
	klineHandlers map[string]KlineHandler

	// orderBookHandlers 订单簿处理器
	// key: 以逗号分隔的交易对列表
	orderBookHandlers map[string]OrderBookHandler

	// tickerHandlers 行情快照处理器
	// key: 以逗号分隔的交易对列表
	tickerHandlers map[string]TickerHandler
}

/*
NewOKXExchange 创建OKX交易所实例

工厂函数，创建并初始化 OKXExchange 实例。

参数：
  - cfg: 交易所配置，包含API端点和交易对列表
  - log: zap日志记录器

返回：
  - 初始化完成的 OKXExchange 指针

初始化内容：
  - 配置日志标签 (exchange=okx)
  - 创建HTTP客户端（30秒超时）
  - 初始化停止信号通道
  - 初始化各类数据处理器映射

注意：
  - 返回后需要调用 Connect() 建立WebSocket连接
  - stopCh 为无缓冲通道，close(stopCh) 会通知所有等待的goroutine
*/
func NewOKXExchange(cfg config.ExchangeConfig, log *zap.Logger) *OKXExchange {
	return &OKXExchange{
		cfg:               cfg,
		log:               log.With(zap.String("exchange", "okx")), // 添加标签便于日志过滤
		httpClient:        &http.Client{Timeout: 30 * time.Second}, // 设置REST API超时
		stopCh:            make(chan struct{}),                     // 无缓冲通道用于停止信号
		tickHandlers:      make(map[string]TickHandler),            // 初始化处理器映射
		klineHandlers:     make(map[string]KlineHandler),
		orderBookHandlers: make(map[string]OrderBookHandler),
		tickerHandlers:    make(map[string]TickerHandler),
	}
}

/*
Name 返回交易所名称

实现 Exchange 接口的 Name() 方法。

返回：
  - model.ExchangeOKX 常量

用途：
  - 区分不同交易所的数据
  - 日志记录和错误追踪
  - 路由和分发数据
*/
func (o *OKXExchange) Name() model.Exchange {
	return model.ExchangeOKX
}

/*
Connect 连接交易所WebSocket

实现 Exchange 接口的 Connect() 方法。
建立与OKX的WebSocket连接，并开始接收实时数据。

参数：
  - ctx: 上下文，用于控制连接超时和取消

返回：
  - 成功返回 nil，失败返回具体错误

执行流程：
 1. 检查是否已连接（幂等性）
 2. 建立WebSocket连接（握手超时10秒）
 3. 订阅配置的频道（成交、K线、深度、行情）
 4. 启动消息处理协程
 5. 启动心跳协程

错误处理：
  - 连接失败时返回错误，不启动协程
  - 订阅失败时关闭连接并返回错误

线程安全：
  - 使用互斥锁保护连接状态
  - 支持并发调用，只会建立一次连接
*/
func (o *OKXExchange) Connect(ctx context.Context) error {
	o.mu.Lock()
	defer o.mu.Unlock()

	// 幂等性检查：如果已连接则直接返回
	if o.isConnected {
		return nil
	}

	o.log.Info("正在连接OKX WebSocket...")

	// 创建WebSocket拨号器，设置握手超时
	dialer := websocket.Dialer{
		HandshakeTimeout: 10 * time.Second,
	}

	// 建立WebSocket连接
	conn, _, err := dialer.DialContext(ctx, o.cfg.WSEndpoint, nil)
	if err != nil {
		return fmt.Errorf("连接WebSocket失败: %w", err)
	}

	o.wsConn = conn
	o.isConnected = true

	// 订阅所有配置的频道
	if err := o.subscribeChannels(); err != nil {
		o.wsConn.Close() // 订阅失败需要关闭连接
		return fmt.Errorf("订阅频道失败: %w", err)
	}

	// 启动消息处理协程（后台运行）
	go o.handleMessages()

	// 启动心跳协程（保持连接活跃）
	go o.heartbeat()

	o.log.Info("OKX WebSocket连接成功")
	return nil
}

/*
subscribeChannels 订阅所有配置的频道

向OKX服务器发送订阅请求，订阅以下频道：
- trades: 逐笔成交数据
- candle1m: 1分钟K线数据
- books5: 5档深度数据
- tickers: 行情快照数据

OKX订阅消息格式：
	{
	    "op": "subscribe",
	    "args": [
	        {"channel": "trades", "instId": "BTC-USDT"},
	        {"channel": "candle1m", "instId": "BTC-USDT"},
	        ...
	    ]
	}

返回：
  - 订阅成功返回 nil
  - WebSocket写入失败返回错误

注意：
  - 一次性订阅所有交易对的所有频道
  - 减少订阅请求次数，提高效率
*/
func (o *OKXExchange) subscribeChannels() error {
	var args []map[string]string

	// 为每个交易对添加四种频道的订阅
	for _, symbol := range o.cfg.Symbols {
		// 成交频道 - 实时逐笔成交
		args = append(args, map[string]string{
			"channel": "trades",
			"instId":  symbol,
		})
		// K线频道 - 1分钟K线
		args = append(args, map[string]string{
			"channel": "candle1m",
			"instId":  symbol,
		})
		// 深度频道 - 5档买卖盘
		args = append(args, map[string]string{
			"channel": "books5",
			"instId":  symbol,
		})
		// 行情频道 - 24小时行情快照
		args = append(args, map[string]string{
			"channel": "tickers",
			"instId":  symbol,
		})
	}

	// 构建订阅消息
	subscribeMsg := map[string]interface{}{
		"op":   "subscribe",
		"args": args,
	}

	// 发送订阅请求（WriteJSON自动序列化为JSON）
	return o.wsConn.WriteJSON(subscribeMsg)
}

/*
heartbeat 心跳保活协程

定时发送心跳消息，保持WebSocket连接活跃。

OKX心跳机制：
- 发送: "ping" (纯文本)
- 接收: "pong" (纯文本)
- 间隔: 25秒（OKX建议30秒内发送）

工作流程：
 1. 创建25秒定时器
 2. 定时发送 "ping"
 3. 收到停止信号时退出

注意：
  - 使用读锁访问 wsConn，允许与消息处理并发
  - ticker.Stop() 在 defer 中调用，确保资源释放
*/
func (o *OKXExchange) heartbeat() {
	ticker := time.NewTicker(25 * time.Second)
	defer ticker.Stop() // 确保定时器资源释放

	for {
		select {
		case <-o.stopCh:
			// 收到停止信号，退出协程
			return
		case <-ticker.C:
			// 发送心跳（使用读锁，允许并发读取）
			o.mu.RLock()
			if o.wsConn != nil {
				o.wsConn.WriteMessage(websocket.TextMessage, []byte("ping"))
			}
			o.mu.RUnlock()
		}
	}
}

/*
handleMessages WebSocket消息处理主循环

持续读取并处理WebSocket消息。这是数据接收的核心逻辑。

工作流程：
 1. 循环读取WebSocket消息
 2. 过滤心跳响应（"pong"）
 3. 分发业务消息给 processMessage

错误处理：
  - 正常关闭（CloseGoingAway）不记录错误
  - 异常关闭触发重连机制

退出条件：
  - 收到 stopCh 信号
  - WebSocket读取错误
*/
func (o *OKXExchange) handleMessages() {
	for {
		select {
		case <-o.stopCh:
			// 收到停止信号，正常退出
			return
		default:
			// 阻塞读取WebSocket消息
			_, message, err := o.wsConn.ReadMessage()
			if err != nil {
				// 检查是否为异常关闭
				if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
					o.log.Error("WebSocket读取错误", zap.Error(err))
				}
				// 触发重连
				o.handleReconnect()
				return
			}

			// 过滤心跳响应
			if string(message) == "pong" {
				continue
			}

			// 处理业务消息
			o.processMessage(message)
		}
	}
}

/*
processMessage 解析并路由WebSocket消息

根据消息中的 channel 字段，将数据分发给对应的处理函数。

OKX推送消息格式：
	{
	    "arg": {"channel": "trades", "instId": "BTC-USDT"},
	    "data": [...]
	}

路由规则：
  - channel == "trades" -> handleTradeMessage
  - channel 以 "candle" 开头 -> handleKlineMessage
  - channel 以 "books" 开头 -> handleDepthMessage
  - channel == "tickers" -> handleTickerMessage

参数：
  - message: 原始JSON字节数组
*/
func (o *OKXExchange) processMessage(message []byte) {
	// 定义消息结构体，用于解析通用格式
	var msg struct {
		Arg struct {
			Channel string `json:"channel"` // 频道名称
			InstID  string `json:"instId"`  // 交易对（OKX称为 instrument ID）
		} `json:"arg"`
		Data json.RawMessage `json:"data"` // 延迟解析，由具体handler处理
	}

	// 解析消息
	if err := json.Unmarshal(message, &msg); err != nil {
		// 可能是事件消息（订阅确认等），忽略
		return
	}

	// 检查数据是否为空
	if len(msg.Data) == 0 {
		return
	}

	channel := msg.Arg.Channel
	symbol := msg.Arg.InstID

	// 根据频道类型分发到对应处理函数
	switch {
	case channel == "trades":
		o.handleTradeMessage(symbol, msg.Data)
	case strings.HasPrefix(channel, "candle"):
		o.handleKlineMessage(symbol, channel, msg.Data)
	case strings.HasPrefix(channel, "books"):
		o.handleDepthMessage(symbol, msg.Data)
	case channel == "tickers":
		o.handleTickerMessage(symbol, msg.Data)
	}
}

/*
handleTradeMessage 处理成交消息

解析OKX的逐笔成交数据，转换为内部 Tick 模型，并分发给订阅者。

OKX成交数据格式：
	[{
	    "instId": "BTC-USDT",
	    "tradeId": "123456",
	    "px": "50000.5",
	    "sz": "0.1",
	    "side": "buy",
	    "ts": "1609459200000"
	}]

参数：
  - symbol: 交易对，如 "BTC-USDT"
  - data: 原始JSON数据

数据转换：
  - px (price) -> Price
  - sz (size) -> Quantity
  - side == "buy" -> IsBuyer = true
  - ts -> 毫秒时间戳转 time.Time

并发处理：
  - 使用 go handler(tick) 异步调用，避免阻塞消息处理主循环
  - 遍历前获取读锁，遍历时不修改 handlers
*/
func (o *OKXExchange) handleTradeMessage(symbol string, data json.RawMessage) {
	// 定义OKX成交数据结构
	var trades []struct {
		InstID  string `json:"instId"`  // 交易对
		TradeID string `json:"tradeId"` // 成交ID
		Price   string `json:"px"`      // 价格 (price)
		Size    string `json:"sz"`      // 数量 (size)
		Side    string `json:"side"`    // 方向：buy/sell
		Ts      string `json:"ts"`      // 时间戳（毫秒）
	}

	// 解析JSON
	if err := json.Unmarshal(data, &trades); err != nil {
		o.log.Error("解析成交数据失败", zap.Error(err))
		return
	}

	// 处理每笔成交
	for _, trade := range trades {
		// 使用 decimal 库解析价格和数量，保证精度
		price, _ := decimal.NewFromString(trade.Price)
		qty, _ := decimal.NewFromString(trade.Size)
		ts, _ := strconv.ParseInt(trade.Ts, 10, 64)

		// 构造内部 Tick 模型
		tick := &model.Tick{
			Exchange:  model.ExchangeOKX,
			Symbol:    symbol,
			TradeID:   trade.TradeID,
			Price:     price,
			Quantity:  qty,
			Timestamp: time.UnixMilli(ts),        // 毫秒转 time.Time
			IsBuyer:   trade.Side == "buy",       // 判断是否为买方主动成交
		}

		// 分发给所有订阅者（使用读锁保护）
		o.mu.RLock()
		for _, handler := range o.tickHandlers {
			go handler(tick) // 异步调用，避免阻塞
		}
		o.mu.RUnlock()
	}
}

/*
handleKlineMessage 处理K线消息

解析OKX的K线数据，转换为内部 Kline 模型，并分发给订阅者。

OKX K线数据格式：
	[[时间戳, 开, 高, 低, 收, 成交量, 计价货币成交量, ..., 确认标志]]
	  索引:   0    1  2  3  4    5         6                  8

参数：
  - symbol: 交易对
  - channel: 频道名称，如 "candle1m"，用于提取周期
  - data: 原始JSON数据

确认标志说明：
  - k[8] == "1": K线已完成（已收盘）
  - k[8] == "0": K线仍在形成中（未收盘）

注意：
  - K线数据是二维数组格式
  - 需要至少9个元素才是完整数据
*/
func (o *OKXExchange) handleKlineMessage(symbol, channel string, data json.RawMessage) {
	// K线数据为二维字符串数组
	var klines [][]string
	if err := json.Unmarshal(data, &klines); err != nil {
		o.log.Error("解析K线数据失败", zap.Error(err))
		return
	}

	// 从channel名称提取时间周期
	// 例如：candle1m -> 1m, candle1H -> 1H
	tf := strings.TrimPrefix(channel, "candle")
	timeframe := o.convertTimeframe(tf)

	// 处理每根K线
	for _, k := range klines {
		// 验证数据完整性
		if len(k) < 9 {
			continue
		}

		// 解析K线数据（使用 decimal 保证精度）
		ts, _ := strconv.ParseInt(k[0], 10, 64)       // 开盘时间戳
		open, _ := decimal.NewFromString(k[1])        // 开盘价
		high, _ := decimal.NewFromString(k[2])        // 最高价
		low, _ := decimal.NewFromString(k[3])         // 最低价
		closePrice, _ := decimal.NewFromString(k[4])  // 收盘价
		volume, _ := decimal.NewFromString(k[5])      // 成交量（基础货币）
		quoteVolume, _ := decimal.NewFromString(k[6]) // 成交额（计价货币）
		confirm := k[8] == "1"                        // 是否已完成

		// 构造内部 Kline 模型
		kline := &model.Kline{
			Exchange:    model.ExchangeOKX,
			Symbol:      symbol,
			Timeframe:   timeframe,
			OpenTime:    time.UnixMilli(ts),
			Open:        open,
			High:        high,
			Low:         low,
			Close:       closePrice,
			Volume:      volume,
			QuoteVolume: quoteVolume,
			IsClosed:    confirm,
		}

		// 分发给所有订阅者
		o.mu.RLock()
		for _, handler := range o.klineHandlers {
			go handler(kline)
		}
		o.mu.RUnlock()
	}
}

/*
convertTimeframe 转换OKX时间周期格式

将OKX的周期字符串转换为内部 Timeframe 类型。

OKX周期格式：
  - 分钟: 1m, 5m, 15m, 30m（小写）
  - 小时: 1H, 4H（大写）
  - 日/周: 1D, 1W（大写）

参数：
  - tf: OKX格式的周期字符串

返回：
  - 对应的 model.Timeframe 常量
  - 未识别的返回默认值 Timeframe1m
*/
func (o *OKXExchange) convertTimeframe(tf string) model.Timeframe {
	switch tf {
	case "1m":
		return model.Timeframe1m
	case "5m":
		return model.Timeframe5m
	case "15m":
		return model.Timeframe15m
	case "30m":
		return model.Timeframe30m
	case "1H":
		return model.Timeframe1h
	case "4H":
		return model.Timeframe4h
	case "1D":
		return model.Timeframe1d
	case "1W":
		return model.Timeframe1w
	default:
		return model.Timeframe1m // 默认返回1分钟
	}
}

/*
handleDepthMessage 处理深度（订单簿）消息

解析OKX的深度数据，转换为内部 OrderBook 模型，并分发给订阅者。

OKX深度数据格式：
	[{
	    "bids": [["50000", "1.5", "0", "2"], ...],  // [价格, 数量, 弃用, 订单数]
	    "asks": [["50001", "0.8", "0", "1"], ...],
	    "ts": "1609459200000"
	}]

参数：
  - symbol: 交易对
  - data: 原始JSON数据

数据特点：
  - bids: 买盘，价格从高到低排序
  - asks: 卖盘，价格从低到高排序
  - 只使用前两个字段（价格和数量）

深度档位：
  - books5: 5档深度
  - books: 完整深度（增量推送）
*/
func (o *OKXExchange) handleDepthMessage(symbol string, data json.RawMessage) {
	// 定义深度数据结构
	var depths []struct {
		Bids [][]string `json:"bids"` // 买盘
		Asks [][]string `json:"asks"` // 卖盘
		Ts   string     `json:"ts"`   // 时间戳
	}

	if err := json.Unmarshal(data, &depths); err != nil {
		o.log.Error("解析深度数据失败", zap.Error(err))
		return
	}

	// 处理每个深度快照
	for _, depth := range depths {
		ts, _ := strconv.ParseInt(depth.Ts, 10, 64)

		// 构造内部 OrderBook 模型
		orderBook := &model.OrderBook{
			Exchange:  model.ExchangeOKX,
			Symbol:    symbol,
			Timestamp: time.UnixMilli(ts),
			Bids:      make([]model.PriceLevel, len(depth.Bids)), // 预分配切片
			Asks:      make([]model.PriceLevel, len(depth.Asks)),
		}

		// 转换买盘数据
		for i, bid := range depth.Bids {
			price, _ := decimal.NewFromString(bid[0]) // 价格
			qty, _ := decimal.NewFromString(bid[1])   // 数量
			orderBook.Bids[i] = model.PriceLevel{Price: price, Quantity: qty}
		}

		// 转换卖盘数据
		for i, ask := range depth.Asks {
			price, _ := decimal.NewFromString(ask[0])
			qty, _ := decimal.NewFromString(ask[1])
			orderBook.Asks[i] = model.PriceLevel{Price: price, Quantity: qty}
		}

		// 分发给所有订阅者
		o.mu.RLock()
		for _, handler := range o.orderBookHandlers {
			go handler(orderBook)
		}
		o.mu.RUnlock()
	}
}

/*
handleTickerMessage 处理行情快照消息

解析OKX的24小时行情数据，转换为内部 Ticker 模型。

OKX行情数据格式：
	[{
	    "instId": "BTC-USDT",
	    "last": "50000.5",      // 最新成交价
	    "bidPx": "50000.0",     // 最佳买价
	    "askPx": "50001.0",     // 最佳卖价
	    "vol24h": "10000",      // 24小时成交量
	    "high24h": "51000",     // 24小时最高价
	    "low24h": "49000",      // 24小时最低价
	    "ts": "1609459200000"
	}]

参数：
  - symbol: 交易对
  - data: 原始JSON数据

用途：
  - 快速获取交易对当前价格
  - 展示24小时涨跌幅
  - 计算买卖价差
*/
func (o *OKXExchange) handleTickerMessage(symbol string, data json.RawMessage) {
	var tickers []struct {
		InstID  string `json:"instId"`  // 交易对
		Last    string `json:"last"`    // 最新价
		BidPx   string `json:"bidPx"`   // 最佳买价
		AskPx   string `json:"askPx"`   // 最佳卖价
		Vol24h  string `json:"vol24h"`  // 24小时成交量
		High24h string `json:"high24h"` // 24小时最高价
		Low24h  string `json:"low24h"`  // 24小时最低价
		Ts      string `json:"ts"`      // 时间戳
	}

	if err := json.Unmarshal(data, &tickers); err != nil {
		o.log.Error("解析行情数据失败", zap.Error(err))
		return
	}

	for _, t := range tickers {
		// 使用 decimal 解析所有价格字段
		lastPrice, _ := decimal.NewFromString(t.Last)
		bidPrice, _ := decimal.NewFromString(t.BidPx)
		askPrice, _ := decimal.NewFromString(t.AskPx)
		volume, _ := decimal.NewFromString(t.Vol24h)
		highPrice, _ := decimal.NewFromString(t.High24h)
		lowPrice, _ := decimal.NewFromString(t.Low24h)
		ts, _ := strconv.ParseInt(t.Ts, 10, 64)

		// 构造内部 Ticker 模型
		ticker := &model.Ticker{
			Exchange:  model.ExchangeOKX,
			Symbol:    symbol,
			LastPrice: lastPrice,
			BidPrice:  bidPrice,
			AskPrice:  askPrice,
			Volume24h: volume,
			High24h:   highPrice,
			Low24h:    lowPrice,
			Timestamp: time.UnixMilli(ts),
		}

		// 分发给所有订阅者
		o.mu.RLock()
		for _, handler := range o.tickerHandlers {
			go handler(ticker)
		}
		o.mu.RUnlock()
	}
}

/*
handleReconnect 处理WebSocket重连

当WebSocket连接断开时，自动尝试重新连接。

重连策略：
  - 使用指数退避算法
  - 初始等待: 1秒
  - 最大等待: 60秒
  - 每次失败后翻倍

执行流程：
 1. 标记连接状态为断开
 2. 等待退避时间
 3. 尝试重连
 4. 失败则增加退避时间，重复步骤2-3
 5. 成功则退出

退出条件：
  - 收到 stopCh 信号（优雅关闭）
  - 重连成功

为什么使用指数退避：
  - 避免频繁重连导致被服务器封禁
  - 给予服务器恢复时间
  - 减少网络拥塞
*/
func (o *OKXExchange) handleReconnect() {
	// 标记断开状态
	o.mu.Lock()
	o.isConnected = false
	o.mu.Unlock()

	o.log.Info("尝试重新连接...")

	// 指数退避参数
	backoff := time.Second      // 初始等待1秒
	maxBackoff := time.Minute   // 最大等待60秒

	for {
		select {
		case <-o.stopCh:
			// 收到停止信号，放弃重连
			return
		case <-time.After(backoff):
			// 尝试重连
			if err := o.Connect(context.Background()); err != nil {
				o.log.Error("重连失败", zap.Error(err))
				// 指数增加等待时间
				backoff *= 2
				if backoff > maxBackoff {
					backoff = maxBackoff // 限制最大等待时间
				}
				continue
			}
			o.log.Info("重连成功")
			return
		}
	}
}

/*
Disconnect 断开交易所连接

实现 Exchange 接口的 Disconnect() 方法。
安全地关闭WebSocket连接和所有后台协程。

执行流程：
 1. 关闭 stopCh 通知所有协程退出
 2. 关闭 WebSocket 连接
 3. 更新连接状态

返回：
  - 成功返回 nil
  - WebSocket关闭失败返回错误

注意：
  - close(stopCh) 会立即通知所有等待该通道的goroutine
  - 方法是幂等的，多次调用是安全的（除了第二次close会panic）
*/
func (o *OKXExchange) Disconnect() error {
	o.mu.Lock()
	defer o.mu.Unlock()

	// 关闭停止通道，通知所有协程
	close(o.stopCh)

	// 关闭WebSocket连接
	if o.wsConn != nil {
		if err := o.wsConn.Close(); err != nil {
			return fmt.Errorf("关闭WebSocket失败: %w", err)
		}
	}

	o.isConnected = false
	o.log.Info("已断开连接")
	return nil
}

/*
SubscribeTick 订阅逐笔成交数据

实现 Exchange 接口的 SubscribeTick() 方法。
注册成交数据处理回调函数。

参数：
  - ctx: 上下文（当前未使用，保留用于未来扩展）
  - symbols: 交易对列表
  - handler: 回调函数，每有新成交时被调用

注意：
  - 实际订阅在 Connect() 时已完成
  - 此方法仅注册处理回调
  - key 使用逗号分隔的交易对列表
*/
func (o *OKXExchange) SubscribeTick(ctx context.Context, symbols []string, handler TickHandler) error {
	o.mu.Lock()
	defer o.mu.Unlock()

	key := strings.Join(symbols, ",")
	o.tickHandlers[key] = handler
	return nil
}

/*
SubscribeKline 订阅K线数据

实现 Exchange 接口的 SubscribeKline() 方法。
注册K线数据处理回调函数。

参数：
  - ctx: 上下文
  - symbols: 交易对列表
  - timeframe: 时间周期
  - handler: 回调函数，每有K线更新时被调用

key格式：
  - "BTC-USDT,ETH-USDT_1m"
  - 交易对和周期用下划线分隔
*/
func (o *OKXExchange) SubscribeKline(ctx context.Context, symbols []string, timeframe model.Timeframe, handler KlineHandler) error {
	o.mu.Lock()
	defer o.mu.Unlock()

	key := fmt.Sprintf("%s_%s", strings.Join(symbols, ","), timeframe)
	o.klineHandlers[key] = handler
	return nil
}

/*
SubscribeOrderBook 订阅订单簿数据

实现 Exchange 接口的 SubscribeOrderBook() 方法。
注册订单簿数据处理回调函数。

参数：
  - ctx: 上下文
  - symbols: 交易对列表
  - handler: 回调函数，每有深度更新时被调用

用途：
  - 获取买卖盘挂单信息
  - 计算买卖价差
  - 分析市场深度
*/
func (o *OKXExchange) SubscribeOrderBook(ctx context.Context, symbols []string, handler OrderBookHandler) error {
	o.mu.Lock()
	defer o.mu.Unlock()

	key := strings.Join(symbols, ",")
	o.orderBookHandlers[key] = handler
	return nil
}

/*
SubscribeTicker 订阅行情快照

实现 Exchange 接口的 SubscribeTicker() 方法。
注册行情快照处理回调函数。

参数：
  - ctx: 上下文
  - symbols: 交易对列表
  - handler: 回调函数，每有行情更新时被调用

行情快照包含：
  - 最新价格
  - 24小时高低价
  - 24小时成交量
  - 最佳买卖价
*/
func (o *OKXExchange) SubscribeTicker(ctx context.Context, symbols []string, handler TickerHandler) error {
	o.mu.Lock()
	defer o.mu.Unlock()

	key := strings.Join(symbols, ",")
	o.tickerHandlers[key] = handler
	return nil
}

/*
GetHistoricalKlines 获取历史K线数据

实现 Exchange 接口的 GetHistoricalKlines() 方法。
通过REST API获取指定时间范围内的历史K线。

API端点：
  - GET /api/v5/market/candles

参数：
  - ctx: 上下文，用于超时和取消
  - symbol: 交易对，如 "BTC-USDT"
  - timeframe: 时间周期
  - start: 开始时间
  - end: 结束时间
  - limit: 返回数量限制（OKX最大100）

返回：
  - K线数组（时间从新到旧）
  - 发生错误时返回 nil 和错误信息

OKX API响应格式：
	{
	    "code": "0",
	    "msg": "",
	    "data": [[时间戳, 开, 高, 低, 收, 成交量, ...], ...]
	}

注意：
  - OKX的 before/after 参数含义与其他交易所不同
  - before: 获取此时间之前的数据
  - after: 获取此时间之后的数据
*/
func (o *OKXExchange) GetHistoricalKlines(ctx context.Context, symbol string, timeframe model.Timeframe, start, end time.Time, limit int) ([]model.Kline, error) {
	// 转换时间周期格式
	bar := o.timeframeToBinanceFormat(timeframe)

	// 构建请求URL
	url := fmt.Sprintf("%s/api/v5/market/candles?instId=%s&bar=%s&before=%d&after=%d&limit=%d",
		o.cfg.RESTEndpoint, symbol, bar, start.UnixMilli(), end.UnixMilli(), limit)

	// 发送HTTP请求
	resp, err := o.doRequest(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	// 解析响应
	var result struct {
		Code string     `json:"code"` // "0" 表示成功
		Msg  string     `json:"msg"`  // 错误信息
		Data [][]string `json:"data"` // K线数据数组
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("解析K线数据失败: %w", err)
	}

	// 检查API返回码
	if result.Code != "0" {
		return nil, fmt.Errorf("API错误: %s", result.Msg)
	}

	// 转换为内部模型
	klines := make([]model.Kline, len(result.Data))
	for i, k := range result.Data {
		if len(k) < 9 {
			continue
		}

		ts, _ := strconv.ParseInt(k[0], 10, 64)
		open, _ := decimal.NewFromString(k[1])
		high, _ := decimal.NewFromString(k[2])
		low, _ := decimal.NewFromString(k[3])
		closePrice, _ := decimal.NewFromString(k[4])
		volume, _ := decimal.NewFromString(k[5])
		quoteVolume, _ := decimal.NewFromString(k[6])
		confirm := k[8] == "1"

		klines[i] = model.Kline{
			Exchange:    model.ExchangeOKX,
			Symbol:      symbol,
			Timeframe:   timeframe,
			OpenTime:    time.UnixMilli(ts),
			Open:        open,
			High:        high,
			Low:         low,
			Close:       closePrice,
			Volume:      volume,
			QuoteVolume: quoteVolume,
			IsClosed:    confirm,
		}
	}

	return klines, nil
}

/*
timeframeToBinanceFormat 转换时间周期为OKX API格式

将内部 Timeframe 类型转换为OKX REST API需要的格式。

转换规则：
  - 分钟: 1m, 5m, 15m, 30m（小写）
  - 小时: 1H, 4H（大写H）
  - 日/周: 1D, 1W（大写）

注意：
  - OKX小时级别用大写H，分钟用小写m
  - 函数名包含Binance是历史遗留，实际已适配OKX
*/
func (o *OKXExchange) timeframeToBinanceFormat(tf model.Timeframe) string {
	switch tf {
	case model.Timeframe1m:
		return "1m"
	case model.Timeframe5m:
		return "5m"
	case model.Timeframe15m:
		return "15m"
	case model.Timeframe30m:
		return "30m"
	case model.Timeframe1h:
		return "1H"
	case model.Timeframe4h:
		return "4H"
	case model.Timeframe1d:
		return "1D"
	case model.Timeframe1w:
		return "1W"
	default:
		return "1m"
	}
}

/*
GetTicker 获取当前行情快照

实现 Exchange 接口的 GetTicker() 方法。
通过REST API获取指定交易对的最新行情。

API端点：
  - GET /api/v5/market/ticker

参数：
  - ctx: 上下文
  - symbol: 交易对，如 "BTC-USDT"

返回：
  - Ticker 指针，包含最新价、买卖价、24小时数据
  - 发生错误时返回 nil 和错误信息

与WebSocket推送的区别：
  - REST API是请求-响应模式，适合一次性获取
  - WebSocket是推送模式，适合实时监控
*/
func (o *OKXExchange) GetTicker(ctx context.Context, symbol string) (*model.Ticker, error) {
	url := fmt.Sprintf("%s/api/v5/market/ticker?instId=%s", o.cfg.RESTEndpoint, symbol)

	resp, err := o.doRequest(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result struct {
		Code string `json:"code"`
		Data []struct {
			InstID  string `json:"instId"`
			Last    string `json:"last"`
			BidPx   string `json:"bidPx"`
			AskPx   string `json:"askPx"`
			Vol24h  string `json:"vol24h"`
			High24h string `json:"high24h"`
			Low24h  string `json:"low24h"`
			Ts      string `json:"ts"`
		} `json:"data"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("解析行情数据失败: %w", err)
	}

	if len(result.Data) == 0 {
		return nil, fmt.Errorf("没有行情数据")
	}

	t := result.Data[0]
	lastPrice, _ := decimal.NewFromString(t.Last)
	bidPrice, _ := decimal.NewFromString(t.BidPx)
	askPrice, _ := decimal.NewFromString(t.AskPx)
	volume, _ := decimal.NewFromString(t.Vol24h)
	highPrice, _ := decimal.NewFromString(t.High24h)
	lowPrice, _ := decimal.NewFromString(t.Low24h)

	return &model.Ticker{
		Exchange:  model.ExchangeOKX,
		Symbol:    symbol,
		LastPrice: lastPrice,
		BidPrice:  bidPrice,
		AskPrice:  askPrice,
		Volume24h: volume,
		High24h:   highPrice,
		Low24h:    lowPrice,
		Timestamp: time.Now(), // REST API不返回时间戳，使用当前时间
	}, nil
}

/*
GetOrderBook 获取订单簿快照

实现 Exchange 接口的 GetOrderBook() 方法。
通过REST API获取指定深度的买卖盘数据。

API端点：
  - GET /api/v5/market/books

参数：
  - ctx: 上下文
  - symbol: 交易对
  - limit: 深度档位数量（OKX支持 5, 25, 100, 400）

返回：
  - OrderBook 指针，包含买卖盘数据
  - 发生错误时返回 nil 和错误信息

数据排序：
  - Bids: 价格从高到低（最高买价在前）
  - Asks: 价格从低到高（最低卖价在前）
*/
func (o *OKXExchange) GetOrderBook(ctx context.Context, symbol string, limit int) (*model.OrderBook, error) {
	url := fmt.Sprintf("%s/api/v5/market/books?instId=%s&sz=%d", o.cfg.RESTEndpoint, symbol, limit)

	resp, err := o.doRequest(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result struct {
		Code string `json:"code"`
		Data []struct {
			Bids [][]string `json:"bids"`
			Asks [][]string `json:"asks"`
			Ts   string     `json:"ts"`
		} `json:"data"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("解析订单簿数据失败: %w", err)
	}

	if len(result.Data) == 0 {
		return nil, fmt.Errorf("没有订单簿数据")
	}

	depth := result.Data[0]
	ts, _ := strconv.ParseInt(depth.Ts, 10, 64)

	orderBook := &model.OrderBook{
		Exchange:  model.ExchangeOKX,
		Symbol:    symbol,
		Timestamp: time.UnixMilli(ts),
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

/*
GetSymbols 获取交易对列表

实现 Exchange 接口的 GetSymbols() 方法。
获取OKX现货市场的所有可交易交易对信息。

API端点：
  - GET /api/v5/public/instruments?instType=SPOT

返回：
  - SymbolInfo 数组，包含所有现货交易对
  - 发生错误时返回 nil 和错误信息

SymbolInfo 字段说明：
  - Symbol: 交易对名称，如 "BTC-USDT"
  - BaseCurrency: 基础货币，如 "BTC"
  - QuoteCurrency: 计价货币，如 "USDT"
  - PricePrecision: 价格精度（小数位数）
  - QtyPrecision: 数量精度（小数位数）
  - MinQty: 最小交易数量
  - Status: 交易对状态（live/suspend/preopen）

精度计算：
  - tickSz (最小价格变动) 的小数位数 = 价格精度
  - lotSz (最小数量变动) 的小数位数 = 数量精度
*/
func (o *OKXExchange) GetSymbols(ctx context.Context) ([]model.SymbolInfo, error) {
	url := fmt.Sprintf("%s/api/v5/public/instruments?instType=SPOT", o.cfg.RESTEndpoint)

	resp, err := o.doRequest(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result struct {
		Code string `json:"code"`
		Data []struct {
			InstID   string `json:"instId"`   // 交易对名称
			BaseCcy  string `json:"baseCcy"`  // 基础货币
			QuoteCcy string `json:"quoteCcy"` // 计价货币
			TickSz   string `json:"tickSz"`   // 最小价格变动
			LotSz    string `json:"lotSz"`    // 最小数量变动
			MinSz    string `json:"minSz"`    // 最小下单数量
			State    string `json:"state"`    // 状态
		} `json:"data"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("解析交易所信息失败: %w", err)
	}

	symbols := make([]model.SymbolInfo, len(result.Data))
	for i, s := range result.Data {
		minQty, _ := strconv.ParseFloat(s.MinSz, 64)
		
		// 计算价格精度：从 tickSz 推导小数位数
		// 例如 tickSz="0.01" -> 精度为2
		pricePrecision := 0
		if tickSz, _ := decimal.NewFromString(s.TickSz); !tickSz.IsZero() {
			pricePrecision = int(tickSz.Exponent() * -1) // Exponent 返回负数
		}
		
		// 计算数量精度
		qtyPrecision := 0
		if lotSz, _ := decimal.NewFromString(s.LotSz); !lotSz.IsZero() {
			qtyPrecision = int(lotSz.Exponent() * -1)
		}

		symbols[i] = model.SymbolInfo{
			Exchange:       string(model.ExchangeOKX),
			Symbol:         s.InstID,
			BaseCurrency:   s.BaseCcy,
			QuoteCurrency:  s.QuoteCcy,
			PricePrecision: pricePrecision,
			QtyPrecision:   qtyPrecision,
			MinQty:         minQty,
			Status:         s.State,
		}
	}

	return symbols, nil
}

/*
Ping 检查与交易所的连接状态

实现 Exchange 接口的 Ping() 方法。
通过调用公共时间API验证网络连接和API可用性。

API端点：
  - GET /api/v5/public/time

返回：
  - 连接正常返回 nil
  - 连接异常返回错误

用途：
  - 健康检查
  - 连接状态监控
  - 服务启动前的预检查
*/
func (o *OKXExchange) Ping(ctx context.Context) error {
	url := fmt.Sprintf("%s/api/v5/public/time", o.cfg.RESTEndpoint)
	resp, err := o.doRequest(ctx, "GET", url, nil)
	if err != nil {
		return err
	}
	resp.Body.Close()
	return nil
}

/*
doRequest 执行HTTP请求

内部辅助方法，封装HTTP请求的创建和发送。

参数：
  - ctx: 上下文，用于超时和取消
  - method: HTTP方法（GET、POST等）
  - url: 完整的请求URL
  - body: 请求体（可选）

返回：
  - HTTP响应指针
  - 发生错误时返回 nil 和错误信息

错误处理：
  - 请求创建失败
  - 网络请求失败
  - 非200状态码（返回响应体内容便于调试）

使用注意：
  - 调用方负责关闭 resp.Body
  - 超时由 httpClient 的 Timeout 设置控制
*/
func (o *OKXExchange) doRequest(ctx context.Context, method, url string, body io.Reader) (*http.Response, error) {
	// 创建带上下文的HTTP请求
	req, err := http.NewRequestWithContext(ctx, method, url, body)
	if err != nil {
		return nil, fmt.Errorf("创建请求失败: %w", err)
	}

	// 设置请求头
	req.Header.Set("Content-Type", "application/json")

	// 发送请求
	resp, err := o.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("请求失败: %w", err)
	}

	// 检查状态码
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		return nil, fmt.Errorf("API返回错误: status=%d, body=%s", resp.StatusCode, string(body))
	}

	return resp, nil
}
