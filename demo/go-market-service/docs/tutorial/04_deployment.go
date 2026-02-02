/*
================================================================================
                    部署与系统集成教程 - Go行情处理系统
================================================================================

本教程详细讲解：
1. 本地开发环境搭建
2. Docker容器化部署
3. Kubernetes生产部署
4. 与Python量化系统集成
5. 监控与运维
*/

package main

import (
	"fmt"
)

// ============================================================================
// 第1章：本地开发环境搭建
// ============================================================================

func chapter1_local_setup() {
	fmt.Println(`
=== 第1章：本地开发环境搭建 ===

【1. 安装Go】
# macOS
brew install go

# Ubuntu
sudo apt install golang-go

# 或者从官网下载
# https://go.dev/dl/

# 验证安装
go version  # 需要 Go 1.22+

# 设置环境变量（通常自动设置）
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin


【2. 安装依赖服务】

# === PostgreSQL + TimescaleDB ===
# 使用Docker（推荐）
docker run -d \
  --name timescaledb \
  -p 5432:5432 \
  -e POSTGRES_USER=quant \
  -e POSTGRES_PASSWORD=quant123 \
  -e POSTGRES_DB=market_data \
  -v timescaledb_data:/var/lib/postgresql/data \
  timescale/timescaledb:latest-pg15

# 验证连接
psql -h localhost -U quant -d market_data
# 密码: quant123


# === Redis ===
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine

# 验证连接
redis-cli ping
# 返回: PONG


【3. 克隆并运行项目】

# 进入项目目录
cd go-market-service

# 下载依赖
go mod tidy

# 如果网络问题，设置代理
go env -w GOPROXY=https://goproxy.cn,direct

# 初始化数据库（可选，GORM会自动迁移）
psql -h localhost -U quant -d market_data -f scripts/init_db.sql

# 修改配置文件
vim configs/config.yaml
# 设置交易所API Key

# 运行服务
go run cmd/server/main.go -config configs/config.yaml

# 验证服务
curl http://localhost:8080/health


【4. 配置IDE（VSCode推荐）】

# 安装Go扩展
# 1. 打开VSCode
# 2. 安装 "Go" 扩展（由Go Team开发）
# 3. 按 Cmd+Shift+P，输入 "Go: Install/Update Tools"
# 4. 全选并安装

# 推荐的settings.json配置
{
    "go.useLanguageServer": true,
    "go.lintTool": "golangci-lint",
    "go.formatTool": "goimports",
    "editor.formatOnSave": true,
    "[go]": {
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}


【5. 常用Go命令】

# 运行
go run main.go

# 构建
go build -o bin/server cmd/server/main.go

# 测试
go test ./...

# 测试覆盖率
go test -cover ./...

# 格式化代码
go fmt ./...
goimports -w .

# 代码检查
go vet ./...
golangci-lint run

# 更新依赖
go get -u ./...
go mod tidy

# 查看依赖
go list -m all

# 清理缓存
go clean -cache
`)
}

// ============================================================================
// 第2章：Docker容器化部署
// ============================================================================

