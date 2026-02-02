module github.com/quant/go-market-service

go 1.22

require (
	// Web框架 - Gin 高性能HTTP框架
	github.com/gin-gonic/gin v1.9.1

	// WebSocket - gorilla/websocket 行业标准
	github.com/gorilla/websocket v1.5.1

	// 配置管理 - viper
	github.com/spf13/viper v1.18.2

	// 日志 - zap 高性能结构化日志
	go.uber.org/zap v1.27.0

	// Redis - go-redis
	github.com/redis/go-redis/v9 v9.4.0

	// 数据库 - gorm + PostgreSQL/TimescaleDB
	gorm.io/gorm v1.25.7
	gorm.io/driver/postgres v1.5.6

	// 消息队列 - kafka
	github.com/segmentio/kafka-go v0.4.47

	// gRPC
	google.golang.org/grpc v1.62.0
	google.golang.org/protobuf v1.32.0

	// 工具库
	github.com/shopspring/decimal v1.3.1  // 高精度小数
	github.com/robfig/cron/v3 v3.0.1       // 定时任务
	golang.org/x/sync v0.6.0               // 并发工具
)
