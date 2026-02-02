/*
Package kline K线聚合器

本包提供K线（蜡烛图）数据的聚合功能，是量化交易系统中行情数据处理的核心组件。

========== 主要功能 ==========

1. Tick到K线聚合：
   - 将逐笔成交数据（Tick）实时聚合为不同时间周期的K线
   - 支持 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w 等周期

2. K线到K线聚合：
   - 将低周期K线（如1分钟）聚合为高周期K线（如1小时）
   - 提高数据效率，减少存储和计算压力

3. K线缓冲区：
   - 维护最近N根K线的内存缓存
   - 为技术指标计算提供快速数据访问

========== 设计思想 ==========

1. 时间对齐：
   - 所有K线严格按照时间周期对齐
   - 例如5分钟K线总是在 00, 05, 10, 15... 分钟开盘

2. 实时更新：
   - K线在周期内持续更新（高、低、收盘价）
   - 周期结束时标记为已完成（IsClosed=true）

3. 回调机制：
   - K线完成时触发回调函数
   - 支持存储、指标计算、推送等后续处理

========== K线聚合原理 ==========

从Tick聚合：
  1. 第一笔成交 → 设置 Open=High=Low=Close=Price
  2. 后续成交 → 更新 High=max(High,Price), Low=min(Low,Price), Close=Price
  3. 累加成交量
  4. 时间跨越周期边界 → 完成旧K线，创建新K线

从低周期K线聚合：
  1. 第一根子K线 → 复制 OHLCV
  2. 后续子K线 → 合并 High=max, Low=min, Close=最新, Volume=累加
  3. 最后一根子K线完成 → 高周期K线完成

========== 使用示例 ==========

	// 创建聚合器，设置完成回调
	aggregator := kline.NewAggregator(logger, func(k *model.Kline) {
	    // K线完成后的处理：保存、计算指标等
	    repository.Save(k)
	    calculator.Calculate(k)
	})

	// 处理Tick数据
	aggregator.ProcessTick(tick, []model.Timeframe{
	    model.Timeframe1m,
	    model.Timeframe5m,
	    model.Timeframe1h,
	})

	// 从1分钟K线聚合高周期
	aggregator.ProcessKline(kline1m, []model.Timeframe{
	    model.Timeframe5m,
	    model.Timeframe15m,
	    model.Timeframe1h,
	})

========== 参考资料 ==========

- K线图理论：https://www.investopedia.com/terms/c/candlestick.asp
- 时间序列数据处理：https://www.timescale.com/
*/
package kline

import (
	"sync"
	"time"

	"github.com/shopspring/decimal"
	"go.uber.org/zap"

	"github.com/quant/go-market-service/internal/model"
)

/*
Aggregator K线聚合器

从Tick数据或低周期K线聚合生成高周期K线。
这是行情数据处理管道中的核心组件。

核心职责：
  - 维护每个交易对每个周期的"正在构建"K线
  - 接收新数据时更新K线状态
  - 检测周期跨越，完成旧K线，创建新K线
  - 触发回调通知下游组件

字段说明：
  - log: 日志记录器，用于调试和错误追踪
  - mu: 读写锁，保护 building map 的并发访问
  - building: 正在构建的K线映射，key格式为 "exchange:symbol:timeframe"
  - onComplete: K线完成时的回调函数

线程安全：
  - 所有公开方法都是线程安全的
  - 回调函数在新goroutine中调用，避免阻塞聚合流程

性能考虑：
  - building map 的 key 使用字符串拼接，简单高效
  - 回调异步执行，不影响主流程性能
*/
type Aggregator struct {
	// log 日志记录器
	// 添加了 component=kline_aggregator 标签
	log *zap.Logger

	// mu 读写锁
	// 保护 building map 的并发访问
	// 读操作（获取K线）使用 RLock
	// 写操作（更新K线）使用 Lock
	mu sync.RWMutex

	// building 正在构建的K线映射
	// key格式: "exchange:symbol:timeframe"
	// 例如: "binance:BTCUSDT:1m"
	// 每个key对应一根未完成的K线
	building map[string]*model.Kline

	// onComplete K线完成回调
	// 当一根K线周期结束时调用
	// 典型用途：保存到数据库、计算指标、推送给客户端
	onComplete func(kline *model.Kline)
}