func chapter2_docker_deployment() {
	fmt.Println(`
=== 第2章：Docker容器化部署 ===

【1. Dockerfile解析】

# ===== go-market-service/Dockerfile =====

# ---------- 构建阶段 ----------
# 使用官方Go镜像作为构建环境
FROM golang:1.22-alpine AS builder

# 设置工作目录
WORKDIR /app

# 安装必要工具（如git，用于私有依赖）
RUN apk add --no-cache git

# 先复制依赖文件，利用Docker层缓存
# 只有go.mod/go.sum变化时才重新下载依赖
COPY go.mod go.sum ./
RUN go mod download

# 复制源代码
COPY . .

# 编译
# CGO_ENABLED=0 - 禁用CGO，生成静态链接二进制
# GOOS=linux - 目标操作系统
# -a - 强制重新构建所有包
# -installsuffix cgo - 安装后缀，避免和其他构建冲突
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo \
    -o market-service cmd/server/main.go


# ---------- 运行阶段 ----------
# 使用精简的Alpine镜像，大小约5MB
FROM alpine:3.19

WORKDIR /app

# 安装证书（HTTPS需要）和时区数据
RUN apk add --no-cache ca-certificates tzdata

# 从构建阶段复制二进制文件
COPY --from=builder /app/market-service .
COPY --from=builder /app/configs ./configs

# 设置时区
ENV TZ=Asia/Shanghai

# 暴露端口
EXPOSE 8080 50051

# 启动命令
CMD ["./market-service", "-config", "configs/config.yaml"]


【2. 构建镜像】

# 构建镜像
docker build -t go-market-service:latest .

# 查看镜像大小
docker images go-market-service
# 预期大小约 20-30MB（非常小！）

# 带版本标签
docker build -t go-market-service:v1.0.0 .

# 推送到仓库（如Docker Hub）
docker login
docker tag go-market-service:latest yourusername/go-market-service:latest
docker push yourusername/go-market-service:latest


【3. Docker Compose编排】

# ===== docker-compose.yaml =====
version: '3.8'

services:
  # TimescaleDB 时序数据库
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    container_name: market-timescaledb
    environment:
      POSTGRES_USER: quant
      POSTGRES_PASSWORD: quant123
      POSTGRES_DB: market_data
    ports:
      - "5432:5432"
    volumes:
      - timescaledb_data:/var/lib/postgresql/data
      # 自动执行初始化SQL
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U quant -d market_data"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    container_name: market-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # 行情服务
  market-service:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: market-service
    # 等待依赖服务健康
    depends_on:
      timescaledb:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8080:8080"
      - "50051:50051"
    environment:
      # 通过环境变量覆盖配置
      MARKET_STORAGE_POSTGRES_HOST: timescaledb
      MARKET_STORAGE_REDIS_ADDR: redis:6379
      MARKET_LOG_LEVEL: info
    volumes:
      # 挂载配置文件（方便修改）
      - ./configs:/app/configs
    restart: unless-stopped

volumes:
  timescaledb_data:
  redis_data:


【4. 使用Docker Compose】

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f market-service

# 查看服务状态
docker-compose ps

# 重启服务
docker-compose restart market-service

# 停止服务
docker-compose down

# 停止并删除数据
docker-compose down -v


【5. 生产环境配置】

# docker-compose.prod.yaml
version: '3.8'

services:
  market-service:
    image: go-market-service:v1.0.0
    deploy:
      replicas: 3  # 3个副本
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    environment:
      MARKET_ENV: production
      MARKET_LOG_FORMAT: json
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
`)
}

// ============================================================================
// 第3章：与Python量化系统集成
// ============================================================================

