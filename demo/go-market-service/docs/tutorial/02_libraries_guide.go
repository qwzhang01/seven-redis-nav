/*
================================================================================
                    项目依赖库详解 - Go行情处理系统
================================================================================

本教程详细介绍项目中使用的每个第三方库：
1. Gin - Web框架
2. gorilla/websocket - WebSocket库
3. GORM - ORM框架
4. go-redis - Redis客户端
5. Zap - 日志库
6. Viper - 配置管理
7. decimal - 高精度计算
*/

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"
)

// ============================================================================
// 第1章：Gin Web框架
// ============================================================================

/*
Gin 是Go语言最流行的Web框架，特点：
1. 性能极高（基于httprouter）
2. 中间件支持
3. JSON验证
4. 路由分组
5. 错误管理

官方文档: https://gin-gonic.com/docs/

安装: go get -u github.com/gin-gonic/gin
*/

// Gin使用示例（伪代码，展示用法）
func ginExamples() {
	fmt.Println(`
=== Gin Web框架使用详解 ===

【1. 基本使用】
import "github.com/gin-gonic/gin"

func main() {
    // 创建默认引擎（包含Logger和Recovery中间件）
    r := gin.Default()
    
    // 或创建无中间件引擎
    r := gin.New()
    
    // 添加中间件
    r.Use(gin.Logger())
    r.Use(gin.Recovery())
    
    // 启动服务
    r.Run(":8080")
}

【2. 路由定义】
// GET请求
r.GET("/ping", func(c *gin.Context) {
    c.JSON(200, gin.H{
        "message": "pong",
    })
})

// POST请求
r.POST("/users", createUser)

// 带参数的路由
r.GET("/users/:id", func(c *gin.Context) {
    id := c.Param("id")  // 路径参数
})

// 查询参数
r.GET("/search", func(c *gin.Context) {
    query := c.Query("q")           // 获取?q=xxx
    page := c.DefaultQuery("page", "1") // 带默认值
})

【3. 路由分组】
// API版本分组
v1 := r.Group("/api/v1")
{
    v1.GET("/klines", getKlines)
    v1.GET("/indicators", getIndicators)
}

v2 := r.Group("/api/v2")
{
    v2.GET("/klines", getKlinesV2)
}

// 带中间件的分组
authorized := r.Group("/admin")
authorized.Use(AuthMiddleware())
{
    authorized.GET("/dashboard", dashboard)
}

【4. 请求绑定】
// 定义请求结构
type KlineRequest struct {
    Symbol    string ` + "`" + `form:"symbol" binding:"required"` + "`" + `
    Timeframe string ` + "`" + `form:"timeframe" binding:"required"` + "`" + `
    Limit     int    ` + "`" + `form:"limit" binding:"min=1,max=1000"` + "`" + `
}

// 绑定查询参数
func getKlines(c *gin.Context) {
    var req KlineRequest
    if err := c.ShouldBindQuery(&req); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    // 使用req.Symbol, req.Timeframe...
}

// 绑定JSON body
type OrderRequest struct {
    Symbol   string  ` + "`" + `json:"symbol" binding:"required"` + "`" + `
    Side     string  ` + "`" + `json:"side" binding:"required,oneof=BUY SELL"` + "`" + `
    Quantity float64 ` + "`" + `json:"quantity" binding:"required,gt=0"` + "`" + `
}

func createOrder(c *gin.Context) {
    var req OrderRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
}

【5. 响应】
// JSON响应
c.JSON(200, gin.H{
    "status": "ok",
    "data": klines,
})

// 带状态码
c.JSON(http.StatusCreated, order)
c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request"})

// 原始数据
c.Data(200, "text/csv", csvData)

// 文件下载
c.Header("Content-Disposition", "attachment; filename=data.csv")
c.Data(200, "text/csv", data)

// 重定向
c.Redirect(http.StatusMovedPermanently, "/new-url")

【6. 中间件】
// 自定义中间件
func Logger() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        path := c.Request.URL.Path
        
        // 处理请求前
        c.Next()  // 继续处理
        
        // 处理请求后
        cost := time.Since(start)
        status := c.Writer.Status()
        log.Printf("[%d] %s - %v", status, path, cost)
    }
}

// CORS中间件
func Cors() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Header("Access-Control-Allow-Origin", "*")
        c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        c.Header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        
        if c.Request.Method == "OPTIONS" {
            c.AbortWithStatus(204)
            return
        }
        c.Next()
    }
}

// 认证中间件
func AuthMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.JSON(401, gin.H{"error": "unauthorized"})
            c.Abort()  // 终止后续处理
            return
        }
        // 验证token...
        c.Set("userID", "user-123")  // 设置上下文值
        c.Next()
    }
}

// 使用上下文值
func handler(c *gin.Context) {
    userID, exists := c.Get("userID")
    if exists {
        // 使用userID
    }
}

【7. 错误处理】
// 恢复中间件（处理panic）
func Recovery() gin.HandlerFunc {
    return func(c *gin.Context) {
        defer func() {
            if err := recover(); err != nil {
                c.JSON(500, gin.H{
                    "error": "Internal Server Error",
                })
                c.Abort()
            }
        }()
        c.Next()
    }
}
`)
}

