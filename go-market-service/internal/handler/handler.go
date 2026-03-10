/*
Package handler HTTP处理器

本包提供了行情系统的HTTP API接口，包括REST API和WebSocket实时推送。
使用Gin框架实现路由和请求处理。

========== API接口概览 ==========

REST API (HTTP):
  - GET /health                健康检查
  - GET /api/v1/klines        获取历史K线
  - GET /api/v1/klines/latest 获取最新K线
  - GET /api/v1/indicators    获取技术指标
  - GET /api/v1/ticker        获取实时行情
  - GET /api/v1/export/csv    导出CSV格式数据
  - GET /api/v1/export/json   导出JSON格式数据

WebSocket:
  - GET /ws                   实时数据推送

========== 请求参数说明 ==========

通用参数：
  - exchange: 交易所名称（binance/okx）
  - symbol: 交易对（BTCUSDT）
  - timeframe: 时间周期（1m/5m/15m/30m/1h/4h/1d/1w）

时间参数：
  - start: 开始时间（RFC3339格式，如 2024-01-01T00:00:00Z）
  - end: 结束时间（RFC3339格式）

========== 响应格式 ==========

成功响应：
	{
	    "exchange": "binance",
	    "symbol": "BTCUSDT",
	    "timeframe": "1h",
	    "count": 100,
	    "data": [...]
	}

错误响应：
	{
	    "error": "错误信息"
	}

========== WebSocket消息格式 ==========

服务端推送：
	{"type": "kline", "data": {...}}
	{"type": "tick", "data": {...}}
	{"type": "ticker", "data": {...}}

========== 使用示例 ==========

curl请求：
	# 获取K线
	curl "http://localhost:8080/api/v1/klines?exchange=binance&symbol=BTCUSDT&timeframe=1h"

	# 获取指标
	curl "http://localhost:8080/api/v1/indicators?exchange=binance&symbol=BTCUSDT&timeframe=1h"

	# 导出CSV
	curl -o data.csv "http://localhost:8080/api/v1/export/csv?exchange=binance&symbol=BTCUSDT&timeframe=1h"

WebSocket连接：
	ws := new WebSocket("ws://localhost:8080/ws")
	ws.onmessage = (event) => {
	    const msg = JSON.parse(event.data)
	    console.log(msg.type, msg.data)
	}
*/
package handler

import (
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
	"go.uber.org/zap"

	"github.com/quant/go-market-service/internal/model"
	"github.com/quant/go-market-service/internal/service"
)

/*
Handler HTTP处理器

封装HTTP请求处理逻辑，提供REST API和WebSocket服务。

字段说明：
  - svc: 核心服务层，提供数据查询和订阅功能
  - log: 日志记录器
  - upgrader: WebSocket升级器，用于将HTTP连接升级为WebSocket
*/
type Handler struct {
	// svc 核心服务层
	// 提供K线查询、指标计算、数据订阅等功能
	svc *service.Service

	// log 日志记录器
	// 添加了 component=handler 标签
	log *zap.Logger

	// upgrader WebSocket升级器
	// 负责将HTTP连接升级为WebSocket长连接
	upgrader websocket.Upgrader
}

/*
New 创建HTTP处理器

工厂函数，创建并初始化Handler实例。

参数：
  - svc: 核心服务层实例
  - log: zap日志记录器

返回：
  - 初始化完成的Handler指针

WebSocket配置：
  - CheckOrigin 返回true，允许所有跨域连接
  - 生产环境应根据需要配置跨域策略
*/
func New(svc *service.Service, log *zap.Logger) *Handler {
	return &Handler{
		svc: svc,
		log: log.With(zap.String("component", "handler")),
		upgrader: websocket.Upgrader{
			// CheckOrigin 检查请求来源
			// 返回true允许所有来源（开发环境）
			// 生产环境应验证 Origin 头
			CheckOrigin: func(r *http.Request) bool {
				return true
			},
		},
	}
}

/*
RegisterRoutes 注册HTTP路由

将所有API端点注册到Gin路由引擎。

参数：
  - r: Gin路由引擎

路由结构：
  - /health: 服务健康检查
  - /api/v1/*: REST API接口组
  - /ws: WebSocket实时推送
*/
func (h *Handler) RegisterRoutes(r *gin.Engine) {
	// 健康检查（无版本前缀）
	r.GET("/health", h.Health)

	// API v1 路由组
	v1 := r.Group("/api/v1")
	{
		// K线相关接口
		v1.GET("/klines", h.GetKlines)        // 历史K线
		v1.GET("/klines/latest", h.GetLatestKline) // 最新K线

		// 指标接口
		v1.GET("/indicators", h.GetIndicators) // 技术指标

		// 行情接口
		v1.GET("/ticker", h.GetTicker) // 实时行情

		// 数据导出接口
		v1.GET("/export/csv", h.ExportCSV)   // CSV格式
		v1.GET("/export/json", h.ExportJSON) // JSON格式
	}

	// WebSocket 实时数据推送
	r.GET("/ws", h.WebSocket)
}

