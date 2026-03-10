/*
================================================================================
                    项目架构与核心代码详解 - Go行情处理系统
================================================================================

本教程详细讲解项目的架构设计和核心代码逻辑，帮助你深入理解系统。

项目采用分层架构：
┌─────────────────────────────────────────────────────────────┐
│                      HTTP/WebSocket Layer                    │
│                  (handler/ middleware/)                      │
├─────────────────────────────────────────────────────────────┤
│                        Service Layer                         │
│              (service/ kline/ indicator/)                    │
├─────────────────────────────────────────────────────────────┤
│                       Exchange Layer                         │
│                      (exchange/)                             │
├─────────────────────────────────────────────────────────────┤
│                       Storage Layer                          │
│              (storage/ model/)                               │
└─────────────────────────────────────────────────────────────┘
*/

package main

import (
	"fmt"
)

// ============================================================================
// 第1章：项目目录结构详解
// ============================================================================

func chapter1_project_structure() {
	fmt.Println(`
=== 第1章：项目目录结构详解 ===

go-market-service/
├── cmd/                        # 可执行文件入口
│   └── server/
│       └── main.go             # 主程序入口
│
├── configs/                    # 配置文件
│   └── config.yaml             # 主配置文件
│
├── internal/                   # 私有代码（不对外暴露）
│   ├── config/                 # 配置管理
│   │   └── config.go           # 配置结构定义和加载
│   │
│   ├── model/                  # 数据模型
│   │   ├── market.go           # 行情相关模型（Kline, Tick, OrderBook）
│   │   └── entity.go           # 数据库实体（ORM映射）
│   │
│   ├── exchange/               # 交易所接口层
│   │   ├── interface.go        # 交易所统一接口定义
│   │   ├── binance.go          # Binance实现
│   │   ├── okx.go              # OKX实现
│   │   └── factory.go          # 工厂模式创建实例
│   │
│   ├── kline/                  # K线处理
│   │   └── aggregator.go       # K线聚合器（多周期生成）
│   │
│   ├── indicator/              # 技术指标
│   │   ├── indicators.go       # 各种指标算法实现
│   │   └── calculator.go       # 指标计算服务
│   │
│   ├── storage/                # 存储层
│   │   ├── storage.go          # 数据库/Redis初始化
│   │   └── kline_repository.go # K线数据仓库
│   │
│   ├── service/                # 业务服务层
│   │   ├── service.go          # 核心服务（数据流处理）
│   │   └── datafeed.go         # 数据输出（回测/实盘）
│   │
│   ├── handler/                # HTTP处理器
│   │   └── handler.go          # REST API路由处理
│   │
│   └── middleware/             # HTTP中间件
│       └── middleware.go       # 日志/恢复/CORS
│
├── pkg/                        # 公共工具包（可对外暴露）
│   └── logger/
│       └── logger.go           # 日志工具
│
├── examples/                   # 使用示例
│   ├── backtest_demo.go        # 回测示例
│   └── live_demo.go            # 实盘示例
│
├── scripts/                    # 脚本
│   ├── init_db.sql             # 数据库初始化SQL
│   └── start.sh                # 启动脚本
│
├── docs/                       # 文档
│   └── tutorial/               # 教程
│
├── go.mod                      # Go模块定义
├── go.sum                      # 依赖校验
├── Dockerfile                  # Docker镜像构建
├── docker-compose.yaml         # Docker编排
└── README.md                   # 项目说明


【设计原则】
1. internal/ - Go特殊目录，代码不能被外部包导入
2. pkg/ - 公共包，可以被其他项目导入
3. cmd/ - 可执行文件，每个子目录是一个可执行程序
4. 分层清晰，职责单一
`)
}

// ============================================================================
// 第2章：数据模型设计
// ============================================================================

