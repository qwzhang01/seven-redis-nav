/*
Package service 核心服务层

本包实现了行情处理系统的核心业务逻辑，是连接各组件的中枢。
它协调交易所连接、数据聚合、指标计算、数据存储等功能。

========== 架构设计 ==========

Service 采用组合模式，整合以下组件：
  - Exchange层：连接不同交易所，获取实时数据
  - Aggregator：K线聚合器，从Tick/低周期K线生成高周期K线
  - KlineBuffer：K线缓冲区，提供快速数据访问
  - Calculator：技术指标计算器
  - Repository：数据持久化层

数据流向：
	交易所 → WebSocket → Tick/K线 → 聚合器 → 缓冲区 → 指标计算
	                                    ↓
	                               数据库存储

========== 发布-订阅模式 ==========

Service 实现了简单的发布-订阅模式，允许外部组件订阅：
  - Tick数据（逐笔成交）
  - K线数据（各周期K线完成时）
  - Ticker数据（行情快照）

订阅者以回调函数形式注册，数据到达时异步通知。

========== 生命周期管理 ==========

1. 创建阶段（New）：
   - 初始化所有组件
   - 设置回调关系

2. 启动阶段（Start）：
   - 创建交易所连接
   - 注册数据处理器
   - 启动后台任务

3. 运行阶段：
   - 接收并处理实时数据
   - 执行定时任务

4. 停止阶段（Stop）：
   - 断开交易所连接
   - 刷新未完成K线
   - 清理资源

========== 使用示例 ==========

	// 创建服务
	svc := service.New(cfg, store, logger)

	// 订阅K线数据
	svc.SubscribeKline(func(k *model.Kline) {
	    fmt.Printf("K线: %s %s 收盘价=%s\n", k.Symbol, k.Timeframe, k.Close)
	})

	// 启动服务
	if err := svc.Start(ctx); err != nil {
	    log.Fatal(err)
	}

	// 查询历史数据
	klines, _ := svc.GetKlines(ctx, exchange, symbol, tf, start, end)

	// 获取指标
	indicators := svc.GetIndicators(exchange, symbol, tf)

	// 停止服务
	svc.Stop()

========== 并发安全 ==========

Service 的所有公开方法都是线程安全的：
  - 使用 sync.RWMutex 保护订阅者列表
  - 回调函数在独立goroutine中执行
  - 各组件内部自行保证线程安全
*/
package service

import (
	"context"
	"sync"
	"time"

	"go.uber.org/zap"

	"github.com/quant/go-market-service/internal/config"
	"github.com/quant/go-market-service/internal/exchange"
	"github.com/quant/go-market-service/internal/indicator"
	"github.com/quant/go-market-service/internal/kline"
	"github.com/quant/go-market-service/internal/model"
	"github.com/quant/go-market-service/internal/storage"
)

/*
Service 行情服务

核心服务结构体，整合所有组件，提供统一的对外接口。

主要职责：
 1. 管理交易所连接
 2. 协调数据流转
 3. 提供数据查询接口
 4. 管理订阅者通知

字段说明：
  - cfg: 全局配置
  - log: 日志记录器
  - store: 存储层（数据库连接）
  - exchanges: 已连接的交易所实例映射
  - aggregator: K线聚合器
  - klineBuffer: K线缓冲区
  - calculator: 指标计算器
  - klineRepo: K线数据仓库
  - xxxSubscribers: 各类型数据的订阅者列表
  - mu: 保护订阅者列表的读写锁
  - stopCh: 停止信号通道

设计模式：
  - 门面模式：对外提供简单统一的接口
  - 观察者模式：订阅-通知机制
  - 依赖注入：组件通过构造函数注入
*/
type Service struct {
	// ========== 基础配置 ==========

	// cfg 全局配置
	// 包含交易所配置、时间周期、数据保留策略等
	cfg *config.Config

	// log 日志记录器
	// 添加了 component=service 标签
	log *zap.Logger

	// store 存储层
	// 提供数据库和 Redis 连接
	store *storage.Storage

	// ========== 核心组件 ==========

	// exchanges 已连接的交易所
	// key: model.Exchange 枚举值
	// value: Exchange 接口实例
	exchanges map[model.Exchange]exchange.Exchange

	// aggregator K线聚合器
	// 从 Tick 或低周期K线生成高周期K线
	aggregator *kline.Aggregator

	// klineBuffer K线缓冲区
	// 缓存最近的K线数据，供指标计算使用
	klineBuffer *kline.KlineBuffer

	// calculator 技术指标计算器
	// 计算 SMA、RSI、MACD 等指标
	calculator *indicator.Calculator

	// klineRepo K线数据仓库
	// 负责K线的持久化和查询
	klineRepo *storage.KlineRepository

	// ========== 订阅者管理 ==========

	// tickSubscribers Tick数据订阅者
	// 每有新成交时调用所有订阅者
	tickSubscribers []func(*model.Tick)

	// klineSubscribers K线数据订阅者
	// 每有K线更新或完成时调用所有订阅者
	klineSubscribers []func(*model.Kline)

	// tickerSubscribers 行情数据订阅者
	// 每有行情快照更新时调用所有订阅者
	tickerSubscribers []func(*model.Ticker)

	// ========== 并发控制 ==========

	// mu 读写锁
	// 保护订阅者列表的并发访问
	mu sync.RWMutex

	// stopCh 停止信号通道
	// 用于通知后台任务退出
	stopCh chan struct{}
}

