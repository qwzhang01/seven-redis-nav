/*
================================================================================
                        Go语言基础教程 - 量化交易系统专用
================================================================================

本教程专为Python开发者设计，帮助你快速掌握Go语言核心概念。
Go语言特点：
1. 编译型语言，性能接近C/C++
2. 内置并发支持（goroutine）
3. 静态类型，编译时检查错误
4. 简洁的语法，容易学习
5. 强大的标准库
*/

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

// ============================================================================
// 第1章：变量与数据类型
// ============================================================================

/*
Go的基本数据类型：
- 整数：int, int8, int16, int32, int64, uint, uint8...
- 浮点：float32, float64
- 布尔：bool
- 字符串：string
- 复数：complex64, complex128
*/

func chapter1_variables() {
	fmt.Println("\n=== 第1章：变量与数据类型 ===")

	// 方式1：var声明（类似Python的显式类型注解）
	var name string = "Bitcoin"
	var price float64 = 50000.0
	var quantity int = 100

	// 方式2：短变量声明（Go最常用，类似Python的自动推断）
	// := 只能在函数内部使用
	symbol := "BTCUSDT"     // 自动推断为string
	volume := 1234.56       // 自动推断为float64
	isActive := true        // 自动推断为bool

	// 方式3：批量声明
	var (
		exchange   = "binance"
		apiKey     = "xxx"
		secretKey  = "yyy"
	)

	// 常量声明（不可修改）
	const (
		MaxRetries = 3
		Timeout    = 30 * time.Second
	)

	// 零值概念（Go的默认值，类似Python的None但更具体）
	var defaultInt int       // 默认0
	var defaultFloat float64 // 默认0.0
	var defaultString string // 默认""
	var defaultBool bool     // 默认false

	fmt.Printf("交易对: %s, 价格: %.2f, 数量: %d\n", name, price, quantity)
	fmt.Printf("Symbol: %s, Volume: %.2f, Active: %v\n", symbol, volume, isActive)
	fmt.Printf("Exchange: %s\n", exchange)
	fmt.Printf("零值示例: int=%d, float=%.2f, string='%s', bool=%v\n",
		defaultInt, defaultFloat, defaultString, defaultBool)

	// 避免编译警告
	_ = apiKey
	_ = secretKey
}

// ============================================================================
// 第2章：复合数据类型
// ============================================================================

// 结构体（类似Python的dataclass或class）
// Go没有类(class)，使用结构体(struct)代替
type Kline struct {
	Symbol    string    `json:"symbol"`    // json标签用于序列化
	Open      float64   `json:"open"`
	High      float64   `json:"high"`
	Low       float64   `json:"low"`
	Close     float64   `json:"close"`
	Volume    float64   `json:"volume"`
	Timestamp time.Time `json:"timestamp"`
}

// 方法（给结构体添加方法，类似Python的类方法）
// (k *Kline) 是接收者，*表示指针，可以修改原值
func (k *Kline) Change() float64 {
	return (k.Close - k.Open) / k.Open * 100
}

// 值接收者（不能修改原值，类似传值）
func (k Kline) String() string {
	return fmt.Sprintf("%s: O=%.2f H=%.2f L=%.2f C=%.2f", 
		k.Symbol, k.Open, k.High, k.Low, k.Close)
}