func chapter2_data_models() {
	fmt.Println(`
=== 第2章：数据模型设计 ===

【1. 行情数据模型 (internal/model/market.go)】

// Exchange 交易所枚举
// 使用自定义类型而非string，增加类型安全
type Exchange string

const (
    ExchangeBinance Exchange = "binance"
    ExchangeOKX     Exchange = "okx"
    ExchangeBybit   Exchange = "bybit"
)

// Timeframe K线周期
// 同样使用自定义类型
type Timeframe string

const (
    Timeframe1m  Timeframe = "1m"
    Timeframe5m  Timeframe = "5m"
    Timeframe15m Timeframe = "15m"
    // ...
)

// Duration() 方法返回周期对应的时间长度
// 这是Go的接口实现方式 - 给类型添加方法
func (t Timeframe) Duration() time.Duration {
    switch t {
    case Timeframe1m:
        return time.Minute
    case Timeframe1h:
        return time.Hour
    // ...
    }
}

// Tick 逐笔成交数据
// 使用decimal.Decimal保证金融计算精度
type Tick struct {
    Exchange  Exchange        ` + "`" + `json:"exchange"` + "`" + `   // 交易所
    Symbol    string          ` + "`" + `json:"symbol"` + "`" + `     // 交易对 BTCUSDT
    TradeID   string          ` + "`" + `json:"trade_id"` + "`" + `   // 成交ID
    Price     decimal.Decimal ` + "`" + `json:"price"` + "`" + `      // 成交价
    Quantity  decimal.Decimal ` + "`" + `json:"quantity"` + "`" + `   // 成交量
    Timestamp time.Time       ` + "`" + `json:"timestamp"` + "`" + `  // 成交时间
    IsBuyer   bool            ` + "`" + `json:"is_buyer"` + "`" + `   // 是否买方主动
}

// Kline K线数据
// 这是系统最核心的数据结构
type Kline struct {
    Exchange    Exchange        ` + "`" + `json:"exchange"` + "`" + `
    Symbol      string          ` + "`" + `json:"symbol"` + "`" + `
    Timeframe   Timeframe       ` + "`" + `json:"timeframe"` + "`" + `
    OpenTime    time.Time       ` + "`" + `json:"open_time"` + "`" + `    // K线开盘时间
    CloseTime   time.Time       ` + "`" + `json:"close_time"` + "`" + `   // K线收盘时间
    Open        decimal.Decimal ` + "`" + `json:"open"` + "`" + `         // 开盘价
    High        decimal.Decimal ` + "`" + `json:"high"` + "`" + `         // 最高价
    Low         decimal.Decimal ` + "`" + `json:"low"` + "`" + `          // 最低价
    Close       decimal.Decimal ` + "`" + `json:"close"` + "`" + `        // 收盘价
    Volume      decimal.Decimal ` + "`" + `json:"volume"` + "`" + `       // 成交量
    QuoteVolume decimal.Decimal ` + "`" + `json:"quote_volume"` + "`" + ` // 成交额
    TradeCount  int64           ` + "`" + `json:"trade_count"` + "`" + `  // 成交笔数
    IsClosed    bool            ` + "`" + `json:"is_closed"` + "`" + `    // 是否已收盘
}


【2. 数据库实体 (internal/model/entity.go)】

// KlineEntity 数据库映射实体
// 使用gorm标签定义数据库字段
type KlineEntity struct {
    // 复合主键：时间+交易所+交易对+周期
    Time        time.Time ` + "`" + `gorm:"column:time;primaryKey"` + "`" + `
    Exchange    string    ` + "`" + `gorm:"column:exchange;primaryKey;size:20"` + "`" + `
    Symbol      string    ` + "`" + `gorm:"column:symbol;primaryKey;size:20"` + "`" + `
    Timeframe   string    ` + "`" + `gorm:"column:timeframe;primaryKey;size:5"` + "`" + `
    
    // OHLCV数据使用double precision存储
    // 注意：数据库用float64，内存用decimal
    Open        float64   ` + "`" + `gorm:"column:open;type:double precision"` + "`" + `
    High        float64   ` + "`" + `gorm:"column:high;type:double precision"` + "`" + `
    Low         float64   ` + "`" + `gorm:"column:low;type:double precision"` + "`" + `
    Close       float64   ` + "`" + `gorm:"column:close;type:double precision"` + "`" + `
    Volume      float64   ` + "`" + `gorm:"column:volume;type:double precision"` + "`" + `
    QuoteVolume float64   ` + "`" + `gorm:"column:quote_volume;type:double precision"` + "`" + `
    TradeCount  int64     ` + "`" + `gorm:"column:trade_count"` + "`" + `
}

// TableName 自定义表名
// GORM约定：实现TableName()方法
func (KlineEntity) TableName() string {
    return "klines"
}


【设计要点】
1. 业务模型和数据库实体分离
   - model.Kline: 业务逻辑使用，用decimal保证精度
   - model.KlineEntity: 数据库存储，用float64
   
2. 在Repository层进行转换
   - toEntity(): Kline -> KlineEntity
   - toModel(): KlineEntity -> Kline
   
3. 使用复合主键
   - TimescaleDB按时间分区，时间必须是主键的一部分
   - 同一时间可能有多个交易对的数据
`)
}

// ============================================================================
// 第3章：交易所接口层
// ============================================================================