// ============================================================================
// 第2章：gorilla/websocket
// ============================================================================

/*
gorilla/websocket 是Go标准的WebSocket库
特点：
1. 完整的WebSocket协议支持
2. 并发安全的API
3. 支持压缩
4. 广泛使用（行业标准）

安装: go get github.com/gorilla/websocket
*/

func websocketExamples() {
	fmt.Println(`
=== gorilla/websocket 使用详解 ===

【1. WebSocket服务端】
import "github.com/gorilla/websocket"

// 升级器配置
var upgrader = websocket.Upgrader{
    ReadBufferSize:  1024,
    WriteBufferSize: 1024,
    // 允许跨域（生产环境应该检查）
    CheckOrigin: func(r *http.Request) bool {
        return true
    },
}

// HTTP处理器
func wsHandler(w http.ResponseWriter, r *http.Request) {
    // 升级HTTP连接为WebSocket
    conn, err := upgrader.Upgrade(w, r, nil)
    if err != nil {
        log.Println("升级失败:", err)
        return
    }
    defer conn.Close()
    
    // 处理消息
    for {
        // 读取消息
        messageType, message, err := conn.ReadMessage()
        if err != nil {
            if websocket.IsUnexpectedCloseError(err,
                websocket.CloseGoingAway,
                websocket.CloseAbnormalClosure) {
                log.Println("读取错误:", err)
            }
            break
        }
        
        log.Printf("收到: %s", message)
        
        // 发送响应
        err = conn.WriteMessage(messageType, message)
        if err != nil {
            log.Println("写入错误:", err)
            break
        }
    }
}

【2. WebSocket客户端】
import "github.com/gorilla/websocket"

func connectExchange() {
    // 连接配置
    dialer := websocket.Dialer{
        HandshakeTimeout: 10 * time.Second,
        // 代理设置
        // Proxy: http.ProxyFromEnvironment,
    }
    
    // 连接服务器
    conn, resp, err := dialer.Dial("wss://stream.binance.com:9443/ws", nil)
    if err != nil {
        log.Fatal("连接失败:", err)
    }
    defer conn.Close()
    
    log.Printf("连接成功，状态: %d", resp.StatusCode)
    
    // 发送订阅消息
    subscribeMsg := map[string]interface{}{
        "method": "SUBSCRIBE",
        "params": []string{"btcusdt@trade"},
        "id":     1,
    }
    conn.WriteJSON(subscribeMsg)
    
    // 读取消息
    for {
        _, message, err := conn.ReadMessage()
        if err != nil {
            log.Println("读取错误:", err)
            break
        }
        log.Printf("收到: %s", message)
    }
}

【3. JSON消息处理】
// 定义消息结构
type TradeMessage struct {
    EventType string ` + "`" + `json:"e"` + "`" + `
    Symbol    string ` + "`" + `json:"s"` + "`" + `
    Price     string ` + "`" + `json:"p"` + "`" + `
    Quantity  string ` + "`" + `json:"q"` + "`" + `
    Timestamp int64  ` + "`" + `json:"T"` + "`" + `
}

// 读取JSON
var trade TradeMessage
err := conn.ReadJSON(&trade)

// 发送JSON
conn.WriteJSON(map[string]string{
    "action": "subscribe",
    "symbol": "BTCUSDT",
})

【4. 心跳保活】
func startHeartbeat(conn *websocket.Conn, interval time.Duration) {
    ticker := time.NewTicker(interval)
    defer ticker.Stop()
    
    for {
        select {
        case <-ticker.C:
            // 发送ping
            err := conn.WriteMessage(websocket.PingMessage, nil)
            if err != nil {
                return
            }
        }
    }
}

// 设置Pong处理器
conn.SetPongHandler(func(appData string) error {
    log.Println("收到Pong")
    return nil
})

【5. 并发安全写入】
// WebSocket写入不是并发安全的，需要加锁
type SafeConn struct {
    conn *websocket.Conn
    mu   sync.Mutex
}

func (c *SafeConn) WriteJSON(v interface{}) error {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.conn.WriteJSON(v)
}

【6. 重连机制】
func connectWithRetry(url string) *websocket.Conn {
    backoff := time.Second
    maxBackoff := time.Minute
    
    for {
        conn, _, err := websocket.DefaultDialer.Dial(url, nil)
        if err == nil {
            return conn
        }
        
        log.Printf("连接失败，%v后重试: %v", backoff, err)
        time.Sleep(backoff)
        
        // 指数退避
        backoff *= 2
        if backoff > maxBackoff {
            backoff = maxBackoff
        }
    }
}
`)
}