func chapter2_composite_types() {
	fmt.Println("\n=== 第2章：复合数据类型 ===")

	// 1. 数组（固定长度，Go中很少直接使用）
	var prices [5]float64 = [5]float64{100.0, 101.5, 99.8, 102.3, 103.0}
	fmt.Println("数组:", prices)

	// 2. 切片（动态数组，最常用，类似Python的list）
	// 切片是数组的引用，可以动态增长
	symbols := []string{"BTCUSDT", "ETHUSDT", "BNBUSDT"}
	
	// 追加元素（类似Python的append）
	symbols = append(symbols, "SOLUSDT")
	
	// 切片操作（和Python类似）
	first := symbols[0]        // 第一个元素
	last := symbols[len(symbols)-1] // 最后一个元素
	subset := symbols[1:3]     // 切片 [1, 3)
	
	fmt.Println("切片:", symbols)
	fmt.Printf("第一个: %s, 最后一个: %s, 子集: %v\n", first, last, subset)

	// 3. Map（字典，类似Python的dict）
	// 声明方式1：make
	tickerPrices := make(map[string]float64)
	tickerPrices["BTCUSDT"] = 50000.0
	tickerPrices["ETHUSDT"] = 3000.0

	// 声明方式2：字面量
	volumes := map[string]float64{
		"BTCUSDT": 1000.5,
		"ETHUSDT": 500.3,
	}

	// 访问Map
	btcPrice := tickerPrices["BTCUSDT"]
	
	// 检查key是否存在（重要！Python会抛异常，Go返回零值）
	price, exists := tickerPrices["XYZUSDT"]
	if exists {
		fmt.Println("价格:", price)
	} else {
		fmt.Println("交易对不存在")
	}

	// 删除元素
	delete(tickerPrices, "ETHUSDT")

	fmt.Printf("BTC价格: %.2f, 成交量: %v\n", btcPrice, volumes)

	// 4. 结构体使用
	kline := Kline{
		Symbol:    "BTCUSDT",
		Open:      50000.0,
		High:      51000.0,
		Low:       49500.0,
		Close:     50500.0,
		Volume:    1234.56,
		Timestamp: time.Now(),
	}
	
	fmt.Printf("K线: %s, 涨跌幅: %.2f%%\n", kline.String(), kline.Change())

	// 5. 指针（Go有指针，但比C简单安全）
	// &取地址，*解引用
	p := &kline  // p是指向kline的指针
	p.Close = 51000.0  // 通过指针修改值
	fmt.Printf("修改后涨跌幅: %.2f%%\n", kline.Change())
}

// ============================================================================
// 第3章：流程控制
// ============================================================================

func chapter3_control_flow() {
	fmt.Println("\n=== 第3章：流程控制 ===")

	price := 50000.0

	// 1. if语句（注意：条件不需要括号）
	if price > 45000 {
		fmt.Println("价格较高")
	} else if price > 30000 {
		fmt.Println("价格中等")
	} else {
		fmt.Println("价格较低")
	}

	// if可以带初始化语句（Go特色，非常实用）
	if change := (price - 48000) / 48000 * 100; change > 0 {
		fmt.Printf("上涨 %.2f%%\n", change)
	} else {
		fmt.Printf("下跌 %.2f%%\n", change)
	}

	// 2. for循环（Go只有for，没有while）
	// 传统for
	for i := 0; i < 3; i++ {
		fmt.Printf("循环 %d\n", i)
	}

	// while风格的for
	count := 0
	for count < 3 {
		fmt.Printf("Count: %d\n", count)
		count++
	}

	// 无限循环（需要break退出）
	// for {
	//     break
	// }

	// range遍历（类似Python的enumerate）
	symbols := []string{"BTC", "ETH", "BNB"}
	for index, symbol := range symbols {
		fmt.Printf("索引 %d: %s\n", index, symbol)
	}

	// 只遍历值
	for _, symbol := range symbols {
		fmt.Println("Symbol:", symbol)
	}

	// 遍历Map
	prices := map[string]float64{"BTC": 50000, "ETH": 3000}
	for key, value := range prices {
		fmt.Printf("%s: %.2f\n", key, value)
	}

	// 3. switch语句（比Python的match更强大）
	timeframe := "1h"
	switch timeframe {
	case "1m":
		fmt.Println("1分钟K线")
	case "5m", "15m": // 多条件
		fmt.Println("分钟K线")
	case "1h", "4h":
		fmt.Println("小时K线")
	default:
		fmt.Println("其他周期")
	}

	// switch可以没有条件（类似if-else链）
	switch {
	case price > 60000:
		fmt.Println("超高价格")
	case price > 40000:
		fmt.Println("高价格")
	default:
		fmt.Println("正常价格")
	}
}

// ============================================================================
// 第4章：函数
// ============================================================================

// 基本函数（类似Python def）
func calculateProfit(entryPrice, exitPrice, quantity float64) float64 {
	return (exitPrice - entryPrice) * quantity
}