func chapter3_exchange_layer() {
	fmt.Println(`
=== 第3章：交易所接口层 ===

【设计模式：策略模式 + 工厂模式】

交易所接口层采用经典的策略模式：
- Exchange接口定义统一行为
- 每个交易所实现该接口
- 通过工厂创建具体实例

【1. 接口定义 (internal/exchange/interface.go)】

// Exchange 交易所统一接口
// Go的接口是隐式实现的，只要实现了所有方法就算实现了接口
type Exchange interface {
    // Name 返回交易所名称
    Name() model.Exchange
    
    // Connect 建立连接
    // ctx用于控制超时和取消
    Connect(ctx context.Context) error
    
    // Disconnect 断开连接
    Disconnect() error
    
    // SubscribeTick 订阅逐笔成交
    // handler是回调函数，收到数据时调用
    SubscribeTick(ctx context.Context, symbols []string, handler TickHandler) error
    
    // SubscribeKline 订阅K线
    SubscribeKline(ctx context.Context, symbols []string, timeframe model.Timeframe, handler KlineHandler) error
    
    // GetHistoricalKlines 获取历史K线
    // REST API调用
    GetHistoricalKlines(ctx context.Context, symbol string, timeframe model.Timeframe, start, end time.Time, limit int) ([]model.Kline, error)
    
    // GetTicker 获取行情快照
    GetTicker(ctx context.Context, symbol string) (*model.Ticker, error)
    
    // Ping 健康检查
    Ping(ctx context.Context) error
}

// TickHandler 回调函数类型定义
type TickHandler func(tick *model.Tick)
type KlineHandler func(kline *model.Kline)


【2. Binance实现 (internal/exchange/binance.go)】

// BinanceExchange Binance交易所实现
type BinanceExchange struct {
    cfg         config.ExchangeConfig  // 配置
    log         *zap.Logger            // 日志器
    wsConn      *websocket.Conn        // WebSocket连接
    httpClient  *http.Client           // HTTP客户端
    mu          sync.RWMutex           // 读写锁（并发安全）
    isConnected bool                   // 连接状态
    stopCh      chan struct{}          // 停止信号通道
    
    // 处理器映射：symbol -> handler
    tickHandlers     map[string]TickHandler
    klineHandlers    map[string]KlineHandler
    // ...
}

// Connect 连接实现
func (b *BinanceExchange) Connect(ctx context.Context) error {
    b.mu.Lock()
    defer b.mu.Unlock()
    
    // 已连接则返回
    if b.isConnected {
        return nil
    }
    
    // 构建WebSocket URL
    // Binance使用组合流：wss://stream.binance.com/stream?streams=xxx
    streams := b.buildStreams()
    wsURL := fmt.Sprintf("%s/stream?streams=%s", b.cfg.WSEndpoint, strings.Join(streams, "/"))
    
    // 建立WebSocket连接
    dialer := websocket.Dialer{HandshakeTimeout: 10 * time.Second}
    conn, _, err := dialer.DialContext(ctx, wsURL, nil)
    if err != nil {
        return fmt.Errorf("连接WebSocket失败: %w", err)  // 错误包装
    }
    
    b.wsConn = conn
    b.isConnected = true
    
    // 启动消息处理协程
    go b.handleMessages()
    
    return nil
}

// handleMessages 消息处理循环
// 这是一个独立的goroutine，持续读取WebSocket消息
func (b *BinanceExchange) handleMessages() {
    for {
        select {
        case <-b.stopCh:  // 收到停止信号
            return
        default:
            // 读取消息
            _, message, err := b.wsConn.ReadMessage()
            if err != nil {
                // 异常关闭时重连
                if websocket.IsUnexpectedCloseError(err, ...) {
                    b.log.Error("WebSocket读取错误", zap.Error(err))
                }
                b.handleReconnect()  // 触发重连
                return
            }
            
            // 处理消息
            b.processMessage(message)
        }
    }
}

// processMessage 解析并分发消息
func (b *BinanceExchange) processMessage(message []byte) {
    // Binance组合流消息格式：
    // {"stream":"btcusdt@trade","data":{...}}
    
    var wrapper struct {
        Stream string          ` + "`" + `json:"stream"` + "`" + `
        Data   json.RawMessage ` + "`" + `json:"data"` + "`" + `
    }
    
    if err := json.Unmarshal(message, &wrapper); err != nil {
        return
    }
    
    // 根据流类型分发
    // 流名称格式：btcusdt@trade, btcusdt@kline_1m
    parts := strings.Split(wrapper.Stream, "@")
    symbol := strings.ToUpper(parts[0])
    streamType := parts[1]
    
    switch {
    case streamType == "trade":
        b.handleTradeMessage(symbol, wrapper.Data)
    case strings.HasPrefix(streamType, "kline"):
        b.handleKlineMessage(symbol, wrapper.Data)
    // ...
    }
}

// handleTradeMessage 处理成交消息
func (b *BinanceExchange) handleTradeMessage(symbol string, data json.RawMessage) {
    // Binance成交消息格式
    var trade struct {
        EventType string ` + "`" + `json:"e"` + "`" + `   // 事件类型 "trade"
        Symbol    string ` + "`" + `json:"s"` + "`" + `   // 交易对
        TradeID   int64  ` + "`" + `json:"t"` + "`" + `   // 成交ID
        Price     string ` + "`" + `json:"p"` + "`" + `   // 价格（字符串）
        Quantity  string ` + "`" + `json:"q"` + "`" + `   // 数量
        Timestamp int64  ` + "`" + `json:"T"` + "`" + `   // 时间戳（毫秒）
        IsBuyer   bool   ` + "`" + `json:"m"` + "`" + `   // 是否买方
    }
    
    json.Unmarshal(data, &trade)
    
    // 转换为内部模型
    price, _ := decimal.NewFromString(trade.Price)
    qty, _ := decimal.NewFromString(trade.Quantity)
    
    tick := &model.Tick{
        Exchange:  model.ExchangeBinance,
        Symbol:    symbol,
        TradeID:   strconv.FormatInt(trade.TradeID, 10),
        Price:     price,
        Quantity:  qty,
        Timestamp: time.UnixMilli(trade.Timestamp),
        IsBuyer:   trade.IsBuyer,
    }
    
    // 调用所有注册的处理器
    b.mu.RLock()  // 读锁
    for _, handler := range b.tickHandlers {
        go handler(tick)  // 异步调用，避免阻塞
    }
    b.mu.RUnlock()
}


【3. 工厂模式 (internal/exchange/factory.go)】

// Factory 交易所工厂
type Factory struct {
    log *zap.Logger
}

// Create 根据配置创建交易所实例
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

// 使用示例
factory := exchange.NewFactory(log)
ex, err := factory.Create(config)
ex.Connect(ctx)
ex.SubscribeTick(ctx, symbols, handler)


【设计要点】
1. 接口抽象
   - 统一的Exchange接口
   - 业务层不关心具体交易所
   
2. 并发安全
   - 使用sync.RWMutex保护共享状态
   - 读多写少场景用RWMutex
   
3. 错误处理
   - 使用%w包装错误，保留原始信息
   - 异常时自动重连
   
4. 资源管理
   - 使用stopCh控制goroutine生命周期
   - defer确保资源释放
`)
}