/*
Health 健康检查接口

用于服务监控和负载均衡器探活。

路由：
  - GET /health

响应：
	{
	    "status": "ok",
	    "time": 1704067200
	}

用途：
  - Kubernetes 存活探针 (Liveness Probe)
  - 负载均衡器健康检查
  - 服务状态监控
*/
func (h *Handler) Health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "ok",
		"time":   time.Now().Unix(),
	})
}

/*
GetKlines 获取历史K线数据

查询指定时间范围内的K线数据。

路由：
  - GET /api/v1/klines

查询参数：
  - exchange: 交易所（必需）
  - symbol: 交易对（必需）
  - timeframe: 时间周期（必需）
  - start: 开始时间（可选，默认7天前）
  - end: 结束时间（可选，默认当前）

响应示例：
	{
	    "exchange": "binance",
	    "symbol": "BTCUSDT",
	    "timeframe": "1h",
	    "count": 168,
	    "data": [{...}, ...]
	}
*/
func (h *Handler) GetKlines(c *gin.Context) {
	// 解析查询参数
	exchange := model.Exchange(c.Query("exchange"))
	symbol := c.Query("symbol")
	timeframe := model.Timeframe(c.Query("timeframe"))

	// 解析时间范围
	start, _ := time.Parse(time.RFC3339, c.Query("start"))
	end, _ := time.Parse(time.RFC3339, c.Query("end"))

	// 设置默认时间范围
	if end.IsZero() {
		end = time.Now()
	}
	if start.IsZero() {
		start = end.AddDate(0, 0, -7) // 默认最近7天
	}

	// 从服务层获取数据
	klines, err := h.svc.GetKlines(c.Request.Context(), exchange, symbol, timeframe, start, end)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// 返回结果
	c.JSON(http.StatusOK, gin.H{
		"exchange":  exchange,
		"symbol":    symbol,
		"timeframe": timeframe,
		"count":     len(klines),
		"data":      klines,
	})
}

/*
GetLatestKline 获取最新K线

获取最近N根K线数据，无需指定时间范围。

路由：
  - GET /api/v1/klines/latest

查询参数：
  - exchange: 交易所（必需）
  - symbol: 交易对（必需）
  - timeframe: 时间周期（必需）
  - count: 获取数量（可选，默认1）

用途：
  - 初始化图表
  - 获取最新价格
*/
func (h *Handler) GetLatestKline(c *gin.Context) {
	exchange := model.Exchange(c.Query("exchange"))
	symbol := c.Query("symbol")
	timeframe := model.Timeframe(c.Query("timeframe"))
	count, _ := strconv.Atoi(c.DefaultQuery("count", "1"))

	klines, err := h.svc.GetRecentKlines(c.Request.Context(), exchange, symbol, timeframe, count)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"exchange":  exchange,
		"symbol":    symbol,
		"timeframe": timeframe,
		"data":      klines,
	})
}

/*
GetIndicators 获取技术指标

计算并返回指定K线的技术指标值。

路由：
  - GET /api/v1/indicators

查询参数：
  - exchange: 交易所（必需）
  - symbol: 交易对（必需）
  - timeframe: 时间周期（必需）

响应内容：
  - SMA各周期值
  - EMA各周期值
  - RSI
  - MACD (macd, signal, histogram)
  - 布林带 (upper, middle, lower)
  - ATR
  - 等...
*/
func (h *Handler) GetIndicators(c *gin.Context) {
	exchange := model.Exchange(c.Query("exchange"))
	symbol := c.Query("symbol")
	timeframe := model.Timeframe(c.Query("timeframe"))

	result := h.svc.GetIndicators(exchange, symbol, timeframe)
	if result == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "指标数据不可用"})
		return
	}

	c.JSON(http.StatusOK, result)
}

/*
GetTicker 获取实时行情快照

从交易所获取当前行情数据。

路由：
  - GET /api/v1/ticker

查询参数：
  - exchange: 交易所（必需）
  - symbol: 交易对（必需）

响应内容：
  - lastPrice: 最新价
  - bidPrice: 最佳买价
  - askPrice: 最佳卖价
  - volume24h: 24小时成交量
  - high24h: 24小时最高
  - low24h: 24小时最低
*/
func (h *Handler) GetTicker(c *gin.Context) {
	exchange := model.Exchange(c.Query("exchange"))
	symbol := c.Query("symbol")

	// 获取交易所实例
	ex, ok := h.svc.GetExchange(exchange)
	if !ok {
		c.JSON(http.StatusNotFound, gin.H{"error": "交易所未连接"})
		return
	}

	// 通过REST API获取实时行情
	ticker, err := ex.GetTicker(c.Request.Context(), symbol)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, ticker)
}