// ============================================================================
// 第3章：GORM ORM框架
// ============================================================================

/*
GORM是Go最流行的ORM框架
特点：
1. 全功能ORM
2. 支持多种数据库（MySQL, PostgreSQL, SQLite, SQL Server）
3. 自动迁移
4. Hook（钩子）
5. 事务支持
6. 预加载

官方文档: https://gorm.io/docs/

安装:
go get -u gorm.io/gorm
go get -u gorm.io/driver/postgres
*/

func gormExamples() {
	fmt.Println(`
=== GORM ORM框架使用详解 ===

【1. 连接数据库】
import (
    "gorm.io/gorm"
    "gorm.io/driver/postgres"
)

// PostgreSQL连接
dsn := "host=localhost port=5432 user=quant password=quant123 dbname=market_data sslmode=disable"
db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
if err != nil {
    log.Fatal("数据库连接失败:", err)
}

// 获取底层sql.DB（配置连接池）
sqlDB, _ := db.DB()
sqlDB.SetMaxOpenConns(100)          // 最大连接数
sqlDB.SetMaxIdleConns(10)           // 最大空闲连接
sqlDB.SetConnMaxLifetime(time.Hour) // 连接最大生命周期

【2. 模型定义】
// 基本模型
type Kline struct {
    ID        uint      ` + "`" + `gorm:"primaryKey"` + "`" + `
    Exchange  string    ` + "`" + `gorm:"column:exchange;size:20;index"` + "`" + `
    Symbol    string    ` + "`" + `gorm:"column:symbol;size:20;index"` + "`" + `
    Timeframe string    ` + "`" + `gorm:"column:timeframe;size:5"` + "`" + `
    OpenTime  time.Time ` + "`" + `gorm:"column:open_time;index"` + "`" + `
    Open      float64   ` + "`" + `gorm:"column:open;type:double precision"` + "`" + `
    High      float64   ` + "`" + `gorm:"column:high;type:double precision"` + "`" + `
    Low       float64   ` + "`" + `gorm:"column:low;type:double precision"` + "`" + `
    Close     float64   ` + "`" + `gorm:"column:close;type:double precision"` + "`" + `
    Volume    float64   ` + "`" + `gorm:"column:volume;type:double precision"` + "`" + `
    CreatedAt time.Time ` + "`" + `gorm:"column:created_at"` + "`" + `
}

// 自定义表名
func (Kline) TableName() string {
    return "klines"
}

// 复合主键
type KlineEntity struct {
    Time      time.Time ` + "`" + `gorm:"column:time;primaryKey"` + "`" + `
    Exchange  string    ` + "`" + `gorm:"column:exchange;primaryKey;size:20"` + "`" + `
    Symbol    string    ` + "`" + `gorm:"column:symbol;primaryKey;size:20"` + "`" + `
    Timeframe string    ` + "`" + `gorm:"column:timeframe;primaryKey;size:5"` + "`" + `
    // ... 其他字段
}

【3. 自动迁移】
// 自动创建/更新表结构
db.AutoMigrate(&Kline{}, &Order{}, &Trade{})

// 手动执行SQL
db.Exec("CREATE INDEX IF NOT EXISTS idx_klines_time ON klines (open_time DESC)")

【4. CRUD操作】
// 创建
kline := Kline{
    Exchange: "binance",
    Symbol:   "BTCUSDT",
    Open:     50000.0,
    Close:    50500.0,
}
result := db.Create(&kline)
// result.RowsAffected - 插入的行数
// result.Error - 错误信息

// 批量创建
klines := []Kline{...}
db.CreateInBatches(klines, 100)  // 每批100条

// 查询单条
var kline Kline
db.First(&kline, 1)  // 主键查询
db.First(&kline, "symbol = ?", "BTCUSDT")  // 条件查询

// 查询多条
var klines []Kline
db.Where("exchange = ? AND symbol = ?", "binance", "BTCUSDT").
    Order("open_time DESC").
    Limit(100).
    Find(&klines)

// 更新
db.Model(&kline).Update("close", 51000.0)
db.Model(&kline).Updates(map[string]interface{}{
    "close": 51000.0,
    "high":  51500.0,
})

// 删除
db.Delete(&kline, 1)  // 软删除（如果有DeletedAt字段）
db.Unscoped().Delete(&kline, 1)  // 硬删除

【5. 高级查询】
// 选择特定字段
db.Select("symbol", "close", "volume").Find(&klines)

// 条件构建
query := db.Model(&Kline{})
if symbol != "" {
    query = query.Where("symbol = ?", symbol)
}
if startTime != nil {
    query = query.Where("open_time >= ?", startTime)
}
query.Find(&klines)

// 原生SQL
db.Raw("SELECT * FROM klines WHERE symbol = ? ORDER BY open_time DESC LIMIT 10", "BTCUSDT").
    Scan(&klines)

// 分页
page := 1
pageSize := 20
var total int64
db.Model(&Kline{}).Count(&total)
db.Offset((page - 1) * pageSize).Limit(pageSize).Find(&klines)

// 聚合查询
var result struct {
    MaxPrice float64
    MinPrice float64
    AvgPrice float64
}
db.Model(&Kline{}).
    Select("MAX(high) as max_price, MIN(low) as min_price, AVG(close) as avg_price").
    Where("symbol = ?", "BTCUSDT").
    Scan(&result)

【6. 事务】
// 自动事务
err := db.Transaction(func(tx *gorm.DB) error {
    if err := tx.Create(&order).Error; err != nil {
        return err  // 回滚
    }
    if err := tx.Create(&trade).Error; err != nil {
        return err  // 回滚
    }
    return nil  // 提交
})

// 手动事务
tx := db.Begin()
if err := tx.Create(&order).Error; err != nil {
    tx.Rollback()
    return err
}
if err := tx.Create(&trade).Error; err != nil {
    tx.Rollback()
    return err
}
tx.Commit()

【7. Hook（钩子）】
// 创建前
func (k *Kline) BeforeCreate(tx *gorm.DB) error {
    if k.OpenTime.IsZero() {
        k.OpenTime = time.Now()
    }
    return nil
}

// 创建后
func (k *Kline) AfterCreate(tx *gorm.DB) error {
    log.Printf("K线已创建: %s %s", k.Symbol, k.OpenTime)
    return nil
}

【8. 日志配置】
import "gorm.io/gorm/logger"

db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
    Logger: logger.Default.LogMode(logger.Info),  // 打印所有SQL
})

// 静默模式（生产环境）
logger.Default.LogMode(logger.Silent)
`)
}