// ============================================================================
// 第4章：K线聚合器
// ============================================================================

func chapter4_kline_aggregator() {
	fmt.Println(`
=== 第4章：K线聚合器 ===

【功能】
从低周期数据（Tick或1分钟K线）聚合生成高周期K线

【核心算法】

// Aggregator K线聚合器
type Aggregator struct {
    log        *zap.Logger
    mu         sync.RWMutex
    
    // 正在构建的K线缓存
    // key格式: exchange:symbol:timeframe
    building map[string]*model.Kline
    
    // K线完成时的回调
    onComplete func(kline *model.Kline)
}

// ProcessTick 从Tick生成K线
func (a *Aggregator) ProcessTick(tick *model.Tick, timeframes []model.Timeframe) {
    a.mu.Lock()
    defer a.mu.Unlock()
    
    for _, tf := range timeframes {
        key := makeKey(tick.Exchange, tick.Symbol, tf)
        kline := a.building[key]
        
        // 计算当前K线应该的开盘时间
        openTime := a.calculateOpenTime(tick.Timestamp, tf)
        
        // 判断是否需要创建新K线
        if kline == nil || !kline.OpenTime.Equal(openTime) {
            // 完成旧K线
            if kline != nil {
                kline.IsClosed = true
                if a.onComplete != nil {
                    go a.onComplete(kline)  // 异步回调
                }
            }
            
            // 创建新K线
            kline = &model.Kline{
                Exchange:  tick.Exchange,
                Symbol:    tick.Symbol,
                Timeframe: tf,
                OpenTime:  openTime,
                CloseTime: openTime.Add(tf.Duration()),
                Open:      tick.Price,
                High:      tick.Price,
                Low:       tick.Price,
                Close:     tick.Price,
                Volume:    tick.Quantity,
                TradeCount: 1,
            }
            a.building[key] = kline
        } else {
            // 更新当前K线
            // 更新最高价
            if tick.Price.GreaterThan(kline.High) {
                kline.High = tick.Price
            }
            // 更新最低价
            if tick.Price.LessThan(kline.Low) {
                kline.Low = tick.Price
            }
            // 收盘价始终是最新价
            kline.Close = tick.Price
            // 累加成交量
            kline.Volume = kline.Volume.Add(tick.Quantity)
            kline.TradeCount++
        }
    }
}

// calculateOpenTime 计算K线开盘时间
// 关键：将时间对齐到周期边界
func (a *Aggregator) calculateOpenTime(ts time.Time, tf model.Timeframe) time.Time {
    switch tf {
    case model.Timeframe1m:
        // 对齐到分钟：12:34:56 -> 12:34:00
        return ts.Truncate(time.Minute)
        
    case model.Timeframe5m:
        // 对齐到5分钟：12:37:00 -> 12:35:00
        return ts.Truncate(5 * time.Minute)
        
    case model.Timeframe1h:
        // 对齐到小时
        return ts.Truncate(time.Hour)
        
    case model.Timeframe4h:
        // 对齐到4小时：需要特殊处理
        // 因为Truncate不支持任意时长
        hour := ts.Hour()
        alignedHour := (hour / 4) * 4  // 0, 4, 8, 12, 16, 20
        return time.Date(ts.Year(), ts.Month(), ts.Day(), 
                        alignedHour, 0, 0, 0, ts.Location())
        
    case model.Timeframe1d:
        // 对齐到UTC 0点（交易所标准）
        return time.Date(ts.Year(), ts.Month(), ts.Day(), 
                        0, 0, 0, 0, time.UTC)
        
    case model.Timeframe1w:
        // 对齐到周一 UTC 0点
        weekday := int(ts.Weekday())
        if weekday == 0 {
            weekday = 7  // 周日算第7天
        }
        monday := ts.AddDate(0, 0, -(weekday - 1))
        return time.Date(monday.Year(), monday.Month(), monday.Day(),
                        0, 0, 0, 0, time.UTC)
    }
    
    return ts.Truncate(tf.Duration())
}

// ProcessKline 从低周期K线聚合高周期K线
// 例如：从1m K线生成5m, 15m, 1h K线
func (a *Aggregator) ProcessKline(sourceKline *model.Kline, targetTimeframes []model.Timeframe) {
    a.mu.Lock()
    defer a.mu.Unlock()
    
    for _, tf := range targetTimeframes {
        // 跳过相同或更小周期
        if tf.Duration() <= sourceKline.Timeframe.Duration() {
            continue
        }
        
        key := makeKey(sourceKline.Exchange, sourceKline.Symbol, tf)
        kline := a.building[key]
        openTime := a.calculateOpenTime(sourceKline.OpenTime, tf)
        
        if kline == nil || !kline.OpenTime.Equal(openTime) {
            // 完成旧K线，创建新K线
            // ... 类似ProcessTick
        } else {
            // 聚合更新
            // 最高价取两者较大值
            if sourceKline.High.GreaterThan(kline.High) {
                kline.High = sourceKline.High
            }
            // 最低价取两者较小值
            if sourceKline.Low.LessThan(kline.Low) {
                kline.Low = sourceKline.Low
            }
            // 收盘价用源K线的收盘价
            kline.Close = sourceKline.Close
            // 成交量累加
            kline.Volume = kline.Volume.Add(sourceKline.Volume)
            kline.TradeCount += sourceKline.TradeCount
        }
    }
}


【K线缓冲区】

// KlineBuffer 环形缓冲区，存储最近N根K线
type KlineBuffer struct {
    mu      sync.RWMutex
    size    int  // 最大容量
    buffers map[string][]*model.Kline  // key -> K线数组
}

// Add 添加K线（超出容量时自动淘汰旧数据）
func (b *KlineBuffer) Add(kline *model.Kline) {
    b.mu.Lock()
    defer b.mu.Unlock()
    
    key := makeKey(kline.Exchange, kline.Symbol, kline.Timeframe)
    buf := b.buffers[key]
    
    buf = append(buf, kline)
    
    // 保持缓冲区大小
    if len(buf) > b.size {
        buf = buf[len(buf)-b.size:]  // 只保留最后size个
    }
    
    b.buffers[key] = buf
}

// Get 获取最近N根K线
func (b *KlineBuffer) Get(exchange model.Exchange, symbol string, tf model.Timeframe, limit int) []*model.Kline {
    b.mu.RLock()
    defer b.mu.RUnlock()
    
    key := makeKey(exchange, symbol, tf)
    buf := b.buffers[key]
    
    if limit <= 0 || limit > len(buf) {
        limit = len(buf)
    }
    
    // 返回最近的limit根
    result := make([]*model.Kline, limit)
    copy(result, buf[len(buf)-limit:])
    return result
}


【设计要点】
1. 时间对齐
   - 所有周期都要正确对齐时间边界
   - 4小时、日线、周线需要特殊处理
   
2. 并发安全
   - 多个goroutine可能同时更新K线
   - 使用读写锁保护
   
3. 内存管理
   - 使用缓冲区避免无限增长
   - 及时清理已完成的K线
`)
}

