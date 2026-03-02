# WebSocket API 文档

## 概述

WebSocket 模块提供实时数据推送功能，包含三个独立的 WebSocket 端点：行情实时推送、交易事件推送、策略信号推送。所有 WebSocket 通信均使用 JSON 格式文本消息。

## 基础信息

| 端点 | 连接地址 | 认证 | 描述 |
|------|---------|------|------|
| 行情 | `ws://{host}/api/v1/ws/market?token={jwt_token}` | 可选 | 行情实时推送（Ticker、K线、深度） |
| 交易 | `ws://{host}/api/v1/ws/trading?token={jwt_token}` | **必填** | 用户私有交易事件推送 |
| 策略 | `ws://{host}/api/v1/ws/strategy?token={jwt_token}` | 可选 | 策略信号实时推送 |

---

## 连接管理器

系统使用全局单例 `WebSocketManager` 统一管理所有 WebSocket 连接，核心功能：

- **连接管理**：维护所有活跃的 WebSocket 连接集合
- **频道订阅**：维护频道与连接的订阅映射关系（channel → Set[WebSocket]）
- **消息广播**：向指定频道内所有订阅者广播消息
- **自动清理**：广播时自动检测并清理已断开的连接

### 支持的频道格式

| 频道格式 | 描述 |
|----------|------|
| `ticker/{symbol}` | 实时 Ticker 行情 |
| `kline/{symbol}/{timeframe}` | K 线数据 |
| `depth/{symbol}` | 市场深度 |
| `strategy/{strategy_id}` | 策略信号 |
| `trading/{user_id}` | 交易事件（私有） |

---

## 通用消息协议

### 客户端 → 服务端

#### 订阅频道

```json
{
  "action": "subscribe",
  "channels": ["ticker/BTCUSDT", "kline/BTCUSDT/1m"]
}
```

**服务端回复：**