/*
NewAggregator 创建K线聚合器

工厂函数，创建并初始化 Aggregator 实例。

参数：
  - log: zap日志记录器
  - onComplete: K线完成时的回调函数（可以为nil）

返回：
  - 初始化完成的 Aggregator 指针

使用示例：
	agg := NewAggregator(logger, func(k *model.Kline) {
	    fmt.Printf("K线完成: %s %s %s\n", k.Symbol, k.Timeframe, k.Close)
	})
*/
func NewAggregator(log *zap.Logger, onComplete func(kline *model.Kline)) *Aggregator {
	return &Aggregator{
		log:        log.With(zap.String("component", "kline_aggregator")),
		building:   make(map[string]*model.Kline),
		onComplete: onComplete,
	}
}

/*
makeKey 生成K线唯一标识

内部辅助函数，生成 building map 的 key。

格式：
  - "exchange:symbol:timeframe"
  - 例如: "binance:BTCUSDT:1m"

参数：
  - exchange: 交易所标识
  - symbol: 交易对
  - tf: 时间周期

返回：
  - 拼接后的字符串key

设计考虑：
  - 使用冒号分隔，清晰易读
  - 字符串拼接比 fmt.Sprintf 性能更好
*/
func makeKey(exchange model.Exchange, symbol string, tf model.Timeframe) string {
	return string(exchange) + ":" + symbol + ":" + string(tf)
}

/*
ProcessTick 处理Tick数据，实时聚合为K线

核心方法，将每一笔成交数据聚合到对应的K线中。

参数：
  - tick: 逐笔成交数据
  - timeframes: 需要聚合的时间周期列表

执行流程：
 1. 遍历所有目标周期
 2. 获取或创建该周期的K线
 3. 检查是否跨越周期边界
 4. 更新K线数据（OHLCV）

周期跨越处理：
  - 标记旧K线为已完成
  - 触发完成回调
  - 创建新周期的K线

K线更新规则：
  - High = max(当前High, 成交价)
  - Low = min(当前Low, 成交价)
  - Close = 最新成交价
  - Volume = 累加成交量
  - TradeCount = 累加成交笔数

使用示例：
	// 处理一笔成交，聚合到1分钟和5分钟K线
	aggregator.ProcessTick(tick, []model.Timeframe{
	    model.Timeframe1m,
	    model.Timeframe5m,
	})

线程安全：
  - 内部使用互斥锁保护，可并发调用
*/
func (a *Aggregator) ProcessTick(tick *model.Tick, timeframes []model.Timeframe) {
	a.mu.Lock()
	defer a.mu.Unlock()

	// 为每个目标周期聚合K线
	for _, tf := range timeframes {
		key := makeKey(tick.Exchange, tick.Symbol, tf)
		kline := a.building[key]

		// 计算当前Tick应该属于哪根K线（开盘时间）
		openTime := a.calculateOpenTime(tick.Timestamp, tf)

		// 检查是否需要创建新K线（新周期或首次）
		if kline == nil || !kline.OpenTime.Equal(openTime) {
			// 完成旧K线（如果存在且未完成）
			if kline != nil && kline.IsClosed == false {
				kline.IsClosed = true
				if a.onComplete != nil {
					go a.onComplete(kline) // 异步回调，避免阻塞
				}
			}

			// 创建新K线
			// 第一笔成交设置所有价格为成交价
			kline = &model.Kline{
				Exchange:   tick.Exchange,
				Symbol:     tick.Symbol,
				Timeframe:  tf,
				OpenTime:   openTime,
				CloseTime:  openTime.Add(tf.Duration()), // 收盘时间 = 开盘时间 + 周期
				Open:       tick.Price,                  // 开盘价 = 第一笔成交价
				High:       tick.Price,                  // 最高价初始化
				Low:        tick.Price,                  // 最低价初始化
				Close:      tick.Price,                  // 收盘价
				Volume:     tick.Quantity,               // 成交量
				TradeCount: 1,                           // 成交笔数
				IsClosed:   false,                       // 未完成
			}
			a.building[key] = kline
		} else {
			// 更新现有K线
			// 更新最高价
			if tick.Price.GreaterThan(kline.High) {
				kline.High = tick.Price
			}
			// 更新最低价
			if tick.Price.LessThan(kline.Low) {
				kline.Low = tick.Price
			}
			// 更新收盘价（总是最新成交价）
			kline.Close = tick.Price
			// 累加成交量
			kline.Volume = kline.Volume.Add(tick.Quantity)
			// 累加成交笔数
			kline.TradeCount++
		}
	}
}