/*
New 创建行情服务实例

工厂函数，创建并初始化 Service 实例。

参数：
  - cfg: 全局配置
  - store: 存储层实例（已初始化的数据库连接）
  - log: zap日志记录器

返回：
  - 初始化完成的 Service 指针

初始化内容：
 1. K线缓冲区（默认500根）
 2. K线聚合器（设置完成回调）
 3. 技术指标计算器
 4. K线数据仓库

注意：
  - 此函数只初始化组件，不建立交易所连接
  - 需要调用 Start() 启动服务
*/
func New(cfg *config.Config, store *storage.Storage, log *zap.Logger) *Service {
	s := &Service{
		cfg:       cfg,
		log:       log.With(zap.String("component", "service")), // 添加组件标签
		store:     store,
		exchanges: make(map[model.Exchange]exchange.Exchange),
		stopCh:    make(chan struct{}),
	}

	// 初始化K线缓冲区（缓存最近500根K线）
	s.klineBuffer = kline.NewKlineBuffer(500)

	// 初始化K线聚合器
	// 设置回调：K线完成时调用 onKlineComplete
	s.aggregator = kline.NewAggregator(log, s.onKlineComplete)

	// 初始化指标计算器
	// 传入 klineBuffer 作为数据源
	s.calculator = indicator.NewCalculator(log, nil, s.klineBuffer)

	// 初始化K线仓库
	s.klineRepo = storage.NewKlineRepository(store)

	return s
}

/*
Start 启动行情服务

连接所有配置的交易所，注册数据处理器，启动后台任务。

参数：
  - ctx: 上下文，用于控制启动过程

返回：
  - 成功返回 nil
  - 失败返回错误（不会中断，会跳过失败的交易所）

执行流程：
 1. 遍历配置的交易所列表
 2. 跳过禁用的交易所
 3. 使用工厂创建交易所实例
 4. 建立 WebSocket 连接
 5. 注册数据处理器
 6. 启动定时任务（数据清理等）

错误处理：
  - 单个交易所失败不影响其他交易所
  - 错误被记录但不返回
*/
func (s *Service) Start(ctx context.Context) error {
	s.log.Info("正在启动行情服务...")

	// 创建交易所工厂
	factory := exchange.NewFactory(s.log)

	// 遍历配置的交易所
	for _, exCfg := range s.cfg.Market.Exchanges {
		// 跳过禁用的交易所
		if !exCfg.Enabled {
			continue
		}

		// 使用工厂创建交易所实例
		ex, err := factory.Create(exCfg)
		if err != nil {
			s.log.Error("创建交易所失败", zap.String("exchange", exCfg.Name), zap.Error(err))
			continue // 继续处理其他交易所
		}

		// 建立 WebSocket 连接
		if err := ex.Connect(ctx); err != nil {
			s.log.Error("连接交易所失败", zap.String("exchange", exCfg.Name), zap.Error(err))
			continue
		}

		// 注册数据处理器
		s.registerHandlers(ex, exCfg.Symbols)

		// 保存交易所实例
		s.exchanges[ex.Name()] = ex
		s.log.Info("交易所已连接", zap.String("exchange", exCfg.Name))
	}

	// 启动后台定时任务
	go s.runScheduledTasks(ctx)

	s.log.Info("行情服务已启动")
	return nil
}