// ============================================================================
// 第4章：go-redis
// ============================================================================

/*
go-redis是Go最流行的Redis客户端
特点：
1. 支持所有Redis命令
2. 支持集群、哨兵
3. 连接池管理
4. Pipeline和事务
5. Pub/Sub支持

安装: go get github.com/redis/go-redis/v9
*/

func redisExamples() {
	fmt.Println(`
=== go-redis 使用详解 ===

【1. 连接Redis】
import "github.com/redis/go-redis/v9"

// 单机模式
rdb := redis.NewClient(&redis.Options{
    Addr:     "localhost:6379",
    Password: "",  // 无密码
    DB:       0,   // 默认DB
    PoolSize: 100, // 连接池大小
})

// 测试连接
ctx := context.Background()
pong, err := rdb.Ping(ctx).Result()

// 集群模式
rdb := redis.NewClusterClient(&redis.ClusterOptions{
    Addrs: []string{
        "node1:6379",
        "node2:6379",
        "node3:6379",
    },
})

【2. 基本操作】
ctx := context.Background()

// String操作
rdb.Set(ctx, "price:BTCUSDT", 50000.0, time.Hour)  // 设置，1小时过期
rdb.SetNX(ctx, "lock:order", 1, time.Second*10)   // 不存在才设置（分布式锁）

val, err := rdb.Get(ctx, "price:BTCUSDT").Result()
if err == redis.Nil {
    // key不存在
} else if err != nil {
    // 其他错误
} else {
    // 成功获取
}

// 获取并转换类型
price, _ := rdb.Get(ctx, "price:BTCUSDT").Float64()

// 删除
rdb.Del(ctx, "price:BTCUSDT")

// 检查存在
exists, _ := rdb.Exists(ctx, "price:BTCUSDT").Result()

// 设置过期时间
rdb.Expire(ctx, "price:BTCUSDT", time.Hour)

【3. Hash操作（适合存储对象）】
// 设置单个字段
rdb.HSet(ctx, "kline:BTCUSDT:1h", "open", 50000.0)

// 设置多个字段
rdb.HSet(ctx, "kline:BTCUSDT:1h", map[string]interface{}{
    "open":   50000.0,
    "high":   51000.0,
    "low":    49500.0,
    "close":  50500.0,
    "volume": 1234.56,
})

// 获取单个字段
open, _ := rdb.HGet(ctx, "kline:BTCUSDT:1h", "open").Float64()

// 获取所有字段
data, _ := rdb.HGetAll(ctx, "kline:BTCUSDT:1h").Result()
// data是map[string]string

【4. List操作（适合队列）】
// 左侧插入（队列）
rdb.LPush(ctx, "trades:BTCUSDT", tradeJSON)

// 右侧弹出
trade, _ := rdb.RPop(ctx, "trades:BTCUSDT").Result()

// 阻塞弹出（消息队列）
result, _ := rdb.BRPop(ctx, time.Second*5, "trades:BTCUSDT").Result()

// 获取范围
trades, _ := rdb.LRange(ctx, "trades:BTCUSDT", 0, 99).Result()

// 列表长度
length, _ := rdb.LLen(ctx, "trades:BTCUSDT").Result()

【5. Sorted Set操作（适合排行榜、时序数据）】
// 添加成员
rdb.ZAdd(ctx, "volume:24h", redis.Z{
    Score:  1234.56,
    Member: "BTCUSDT",
})

// 批量添加
rdb.ZAdd(ctx, "volume:24h",
    redis.Z{Score: 1234.56, Member: "BTCUSDT"},
    redis.Z{Score: 567.89, Member: "ETHUSDT"},
)

// 获取排名（从高到低）
rank, _ := rdb.ZRevRank(ctx, "volume:24h", "BTCUSDT").Result()

// 获取Top N
top10, _ := rdb.ZRevRangeWithScores(ctx, "volume:24h", 0, 9).Result()
for _, z := range top10 {
    fmt.Printf("%s: %.2f\n", z.Member, z.Score)
}

// 按分数范围获取
results, _ := rdb.ZRangeByScore(ctx, "prices:BTCUSDT", &redis.ZRangeBy{
    Min: "50000",
    Max: "51000",
}).Result()

【6. 发布订阅】
// 订阅
pubsub := rdb.Subscribe(ctx, "market:ticker", "market:trade")
defer pubsub.Close()

// 接收消息
for msg := range pubsub.Channel() {
    fmt.Printf("收到 [%s]: %s\n", msg.Channel, msg.Payload)
}

// 发布
rdb.Publish(ctx, "market:ticker", tickerJSON)

【7. Pipeline（批量操作）】
// 减少网络往返，提高性能
pipe := rdb.Pipeline()
pipe.Set(ctx, "key1", "value1", 0)
pipe.Set(ctx, "key2", "value2", 0)
pipe.Get(ctx, "key3")
cmds, err := pipe.Exec(ctx)

// 获取结果
for _, cmd := range cmds {
    fmt.Println(cmd.(*redis.StringCmd).Val())
}

【8. 事务】
// MULTI/EXEC
pipe := rdb.TxPipeline()
pipe.Set(ctx, "balance:user1", 100, 0)
pipe.Set(ctx, "balance:user2", 200, 0)
_, err := pipe.Exec(ctx)

// WATCH（乐观锁）
err := rdb.Watch(ctx, func(tx *redis.Tx) error {
    n, err := tx.Get(ctx, "counter").Int()
    if err != nil {
        return err
    }
    _, err = tx.TxPipelined(ctx, func(pipe redis.Pipeliner) error {
        pipe.Set(ctx, "counter", n+1, 0)
        return nil
    })
    return err
}, "counter")

【9. 分布式锁】
// 获取锁
func acquireLock(ctx context.Context, rdb *redis.Client, key string, ttl time.Duration) (bool, error) {
    return rdb.SetNX(ctx, "lock:"+key, 1, ttl).Result()
}

// 释放锁（使用Lua脚本确保原子性）
var releaseLockScript = redis.NewScript(` + "`" + `
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
` + "`" + `)

func releaseLock(ctx context.Context, rdb *redis.Client, key, value string) error {
    return releaseLockScript.Run(ctx, rdb, []string{"lock:" + key}, value).Err()
}
`)
}