/*
ProcessKline 处理低周期K线，聚合生成高周期K线

从低周期K线（如1分钟）聚合生成高周期K线（如1小时）。
这种方式比从Tick聚合更高效，适合处理大量历史数据。

参数：
  - sourceKline: 源K线（低周期）
  - targetTimeframes: 目标周期列表（高周期）

执行流程：
 1. 遍历目标周期
 2. 跳过相同或更低的周期
 3. 获取或创建目标周期K线
 4. 合并源K线数据

合并规则：
  - Open = 第一根子K线的开盘价
  - High = 所有子K线最高价的最大值
  - Low = 所有子K线最低价的最小值
  - Close = 最后一根子K线的收盘价
  - Volume = 所有子K线成交量之和

完成条件：
  - 源K线已完成（IsClosed=true）
  - 当前时间已超过目标K线收盘时间

使用示例：
	// 将1分钟K线聚合到5分钟、15分钟、1小时
	aggregator.ProcessKline(kline1m, []model.Timeframe{
	    model.Timeframe5m,
	    model.Timeframe15m,
	    model.Timeframe1h,
	})

注意事项：
  - sourceKline 必须是低于目标周期的K线
  - 相同周期或更高周期会被自动跳过
*/
func (a *Aggregator) ProcessKline(sourceKline *model.Kline, targetTimeframes []model.Timeframe) {
	a.mu.Lock()
	defer a.mu.Unlock()

	for _, tf := range targetTimeframes {
		// 跳过相同或更小周期（只能从低周期聚合到高周期）
		if tf.Duration() <= sourceKline.Timeframe.Duration() {
			continue
		}

		key := makeKey(sourceKline.Exchange, sourceKline.Symbol, tf)
		kline := a.building[key]

		// 计算目标周期的开盘时间
		openTime := a.calculateOpenTime(sourceKline.OpenTime, tf)

		// 检查是否需要创建新K线
		if kline == nil || !kline.OpenTime.Equal(openTime) {
			// 完成旧K线
			if kline != nil {
				kline.IsClosed = true
				if a.onComplete != nil {
					go a.onComplete(kline)
				}
			}

			// 创建新K线（使用源K线的数据初始化）
			kline = &model.Kline{
				Exchange:    sourceKline.Exchange,
				Symbol:      sourceKline.Symbol,
				Timeframe:   tf,
				OpenTime:    openTime,
				CloseTime:   openTime.Add(tf.Duration()),
				Open:        sourceKline.Open,        // 使用第一根子K线的开盘价
				High:        sourceKline.High,
				Low:         sourceKline.Low,
				Close:       sourceKline.Close,
				Volume:      sourceKline.Volume,
				QuoteVolume: sourceKline.QuoteVolume,
				TradeCount:  sourceKline.TradeCount,
				IsClosed:    false,
			}
			a.building[key] = kline
		} else {
			// 合并K线数据
			// 更新最高价
			if sourceKline.High.GreaterThan(kline.High) {
				kline.High = sourceKline.High
			}
			// 更新最低价
			if sourceKline.Low.LessThan(kline.Low) {
				kline.Low = sourceKline.Low
			}
			// 更新收盘价（总是使用最新子K线的收盘价）
			kline.Close = sourceKline.Close
			// 累加成交量
			kline.Volume = kline.Volume.Add(sourceKline.Volume)
			kline.QuoteVolume = kline.QuoteVolume.Add(sourceKline.QuoteVolume)
			// 累加成交笔数
			kline.TradeCount += sourceKline.TradeCount
		}

		// 检查是否应该收盘
		// 条件：源K线已完成 且 当前时间已超过目标K线收盘时间
		if sourceKline.IsClosed && time.Now().After(kline.CloseTime) {
			kline.IsClosed = true
			if a.onComplete != nil {
				go a.onComplete(kline)
			}
		}
	}
}