// ============================================================================
// 第5章：技术指标计算
// ============================================================================

func chapter5_indicators() {
	fmt.Println(`
=== 第5章：技术指标计算 ===

【指标分类】
1. 趋势指标：SMA, EMA, MACD, ADX
2. 震荡指标：RSI, KDJ
3. 波动指标：布林带, ATR
4. 成交量指标：OBV, VWAP

【核心算法实现】

// ========== SMA 简单移动平均 ==========
// SMA = (P1 + P2 + ... + Pn) / n
func SMA(prices []decimal.Decimal, period int) []decimal.Decimal {
    if len(prices) < period {
        return nil
    }
    
    result := make([]decimal.Decimal, len(prices))
    
    // 计算初始SMA（前period个的平均）
    sum := decimal.Zero
    for i := 0; i < period; i++ {
        sum = sum.Add(prices[i])
    }
    result[period-1] = sum.Div(decimal.NewFromInt(int64(period)))
    
    // 滑动窗口计算后续值
    // 优化：不需要每次都重新累加
    for i := period; i < len(prices); i++ {
        // 减去窗口最左边的值，加上新值
        sum = sum.Sub(prices[i-period]).Add(prices[i])
        result[i] = sum.Div(decimal.NewFromInt(int64(period)))
    }
    
    return result
}


// ========== EMA 指数移动平均 ==========
// EMA = Price * k + EMA_prev * (1-k)
// k = 2 / (period + 1)
func EMA(prices []decimal.Decimal, period int) []decimal.Decimal {
    if len(prices) < period {
        return nil
    }
    
    result := make([]decimal.Decimal, len(prices))
    
    // 计算乘数 k = 2/(n+1)
    multiplier := decimal.NewFromFloat(2.0 / float64(period+1))
    oneMinusK := decimal.NewFromInt(1).Sub(multiplier)
    
    // 用SMA作为初始EMA
    sma := SMA(prices[:period], period)
    result[period-1] = sma[period-1]
    
    // 递归计算EMA
    for i := period; i < len(prices); i++ {
        // EMA = 今日价格 * k + 昨日EMA * (1-k)
        result[i] = prices[i].Mul(multiplier).Add(result[i-1].Mul(oneMinusK))
    }
    
    return result
}


// ========== RSI 相对强弱指标 ==========
// RSI = 100 - 100/(1 + RS)
// RS = 平均上涨幅度 / 平均下跌幅度
func RSI(prices []decimal.Decimal, period int) []decimal.Decimal {
    if len(prices) < period+1 {
        return nil
    }
    
    result := make([]decimal.Decimal, len(prices))
    gains := make([]decimal.Decimal, len(prices))
    losses := make([]decimal.Decimal, len(prices))
    
    // 计算每日涨跌
    for i := 1; i < len(prices); i++ {
        change := prices[i].Sub(prices[i-1])
        if change.GreaterThan(decimal.Zero) {
            gains[i] = change      // 上涨
        } else {
            losses[i] = change.Abs()  // 下跌（取绝对值）
        }
    }
    
    // 计算初始平均涨跌幅
    avgGain := decimal.Zero
    avgLoss := decimal.Zero
    for i := 1; i <= period; i++ {
        avgGain = avgGain.Add(gains[i])
        avgLoss = avgLoss.Add(losses[i])
    }
    avgGain = avgGain.Div(decimal.NewFromInt(int64(period)))
    avgLoss = avgLoss.Div(decimal.NewFromInt(int64(period)))
    
    // 计算RSI
    hundred := decimal.NewFromInt(100)
    
    if avgLoss.IsZero() {
        result[period] = hundred  // 全涨，RSI=100
    } else {
        rs := avgGain.Div(avgLoss)
        result[period] = hundred.Sub(hundred.Div(decimal.NewFromInt(1).Add(rs)))
    }
    
    // 平滑计算后续RSI
    periodDec := decimal.NewFromInt(int64(period))
    periodMinusOne := decimal.NewFromInt(int64(period - 1))
    
    for i := period + 1; i < len(prices); i++ {
        // 平滑平均 = (前值 * (n-1) + 新值) / n
        avgGain = avgGain.Mul(periodMinusOne).Add(gains[i]).Div(periodDec)
        avgLoss = avgLoss.Mul(periodMinusOne).Add(losses[i]).Div(periodDec)
        
        if avgLoss.IsZero() {
            result[i] = hundred
        } else {
            rs := avgGain.Div(avgLoss)
            result[i] = hundred.Sub(hundred.Div(decimal.NewFromInt(1).Add(rs)))
        }
    }
    
    return result
}


// ========== MACD ==========
// MACD = EMA(fast) - EMA(slow)
// Signal = EMA(MACD, signal_period)
// Histogram = MACD - Signal
type MACDResult struct {
    MACD      []decimal.Decimal
    Signal    []decimal.Decimal
    Histogram []decimal.Decimal
}

func MACD(prices []decimal.Decimal, fastPeriod, slowPeriod, signalPeriod int) *MACDResult {
    fastEMA := EMA(prices, fastPeriod)
    slowEMA := EMA(prices, slowPeriod)
    
    // MACD线 = 快线 - 慢线
    macdLine := make([]decimal.Decimal, len(prices))
    for i := 0; i < len(prices); i++ {
        if !fastEMA[i].IsZero() && !slowEMA[i].IsZero() {
            macdLine[i] = fastEMA[i].Sub(slowEMA[i])
        }
    }
    
    // 信号线 = MACD的EMA
    signalLine := EMA(macdLine[slowPeriod-1:], signalPeriod)
    
    // 柱状图 = MACD - Signal
    histogram := make([]decimal.Decimal, len(prices))
    for i := 0; i < len(signalLine); i++ {
        idx := slowPeriod - 1 + i
        if !macdLine[idx].IsZero() && !signalLine[i].IsZero() {
            histogram[idx] = macdLine[idx].Sub(signalLine[i])
        }
    }
    
    return &MACDResult{
        MACD:      macdLine,
        Signal:    signalLine,
        Histogram: histogram,
    }
}


// ========== 布林带 ==========
type BollingerBandsResult struct {
    Upper  []decimal.Decimal  // 上轨 = MA + k*σ
    Middle []decimal.Decimal  // 中轨 = MA
    Lower  []decimal.Decimal  // 下轨 = MA - k*σ
}

func BollingerBands(prices []decimal.Decimal, period int, stdDev float64) *BollingerBandsResult {
    middle := SMA(prices, period)
    upper := make([]decimal.Decimal, len(prices))
    lower := make([]decimal.Decimal, len(prices))
    
    for i := period - 1; i < len(prices); i++ {
        // 计算标准差
        var sum float64
        mean, _ := middle[i].Float64()
        for j := i - period + 1; j <= i; j++ {
            p, _ := prices[j].Float64()
            diff := p - mean
            sum += diff * diff
        }
        std := math.Sqrt(sum / float64(period))
        
        // 上下轨
        deviation := decimal.NewFromFloat(std * stdDev)
        upper[i] = middle[i].Add(deviation)
        lower[i] = middle[i].Sub(deviation)
    }
    
    return &BollingerBandsResult{
        Upper:  upper,
        Middle: middle,
        Lower:  lower,
    }
}


【指标计算服务】

// Calculator 指标计算器
type Calculator struct {
    log    *zap.Logger
    cfg    *IndicatorConfig
    buffer *kline.KlineBuffer  // K线数据源
    cache  map[string]*CalculatorResult  // 结果缓存
    mu     sync.RWMutex
}

// Calculate 计算所有指标
func (c *Calculator) Calculate(exchange model.Exchange, symbol string, tf model.Timeframe) *CalculatorResult {
    // 获取K线数据
    opens, highs, lows, closes, volumes := c.buffer.GetOHLCV(exchange, symbol, tf, 200)
    
    if len(closes) < 26 {
        return nil  // 数据不足
    }
    
    indicators := make(map[string]decimal.Decimal)
    
    // 计算各指标
    if len(closes) >= 14 {
        rsi := RSI(closes, 14)
        indicators["rsi"] = rsi[len(rsi)-1]
    }
    
    if len(closes) >= 26 {
        macd := MACD(closes, 12, 26, 9)
        indicators["macd"] = macd.MACD[len(macd.MACD)-1]
        indicators["macd_signal"] = macd.Signal[len(macd.Signal)-1]
    }
    
    // ... 其他指标
    
    return &CalculatorResult{
        Exchange:   exchange,
        Symbol:     symbol,
        Timeframe:  tf,
        Indicators: indicators,
    }
}
`)
}