// ============================================================================
// 第5章：Zap日志库
// ============================================================================

/*
Zap是Uber开发的高性能结构化日志库
特点：
1. 极高性能（零分配）
2. 结构化日志
3. 日志级别
4. 多输出目标
5. 日志采样

安装: go get -u go.uber.org/zap
*/

func zapExamples() {
	fmt.Println(`
=== Zap日志库使用详解 ===

【1. 快速开始】
import "go.uber.org/zap"

// 开发环境（格式化输出）
logger, _ := zap.NewDevelopment()
defer logger.Sync()

// 生产环境（JSON输出）
logger, _ := zap.NewProduction()

// 使用
logger.Info("服务启动",
    zap.String("env", "production"),
    zap.Int("port", 8080),
)

【2. 日志级别】
logger.Debug("调试信息")  // 最低级别
logger.Info("普通信息")
logger.Warn("警告信息")
logger.Error("错误信息")
logger.DPanic("开发panic")  // 开发环境panic
logger.Panic("panic")       // 记录后panic
logger.Fatal("致命错误")    // 记录后os.Exit(1)

【3. 结构化日志】
// 类型安全的字段
logger.Info("K线数据",
    zap.String("symbol", "BTCUSDT"),
    zap.Float64("price", 50000.0),
    zap.Int64("volume", 1234),
    zap.Time("timestamp", time.Now()),
    zap.Duration("latency", 100*time.Millisecond),
    zap.Bool("is_closed", true),
    zap.Any("data", kline),  // 任意类型
)

// 错误日志
logger.Error("请求失败",
    zap.Error(err),
    zap.String("url", url),
)

【4. 子日志器（添加上下文）】
// 创建带固定字段的子日志器
exchangeLogger := logger.With(
    zap.String("exchange", "binance"),
    zap.String("component", "websocket"),
)

// 后续所有日志都带这些字段
exchangeLogger.Info("连接成功")
exchangeLogger.Error("连接断开", zap.Error(err))

【5. 自定义配置】
import (
    "go.uber.org/zap"
    "go.uber.org/zap/zapcore"
)

func NewLogger() *zap.Logger {
    // 编码器配置
    encoderConfig := zapcore.EncoderConfig{
        TimeKey:        "time",
        LevelKey:       "level",
        NameKey:        "logger",
        CallerKey:      "caller",
        MessageKey:     "msg",
        StacktraceKey:  "stacktrace",
        LineEnding:     zapcore.DefaultLineEnding,
        EncodeLevel:    zapcore.LowercaseLevelEncoder,  // 小写级别
        EncodeTime:     zapcore.ISO8601TimeEncoder,     // ISO8601时间
        EncodeDuration: zapcore.SecondsDurationEncoder,
        EncodeCaller:   zapcore.ShortCallerEncoder,
    }
    
    // JSON编码器（生产）
    encoder := zapcore.NewJSONEncoder(encoderConfig)
    
    // Console编码器（开发）
    // encoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
    // encoder := zapcore.NewConsoleEncoder(encoderConfig)
    
    // 输出目标
    writeSyncer := zapcore.AddSync(os.Stdout)
    
    // 日志级别
    level := zapcore.InfoLevel
    
    // 创建Core
    core := zapcore.NewCore(encoder, writeSyncer, level)
    
    // 创建Logger
    logger := zap.New(core,
        zap.AddCaller(),      // 添加调用者信息
        zap.AddStacktrace(zapcore.ErrorLevel),  // Error以上添加堆栈
    )
    
    return logger
}

【6. 多输出目标】
// 同时输出到控制台和文件
consoleWriter := zapcore.AddSync(os.Stdout)
fileWriter := zapcore.AddSync(logFile)

// 创建多输出Core
core := zapcore.NewTee(
    zapcore.NewCore(consoleEncoder, consoleWriter, zapcore.DebugLevel),
    zapcore.NewCore(jsonEncoder, fileWriter, zapcore.InfoLevel),
)

【7. 日志轮转】
// 使用lumberjack进行日志轮转
import "gopkg.in/natefinch/lumberjack.v2"

lumberJackLogger := &lumberjack.Logger{
    Filename:   "/var/log/app.log",
    MaxSize:    100,  // MB
    MaxBackups: 5,
    MaxAge:     30,   // 天
    Compress:   true,
}

writeSyncer := zapcore.AddSync(lumberJackLogger)

【8. SugaredLogger（更方便但性能稍低）】
sugar := logger.Sugar()

// Printf风格
sugar.Infof("价格: %.2f", price)

// 键值对风格
sugar.Infow("K线数据",
    "symbol", "BTCUSDT",
    "price", 50000.0,
)
`)
}