/*
calculateOpenTime 计算K线开盘时间

根据给定时间戳和周期，计算该时间所属K线的开盘时间。
这是K线聚合的核心算法，确保所有K线严格对齐到标准时间点。

参数：
  - ts: 任意时间戳
  - tf: 目标时间周期

返回：
  - 对齐后的开盘时间

对齐规则：

  - 1分钟: 对齐到分钟边界
    例如 10:23:45 -> 10:23:00

  - 5分钟: 对齐到5的倍数分钟
    例如 10:23:45 -> 10:20:00

  - 15分钟: 对齐到15的倍数分钟
    例如 10:23:45 -> 10:15:00

  - 30分钟: 对齐到30的倍数分钟
    例如 10:23:45 -> 10:00:00

  - 1小时: 对齐到小时边界
    例如 10:23:45 -> 10:00:00

  - 4小时: 对齐到4的倍数小时
    例如 10:23:45 -> 08:00:00（因为 10/4*4=8）

  - 1天: 对齐到 UTC 00:00:00
    例如 2025-01-15 10:23:45 -> 2025-01-15 00:00:00 UTC

  - 1周: 对齐到周一 UTC 00:00:00
    例如 2025-01-15 (周三) -> 2025-01-13 00:00:00 UTC

特殊处理：
  - 日K线和周K线使用 UTC 时区，保证全球一致性
  - 周K线考虑 Go 语言中 Weekday() 返回 0 代表周日的情况

使用示例：
	// 计算某笔成交属于哪根5分钟K线
	openTime := aggregator.calculateOpenTime(trade.Timestamp, model.Timeframe5m)
*/
func (a *Aggregator) calculateOpenTime(ts time.Time, tf model.Timeframe) time.Time {
	duration := tf.Duration()

	switch tf {
	case model.Timeframe1m:
		// 1分钟：截断到分钟
		return ts.Truncate(time.Minute)

	case model.Timeframe5m:
		// 5分钟：截断到5分钟边界
		return ts.Truncate(5 * time.Minute)

	case model.Timeframe15m:
		// 15分钟：截断到15分钟边界
		return ts.Truncate(15 * time.Minute)

	case model.Timeframe30m:
		// 30分钟：截断到30分钟边界
		return ts.Truncate(30 * time.Minute)

	case model.Timeframe1h:
		// 1小时：截断到小时边界
		return ts.Truncate(time.Hour)

	case model.Timeframe4h:
		// 4小时：对齐到4小时边界
		// 例如：0-3点 -> 0点，4-7点 -> 4点，8-11点 -> 8点
		hour := ts.Hour()
		alignedHour := (hour / 4) * 4 // 整除后乘回来
		return time.Date(ts.Year(), ts.Month(), ts.Day(), alignedHour, 0, 0, 0, ts.Location())

	case model.Timeframe1d:
		// 日K线：对齐到 UTC 00:00:00
		// 使用 UTC 时区保证全球一致性
		return time.Date(ts.Year(), ts.Month(), ts.Day(), 0, 0, 0, 0, time.UTC)

	case model.Timeframe1w:
		// 周K线：对齐到周一 UTC 00:00:00
		// Go 的 Weekday(): Sunday=0, Monday=1, ..., Saturday=6
		weekday := int(ts.Weekday())
		if weekday == 0 {
			weekday = 7 // 将周日从0改为7，方便计算
		}
		// 计算距离本周一的天数
		monday := ts.AddDate(0, 0, -(weekday - 1))
		return time.Date(monday.Year(), monday.Month(), monday.Day(), 0, 0, 0, 0, time.UTC)

	default:
		// 其他周期：使用通用截断
		return ts.Truncate(duration)
	}
}

/*
GetBuildingKline 获取正在构建的K线

获取指定交易对和周期当前正在构建（未完成）的K线。

参数：
  - exchange: 交易所
  - symbol: 交易对
  - tf: 时间周期

返回：
  - K线指针（返回副本，防止外部修改）
  - 如果不存在返回 nil

用途：
  - 查看实时K线状态
  - 调试和监控
  - 向客户端推送实时K线

注意：
  - 返回的是副本，修改不会影响内部状态
  - 使用读锁，允许并发调用
*/
func (a *Aggregator) GetBuildingKline(exchange model.Exchange, symbol string, tf model.Timeframe) *model.Kline {
	a.mu.RLock()
	defer a.mu.RUnlock()

	key := makeKey(exchange, symbol, tf)
	if kline, exists := a.building[key]; exists {
		// 返回副本，防止外部修改内部状态
		copy := *kline
		return &copy
	}
	return nil
}

