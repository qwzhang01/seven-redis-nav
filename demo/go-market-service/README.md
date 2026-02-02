# Go量化交易行情处理系统

高性能的量化交易行情处理后端系统，使用Go语言实现。

## 🚀 特性

- **多交易所支持**: Binance、OKX等主流交易所
- **实时数据采集**: WebSocket实时推送，毫秒级延迟
- **多周期K线聚合**: 支持1m/5m/15m/30m/1h/4h/1d/1w等周期
- **技术指标计算**: SMA/EMA/RSI/MACD/布林带/ATR/ADX/KDJ等
- **高性能存储**: PostgreSQL + TimescaleDB时序数据库
- **实时缓存**: Redis缓存热点数据
- **数据输出服务**: 支持回测和实盘两种模式
- **REST API**: 提供完整的HTTP接口
- **WebSocket推送**: 实时数据推送

## 📦 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web框架 | Gin | 高性能HTTP框架 |
| WebSocket | gorilla/websocket | 行业标准WebSocket库 |
| 配置管理 | Viper | 支持YAML/JSON/环境变量 |
| 日志 | Zap | 高性能结构化日志 |
| 数据库 | GORM + PostgreSQL | ORM + TimescaleDB时序扩展 |
| 缓存 | go-redis | Redis客户端 |
| 消息队列 | kafka-go | Kafka消息中间件 |
| 精度计算 | shopspring/decimal | 高精度小数运算 |

## 📁 项目结构

```
go-market-service/
├── cmd/
│   └── server/
│       └── main.go           # 程序入口
├── configs/
│   └── config.yaml           # 配置文件
├── internal/
│   ├── config/               # 配置管理
│   ├── exchange/             # 交易所接口
│   │   ├── interface.go      # 交易所接口定义
│   │   ├── binance.go        # Binance实现
│   │   ├── okx.go            # OKX实现
│   │   └── factory.go        # 交易所工厂
│   ├── model/                # 数据模型
│   │   ├── market.go         # 行情模型
│   │   └── entity.go         # 数据库实体
│   ├── kline/                # K线处理
│   │   └── aggregator.go     # K线聚合器
│   ├── indicator/            # 技术指标
│   │   ├── indicators.go     # 指标算法实现
│   │   └── calculator.go     # 指标计算服务
│   ├── storage/              # 存储层
│   │   ├── storage.go        # 存储初始化
│   │   └── kline_repository.go # K线仓库
│   ├── service/              # 业务服务
│   │   ├── service.go        # 核心服务
│   │   └── datafeed.go       # 数据输出服务
│   ├── handler/              # HTTP处理器
│   │   └── handler.go        # 路由处理
│   └── middleware/           # 中间件
│       └── middleware.go     # 日志/恢复/CORS
├── pkg/
│   └── logger/               # 日志工具
├── examples/
│   ├── backtest_demo.go      # 回测示例
│   └── live_demo.go          # 实盘示例
├── go.mod                    # Go模块定义
└── README.md                 # 项目说明
```

## 🛠️ 快速开始

### 1. 环境准备

```bash
# 安装PostgreSQL + TimescaleDB
docker run -d --name timescaledb -p 5432:5432 \
  -e POSTGRES_PASSWORD=quant123 \
  -e POSTGRES_USER=quant \
  -e POSTGRES_DB=market_data \
  timescale/timescaledb:latest-pg15

# 安装Redis
docker run -d --name redis -p 6379:6379 redis:latest

# 可选：安装Kafka
docker run -d --name kafka -p 9092:9092 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  confluentinc/cp-kafka:latest
```

### 2. 配置修改

编辑 `configs/config.yaml`:

```yaml
market:
  exchanges:
    - name: binance
      enabled: true
      api_key: YOUR_API_KEY
      secret_key: YOUR_SECRET_KEY
      symbols:
        - BTCUSDT
        - ETHUSDT
```

### 3. 启动服务

```bash
# 下载依赖
go mod tidy

# 运行服务
go run cmd/server/main.go -config configs/config.yaml
```

### 4. 验证服务

```bash
# 健康检查
curl http://localhost:8080/health

# 获取K线
curl "http://localhost:8080/api/v1/klines?exchange=binance&symbol=BTCUSDT&timeframe=1h"

# 获取指标
curl "http://localhost:8080/api/v1/indicators?exchange=binance&symbol=BTCUSDT&timeframe=1h"
```

## 📡 API接口

### REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查 |
| GET | /api/v1/klines | 获取K线数据 |
| GET | /api/v1/klines/latest | 获取最新K线 |
| GET | /api/v1/indicators | 获取技术指标 |
| GET | /api/v1/ticker | 获取行情快照 |
| GET | /api/v1/export/csv | 导出CSV数据 |
| GET | /api/v1/export/json | 导出JSON数据 |
| WS | /ws | WebSocket实时推送 |

### WebSocket消息格式

```json
// K线数据
{
  "type": "kline",
  "data": {
    "exchange": "binance",
    "symbol": "BTCUSDT",
    "timeframe": "1m",
    "open": "50000.00",
    "high": "50100.00",
    "low": "49900.00",
    "close": "50050.00",
    "volume": "100.5",
    "is_closed": true
  }
}

// Tick数据
{
  "type": "tick",
  "data": {
    "exchange": "binance",
    "symbol": "BTCUSDT",
    "price": "50000.00",
    "quantity": "0.1",
    "is_buyer": true
  }
}
```

## 📊 支持的技术指标

| 类型 | 指标 | 说明 |
|------|------|------|
| 均线 | SMA | 简单移动平均线 |
| 均线 | EMA | 指数移动平均线 |
| 均线 | WMA | 加权移动平均线 |
| 均线 | DEMA | 双指数移动平均线 |
| 震荡 | RSI | 相对强弱指标 |
| 震荡 | MACD | 指数平滑异同移动平均线 |
| 震荡 | KDJ | 随机指标 |
| 波动 | 布林带 | Bollinger Bands |
| 波动 | ATR | 真实波动幅度均值 |
| 趋势 | ADX | 平均趋向指标 |
| 趋势 | 一目均衡表 | Ichimoku Cloud |
| 成交量 | OBV | 能量潮指标 |
| 成交量 | VWAP | 成交量加权平均价 |
| 支撑阻力 | Pivot Points | 轴心点 |

## 🔄 数据输出服务

### 回测模式

```go
feedCfg := &service.DataFeedConfig{
    Mode:       service.DataFeedModeBacktest,
    Exchange:   model.ExchangeBinance,
    Symbols:    []string{"BTCUSDT"},
    Timeframes: []model.Timeframe{model.Timeframe1h},
    StartTime:  time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
    EndTime:    time.Date(2024, 6, 1, 0, 0, 0, 0, time.UTC),
    Speed:      100, // 100倍速回放
    EnableIndicators: true,
    Indicators: []string{"rsi", "macd", "ema_12", "ema_26"},
}

feed := service.NewDataFeed(feedCfg, svc, log)
feed.Subscribe(func(dp *service.DataPoint) {
    // 处理数据点
})
feed.Start(ctx)
```

### 实盘模式

```go
feedCfg := &service.DataFeedConfig{
    Mode:       service.DataFeedModeLive,
    Exchange:   model.ExchangeBinance,
    Symbols:    []string{"BTCUSDT", "ETHUSDT"},
    Timeframes: []model.Timeframe{model.Timeframe1m, model.Timeframe5m},
    EnableIndicators: true,
}

feed := service.NewDataFeed(feedCfg, svc, log)
feed.Subscribe(handler)
feed.Start(ctx)
```

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ REST API │  │WebSocket │  │   gRPC   │  │  Kafka   │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
└───────┼─────────────┼─────────────┼─────────────┼───────────┘
        │             │             │             │
┌───────┴─────────────┴─────────────┴─────────────┴───────────┐
│                       Service Layer                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Data Service                       │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐      │   │
│  │  │ DataFeed   │  │ Indicator  │  │ Kline      │      │   │
│  │  │ (回测/实盘) │  │ Calculator │  │ Aggregator │      │   │
│  │  └────────────┘  └────────────┘  └────────────┘      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
        │
┌───────┴─────────────────────────────────────────────────────┐
│                      Exchange Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ Binance  │  │   OKX    │  │  Bybit   │  ...              │
│  │ Adapter  │  │ Adapter  │  │ Adapter  │                   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                   │
└───────┼─────────────┼─────────────┼─────────────────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │ WebSocket / REST
        ┌─────────────┴─────────────┐
        │      Exchange APIs        │
        └───────────────────────────┘
```

## 📈 性能优化

1. **并发处理**: 使用goroutine并发处理多个交易对
2. **内存缓存**: K线缓冲区减少数据库访问
3. **批量写入**: 批量插入数据库提高写入效率
4. **连接池**: 数据库和Redis连接池复用
5. **时序数据库**: TimescaleDB优化时序数据存储

## 📝 License

MIT License