// 多返回值（Go的特色，非常实用）
// Python需要返回tuple，Go原生支持
func divide(a, b float64) (float64, error) {
	if b == 0 {
		return 0, fmt.Errorf("除数不能为零")
	}
	return a / b, nil
}

// 命名返回值（可以直接return）
func getOHLC(prices []float64) (open, high, low, closePrice float64) {
	if len(prices) == 0 {
		return // 返回零值
	}
	open = prices[0]
	closePrice = prices[len(prices)-1]
	high = prices[0]
	low = prices[0]
	for _, p := range prices {
		if p > high {
			high = p
		}
		if p < low {
			low = p
		}
	}
	return // 返回命名的值
}

// 可变参数（类似Python的*args）
func sum(numbers ...float64) float64 {
	total := 0.0
	for _, n := range numbers {
		total += n
	}
	return total
}

// 函数作为参数（类似Python的高阶函数）
type PriceFilter func(float64) bool

func filterPrices(prices []float64, filter PriceFilter) []float64 {
	result := []float64{}
	for _, p := range prices {
		if filter(p) {
			result = append(result, p)
		}
	}
	return result
}

// 闭包（和Python一样支持）
func createMultiplier(factor float64) func(float64) float64 {
	return func(x float64) float64 {
		return x * factor
	}
}

func chapter4_functions() {
	fmt.Println("\n=== 第4章：函数 ===")

	// 基本调用
	profit := calculateProfit(50000, 52000, 1.5)
	fmt.Printf("利润: %.2f\n", profit)

	// 多返回值
	result, err := divide(100, 3)
	if err != nil {
		fmt.Println("错误:", err)
	} else {
		fmt.Printf("结果: %.2f\n", result)
	}

	// 忽略某个返回值用_
	_, err = divide(100, 0)
	if err != nil {
		fmt.Println("错误:", err)
	}

	// 命名返回值
	o, h, l, c := getOHLC([]float64{100, 105, 95, 102})
	fmt.Printf("OHLC: %.2f, %.2f, %.2f, %.2f\n", o, h, l, c)

	// 可变参数
	total := sum(1.0, 2.0, 3.0, 4.0, 5.0)
	fmt.Printf("总和: %.2f\n", total)

	// 切片展开（类似Python的*list）
	numbers := []float64{10, 20, 30}
	total = sum(numbers...)
	fmt.Printf("切片总和: %.2f\n", total)

	// 高阶函数
	prices := []float64{100, 200, 300, 400, 500}
	highPrices := filterPrices(prices, func(p float64) bool {
		return p > 250
	})
	fmt.Println("高价格:", highPrices)

	// 闭包
	double := createMultiplier(2.0)
	triple := createMultiplier(3.0)
	fmt.Printf("Double(100): %.2f, Triple(100): %.2f\n", double(100), triple(100))

	// defer（延迟执行，类似Python的finally，常用于资源清理）
	// defer按LIFO顺序执行
	defer fmt.Println("defer 1")
	defer fmt.Println("defer 2")
	fmt.Println("正常执行")
	// 输出顺序：正常执行 -> defer 2 -> defer 1
}

// ============================================================================
// 第5章：接口（Go的核心特性）
// ============================================================================

/*
Go的接口是隐式实现的！
- 不需要显式声明implements
- 只要实现了接口的所有方法，就自动实现了该接口
- 这是Go最重要的设计理念之一
*/

// 定义接口（类似Python的Protocol或ABC）
type Exchange interface {
	GetPrice(symbol string) (float64, error)
	PlaceOrder(symbol string, side string, quantity float64) error
}

// Binance实现
type Binance struct {
	APIKey    string
	SecretKey string
}

// 实现Exchange接口的方法（隐式实现）
func (b *Binance) GetPrice(symbol string) (float64, error) {
	// 模拟获取价格
	prices := map[string]float64{
		"BTCUSDT": 50000.0,
		"ETHUSDT": 3000.0,
	}
	if price, ok := prices[symbol]; ok {
		return price, nil
	}
	return 0, fmt.Errorf("symbol not found: %s", symbol)
}