/*
FlushAll 强制完成所有构建中的K线

立即标记所有正在构建的K线为已完成，并触发回调。
通常在服务关闭或需要立即持久化数据时调用。

执行流程：
 1. 遍历所有构建中的K线
 2. 标记为已完成
 3. 触发完成回调
 4. 从 building map 中删除

注意：
  - 这是同步操作，回调在当前goroutine执行
  - 调用后 building map 将被清空
  - 适用于优雅关闭场景
*/
func (a *Aggregator) FlushAll() {
	a.mu.Lock()
	defer a.mu.Unlock()

	for key, kline := range a.building {
		if !kline.IsClosed {
			kline.IsClosed = true
			if a.onComplete != nil {
				// 注意：这里是同步调用，确保数据持久化完成
				a.onComplete(kline)
			}
		}
		delete(a.building, key)
	}
}

/*
KlineBuffer K线缓冲区

维护每个交易对每个周期最近N根K线的内存缓存。
为技术指标计算提供快速的数据访问。

设计目的：
  - 避免频繁查询数据库
  - 为指标计算提供连续的K线序列
  - 支持实时数据推送

核心特性：
  - 固定大小缓冲区（FIFO，先进先出）
  - 线程安全（使用读写锁）
  - 按 exchange:symbol:timeframe 分组存储

字段说明：
  - mu: 读写锁，保护并发访问
  - size: 缓冲区大小（每组最多保存多少根K线）
  - buffers: K线缓冲区映射，key格式同 Aggregator

内存占用估算：
  - 假设每根K线约 200 字节
  - 每个交易对每个周期 500 根 = 100KB
  - 10个交易对 * 5个周期 = 5MB

使用场景：
  - 计算 RSI、MACD 等需要历史数据的指标
  - 通过 WebSocket 推送最近K线给客户端
  - 策略回测时快速获取数据
*/
type KlineBuffer struct {
	// mu 读写锁
	mu sync.RWMutex

	// size 缓冲区大小
	// 每组（exchange:symbol:timeframe）最多保存的K线数量
	size int

	// buffers K线缓冲区映射
	// key: exchange:symbol:timeframe
	// value: K线切片，按时间顺序排列（旧在前，新在后）
	buffers map[string][]*model.Kline
}

/*
NewKlineBuffer 创建K线缓冲区

工厂函数，创建指定大小的K线缓冲区。

参数：
  - size: 每组最多保存的K线数量

返回：
  - 初始化完成的 KlineBuffer 指针

使用示例：
	// 创建缓冲区，每组保存最近500根K线
	buffer := kline.NewKlineBuffer(500)
*/
func NewKlineBuffer(size int) *KlineBuffer {
	return &KlineBuffer{
		size:    size,
		buffers: make(map[string][]*model.Kline),
	}
}

/*
Add 添加K线到缓冲区

将新K线添加到对应的缓冲区，自动维护缓冲区大小。

参数：
  - kline: 要添加的K线

执行流程：
 1. 获取对应的缓冲区（不存在则创建）
 2. 将K线追加到末尾
 3. 如果超出大小限制，移除最旧的K线

注意：
  - 不检查K线是否重复，调用方应确保数据正确性
  - K线应按时间顺序添加
*/
func (b *KlineBuffer) Add(kline *model.Kline) {
	b.mu.Lock()
	defer b.mu.Unlock()

	key := makeKey(kline.Exchange, kline.Symbol, kline.Timeframe)
	buf := b.buffers[key]

	// 添加到缓冲区末尾
	buf = append(buf, kline)

	// 如果超出大小限制，移除最旧的（保留最新的 size 根）
	if len(buf) > b.size {
		buf = buf[len(buf)-b.size:]
	}

	b.buffers[key] = buf
}