// ============================================================================
// 第6章：Viper配置管理
// ============================================================================

/*
Viper是Go最流行的配置管理库
特点：
1. 支持多种格式（YAML, JSON, TOML, ENV）
2. 环境变量支持
3. 配置热重载
4. 默认值设置
5. 配置验证

安装: go get github.com/spf13/viper
*/

func viperExamples() {
	fmt.Println(`
=== Viper配置管理使用详解 ===

【1. 基本使用】
import "github.com/spf13/viper"

func main() {
    // 设置配置文件
    viper.SetConfigName("config")     // 配置文件名（不带扩展名）
    viper.SetConfigType("yaml")       // 配置文件类型
    viper.AddConfigPath("./configs")  // 配置文件路径
    viper.AddConfigPath(".")          // 也搜索当前目录
    
    // 读取配置
    if err := viper.ReadInConfig(); err != nil {
        log.Fatal("读取配置失败:", err)
    }
    
    fmt.Println("使用配置文件:", viper.ConfigFileUsed())
}

【2. 获取配置值】
// 获取字符串
host := viper.GetString("server.host")

// 获取整数
port := viper.GetInt("server.port")

// 获取浮点数
timeout := viper.GetFloat64("server.timeout")

// 获取布尔值
debug := viper.GetBool("debug")

// 获取时间
duration := viper.GetDuration("server.read_timeout")

// 获取切片
symbols := viper.GetStringSlice("market.symbols")

// 获取Map
exchanges := viper.GetStringMap("exchanges")

// 检查key是否存在
if viper.IsSet("api_key") {
    // 存在
}

【3. 设置默认值】
viper.SetDefault("server.host", "localhost")
viper.SetDefault("server.port", 8080)
viper.SetDefault("server.timeout", 30)
viper.SetDefault("market.timeframes", []string{"1m", "5m", "1h"})

【4. 环境变量】
// 自动读取环境变量
viper.AutomaticEnv()

// 设置环境变量前缀
viper.SetEnvPrefix("MARKET")  // 环境变量: MARKET_SERVER_PORT

// 替换环境变量中的点和连字符
viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_", "-", "_"))

// 现在可以通过环境变量覆盖配置
// MARKET_SERVER_PORT=9090 会覆盖 server.port

// 绑定特定环境变量
viper.BindEnv("api_key", "BINANCE_API_KEY")

【5. 解析到结构体】
type Config struct {
    Env    string       ` + "`" + `mapstructure:"env"` + "`" + `
    Server ServerConfig ` + "`" + `mapstructure:"server"` + "`" + `
    Market MarketConfig ` + "`" + `mapstructure:"market"` + "`" + `
}

type ServerConfig struct {
    Host         string        ` + "`" + `mapstructure:"host"` + "`" + `
    Port         int           ` + "`" + `mapstructure:"port"` + "`" + `
    ReadTimeout  time.Duration ` + "`" + `mapstructure:"read_timeout"` + "`" + `
    WriteTimeout time.Duration ` + "`" + `mapstructure:"write_timeout"` + "`" + `
}

type MarketConfig struct {
    Exchanges  []ExchangeConfig ` + "`" + `mapstructure:"exchanges"` + "`" + `
    Timeframes []string         ` + "`" + `mapstructure:"timeframes"` + "`" + `
}

// 解析
var cfg Config
if err := viper.Unmarshal(&cfg); err != nil {
    log.Fatal("解析配置失败:", err)
}

【6. 配置热重载】
viper.WatchConfig()
viper.OnConfigChange(func(e fsnotify.Event) {
    fmt.Println("配置文件变化:", e.Name)
    // 重新加载配置
    viper.Unmarshal(&cfg)
})

【7. 写入配置】
// 修改配置
viper.Set("server.port", 9090)

// 写入当前配置文件
viper.WriteConfig()

// 写入新文件
viper.WriteConfigAs("./configs/config_new.yaml")

【8. 多实例】
// 创建新的Viper实例（不使用全局）
v := viper.New()
v.SetConfigFile("another_config.yaml")
v.ReadInConfig()

【9. 配置文件示例】
// configs/config.yaml
` + "```" + `yaml
env: production

server:
  host: 0.0.0.0
  port: 8080
  read_timeout: 30s
  write_timeout: 30s

storage:
  postgres:
    host: localhost
    port: 5432
    user: quant
    password: ${DB_PASSWORD}  # 从环境变量
    dbname: market_data
  redis:
    addr: localhost:6379
    pool_size: 100

market:
  timeframes:
    - 1m
    - 5m
    - 1h
    - 1d
  exchanges:
    - name: binance
      enabled: true
      api_key: ${BINANCE_API_KEY}
      symbols:
        - BTCUSDT
        - ETHUSDT
` + "```" + `
`)
}