func (b *Binance) PlaceOrder(symbol string, side string, quantity float64) error {
	fmt.Printf("[Binance] %s %s %.4f\n", side, symbol, quantity)
	return nil
}

// OKX实现
type OKX struct {
	APIKey string
}

func (o *OKX) GetPrice(symbol string) (float64, error) {
	return 50100.0, nil // 简化示例
}

func (o *OKX) PlaceOrder(symbol string, side string, quantity float64) error {
	fmt.Printf("[OKX] %s %s %.4f\n", side, symbol, quantity)
	return nil
}

// 使用接口（多态）
func executeTrade(ex Exchange, symbol string, quantity float64) {
	price, err := ex.GetPrice(symbol)
	if err != nil {
		fmt.Println("获取价格失败:", err)
		return
	}
	fmt.Printf("当前价格: %.2f\n", price)
	ex.PlaceOrder(symbol, "BUY", quantity)
}

// 空接口（类似Python的Any）
// interface{} 可以存储任何类型
func printAny(v interface{}) {
	// 类型断言
	switch val := v.(type) {
	case int:
		fmt.Printf("整数: %d\n", val)
	case string:
		fmt.Printf("字符串: %s\n", val)
	case float64:
		fmt.Printf("浮点数: %.2f\n", val)
	default:
		fmt.Printf("未知类型: %v\n", val)
	}
}

func chapter5_interfaces() {
	fmt.Println("\n=== 第5章：接口 ===")

	// 接口变量可以存储任何实现了该接口的类型
	var ex Exchange

	// 使用Binance
	ex = &Binance{APIKey: "xxx", SecretKey: "yyy"}
	executeTrade(ex, "BTCUSDT", 0.1)

	// 使用OKX（无需修改executeTrade函数）
	ex = &OKX{APIKey: "xxx"}
	executeTrade(ex, "BTCUSDT", 0.1)

	// 空接口
	printAny(42)
	printAny("hello")
	printAny(3.14)

	// Go 1.18+ 可以用any代替interface{}
	var anything any = "Go is awesome"
	fmt.Println(anything)
}

// ============================================================================
// 第6章：并发编程（Go的核心优势）
// ============================================================================

/*
Go的并发模型基于CSP（Communicating Sequential Processes）
核心概念：
1. goroutine - 轻量级线程（比Python的threading轻量得多）
2. channel - 通道，用于goroutine之间通信
3. select - 多路复用，监听多个channel

Go的并发哲学：
"Don't communicate by sharing memory; share memory by communicating."
（不要通过共享内存来通信，而要通过通信来共享内存）
*/

// 模拟获取价格
func fetchPrice(exchange string, symbol string, ch chan<- string) {
	// 模拟网络延迟
	time.Sleep(100 * time.Millisecond)
	result := fmt.Sprintf("[%s] %s: %.2f", exchange, symbol, 50000.0+float64(len(exchange)*100))
	ch <- result // 发送到channel
}

// 使用WaitGroup等待多个goroutine完成
func fetchAllPrices(symbols []string) {
	var wg sync.WaitGroup

	for _, symbol := range symbols {
		wg.Add(1) // 增加计数
		go func(s string) {
			defer wg.Done() // 完成时减少计数
			time.Sleep(50 * time.Millisecond)
			fmt.Printf("获取 %s 价格完成\n", s)
		}(symbol) // 注意：必须传递参数，避免闭包陷阱
	}

	wg.Wait() // 等待所有goroutine完成
	fmt.Println("所有价格获取完成")
}

// 使用Mutex保护共享数据
type SafeCounter struct {
	mu    sync.Mutex
	count int
}

func (c *SafeCounter) Increment() {
	c.mu.Lock()         // 加锁
	defer c.mu.Unlock() // 解锁
	c.count++
}

func (c *SafeCounter) Value() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.count
}

// 使用RWMutex（读写锁，允许多读单写）
type PriceCache struct {
	mu     sync.RWMutex
	prices map[string]float64
}

func (c *PriceCache) Get(symbol string) (float64, bool) {
	c.mu.RLock()         // 读锁
	defer c.mu.RUnlock()
	price, ok := c.prices[symbol]
	return price, ok
}