/*
Get 获取K线列表

获取指定交易对和周期的最近N根K线。

参数：
  - exchange: 交易所
  - symbol: 交易对
  - tf: 时间周期
  - limit: 获取数量（0或负数表示获取全部）

返回：
  - K线指针切片，按时间顺序排列（旧在前，新在后）
  - 如果不存在返回 nil

使用示例：
	// 获取最近20根1小时K线
	klines := buffer.Get(model.ExchangeBinance, "BTCUSDT", model.Timeframe1h, 20)
*/
func (b *KlineBuffer) Get(exchange model.Exchange, symbol string, tf model.Timeframe, limit int) []*model.Kline {
	b.mu.RLock()
	defer b.mu.RUnlock()

	key := makeKey(exchange, symbol, tf)
	buf := b.buffers[key]

	if len(buf) == 0 {
		return nil
	}

	// 处理 limit 参数
	if limit <= 0 || limit > len(buf) {
		limit = len(buf)
	}

	// 返回最近的 limit 根K线（从缓冲区末尾截取）
	result := make([]*model.Kline, limit)
	copy(result, buf[len(buf)-limit:])
	return result
}

/*
GetLatest 获取最新K线

获取指定交易对和周期的最新一根K线。

参数：
  - exchange: 交易所
  - symbol: 交易对
  - tf: 时间周期

返回：
  - 最新K线指针
  - 如果不存在返回 nil

这是 Get(exchange, symbol, tf, 1) 的便捷方法。
*/
func (b *KlineBuffer) GetLatest(exchange model.Exchange, symbol string, tf model.Timeframe) *model.Kline {
	klines := b.Get(exchange, symbol, tf, 1)
	if len(klines) > 0 {
		return klines[0]
	}
	return nil
}

/*
GetPrices 获取收盘价序列

获取指定交易对和周期的收盘价序列，用于技术指标计算。

参数：
  - exchange: 交易所
  - symbol: 交易对
  - tf: 时间周期
  - limit: 获取数量

返回：
  - 收盘价序列（decimal.Decimal 切片）
  - 按时间顺序排列（旧在前，新在后）

用途：
  - 计算 SMA、EMA 等基于收盘价的指标
  - 绘制价格曲线图

使用示例：
	prices := buffer.GetPrices(exchange, symbol, tf, 20)
	sma := indicator.SMA(prices, 20)
*/
func (b *KlineBuffer) GetPrices(exchange model.Exchange, symbol string, tf model.Timeframe, limit int) []decimal.Decimal {
	klines := b.Get(exchange, symbol, tf, limit)
	prices := make([]decimal.Decimal, len(klines))
	for i, k := range klines {
		prices[i] = k.Close
	}
	return prices
}

/*
GetOHLCV 获取完整OHLCV数据

获取指定交易对和周期的完整OHLCV（开高低收量）数据序列。

参数：
  - exchange: 交易所
  - symbol: 交易对
  - tf: 时间周期
  - limit: 获取数量

返回（5个切片，长度相同）：
  - opens: 开盘价序列
  - highs: 最高价序列
  - lows: 最低价序列
  - closes: 收盘价序列
  - volumes: 成交量序列

用途：
  - 计算布林带、ATR等需要多个价格字段的指标
  - 计算 OBV、VWAP 等需要成交量的指标
  - 导出数据用于外部分析

使用示例：
	opens, highs, lows, closes, volumes := buffer.GetOHLCV(exchange, symbol, tf, 20)
	atr := indicator.ATR(highs, lows, closes, 14)
	bbands := indicator.BollingerBands(closes, 20, 2.0)
*/
func (b *KlineBuffer) GetOHLCV(exchange model.Exchange, symbol string, tf model.Timeframe, limit int) (opens, highs, lows, closes, volumes []decimal.Decimal) {
	klines := b.Get(exchange, symbol, tf, limit)
	n := len(klines)

	// 预分配切片，提高性能
	opens = make([]decimal.Decimal, n)
	highs = make([]decimal.Decimal, n)
	lows = make([]decimal.Decimal, n)
	closes = make([]decimal.Decimal, n)
	volumes = make([]decimal.Decimal, n)

	// 提取各字段
	for i, k := range klines {
		opens[i] = k.Open
		highs[i] = k.High
		lows[i] = k.Low
		closes[i] = k.Close
		volumes[i] = k.Volume
	}

	return
}