/*
registerHandlers 注册数据处理器

为指定交易所注册 Tick、K线、Ticker 数据的处理回调。

参数：
  - ex: 交易所接口实例
  - symbols: 需要订阅的交易对列表

处理流程：
  - Tick数据 → onTick（聚合K线 + 通知订阅者）
  - K线数据 → onKline（缓存 + 聚合 + 存储 + 计算指标 + 通知）
  - Ticker数据 → onTicker（通知订阅者）

这是数据处理管道的入口点。
*/
func (s *Service) registerHandlers(ex exchange.Exchange, symbols []string) {
	ctx := context.Background()

	// 订阅 Tick（逐笔成交）
	ex.SubscribeTick(ctx, symbols, func(tick *model.Tick) {
		s.onTick(tick)
	})

	// 订阅 K线（1分钟作为基础周期）
	ex.SubscribeKline(ctx, symbols, model.Timeframe1m, func(k *model.Kline) {
		s.onKline(k)
	})

	// 订阅 Ticker（行情快照）
	ex.SubscribeTicker(ctx, symbols, func(ticker *model.Ticker) {
		s.onTicker(ticker)
	})
}

/*
onTick 处理逐笔成交数据

内部方法，处理从交易所收到的每笔成交数据。

参数：
  - tick: 成交数据

处理流程：
 1. 将 Tick 传给聚合器，生成/更新 K线
 2. 异步通知所有 Tick 订阅者

技术细节：
  - 聚合器根据配置的时间周期生成多周期K线
  - 订阅者回调在独立goroutine中执行，避免阻塞
*/
func (s *Service) onTick(tick *model.Tick) {
	// 获取配置的时间周期列表
	timeframes := s.parseTimeframes()

	// 将 Tick 传给聚合器处理
	s.aggregator.ProcessTick(tick, timeframes)

	// 获取订阅者列表（读锁保护）
	s.mu.RLock()
	subscribers := s.tickSubscribers
	s.mu.RUnlock()

	// 异步通知所有订阅者
	for _, sub := range subscribers {
		go sub(tick) // 在独立goroutine中执行，避免阻塞
	}
}

/*
onKline 处理K线数据

内部方法，处理从交易所收到的K线数据。

参数：
  - k: K线数据

处理流程：
 1. 添加到缓冲区（供指标计算使用）
 2. 传给聚合器生成高周期K线
 3. 如果K线已完成：
    - 异步保存到数据库
    - 异步计算技术指标
 4. 通知所有订阅者

K线状态：
  - IsClosed=false: K线仍在形成中，只更新缓冲区和通知订阅者
  - IsClosed=true: K线已完成，额外执行存储和指标计算
*/
func (s *Service) onKline(k *model.Kline) {
	// 添加到缓冲区
	s.klineBuffer.Add(k)

	// 聚合生成高周期K线
	timeframes := s.parseTimeframes()
	s.aggregator.ProcessKline(k, timeframes)

	// 如果K线已完成，执行持久化和计算
	if k.IsClosed {
		// 异步保存到数据库
		go func() {
			ctx := context.Background()
			if err := s.klineRepo.Save(ctx, k); err != nil {
				s.log.Error("保存K线失败", zap.Error(err))
			}
		}()

		// 异步计算技术指标
		go s.calculator.Calculate(k.Exchange, k.Symbol, k.Timeframe)
	}

	// 通知所有订阅者
	s.mu.RLock()
	subscribers := s.klineSubscribers
	s.mu.RUnlock()

	for _, sub := range subscribers {
		go sub(k)
	}
}

/*
onKlineComplete 聚合器K线完成回调

当聚合器完成一根高周期K线时调用。
这是从 Tick 或低周期K线聚合出的K线。

参数：
  - k: 已完成的K线

处理流程：
 1. 添加到缓冲区
 2. 异步保存到数据库
 3. 异步计算技术指标
 4. 通知所有订阅者

与 onKline 的区别：
  - onKline: 处理交易所直接推送的K线
  - onKlineComplete: 处理本地聚合生成的K线
  - 两者最终处理逻辑相似
*/
func (s *Service) onKlineComplete(k *model.Kline) {
	// 添加到缓冲区
	s.klineBuffer.Add(k)

	// 异步保存到数据库
	go func() {
		ctx := context.Background()
		if err := s.klineRepo.Save(ctx, k); err != nil {
			s.log.Error("保存聚合K线失败", zap.Error(err))
		}
	}()

	// 异步计算技术指标
	go s.calculator.Calculate(k.Exchange, k.Symbol, k.Timeframe)

	// 通知所有订阅者
	s.mu.RLock()
	subscribers := s.klineSubscribers
	s.mu.RUnlock()

	for _, sub := range subscribers {
		go sub(k)
	}
}

