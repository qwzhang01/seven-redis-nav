# WebSocket API 文档

## 概述

WebSocket 模块提供实时数据推送功能，包括行情实时推送、交易事件推送和策略信号推送三个独立的 WebSocket 端点。

## 基础信息

- **行情WebSocket**: `ws://{host}/api/v1/ws/market?token={jwt_token}`
- **交易WebSocket**: `ws://{host}/api/v1/ws/trading?token={jwt_token}`
- **策略WebSocket**: `ws://{host}/api/v1/ws/strategy?token={jwt_token}`

---

## 连接端点

| 端点 | 路径 | 认证 | 描述 |
|------|------|------|------|
| 行情 | `/api/v1/ws/market?token={jwt_token}` | 可选 | 行情实时推送 |
| 交易 | `/api/v1/ws/trading?token={jwt_token}` | **必填** | 交易事件推送（用户私有） |
| 策略 | `/api/v1/ws/strategy?token={jwt_token}` | 可选 | 策略信号推送 |

---

## 1. 行情 WebSocket

### 连接地址

```
ws://{host}/api/v1/ws/market?token={jwt_token}
```

Token 为可选，用于身份识别。

### 支持频道

| 频道格式 | 描述 | 示例 |
|----------|------|------|
| `ticker/{symbol}` | 实时 Ticker（最新价、涨跌幅、成交量） | `ticker/BTCUSDT` |
| `kline/{symbol}/{timeframe}` | K 线数据（实时更新） | `kline/BTCUSDT/1m` |
| `depth/{symbol}` | 市场深度（买卖盘） | `depth/BTCUSDT` |

### 客户端 → 服务端 消息

#### 订阅

```json
{
  "action": "subscribe",
  "channels": ["ticker/BTCUSDT", "kline/BTCUSDT/1m"]
}
```

#### 取消订阅

```json
{
  "action": "unsubscribe",
  "channels": ["ticker/BTCUSDT"]
}
```

#### 心跳

```json
{
  "action": "ping"
}
```

### 服务端 → 客户端 消息

#### 连接成功

```json
{
  "type": "connected",
  "message": "行情 WebSocket 连接成功",
  "timestamp": "2025-02-24T19:00:00Z"
}
```

#### Ticker 推送

```json
{
  "type": "ticker",
  "channel": "ticker/BTCUSDT",
  "data": {
    "symbol": "BTCUSDT",
    "last_price": 91200.0,
    "bid_price": 91199.0,
    "ask_price": 91201.0,
    "volume": 12345.6,
    "timestamp": 1708000000
  }
}
```

#### K线推送

```json
{
  "type": "kline",
  "channel": "kline/BTCUSDT/1m",
  "data": {
    "timestamp": 1708000000,
    "open": 91000.0,
    "high": 91500.0,
    "low": 90800.0,
    "close": 91200.0,
    "volume": 125.5
  }
}
```

#### 深度推送

```json
{
  "type": "depth",
  "channel": "depth/BTCUSDT",
  "data": {
    "bids": [{"price": 91199.0, "size": 0.5}],
    "asks": [{"price": 91201.0, "size": 0.3}],
    "timestamp": 1708000000
  }
}
```

#### 心跳回复

```json
{
  "type": "pong"
}
```

#### 错误消息

```json
{
  "type": "error",
  "message": "错误描述"
}
```

---

## 2. 交易 WebSocket

### 连接地址

```
ws://{host}/api/v1/ws/trading?token={jwt_token}
```

**Token 必填**，未提供或无效的 Token 将被拒绝连接（关闭码 4001）。

### 自动订阅

连接成功后自动订阅当前用户的私有交易频道 `trading/{user_id}`。

### 连接成功消息

```json
{
  "type": "connected",
  "message": "交易 WebSocket 连接成功",
  "user_id": "user_123",
  "subscribed_channels": ["trading/user_123"],
  "timestamp": "2025-02-24T19:00:00Z"
}
```

### 推送事件类型

#### 订单状态变化

```json
{
  "type": "order_update",
  "data": {
    "order_id": "order_123",
    "symbol": "BTCUSDT",
    "side": "buy",
    "status": "filled",
    "quantity": 0.1,
    "price": 91000.0,
    "avg_price": 90950.0
  }
}
```

#### 成交通知

```json
{
  "type": "trade",
  "data": {
    "trade_id": "trade_001",
    "order_id": "order_123",
    "symbol": "BTCUSDT",
    "side": "buy",
    "price": 91000.0,
    "quantity": 0.1,
    "commission": 0.91
  }
}
```

#### 持仓变化

```json
{
  "type": "position",
  "data": {
    "symbol": "BTCUSDT",
    "quantity": 0.1,
    "avg_price": 91000.0,
    "unrealized_pnl": 50.0
  }
}
```

#### 账户余额变化

```json
{
  "type": "account",
  "data": {
    "total_equity": 100000.0,
    "available_margin": 95000.0
  }
}
```

---

## 3. 策略 WebSocket

### 连接地址

```
ws://{host}/api/v1/ws/strategy?token={jwt_token}
```

Token 为可选，用于身份识别。

### 支持频道

| 频道格式 | 描述 | 示例 |
|----------|------|------|
| `strategy/{strategy_id}` | 策略信号推送 | `strategy/strategy_abc123` |

### 订阅消息

```json
{
  "action": "subscribe",
  "channels": ["strategy/strategy_abc123"]
}
```

### 推送事件类型

#### 策略信号

```json
{
  "type": "signal",
  "channel": "strategy/strategy_abc123",
  "data": {
    "strategy_id": "strategy_abc123",
    "symbol": "BTCUSDT",
    "signal_type": "buy",
    "price": 91000.0,
    "quantity": 0.1,
    "confidence": 0.85,
    "timestamp": 1708000000
  }
}
```

#### 策略状态变化

```json
{
  "type": "strategy_status",
  "channel": "strategy/strategy_abc123",
  "data": {
    "strategy_id": "strategy_abc123",
    "state": "running",
    "message": "策略已启动"
  }
}
```

---

## 通用说明

### 消息协议

所有 WebSocket 通信均使用 JSON 格式文本消息。

### 客户端操作

| 操作 | action 值 | 描述 |
|------|----------|------|
| 订阅 | `subscribe` | 订阅一个或多个频道 |
| 取消订阅 | `unsubscribe` | 取消订阅一个或多个频道 |
| 心跳 | `ping` | 客户端心跳，服务端回复 pong |

### 连接关闭码

| 关闭码 | 描述 |
|--------|------|
| 1000 | 正常关闭 |
| 4001 | 认证失败（Token 无效或缺失，仅 trading WS） |

### 重连建议

- 建议客户端在连接断开后使用指数退避策略重连
- 重连后需重新订阅之前的频道
- 交易 WebSocket 会自动重新订阅用户私有频道