func (c *PriceCache) Set(symbol string, price float64) {
	c.mu.Lock()         // 写锁
	defer c.mu.Unlock()
	c.prices[symbol] = price
}

func chapter6_concurrency() {
	fmt.Println("\n=== 第6章：并发编程 ===")

	// 1. goroutine（使用go关键字启动）
	fmt.Println("--- goroutine示例 ---")
	go func() {
		fmt.Println("这是一个goroutine")
	}()
	time.Sleep(10 * time.Millisecond) // 等待goroutine执行

	// 2. channel（通道）
	fmt.Println("\n--- channel示例 ---")
	
	// 无缓冲channel（同步通信）
	ch := make(chan string)
	
	go fetchPrice("Binance", "BTCUSDT", ch)
	go fetchPrice("OKX", "BTCUSDT", ch)
	
	// 接收两个结果
	result1 := <-ch
	result2 := <-ch
	fmt.Println(result1)
	fmt.Println(result2)

	// 3. 带缓冲的channel
	fmt.Println("\n--- 缓冲channel示例 ---")
	bufferedCh := make(chan int, 3) // 缓冲大小为3
	bufferedCh <- 1
	bufferedCh <- 2
	bufferedCh <- 3
	// bufferedCh <- 4 // 这会阻塞，因为缓冲已满
	
	fmt.Println(<-bufferedCh) // 1
	fmt.Println(<-bufferedCh) // 2

	// 4. select多路复用
	fmt.Println("\n--- select示例 ---")
	ch1 := make(chan string)
	ch2 := make(chan string)

	go func() {
		time.Sleep(50 * time.Millisecond)
		ch1 <- "来自ch1"
	}()
	go func() {
		time.Sleep(30 * time.Millisecond)
		ch2 <- "来自ch2"
	}()

	// select会等待第一个可用的channel
	select {
	case msg := <-ch1:
		fmt.Println(msg)
	case msg := <-ch2:
		fmt.Println(msg)
	case <-time.After(100 * time.Millisecond):
		fmt.Println("超时")
	}

	// 5. WaitGroup
	fmt.Println("\n--- WaitGroup示例 ---")
	fetchAllPrices([]string{"BTC", "ETH", "BNB"})

	// 6. Mutex
	fmt.Println("\n--- Mutex示例 ---")
	counter := &SafeCounter{}
	var wg sync.WaitGroup

	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			counter.Increment()
		}()
	}
	wg.Wait()
	fmt.Printf("最终计数: %d\n", counter.Value())

	// 7. 关闭channel
	fmt.Println("\n--- 关闭channel示例 ---")
	jobs := make(chan int, 5)
	done := make(chan bool)

	// 消费者
	go func() {
		for {
			job, more := <-jobs
			if more {
				fmt.Printf("处理任务 %d\n", job)
			} else {
				fmt.Println("所有任务完成")
				done <- true
				return
			}
		}
	}()

	// 生产者
	for i := 1; i <= 3; i++ {
		jobs <- i
	}
	close(jobs) // 关闭channel
	<-done
}

// ============================================================================
// 第7章：Context（上下文控制）
// ============================================================================

/*
Context用于：
1. 控制goroutine的生命周期
2. 传递请求范围的值
3. 设置超时和取消
4. 在HTTP服务中传递请求上下文

这在量化交易中非常重要，用于：
- 控制API请求超时
- 取消正在执行的交易操作
- 优雅关闭服务
*/

// 模拟API请求
func fetchWithContext(ctx context.Context, symbol string) (float64, error) {
	// 模拟耗时操作
	select {
	case <-time.After(200 * time.Millisecond):
		return 50000.0, nil
	case <-ctx.Done():
		return 0, ctx.Err() // 返回context的错误
	}
}