/*
onTicker 处理行情快照数据

内部方法，处理从交易所收到的行情数据。

参数：
  - ticker: 行情快照数据

处理流程：
  - 异步通知所有订阅者

行情数据通常用于：
  - 显示实时价格
  - 计算涨跌幅
  - 触发价格预警
*/
func (s *Service) onTicker(ticker *model.Ticker) {
	// 获取订阅者列表
	s.mu.RLock()
	subscribers := s.tickerSubscribers
	s.mu.RUnlock()

	// 异步通知所有订阅者
	for _, sub := range subscribers {
		go sub(ticker)
	}
}

/*
parseTimeframes 解析时间周期配置

从配置文件解析需要处理的时间周期列表。

返回：
  - 时间周期切片

配置示例（config.yaml）：
	market:
	  timeframes:
	    - 1m
	    - 5m
	    - 15m
	    - 1h
	    - 4h
	    - 1d
*/
func (s *Service) parseTimeframes() []model.Timeframe {
	tfs := make([]model.Timeframe, len(s.cfg.Market.Timeframes))
	for i, tf := range s.cfg.Market.Timeframes {
		tfs[i] = model.Timeframe(tf) // 字符串转枚举类型
	}
	return tfs
}

/*
runScheduledTasks 运行后台定时任务

在后台goroutine中运行定时任务。

当前任务：
  - 每小时清理过期K线数据

参数：
  - ctx: 上下文，用于接收取消信号

退出条件：
  - context 被取消
  - stopCh 被关闭
*/
func (s *Service) runScheduledTasks(ctx context.Context) {
	// 创建1小时定时器
	cleanupTicker := time.NewTicker(time.Hour)
	defer cleanupTicker.Stop()

	for {
		select {
		case <-ctx.Done():
			// context 被取消
			return
		case <-s.stopCh:
			// 收到停止信号
			return
		case <-cleanupTicker.C:
			// 执行定时清理
			// 删除超过保留期限的旧K线数据
			s.klineRepo.DeleteOldKlines(ctx, s.cfg.Market.RetentionDays)
		}
	}
}

/*
Stop 停止行情服务

优雅地关闭服务，释放所有资源。

执行流程：
 1. 关闭 stopCh 通知后台任务退出
 2. 断开所有交易所连接
 3. 刷新聚合器中未完成的K线

调用时机：
  - 程序收到终止信号（SIGTERM/SIGINT）
  - 需要重启服务时

注意：
  - 应确保调用此方法后不再使用 Service 实例
  - 此方法是阻塞的，会等待所有资源释放完成
*/
func (s *Service) Stop() {
	s.log.Info("正在停止行情服务...")

	// 关闭停止通道，通知所有后台任务
	close(s.stopCh)

	// 断开所有交易所连接
	for name, ex := range s.exchanges {
		if err := ex.Disconnect(); err != nil {
			s.log.Error("断开交易所失败", zap.String("exchange", string(name)), zap.Error(err))
		}
	}

	// 刷新聚合器，保存所有未完成的K线
	s.aggregator.FlushAll()

	s.log.Info("行情服务已停止")
}

// ==================== 订阅接口 ====================

/*
SubscribeTick 订阅Tick数据

注册逐笔成交数据的回调处理函数。

参数：
  - handler: 回调函数，每有新成交时被调用

使用示例：
	service.SubscribeTick(func(tick *model.Tick) {
	    fmt.Printf("成交: %s 价格=%s 数量=%s\n",
	        tick.Symbol, tick.Price, tick.Quantity)
	})

注意：
  - handler 在独立goroutine中执行
  - 应避免在 handler 中执行耗时操作
*/
func (s *Service) SubscribeTick(handler func(*model.Tick)) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.tickSubscribers = append(s.tickSubscribers, handler)
}

/*
SubscribeKline 订阅K线数据

注册K线数据的回调处理函数。

参数：
  - handler: 回调函数，K线更新或完成时被调用

使用示例：
	service.SubscribeKline(func(k *model.Kline) {
	    if k.IsClosed {
	        fmt.Printf("K线完成: %s %s 收盘=%s\n",
	            k.Symbol, k.Timeframe, k.Close)
	    }
	})

注意：
  - 会收到所有周期的K线更新
  - 通过 IsClosed 字段判断K线是否完成
*/
func (s *Service) SubscribeKline(handler func(*model.Kline)) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.klineSubscribers = append(s.klineSubscribers, handler)
}