```json
{
  "type": "subscribed",
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

**服务端回复：**

```json
{
  "type": "unsubscribed",
  "channels": ["ticker/BTCUSDT"]
}
```

#### 心跳

```json
{
  "action": "ping"
}
```

**服务端回复：**

```json
{
  "type": "pong"
}
```

#### 错误消息

当客户端发送无效 JSON 或未知 action 时，服务端回复：

```json
{
  "type": "error",
  "message": "无效的 JSON 格式"
}
```

```json
{
  "type": "error",
  "message": "未知 action: xxx"
}
```

---

## 1. 行情 WebSocket

### 连接地址

```
ws://{host}/api/v1/ws/market?token={jwt_token}
```

### 参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | 否 | JWT Token，用于身份识别 |

### 连接流程

1. 客户端发起 WebSocket 连接
2. 服务端通过可选 token 解析 `user_id`（通过 `JWTUtils.verify_token` 从 `user_id` 或 `sub` 字段获取）
3. 连接建立，服务端发送欢迎消息
4. 客户端通过 subscribe/unsubscribe 消息管理频道订阅

### 连接成功消息

```json
{
  "type": "connected",
  "message": "行情 WebSocket 连接成功",
  "timestamp": "2025-02-24T19:00:00.000000"
}
```

### 支持频道

| 频道格式 | 描述 | 示例 |
|----------|------|------|
| `ticker/{symbol}` | 实时 Ticker（最新价、涨跌幅、成交量） | `ticker/BTCUSDT` |
| `kline/{symbol}/{timeframe}` | K 线数据（实时更新） | `kline/BTCUSDT/1m` |
| `depth/{symbol}` | 市场深度（买卖盘） | `depth/BTCUSDT` |

### 服务端推送消息

#### Ticker 推送

由行情服务（`MarketService`）在收到新 Tick 时通过 `push_ticker(symbol, data)` 推送。

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

#### K 线推送

由行情服务在 K 线更新时通过 `push_kline(symbol, timeframe, data)` 推送。

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

通过 `push_depth(symbol, data)` 推送。

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

---

## 2. 交易 WebSocket

### 连接地址

```
ws://{host}/api/v1/ws/trading?token={jwt_token}
```

### 参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | **是** | JWT 访问令牌 |

### 认证机制

- Token **必填**，通过 `JWTUtils.verify_token` 验证
- 从 token payload 的 `user_id` 或 `sub` 字段提取用户 ID
- Token 缺失或无效时，服务端关闭连接（关闭码 **4001**，携带错误原因）

### 连接流程

1. 客户端发起 WebSocket 连接，必须携带 token 参数
2. 服务端验证 token，失败则关闭连接（4001）
3. 连接建立，**自动订阅**用户私有频道 `trading/{user_id}`
4. 服务端发送连接成功消息（含用户信息和已订阅频道）
5. 客户端可通过 subscribe/unsubscribe 额外订阅其他频道

### 连接成功消息

```json
{
  "type": "connected",
  "message": "交易 WebSocket 连接成功",
  "user_id": "user_123",
  "subscribed_channels": ["trading/user_123"],
  "timestamp": "2025-02-24T19:00:00.000000"
}
```

### 推送事件类型

#### 订单状态变化

由交易引擎在订单状态变化时通过 `push_order_update(user_id, order_data)` 推送。

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

通过 `push_trade_notification(user_id, trade_data)` 推送。

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

通过 `push_position_update(user_id, position_data)` 推送。

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

---

## 3. 策略 WebSocket

### 连接地址

```
ws://{host}/api/v1/ws/strategy?token={jwt_token}
```

### 参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | 否 | JWT Token，用于身份识别 |

### 连接流程

1. 客户端发起 WebSocket 连接
2. 服务端通过可选 token 解析 `user_id`
3. 连接建立，服务端发送欢迎消息
4. 客户端通过 subscribe 订阅感兴趣的策略频道

### 连接成功消息

```json
{
  "type": "connected",
  "message": "策略 WebSocket 连接成功",
  "timestamp": "2025-02-24T19:00:00.000000"
}
```

### 支持频道

| 频道格式 | 描述 | 示例 |
|----------|------|------|
| `strategy/{strategy_id}` | 指定策略的信号推送 | `strategy/strategy_abc123` |

### 订阅示例

```json
{
  "action": "subscribe",
  "channels": ["strategy/strategy_abc123"]
}
```

### 推送事件类型

#### 策略信号

由策略引擎在产生信号时通过 `push_signal(strategy_id, signal_data)` 推送。

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

通过 `push_strategy_status(strategy_id, status_data)` 推送。

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

## 连接关闭码

| 关闭码 | 描述 |
|--------|------|
| 1000 | 正常关闭 |
| 4001 | 认证失败（Token 无效或缺失，仅交易 WebSocket） |

## 重连建议

- 建议客户端在连接断开后使用指数退避策略重连
- 重连后需重新发送 subscribe 消息订阅之前的频道
- 交易 WebSocket 重连后会自动重新订阅用户私有频道 `trading/{user_id}`

## 服务端推送函数一览

| 函数 | 所属模块 | 推送频道 | 描述 |
|------|---------|---------|------|
| `push_ticker(symbol, data)` | market_ws | `ticker/{symbol}` | 推送实时 Ticker |
| `push_kline(symbol, timeframe, data)` | market_ws | `kline/{symbol}/{timeframe}` | 推送 K 线数据 |
| `push_depth(symbol, data)` | market_ws | `depth/{symbol}` | 推送市场深度 |
| `push_order_update(user_id, order_data)` | trading_ws | `trading/{user_id}` | 推送订单状态变化 |
| `push_trade_notification(user_id, trade_data)` | trading_ws | `trading/{user_id}` | 推送成交通知 |
| `push_position_update(user_id, position_data)` | trading_ws | `trading/{user_id}` | 推送持仓变化 |
| `push_signal(strategy_id, signal_data)` | strategy_ws | `strategy/{strategy_id}` | 推送策略信号 |
| `push_strategy_status(strategy_id, status_data)` | strategy_ws | `strategy/{strategy_id}` | 推送策略状态变化 |