func chapter7_context() {
	fmt.Println("\n=== 第7章：Context ===")

	// 1. 带超时的context
	fmt.Println("--- 超时context ---")
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel() // 重要：始终调用cancel释放资源

	price, err := fetchWithContext(ctx, "BTCUSDT")
	if err != nil {
		fmt.Println("请求失败:", err) // context deadline exceeded
	} else {
		fmt.Printf("价格: %.2f\n", price)
	}

	// 2. 带取消的context
	fmt.Println("\n--- 取消context ---")
	ctx2, cancel2 := context.WithCancel(context.Background())

	go func() {
		time.Sleep(50 * time.Millisecond)
		cancel2() // 50ms后取消
	}()

	price, err = fetchWithContext(ctx2, "ETHUSDT")
	if err != nil {
		fmt.Println("请求被取消:", err)
	}

	// 3. 带值的context（传递请求级别的数据）
	fmt.Println("\n--- 值context ---")
	type contextKey string
	const requestIDKey contextKey = "requestID"

	ctx3 := context.WithValue(context.Background(), requestIDKey, "req-12345")
	
	// 获取值
	if reqID, ok := ctx3.Value(requestIDKey).(string); ok {
		fmt.Println("请求ID:", reqID)
	}
}

// ============================================================================
// 第8章：错误处理
// ============================================================================

/*
Go的错误处理哲学：
- 错误是值，不是异常
- 显式处理每个错误
- 没有try-catch，使用if err != nil

这与Python的try-except完全不同！
*/

// 自定义错误类型
type TradeError struct {
	Code    int
	Message string
	Symbol  string
}

// 实现error接口
func (e *TradeError) Error() string {
	return fmt.Sprintf("[%d] %s: %s", e.Code, e.Symbol, e.Message)
}

// 返回错误
func placeTrade(symbol string, quantity float64) error {
	if quantity <= 0 {
		return &TradeError{
			Code:    1001,
			Message: "数量必须大于0",
			Symbol:  symbol,
		}
	}
	if quantity > 100 {
		return fmt.Errorf("数量超过限制: %.2f > 100", quantity)
	}
	return nil
}

// 错误包装（Go 1.13+）
func executeOrder(symbol string, quantity float64) error {
	err := placeTrade(symbol, quantity)
	if err != nil {
		// 包装错误，保留原始错误信息
		return fmt.Errorf("执行订单失败: %w", err)
	}
	return nil
}

func chapter8_error_handling() {
	fmt.Println("\n=== 第8章：错误处理 ===")

	// 基本错误处理
	err := placeTrade("BTCUSDT", -1)
	if err != nil {
		fmt.Println("错误:", err)

		// 类型断言检查错误类型
		if tradeErr, ok := err.(*TradeError); ok {
			fmt.Printf("错误代码: %d\n", tradeErr.Code)
		}
	}

	// 错误包装
	err = executeOrder("BTCUSDT", 200)
	if err != nil {
		fmt.Println("包装错误:", err)
	}

	// panic和recover（类似Python的raise和except）
	// 只在真正不可恢复的错误时使用panic
	func() {
		defer func() {
			if r := recover(); r != nil {
				fmt.Println("从panic恢复:", r)
			}
		}()
		
		// panic("这是一个严重错误")
		fmt.Println("正常执行")
	}()
}

// ============================================================================
// 第9章：JSON处理
// ============================================================================

// 使用json标签控制序列化
type Order struct {
	ID        string  `json:"id"`
	Symbol    string  `json:"symbol"`
	Side      string  `json:"side"`
	Price     float64 `json:"price"`
	Quantity  float64 `json:"qty"`          // 自定义名称
	Status    string  `json:"status,omitempty"` // 空值时忽略
	Internal  string  `json:"-"`            // 不序列化
}