/*
SubscribeTicker 订阅行情数据

注册行情快照的回调处理函数。

参数：
  - handler: 回调函数，行情更新时被调用

使用示例：
	service.SubscribeTicker(func(t *model.Ticker) {
	    fmt.Printf("行情: %s 最新价=%s 24h成交量=%s\n",
	        t.Symbol, t.LastPrice, t.Volume24h)
	})
*/
func (s *Service) SubscribeTicker(handler func(*model.Ticker)) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.tickerSubscribers = append(s.tickerSubscribers, handler)
}

// ==================== 数据查询接口 ====================

/*
GetKlines 获取历史K线数据

查询指定时间范围内的K线数据。

参数：
  - ctx: 上下文
  - exchange: 交易所
  - symbol: 交易对
  - tf: 时间周期
  - start: 开始时间
  - end: 结束时间

返回：
  - K线数据切片
  - 发生错误时返回错误

数据来源：
  - 从 TimescaleDB 数据库查询

使用示例：
	klines, err := service.GetKlines(ctx,
	    model.ExchangeBinance, "BTCUSDT", model.Timeframe1h,
	    time.Now().Add(-24*time.Hour), time.Now())
*/
func (s *Service) GetKlines(ctx context.Context, exchange model.Exchange, symbol string, tf model.Timeframe, start, end time.Time) ([]*model.Kline, error) {
	return s.klineRepo.GetKlines(ctx, exchange, symbol, tf, start, end, 0)
}

/*
GetRecentKlines 获取最近K线数据

获取最近N根K线，无需指定时间范围。

参数：
  - ctx: 上下文
  - exchange: 交易所
  - symbol: 交易对
  - tf: 时间周期
  - count: 获取数量

返回：
  - K线数据切片（按时间正序）
  - 发生错误时返回错误

使用场景：
  - 初始化图表时获取历史数据
  - 策略回测需要历史数据
*/
func (s *Service) GetRecentKlines(ctx context.Context, exchange model.Exchange, symbol string, tf model.Timeframe, count int) ([]*model.Kline, error) {
	return s.klineRepo.GetRecentKlines(ctx, exchange, symbol, tf, count)
}

/*
GetIndicators 获取技术指标

计算并返回指定K线的技术指标值。

参数：
  - exchange: 交易所
  - symbol: 交易对
  - tf: 时间周期

返回：
  - CalculatorResult 包含所有计算完成的指标

计算的指标包括：
  - SMA（简单移动平均线）
  - EMA（指数移动平均线）
  - RSI（相对强弱指标）
  - MACD（移动平均收敛/发散指标）
  - 布林带
  - ATR（平均真实波幅）
  - 等...

使用示例：
	result := service.GetIndicators(exchange, symbol, tf)
	fmt.Printf("RSI(14)=%v, MACD=%v\n", result.RSI, result.MACD)
*/
func (s *Service) GetIndicators(exchange model.Exchange, symbol string, tf model.Timeframe) *indicator.CalculatorResult {
	return s.calculator.Calculate(exchange, symbol, tf)
}

/*
GetKlineBuffer 获取K线缓冲区

返回内部的K线缓冲区实例，用于直接访问内存中的K线数据。

返回：
  - KlineBuffer 指针

使用场景：
  - 需要快速访问最近K线（无需查询数据库）
  - 自定义指标计算
  - 数据分析和调试

注意：
  - 返回的是内部实例，不是副本
  - 应只读使用，不要修改其状态
*/
func (s *Service) GetKlineBuffer() *kline.KlineBuffer {
	return s.klineBuffer
}

/*
GetExchange 获取交易所实例

根据名称获取已连接的交易所实例。

参数：
  - name: 交易所名称枚举值

返回：
  - exchange.Exchange 接口实例
  - bool 表示是否找到

使用场景：
  - 需要直接调用交易所API
  - 获取交易所特定信息

使用示例：
	if ex, ok := service.GetExchange(model.ExchangeBinance); ok {
	    ticker, _ := ex.GetTicker(ctx, "BTCUSDT")
	    fmt.Println(ticker.LastPrice)
	}
*/
func (s *Service) GetExchange(name model.Exchange) (exchange.Exchange, bool) {
	ex, ok := s.exchanges[name]
	return ex, ok
}