// ============================================================================
// 第6章：服务层与数据流
// ============================================================================

func chapter6_service_layer() {
	fmt.Println(`
=== 第6章：服务层与数据流 ===

【数据流架构】

交易所WebSocket
       │
       ▼
   Exchange层 (Binance/OKX)
       │
       ├──▶ Tick数据 ──▶ Aggregator ──▶ K线数据
       │                                    │
       ├──▶ K线数据 ──────────────────────▶ │
       │                                    │
       └──▶ 行情数据                        │
                                            ▼
                                    KlineBuffer (内存缓存)
                                            │
                        ┌───────────────────┼───────────────────┐
                        │                   │                   │
                        ▼                   ▼                   ▼
                   Storage层          Indicator层          DataFeed层
                   (PostgreSQL)       (指标计算)          (数据输出)
                                            │
                                            ▼
                                    HTTP/WebSocket/gRPC
                                            │
                                            ▼
                                    客户端(策略/回测)


【核心服务实现】

// Service 行情服务（系统核心）
type Service struct {
    cfg    *config.Config
    log    *zap.Logger
    store  *storage.Storage
    
    // 核心组件
    exchanges   map[model.Exchange]exchange.Exchange
    aggregator  *kline.Aggregator
    klineBuffer *kline.KlineBuffer
    calculator  *indicator.Calculator
    klineRepo   *storage.KlineRepository
    
    // 订阅者列表
    tickSubscribers   []func(*model.Tick)
    klineSubscribers  []func(*model.Kline)
    
    stopCh chan struct{}
    mu     sync.RWMutex
}

// Start 启动服务
func (s *Service) Start(ctx context.Context) error {
    s.log.Info("启动行情服务...")
    
    // 创建交易所工厂
    factory := exchange.NewFactory(s.log)
    
    // 遍历配置，连接启用的交易所
    for _, exCfg := range s.cfg.Market.Exchanges {
        if !exCfg.Enabled {
            continue
        }
        
        // 创建交易所实例
        ex, err := factory.Create(exCfg)
        if err != nil {
            s.log.Error("创建交易所失败", zap.Error(err))
            continue
        }
        
        // 连接交易所
        if err := ex.Connect(ctx); err != nil {
            s.log.Error("连接交易所失败", zap.Error(err))
            continue
        }
        
        // 注册数据处理器
        s.registerHandlers(ex, exCfg.Symbols)
        
        s.exchanges[ex.Name()] = ex
    }
    
    // 启动后台任务
    go s.runScheduledTasks(ctx)
    
    return nil
}

// registerHandlers 注册数据处理器
func (s *Service) registerHandlers(ex exchange.Exchange, symbols []string) {
    ctx := context.Background()
    
    // 订阅Tick数据
    ex.SubscribeTick(ctx, symbols, func(tick *model.Tick) {
        s.onTick(tick)  // 调用处理方法
    })
    
    // 订阅K线数据
    ex.SubscribeKline(ctx, symbols, model.Timeframe1m, func(k *model.Kline) {
        s.onKline(k)
    })
}

// onTick Tick数据处理
func (s *Service) onTick(tick *model.Tick) {
    // 1. 聚合生成K线
    timeframes := s.parseTimeframes()  // [1m, 5m, 15m, 1h...]
    s.aggregator.ProcessTick(tick, timeframes)
    
    // 2. 通知所有订阅者
    s.mu.RLock()
    subscribers := s.tickSubscribers
    s.mu.RUnlock()
    
    for _, sub := range subscribers {
        go sub(tick)  // 异步调用，避免阻塞数据流
    }
}

// onKline K线数据处理
func (s *Service) onKline(k *model.Kline) {
    // 1. 添加到内存缓冲区
    s.klineBuffer.Add(k)
    
    // 2. 聚合生成高周期K线
    timeframes := s.parseTimeframes()
    s.aggregator.ProcessKline(k, timeframes)
    
    // 3. 如果K线已完成
    if k.IsClosed {
        // 保存到数据库（异步）
        go func() {
            ctx := context.Background()
            if err := s.klineRepo.Save(ctx, k); err != nil {
                s.log.Error("保存K线失败", zap.Error(err))
            }
        }()
        
        // 计算技术指标（异步）
        go s.calculator.Calculate(k.Exchange, k.Symbol, k.Timeframe)
    }
    
    // 4. 通知订阅者
    s.mu.RLock()
    subscribers := s.klineSubscribers
    s.mu.RUnlock()
    
    for _, sub := range subscribers {
        go sub(k)
    }
}

// SubscribeKline 订阅K线数据
// 其他模块调用此方法接收数据
func (s *Service) SubscribeKline(handler func(*model.Kline)) {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.klineSubscribers = append(s.klineSubscribers, handler)
}


【数据输出服务】

// DataFeed 统一的数据输出服务
// 支持回测和实盘两种模式
type DataFeed struct {
    cfg      *DataFeedConfig
    svc      *Service
    handlers []DataFeedHandler
    stopCh   chan struct{}
}

// 回测模式
func (f *DataFeed) startBacktest(ctx context.Context) error {
    go func() {
        // 获取历史数据
        klines, _ := f.svc.GetKlines(ctx, f.cfg.Exchange, f.cfg.Symbol, 
                                      f.cfg.Timeframe, f.cfg.StartTime, f.cfg.EndTime)
        
        // 按时间顺序回放
        for _, k := range klines {
            select {
            case <-ctx.Done():
                return
            default:
                // 构建数据点
                dp := &DataPoint{
                    Kline:      k,
                    Indicators: f.calculateIndicators(k),
                }
                
                // 通知订阅者
                for _, h := range f.handlers {
                    h(dp)
                }
                
                // 控制回放速度
                if f.cfg.Speed > 0 {
                    time.Sleep(time.Duration(1000/f.cfg.Speed) * time.Millisecond)
                }
            }
        }
    }()
    return nil
}

// 实盘模式
func (f *DataFeed) startLive(ctx context.Context) error {
    // 订阅实时数据
    f.svc.SubscribeKline(func(k *model.Kline) {
        // 过滤关注的交易对
        if k.Exchange != f.cfg.Exchange || k.Symbol != f.cfg.Symbol {
            return
        }
        
        dp := &DataPoint{
            Kline:      k,
            Indicators: f.calculateIndicators(k),
        }
        
        for _, h := range f.handlers {
            go h(dp)
        }
    })
    return nil
}
`)
}

// ============================================================================
// 主函数
// ============================================================================

func main() {
	fmt.Println("╔════════════════════════════════════════════════════════════════╗")
	fmt.Println("║             项目架构与核心代码详解                             ║")
	fmt.Println("╚════════════════════════════════════════════════════════════════╝")

	chapter1_project_structure()
	chapter2_data_models()
	chapter3_exchange_layer()
	chapter4_kline_aggregator()
	chapter5_indicators()
	chapter6_service_layer()

	fmt.Println("\n" + "═"*60)
	fmt.Println("架构总结:")
	fmt.Println("═"*60)
	fmt.Println(`
【分层职责】
1. Handler层：HTTP路由、请求验证、响应格式化
2. Service层：业务逻辑、数据流处理、订阅分发
3. Exchange层：交易所对接、协议转换、重连机制
4. Storage层：数据持久化、缓存管理

【设计模式】
1. 策略模式：Exchange接口，不同交易所实现
2. 工厂模式：创建交易所实例
3. 观察者模式：数据订阅机制
4. 仓库模式：数据访问抽象

【并发模型】
1. goroutine处理数据流
2. channel传递数据
3. 读写锁保护共享状态
4. context控制生命周期

下一步：阅读 04_deployment.go 了解部署
`)
}