// ============================================================================
// 第7章：shopspring/decimal 高精度计算
// ============================================================================

/*
decimal库用于高精度小数计算
特点：
1. 任意精度
2. 避免浮点数精度问题
3. 金融计算必备
4. 支持JSON序列化

安装: go get github.com/shopspring/decimal
*/

func decimalExamples() {
	fmt.Println(`
=== shopspring/decimal 高精度计算详解 ===

【为什么需要decimal？】
// 浮点数精度问题演示
a := 0.1
b := 0.2
fmt.Println(a + b)  // 0.30000000000000004 !!!

// 金融计算中这是不可接受的

【1. 创建Decimal】
import "github.com/shopspring/decimal"

// 从字符串创建（推荐）
price, _ := decimal.NewFromString("50000.12345678")

// 从整数创建
qty := decimal.NewFromInt(100)

// 从浮点数创建（可能有精度损失）
value := decimal.NewFromFloat(3.14159)

// 从分数创建
ratio := decimal.NewFromFloatWithExponent(123.456, -2)  // 123.46

【2. 基本运算】
a := decimal.NewFromFloat(100.5)
b := decimal.NewFromFloat(50.25)

// 加法
sum := a.Add(b)  // 150.75

// 减法
diff := a.Sub(b)  // 50.25

// 乘法
product := a.Mul(b)  // 5050.125

// 除法
quotient := a.Div(b)  // 2.0

// 取模
remainder := a.Mod(b)

// 幂运算
squared := a.Pow(decimal.NewFromInt(2))

// 绝对值
abs := a.Abs()

// 取反
neg := a.Neg()

【3. 比较运算】
a := decimal.NewFromFloat(100)
b := decimal.NewFromFloat(200)

// 相等
a.Equal(b)  // false

// 大于
a.GreaterThan(b)  // false

// 大于等于
a.GreaterThanOrEqual(b)  // false

// 小于
a.LessThan(b)  // true

// 小于等于
a.LessThanOrEqual(b)  // true

// 比较
cmp := a.Cmp(b)  // -1 (a < b), 0 (a == b), 1 (a > b)

// 是否为零
a.IsZero()

// 是否为正
a.IsPositive()

// 是否为负
a.IsNegative()

【4. 精度控制】
price := decimal.NewFromFloat(50000.123456789)

// 四舍五入到指定小数位
rounded := price.Round(2)  // 50000.12

// 截断
truncated := price.Truncate(2)  // 50000.12

// 向上取整
ceil := price.Ceil()  // 50001

// 向下取整
floor := price.Floor()  // 50000

// 银行家舍入（四舍六入五成双）
bankRound := price.RoundBank(2)

【5. 字符串转换】
price := decimal.NewFromFloat(50000.12)

// 转字符串
str := price.String()  // "50000.12"

// 固定小数位
fixed := price.StringFixed(4)  // "50000.1200"

// 转浮点数（可能损失精度）
f, _ := price.Float64()

// 转整数
i := price.IntPart()  // 50000

// 小数部分
frac := price.Sub(decimal.NewFromInt(i))

【6. 金融计算示例】
// 计算收益
func calculateProfit(entryPrice, exitPrice, quantity decimal.Decimal) decimal.Decimal {
    return exitPrice.Sub(entryPrice).Mul(quantity)
}

// 计算收益率
func calculateReturn(entryPrice, exitPrice decimal.Decimal) decimal.Decimal {
    return exitPrice.Sub(entryPrice).Div(entryPrice).Mul(decimal.NewFromInt(100))
}

// 计算手续费
func calculateFee(amount decimal.Decimal, feeRate decimal.Decimal) decimal.Decimal {
    return amount.Mul(feeRate).Round(8)  // 保留8位小数
}

// 计算平均价
func calculateAvgPrice(prices []decimal.Decimal) decimal.Decimal {
    if len(prices) == 0 {
        return decimal.Zero
    }
    sum := decimal.Zero
    for _, p := range prices {
        sum = sum.Add(p)
    }
    return sum.Div(decimal.NewFromInt(int64(len(prices))))
}

【7. JSON序列化】
type Order struct {
    Symbol   string          ` + "`" + `json:"symbol"` + "`" + `
    Price    decimal.Decimal ` + "`" + `json:"price"` + "`" + `
    Quantity decimal.Decimal ` + "`" + `json:"quantity"` + "`" + `
}

order := Order{
    Symbol:   "BTCUSDT",
    Price:    decimal.NewFromFloat(50000.12),
    Quantity: decimal.NewFromFloat(1.5),
}

// 序列化
jsonData, _ := json.Marshal(order)
// {"symbol":"BTCUSDT","price":"50000.12","quantity":"1.5"}

// 反序列化
var order2 Order
json.Unmarshal(jsonData, &order2)

【8. 数据库存储】
// 使用GORM时，decimal自动处理
type Kline struct {
    Open   decimal.Decimal ` + "`" + `gorm:"type:decimal(20,8)"` + "`" + `
    High   decimal.Decimal ` + "`" + `gorm:"type:decimal(20,8)"` + "`" + `
    Low    decimal.Decimal ` + "`" + `gorm:"type:decimal(20,8)"` + "`" + `
    Close  decimal.Decimal ` + "`" + `gorm:"type:decimal(20,8)"` + "`" + `
    Volume decimal.Decimal ` + "`" + `gorm:"type:decimal(30,8)"` + "`" + `
}
`)
}

// ============================================================================
// 主函数
// ============================================================================

func main() {
	fmt.Println("╔════════════════════════════════════════════════════════════════╗")
	fmt.Println("║              Go项目依赖库详解 - 行情处理系统                   ║")
	fmt.Println("╚════════════════════════════════════════════════════════════════╝")

	ginExamples()
	websocketExamples()
	gormExamples()
	redisExamples()
	zapExamples()
	viperExamples()
	decimalExamples()

	fmt.Println("\n" + "═"*60)
	fmt.Println("库文档汇总:")
	fmt.Println("═"*60)
	fmt.Println(`
1. Gin:       https://gin-gonic.com/docs/
2. WebSocket: https://github.com/gorilla/websocket
3. GORM:      https://gorm.io/docs/
4. go-redis:  https://redis.uptrace.dev/
5. Zap:       https://pkg.go.dev/go.uber.org/zap
6. Viper:     https://github.com/spf13/viper
7. Decimal:   https://github.com/shopspring/decimal

下一步：
- 阅读 03_architecture.go 了解项目架构
- 阅读 04_deployment.go 了解部署方式
`)
}