func chapter3_python_integration() {
	fmt.Println(`
=== 第3章：与Python量化系统集成 ===

【集成架构】

┌─────────────────────────────────────────────────────────────┐
│                    Python量化交易系统                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  策略引擎   │  │  回测引擎   │  │  AI训练     │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│              ┌───────────┴───────────┐                      │
│              │     数据接口层        │                      │
│              │  (REST/WebSocket)     │                      │
│              └───────────┬───────────┘                      │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           │ HTTP/WebSocket
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                          ▼                                  │
│              ┌───────────────────────┐                      │
│              │   Go行情处理系统      │                      │
│              │   (go-market-service) │                      │
│              └───────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘


【1. REST API调用】

# Python代码示例
import requests
import pandas as pd
from datetime import datetime, timedelta

class MarketDataClient:
    """Go行情服务客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_klines(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        start: datetime = None,
        end: datetime = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """获取K线数据"""
        params = {
            "exchange": exchange,
            "symbol": symbol,
            "timeframe": timeframe,
            "limit": limit
        }
        
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        
        response = self.session.get(
            f"{self.base_url}/api/v1/klines",
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        df = pd.DataFrame(data["data"])
        
        # 转换数据类型
        df["open_time"] = pd.to_datetime(df["open_time"])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col])
        
        return df.set_index("open_time")
    
    def get_indicators(
        self,
        exchange: str,
        symbol: str,
        timeframe: str
    ) -> dict:
        """获取技术指标"""
        params = {
            "exchange": exchange,
            "symbol": symbol,
            "timeframe": timeframe
        }
        
        response = self.session.get(
            f"{self.base_url}/api/v1/indicators",
            params=params
        )
        response.raise_for_status()
        
        return response.json()["indicators"]
    
    def export_csv(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        output_path: str
    ):
        """导出CSV数据"""
        params = {
            "exchange": exchange,
            "symbol": symbol,
            "timeframe": timeframe,
            "start": start.isoformat(),
            "end": end.isoformat()
        }
        
        response = self.session.get(
            f"{self.base_url}/api/v1/export/csv",
            params=params
        )
        
        with open(output_path, "wb") as f:
            f.write(response.content)


# 使用示例
client = MarketDataClient()

# 获取K线
df = client.get_klines(
    exchange="binance",
    symbol="BTCUSDT",
    timeframe="1h",
    limit=200
)

# 获取指标
indicators = client.get_indicators("binance", "BTCUSDT", "1h")
print(f"RSI: {indicators['rsi']}")
print(f"MACD: {indicators['macd']}")


【2. WebSocket实时数据】

import asyncio
import websockets
import json

class MarketDataStream:
    """WebSocket实时数据流"""
    
    def __init__(self, url: str = "ws://localhost:8080/ws"):
        self.url = url
        self.callbacks = {
            "tick": [],
            "kline": [],
            "ticker": []
        }
    
    def on_tick(self, callback):
        """注册Tick回调"""
        self.callbacks["tick"].append(callback)
        return callback
    
    def on_kline(self, callback):
        """注册K线回调"""
        self.callbacks["kline"].append(callback)
        return callback
    
    async def connect(self):
        """连接并处理消息"""
        async with websockets.connect(self.url) as ws:
            print(f"已连接: {self.url}")
            
            async for message in ws:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type in self.callbacks:
                    for callback in self.callbacks[msg_type]:
                        callback(data["data"])
    
    def run(self):
        """启动事件循环"""
        asyncio.run(self.connect())


# 使用示例
stream = MarketDataStream()

@stream.on_kline
def handle_kline(kline):
    print(f"K线: {kline['symbol']} {kline['close']}")
    
    # 如果K线完成，触发策略计算
    if kline.get("is_closed"):
        # 调用策略...
        pass

@stream.on_tick
def handle_tick(tick):
    print(f"Tick: {tick['symbol']} {tick['price']}")

# 启动
stream.run()


【3. 在Python策略中使用Go数据】

from quant_trading_system.services.strategy import Strategy
from market_data_client import MarketDataClient

class MyStrategy(Strategy):
    """使用Go行情数据的策略"""
    
    def __init__(self):
        super().__init__()
        self.market_client = MarketDataClient()
    
    def on_init(self):
        """初始化：加载历史数据"""
        # 从Go服务获取历史K线
        self.df = self.market_client.get_klines(
            exchange="binance",
            symbol="BTCUSDT",
            timeframe="1h",
            limit=500
        )
    
    def on_bar(self, bar):
        """K线事件"""
        # 获取最新指标
        indicators = self.market_client.get_indicators(
            "binance", "BTCUSDT", "1h"
        )
        
        rsi = float(indicators["rsi"])
        macd = float(indicators["macd"])
        
        # 策略逻辑
        if rsi < 30 and macd > 0:
            self.buy("BTCUSDT", 1.0)
        elif rsi > 70 and macd < 0:
            self.sell("BTCUSDT", 1.0)


【4. 回测集成】

# 从Go服务导出历史数据用于回测
def prepare_backtest_data(
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime
) -> pd.DataFrame:
    """准备回测数据"""
    client = MarketDataClient()
    
    # 导出CSV（大量数据更高效）
    csv_path = f"data/{symbol}_{timeframe}.csv"
    client.export_csv(
        exchange="binance",
        symbol=symbol,
        timeframe=timeframe,
        start=start,
        end=end,
        output_path=csv_path
    )
    
    # 读取CSV
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    return df.set_index("timestamp")


# 回测
from quant_trading_system.services.backtest import BacktestEngine

df = prepare_backtest_data(
    "BTCUSDT", "1h",
    datetime(2024, 1, 1),
    datetime(2024, 12, 31)
)

engine = BacktestEngine(
    data=df,
    strategy=MyStrategy(),
    initial_capital=100000
)
result = engine.run()
print(result.summary())
`)
}

// ============================================================================
// 第4章：监控与运维
// ============================================================================