/*
ExportCSV 导出CSV格式数据

将K线数据导出为CSV文件，便于数据分析和回测。

路由：
  - GET /api/v1/export/csv

查询参数：
  - exchange: 交易所（必需）
  - symbol: 交易对（必需）
  - timeframe: 时间周期（必需）
  - start: 开始时间（可选，默认30天前）
  - end: 结束时间（可选，默认当前）

响应：
  - Content-Type: text/csv
  - Content-Disposition: attachment
  - 文件名格式: BTCUSDT_1h_20240101.csv
*/
func (h *Handler) ExportCSV(c *gin.Context) {
	exchange := model.Exchange(c.Query("exchange"))
	symbol := c.Query("symbol")
	timeframe := model.Timeframe(c.Query("timeframe"))

	// 解析时间范围
	start, _ := time.Parse(time.RFC3339, c.Query("start"))
	end, _ := time.Parse(time.RFC3339, c.Query("end"))
	if end.IsZero() {
		end = time.Now()
	}
	if start.IsZero() {
		start = end.AddDate(0, 0, -30) // 默认30天
	}

	// 创建数据提供者并导出
	provider := service.NewBacktestDataProvider(h.svc, h.log)
	data, err := provider.ExportCSV(c.Request.Context(), exchange, symbol, timeframe, start, end)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// 设置响应头，触发浏览器下载
	filename := symbol + "_" + string(timeframe) + "_" + time.Now().Format("20060102") + ".csv"
	c.Header("Content-Disposition", "attachment; filename="+filename)
	c.Data(http.StatusOK, "text/csv", data)
}

/*
ExportJSON 导出JSON格式数据

将K线数据导出为JSON文件。

路由：
  - GET /api/v1/export/json

参数与ExportCSV相同。

响应：
  - Content-Type: application/json
  - Content-Disposition: attachment
*/
func (h *Handler) ExportJSON(c *gin.Context) {
	exchange := model.Exchange(c.Query("exchange"))
	symbol := c.Query("symbol")
	timeframe := model.Timeframe(c.Query("timeframe"))

	start, _ := time.Parse(time.RFC3339, c.Query("start"))
	end, _ := time.Parse(time.RFC3339, c.Query("end"))
	if end.IsZero() {
		end = time.Now()
	}
	if start.IsZero() {
		start = end.AddDate(0, 0, -30)
	}

	provider := service.NewBacktestDataProvider(h.svc, h.log)
	data, err := provider.ExportJSON(c.Request.Context(), exchange, symbol, timeframe, start, end)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	filename := symbol + "_" + string(timeframe) + "_" + time.Now().Format("20060102") + ".json"
	c.Header("Content-Disposition", "attachment; filename="+filename)
	c.Data(http.StatusOK, "application/json", data)
}

/*
WebSocket 实时数据推送

建立WebSocket长连接，实时推送行情数据。

路由：
  - GET /ws（会升级为WebSocket）

推送数据类型：
  - kline: K线更新
  - tick: 逐笔成交
  - ticker: 行情快照

消息格式：
	{"type": "kline", "data": {...}}

连接生命周期：
 1. HTTP请求升级为WebSocket
 2. 注册数据订阅回调
 3. 循环接收客户端消息（保持连接）
 4. 客户端断开时清理资源

注意：
  - 当前实现订阅所有数据，未做过滤
  - 生产环境应根据客户端请求过滤推送内容
*/
func (h *Handler) WebSocket(c *gin.Context) {
	// 将HTTP连接升级为WebSocket
	conn, err := h.upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		h.log.Error("WebSocket升级失败", zap.Error(err))
		return
	}
	defer conn.Close() // 确保连接关闭

	h.log.Info("WebSocket客户端连接", zap.String("remote", c.Request.RemoteAddr))

	// 创建退出信号通道
	done := make(chan struct{})

	// 订阅K线数据
	h.svc.SubscribeKline(func(k *model.Kline) {
		select {
		case <-done:
			return // 连接已关闭，忽略
		default:
			conn.WriteJSON(gin.H{
				"type": "kline",
				"data": k,
			})
		}
	})

	// 订阅Tick数据
	h.svc.SubscribeTick(func(tick *model.Tick) {
		select {
		case <-done:
			return
		default:
			conn.WriteJSON(gin.H{
				"type": "tick",
				"data": tick,
			})
		}
	})

	// 订阅行情数据
	h.svc.SubscribeTicker(func(ticker *model.Ticker) {
		select {
		case <-done:
			return
		default:
			conn.WriteJSON(gin.H{
				"type": "ticker",
				"data": ticker,
			})
		}
	})

	// 处理客户端消息（保持连接活跃）
	for {
		// 阻塞读取消息
		_, _, err := conn.ReadMessage()
		if err != nil {
			// 检查是否为异常关闭
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				h.log.Error("WebSocket读取错误", zap.Error(err))
			}
			break // 退出循环
		}
		// 当前忽略客户端消息，仅用于保持连接
	}

	// 通知所有订阅回调退出
	close(done)
	h.log.Info("WebSocket客户端断开", zap.String("remote", c.Request.RemoteAddr))
}