func chapter9_json() {
	fmt.Println("\n=== 第9章：JSON处理 ===")

	// 1. 结构体转JSON（Marshal）
	order := Order{
		ID:       "ord-123",
		Symbol:   "BTCUSDT",
		Side:     "BUY",
		Price:    50000.0,
		Quantity: 1.5,
		Internal: "secret",
	}

	jsonData, err := json.Marshal(order)
	if err != nil {
		fmt.Println("JSON编码失败:", err)
		return
	}
	fmt.Println("JSON:", string(jsonData))

	// 格式化输出
	prettyJSON, _ := json.MarshalIndent(order, "", "  ")
	fmt.Println("格式化JSON:\n", string(prettyJSON))

	// 2. JSON转结构体（Unmarshal）
	jsonStr := `{"id":"ord-456","symbol":"ETHUSDT","side":"SELL","price":3000.5,"qty":2.0}`
	
	var newOrder Order
	err = json.Unmarshal([]byte(jsonStr), &newOrder)
	if err != nil {
		fmt.Println("JSON解码失败:", err)
		return
	}
	fmt.Printf("解析订单: %+v\n", newOrder)

	// 3. 解析未知结构的JSON（使用map）
	unknownJSON := `{"name":"test","value":123,"nested":{"key":"value"}}`
	
	var data map[string]interface{}
	json.Unmarshal([]byte(unknownJSON), &data)
	fmt.Printf("动态解析: %v\n", data)

	// 4. 流式JSON处理（大文件）
	// encoder := json.NewEncoder(os.Stdout)
	// decoder := json.NewDecoder(reader)
}

// ============================================================================
// 第10章：实战练习
// ============================================================================

// 简单的价格监控示例
type PriceMonitor struct {
	symbol     string
	threshold  float64
	currentPrice float64
	alerts     chan string
	stopCh     chan struct{}
}

func NewPriceMonitor(symbol string, threshold float64) *PriceMonitor {
	return &PriceMonitor{
		symbol:    symbol,
		threshold: threshold,
		alerts:    make(chan string, 10),
		stopCh:    make(chan struct{}),
	}
}

func (m *PriceMonitor) Start(ctx context.Context) {
	go func() {
		ticker := time.NewTicker(100 * time.Millisecond)
		defer ticker.Stop()

		for {
			select {
			case <-ctx.Done():
				fmt.Println("监控停止：context取消")
				return
			case <-m.stopCh:
				fmt.Println("监控停止：手动停止")
				return
			case <-ticker.C:
				// 模拟价格变化
				m.currentPrice = 50000 + float64(time.Now().UnixNano()%1000)
				
				if m.currentPrice > m.threshold {
					select {
					case m.alerts <- fmt.Sprintf("警报: %s 价格 %.2f 超过阈值 %.2f",
						m.symbol, m.currentPrice, m.threshold):
					default:
						// channel满了，丢弃
					}
				}
			}
		}
	}()
}

func (m *PriceMonitor) Stop() {
	close(m.stopCh)
}

func (m *PriceMonitor) Alerts() <-chan string {
	return m.alerts
}

func chapter10_practice() {
	fmt.Println("\n=== 第10章：实战练习 ===")

	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()

	monitor := NewPriceMonitor("BTCUSDT", 50500)
	monitor.Start(ctx)

	// 处理警报
	alertCount := 0
	for {
		select {
		case alert := <-monitor.Alerts():
			fmt.Println(alert)
			alertCount++
			if alertCount >= 3 {
				fmt.Println("收到3个警报，停止监控")
				monitor.Stop()
				return
			}
		case <-ctx.Done():
			fmt.Println("监控超时")
			return
		}
	}
}

// ============================================================================
// 主函数
// ============================================================================

func main() {
	fmt.Println("╔════════════════════════════════════════════════════════════╗")
	fmt.Println("║           Go语言基础教程 - 量化交易系统专用                ║")
	fmt.Println("╚════════════════════════════════════════════════════════════╝")

	chapter1_variables()
	chapter2_composite_types()
	chapter3_control_flow()
	chapter4_functions()
	chapter5_interfaces()
	chapter6_concurrency()
	chapter7_context()
	chapter8_error_handling()
	chapter9_json()
	chapter10_practice()

	fmt.Println("\n" + "═"*60)
	fmt.Println("教程完成！")
	fmt.Println("═"*60)
	
	fmt.Println(`
下一步学习建议：
1. 运行本教程: go run 01_go_basics.go
2. 学习标准库: net/http, database/sql, encoding/json
3. 学习项目中使用的第三方库: Gin, GORM, Zap
4. 阅读02_libraries_guide.go了解库的使用
5. 实践项目代码，理解架构设计
`)
}