func chapter4_monitoring() {
	fmt.Println(`
=== 第4章：监控与运维 ===

【1. 健康检查】

# 简单健康检查
curl http://localhost:8080/health
# 返回: {"status":"ok","time":1234567890}

# 添加详细健康检查端点
// handler/health.go
func (h *Handler) HealthDetailed(c *gin.Context) {
    // 检查数据库
    dbOK := h.checkDB()
    // 检查Redis
    redisOK := h.checkRedis()
    // 检查交易所连接
    exchangesOK := h.checkExchanges()
    
    status := "ok"
    if !dbOK || !redisOK {
        status = "degraded"
    }
    
    c.JSON(200, gin.H{
        "status": status,
        "components": gin.H{
            "database":  dbOK,
            "redis":     redisOK,
            "exchanges": exchangesOK,
        },
        "timestamp": time.Now().Unix(),
    })
}


【2. Prometheus指标】

# 安装prometheus客户端
go get github.com/prometheus/client_golang/prometheus

// metrics/metrics.go
import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    // 请求计数
    HttpRequestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "HTTP请求总数",
        },
        []string{"method", "path", "status"},
    )
    
    // 请求延迟
    HttpRequestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "http_request_duration_seconds",
            Help:    "HTTP请求延迟",
            Buckets: prometheus.DefBuckets,
        },
        []string{"method", "path"},
    )
    
    // K线处理数
    KlinesProcessed = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "klines_processed_total",
            Help: "处理的K线数量",
        },
        []string{"exchange", "symbol", "timeframe"},
    )
    
    // WebSocket连接数
    WsConnections = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "websocket_connections",
            Help: "当前WebSocket连接数",
        },
    )
)

// 在中间件中记录
func MetricsMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        
        c.Next()
        
        duration := time.Since(start).Seconds()
        status := strconv.Itoa(c.Writer.Status())
        
        HttpRequestsTotal.WithLabelValues(
            c.Request.Method,
            c.FullPath(),
            status,
        ).Inc()
        
        HttpRequestDuration.WithLabelValues(
            c.Request.Method,
            c.FullPath(),
        ).Observe(duration)
    }
}

// 暴露指标端点
r.GET("/metrics", gin.WrapH(promhttp.Handler()))


【3. 日志管理】

# 生产环境日志配置
# configs/config.yaml
log:
  level: info
  format: json  # 结构化JSON日志
  output_path: /var/log/market-service/app.log

# 日志轮转（使用logrotate）
# /etc/logrotate.d/market-service
/var/log/market-service/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}

# ELK日志收集
# docker-compose-logging.yaml
services:
  filebeat:
    image: docker.elastic.co/beats/filebeat:8.11.0
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml
      - /var/log/market-service:/var/log/market-service:ro


【4. 常见问题排查】

# 1. 检查服务状态
docker-compose ps

# 2. 查看日志
docker-compose logs -f --tail=100 market-service

# 3. 进入容器调试
docker exec -it market-service sh

# 4. 检查端口
netstat -tlnp | grep 8080

# 5. 检查数据库连接
docker exec -it market-timescaledb psql -U quant -d market_data -c "SELECT count(*) FROM klines;"

# 6. 检查Redis
docker exec -it market-redis redis-cli info

# 7. 检查内存使用
docker stats market-service

# 8. Go性能分析
# 添加pprof端点
import _ "net/http/pprof"
// 访问 http://localhost:8080/debug/pprof/

# 生成CPU profile
go tool pprof http://localhost:8080/debug/pprof/profile?seconds=30

# 生成内存profile
go tool pprof http://localhost:8080/debug/pprof/heap


【5. 备份与恢复】

# 备份PostgreSQL
docker exec market-timescaledb pg_dump -U quant market_data > backup.sql

# 恢复
docker exec -i market-timescaledb psql -U quant market_data < backup.sql

# 定时备份脚本
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backup/market

mkdir -p $BACKUP_DIR

# 备份数据库
docker exec market-timescaledb pg_dump -U quant market_data | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 备份Redis
docker exec market-redis redis-cli BGSAVE
docker cp market-redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# 保留最近7天
find $BACKUP_DIR -mtime +7 -delete

# 添加到crontab
# 0 2 * * * /path/to/backup.sh
`)
}

// ============================================================================
// 第5章：面试问题与解答
// ============================================================================

func chapter5_interview() {
	fmt.Println(`
=== 第5章：Go行情系统面试问题 ===

【Q1: 为什么选择Go而不是Python处理行情数据？】

A: 
1. 性能: Go编译型语言，性能是Python的10-100倍
2. 并发: goroutine轻量级协程，可同时处理数千连接
3. 内存: Go内存占用小，GC效率高
4. 部署: 编译成单一二进制，无需安装运行时
5. 类型安全: 编译时检查，减少运行时错误

具体场景:
- 交易所WebSocket需要保持长连接，Go的net包非常高效
- 多交易对数据需要并发处理，goroutine非常适合
- 实时计算指标需要低延迟，Go性能更好


【Q2: 解释一下项目的并发模型】

A:
1. goroutine处理:
   - 每个交易所连接一个goroutine处理消息
   - 数据回调使用go关键字异步执行
   - 避免阻塞主数据流

2. channel通信:
   - stopCh用于优雅关闭
   - 数据传递通过channel而非共享内存

3. 锁保护:
   - sync.RWMutex保护共享状态
   - 读多写少场景使用读写锁

4. context控制:
   - 用于超时和取消
   - 传递请求级别的信息


【Q3: 如何保证K线数据的准确性？】

A:
1. 时间对齐:
   - calculateOpenTime()正确对齐各周期边界
   - 考虑UTC时区问题

2. 原子操作:
   - K线更新在锁保护下进行
   - 使用decimal避免浮点精度问题

3. 数据验证:
   - 检查High >= max(Open, Close)
   - 检查Low <= min(Open, Close)

4. 重复数据处理:
   - 数据库使用UPSERT避免重复
   - Redis缓存有过期时间


【Q4: WebSocket断线重连机制是怎样的？】

A:
func (b *BinanceExchange) handleReconnect() {
    b.mu.Lock()
    b.isConnected = false
    b.mu.Unlock()
    
    // 指数退避重连
    backoff := time.Second
    maxBackoff := time.Minute
    
    for {
        select {
        case <-b.stopCh:  // 主动停止
            return
        case <-time.After(backoff):
            err := b.Connect(context.Background())
            if err != nil {
                // 增加等待时间
                backoff *= 2
                if backoff > maxBackoff {
                    backoff = maxBackoff
                }
                continue
            }
            return  // 重连成功
        }
    }
}

关键点:
1. 指数退避：避免频繁重连
2. 最大等待时间限制
3. 支持主动停止


【Q5: 如何保证高并发下的数据一致性？】

A:
1. 锁策略:
   - 读写分离，RWMutex
   - 锁粒度控制，避免大锁

2. 并发安全数据结构:
   - sync.Map用于高并发读写
   - channel用于数据传递

3. 数据库层:
   - 使用GORM事务
   - 数据库连接池

4. 缓存一致性:
   - 写入DB后更新Redis
   - 设置合理的TTL


【Q6: 项目中用到了哪些设计模式？】

A:
1. 策略模式 (Exchange接口):
   - 定义统一接口
   - 不同交易所不同实现
   - 业务层无需关心具体交易所

2. 工厂模式 (ExchangeFactory):
   - 根据配置创建实例
   - 封装创建逻辑

3. 观察者模式 (订阅机制):
   - SubscribeKline/SubscribeTick
   - 发布-订阅解耦

4. 仓库模式 (KlineRepository):
   - 数据访问抽象
   - 隔离存储细节

5. 建造者模式 (配置加载):
   - Viper灵活配置
   - 支持多来源


【Q7: 如何优化系统性能？】

A:
1. 减少内存分配:
   - 预分配slice容量
   - 对象复用

2. 批量操作:
   - 数据库批量插入
   - Redis Pipeline

3. 缓存策略:
   - 内存缓存最近K线
   - Redis缓存热点数据

4. 并发优化:
   - goroutine池
   - 读写锁分离

5. 数据库优化:
   - TimescaleDB时序优化
   - 合理的索引设计
`)
}

// ============================================================================
// 主函数
// ============================================================================

func main() {
	fmt.Println("╔════════════════════════════════════════════════════════════════╗")
	fmt.Println("║               部署与系统集成教程                               ║")
	fmt.Println("╚════════════════════════════════════════════════════════════════╝")

	chapter1_local_setup()
	chapter2_docker_deployment()
	chapter3_python_integration()
	chapter4_monitoring()
	chapter5_interview()

	fmt.Println("\n" + "═"*60)
	fmt.Println("教程完成！")
	fmt.Println("═"*60)
	fmt.Println(`
【学习路径总结】
1. 01_go_basics.go - Go语言基础
2. 02_libraries_guide.go - 依赖库详解
3. 03_architecture.go - 项目架构
4. 04_deployment.go - 部署与集成（本文件）

【快速启动】
cd go-market-service
docker-compose up -d
go run cmd/server/main.go

【验证服务】
curl http://localhost:8080/health
curl "http://localhost:8080/api/v1/klines?exchange=binance&symbol=BTCUSDT&timeframe=1h"

祝你学习顺利！
`)
}
