# WebSocket 实时推送 API 文档

## 概述

系统提供三条 WebSocket 连接通道，分别用于行情实时推送、策略信号推送和交易事件推送。所有通道均基于统一的消息协议，前端通过订阅/取消订阅机制按需接收数据。

## 基础信息

| 通道 | 连接地址 | 认证 | 说明 |
|------|----------|------|------|
| 行情 | `ws://host/ws/market` | 可选 | 实时 Ticker、K 线、深度数据 |
| 策略信号 | `ws://host/ws/strategy` | 可选 | 策略产生的交易信号 |
| 交易事件 | `ws://host/ws/trading` | **必填** | 用户私有订单/成交/持仓通知 |

> **协议说明**：生产环境请使用 `wss://`（TLS 加密）。

---

## 通用消息协议

所有消息均为 **JSON 文本帧**，编码为 UTF-8。

### 客户端 → 服务端

| action | 说明 | 示例 |
|--------|------|------|
| `subscribe` | 订阅频道 | `{"action": "subscribe", "channels": ["ticker/BTCUSDT"]}` |
| `unsubscribe` | 取消订阅 | `{"action": "unsubscribe", "channels": ["ticker/BTCUSDT"]}` |
| `ping` | 心跳保活 | `{"action": "ping"}` |

### 服务端 → 客户端

| type | 触发时机 | 说明 |
|------|----------|------|
| `connected` | 连接建立后立即推送 | 欢迎消息，含已订阅频道信息 |
| `subscribed` | 订阅成功后 | 确认订阅的频道列表 |
| `unsubscribed` | 取消订阅后 | 确认取消的频道列表 |
| `pong` | 收到 ping 后 | 心跳响应 |
| `error` | 消息格式错误或未知 action | 错误描述 |
| 数据推送 | 频道有新数据时 | 见各通道说明 |

---

## 一、行情 WebSocket

**连接地址**：`ws://host/ws/market`

**认证**：可选。连接时可通过 Query 参数传入 JWT Token 用于身份识别，不传也可正常接收行情数据。

```
ws://host/ws/market?token=<JWT_TOKEN>
```

### 支持的频道

| 频道格式 | 说明 | 示例 |
|----------|------|------|
| `ticker/{symbol}` | 实时 Ticker（最新价、涨跌幅、成交量） | `ticker/BTCUSDT` |
| `kline/{symbol}/{timeframe}` | K 线数据（实时更新） | `kline/BTCUSDT/1m` |
| `depth/{symbol}` | 市场深度（买卖盘） | `depth/BTCUSDT` |

**支持的 timeframe**：`1m` `5m` `15m` `1h` `4h` `1d`

### 连接流程

```
客户端                              服务端
  │                                   │
  │──── WebSocket 握手 ───────────────▶│
  │◀─── {"type":"connected",...} ──────│  连接成功
  │                                   │
  │──── {"action":"subscribe",        │
  │      "channels":["ticker/BTCUSDT",│
  │      "kline/BTCUSDT/1m"]} ───────▶│
  │◀─── {"type":"subscribed",         │
  │      "channels":[...]} ───────────│  订阅确认
  │                                   │
  │◀─── {"type":"ticker",...} ─────────│  行情推送（持续）
  │◀─── {"type":"kline",...} ──────────│
  │                                   │
  │──── {"action":"ping"} ────────────▶│
  │◀─── {"type":"pong"} ───────────────│  心跳响应
```

### 消息格式

#### 连接成功（服务端推送）

```json
{
  "type": "connected",
  "message": "行情 WebSocket 连接成功",
  "timestamp": "2026-02-21T10:00:00.000000"
}
```

#### 订阅频道（客户端发送）

```json
{
  "action": "subscribe",
  "channels": ["ticker/BTCUSDT", "kline/BTCUSDT/1m", "depth/ETHUSDT"]
}
```

#### 订阅确认（服务端推送）

```json
{
  "type": "subscribed",
  "channels": ["ticker/BTCUSDT", "kline/BTCUSDT/1m", "depth/ETHUSDT"]
}
```

#### Ticker 推送（服务端推送）

```json
{
  "type": "ticker",
  "channel": "ticker/BTCUSDT",
  "data": {
    "symbol": "BTCUSDT",
    "price": "50000.00",
    "change": "1500.00",
    "change_percent": "3.09",
    "volume": "12345.67",
    "timestamp": "2026-02-21T10:00:00.000000"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定为 `ticker` |
| channel | string | 频道名，格式 `ticker/{symbol}` |
| data.symbol | string | 交易对 |
| data.price | string | 最新价 |
| data.change | string | 24h 价格变化 |
| data.change_percent | string | 24h 涨跌幅（%） |
| data.volume | string | 24h 成交量 |
| data.timestamp | string | 数据时间戳（UTC） |

#### K 线推送（服务端推送）

```json
{
  "type": "kline",
  "channel": "kline/BTCUSDT/1m",
  "data": {
    "symbol": "BTCUSDT",
    "timeframe": "1m",
    "open": "49800.00",
    "high": "50200.00",
    "low": "49750.00",
    "close": "50000.00",
    "volume": "123.45",
    "timestamp": "2026-02-21T10:00:00.000000",
    "is_closed": false
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| data.open | string | 开盘价 |
| data.high | string | 最高价 |
| data.low | string | 最低价 |
| data.close | string | 收盘价（当前价） |
| data.volume | string | 成交量 |
| data.is_closed | boolean | K 线是否已收盘 |

#### 深度推送（服务端推送）

```json
{
  "type": "depth",
  "channel": "depth/BTCUSDT",
  "data": {
    "symbol": "BTCUSDT",
    "bids": [
      ["49990.00", "0.5"],
      ["49980.00", "1.2"]
    ],
    "asks": [
      ["50010.00", "0.3"],
      ["50020.00", "0.8"]
    ],
    "timestamp": "2026-02-21T10:00:00.000000"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| data.bids | array | 买盘列表，每项为 `[价格, 数量]`，按价格降序 |
| data.asks | array | 卖盘列表，每项为 `[价格, 数量]`，按价格升序 |

---

## 二、策略信号 WebSocket

**连接地址**：`ws://host/ws/strategy`

**认证**：可选。连接时可通过 Query 参数传入 JWT Token。

```
ws://host/ws/strategy?token=<JWT_TOKEN>
```

### 支持的频道

| 频道格式 | 说明 | 示例 |
|----------|------|------|
| `strategy/{strategy_id}` | 指定策略的信号推送 | `strategy/alice__123456` |

### 连接流程

```
客户端                              服务端
  │                                   │
  │──── WebSocket 握手 ───────────────▶│
  │◀─── {"type":"connected",...} ──────│  连接成功
  │                                   │
  │──── {"action":"subscribe",        │
  │      "channels":              │
  │      ["strategy/alice__123456"]}──▶│
  │◀─── {"type":"subscribed",...} ─────│  订阅确认
  │                                   │
  │◀─── {"type":"signal",...} ─────────│  信号推送（策略产生信号时）
  │◀─── {"type":"strategy_status",...}─│  策略状态变化时
```

### 消息格式

#### 连接成功（服务端推送）

```json
{
  "type": "connected",
  "message": "策略 WebSocket 连接成功",
  "timestamp": "2026-02-21T10:00:00.000000"
}
```

#### 策略信号推送（服务端推送）

```json
{
  "type": "signal",
  "channel": "strategy/alice__123456",
  "data": {
    "signal_id": "987654321",
    "strategy_id": "alice__123456",
    "symbol": "BTCUSDT",
    "action": "buy",
    "price": "50000.00",
    "quantity": "0.01",
    "reason": "均线金叉",
    "timestamp": "2026-02-21T10:00:00.000000"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定为 `signal` |
| channel | string | 频道名，格式 `strategy/{strategy_id}` |
| data.signal_id | string | 信号唯一ID |
| data.strategy_id | string | 策略ID |
| data.symbol | string | 交易对 |
| data.action | string | 信号方向：`buy` / `sell` / `close` |
| data.price | string | 信号价格 |
| data.quantity | string | 建议数量 |
| data.reason | string | 信号产生原因 |
| data.timestamp | string | 信号时间戳（UTC） |

#### 策略状态变化推送（服务端推送）

```json
{
  "type": "strategy_status",
  "channel": "strategy/alice__123456",
  "data": {
    "strategy_id": "alice__123456",
    "state": "running",
    "timestamp": "2026-02-21T10:00:00.000000"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| data.state | string | 策略状态：`running` / `stopped` / `paused` |

---

## 三、交易事件 WebSocket

**连接地址**：`ws://host/ws/trading`

**认证**：**必填**。必须通过 Query 参数传入有效的 JWT Token，否则连接将被拒绝（关闭码 4001）。

```
ws://host/ws/trading?token=<JWT_TOKEN>
```

### 频道说明

交易 WebSocket 连接成功后，服务端会**自动订阅**当前用户的私有频道 `trading/{user_id}`，无需客户端手动发送订阅消息。

| 频道格式 | 说明 |
|----------|------|
| `trading/{user_id}` | 用户私有交易事件（自动订阅） |

### 连接流程

```
客户端                              服务端
  │                                   │
  │──── WebSocket 握手                │
  │     ?token=<JWT_TOKEN> ──────────▶│
  │                                   │── 验证 Token
  │                                   │── 自动订阅 trading/{user_id}
  │◀─── {"type":"connected",          │
  │      "user_id":"...",             │
  │      "subscribed_channels":[...]} │  连接成功（含已订阅频道）
  │                                   │
  │◀─── {"type":"order_update",...} ───│  订单状态变化时推送
  │◀─── {"type":"trade",...} ──────────│  成交时推送
  │◀─── {"type":"position",...} ───────│  持仓变化时推送
  │◀─── {"type":"account",...} ────────│  账户余额变化时推送
```

### 连接被拒绝的情况

| 关闭码 | 原因 |
|--------|------|
| 4001 | Token 未提供、无效或已过期 |

### 消息格式

#### 连接成功（服务端推送）

```json
{
  "type": "connected",
  "message": "交易 WebSocket 连接成功",
  "user_id": "alice",
  "subscribed_channels": ["trading/alice"],
  "timestamp": "2026-02-21T10:00:00.000000"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | string | 当前用户ID |
| subscribed_channels | array[string] | 已自动订阅的频道列表 |

#### 订单状态变化（服务端推送）

```json
{
  "type": "order_update",
  "data": {
    "order_id": "order_uuid",
    "symbol": "BTCUSDT",
    "side": "buy",
    "type": "limit",
    "status": "filled",
    "price": "50000.00",
    "quantity": "0.01",
    "filled_quantity": "0.01",
    "avg_price": "50000.00",
    "timestamp": "2026-02-21T10:00:00.000000"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| data.order_id | string | 订单ID |
| data.symbol | string | 交易对 |
| data.side | string | 方向：`buy` / `sell` |
| data.type | string | 订单类型：`limit` / `market` |
| data.status | string | 订单状态：`pending` / `partial` / `filled` / `cancelled` |
| data.price | string | 委托价格 |
| data.quantity | string | 委托数量 |
| data.filled_quantity | string | 已成交数量 |
| data.avg_price | string | 平均成交价 |

#### 成交通知（服务端推送）

```json
{
  "type": "trade",
  "data": {
    "trade_id": "trade_uuid",
    "order_id": "order_uuid",
    "symbol": "BTCUSDT",
    "side": "buy",
    "price": "50000.00",
    "quantity": "0.01",
    "fee": "0.05",
    "fee_currency": "USDT",
    "timestamp": "2026-02-21T10:00:00.000000"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| data.trade_id | string | 成交记录ID |
| data.order_id | string | 关联订单ID |
| data.fee | string | 手续费金额 |
| data.fee_currency | string | 手续费币种 |

#### 持仓变化（服务端推送）

```json
{
  "type": "position",
  "data": {
    "symbol": "BTCUSDT",
    "side": "long",
    "quantity": "0.01",
    "avg_price": "50000.00",
    "unrealized_pnl": "20.00",
    "realized_pnl": "0.00",
    "timestamp": "2026-02-21T10:00:00.000000"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| data.side | string | 持仓方向：`long` / `short` |
| data.unrealized_pnl | string | 未实现盈亏 |
| data.realized_pnl | string | 已实现盈亏 |

#### 账户余额变化（服务端推送）

```json
{
  "type": "account",
  "data": {
    "currency": "USDT",
    "available": "9500.00",
    "frozen": "500.00",
    "total": "10000.00",
    "timestamp": "2026-02-21T10:00:00.000000"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| data.currency | string | 币种 |
| data.available | string | 可用余额 |
| data.frozen | string | 冻结余额 |
| data.total | string | 总余额 |

---

## 通用消息格式

### 心跳（客户端发送）

```json
{"action": "ping"}
```

### 心跳响应（服务端推送）

```json
{"type": "pong"}
```

### 错误消息（服务端推送）

```json
{
  "type": "error",
  "message": "无效的 JSON 格式"
}
```

常见错误原因：
- `无效的 JSON 格式` — 客户端发送了非 JSON 格式的消息
- `未知 action: xxx` — 发送了不支持的 action

---

## 前端对接示例

### 行情订阅示例（JavaScript）

```javascript
const ws = new WebSocket('wss://host/ws/market');

ws.onopen = () => {
  // 连接成功后订阅频道
  ws.send(JSON.stringify({
    action: 'subscribe',
    channels: ['ticker/BTCUSDT', 'kline/BTCUSDT/1m']
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  switch (msg.type) {
    case 'connected':
      console.log('行情 WebSocket 连接成功');
      break;
    case 'subscribed':
      console.log('订阅成功:', msg.channels);
      break;
    case 'ticker':
      console.log(`${msg.data.symbol} 最新价: ${msg.data.price}`);
      break;
    case 'kline':
      console.log(`K线更新: ${msg.data.symbol} ${msg.data.timeframe}`, msg.data);
      break;
    case 'depth':
      console.log('深度更新:', msg.data);
      break;
    case 'error':
      console.error('错误:', msg.message);
      break;
  }
};

ws.onclose = (event) => {
  console.log('连接断开，code:', event.code);
};

// 心跳保活（每 30 秒发送一次）
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'ping' }));
  }
}, 30000);
```

### 交易事件订阅示例（JavaScript）

```javascript
const token = localStorage.getItem('access_token');
const ws = new WebSocket(`wss://host/ws/trading?token=${token}`);

ws.onopen = () => {
  console.log('交易 WebSocket 已连接，等待服务端确认...');
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  switch (msg.type) {
    case 'connected':
      console.log('交易 WebSocket 连接成功，用户:', msg.user_id);
      console.log('已订阅频道:', msg.subscribed_channels);
      break;
    case 'order_update':
      console.log('订单状态变化:', msg.data);
      // 更新订单列表 UI
      break;
    case 'trade':
      console.log('成交通知:', msg.data);
      // 显示成交提示
      break;
    case 'position':
      console.log('持仓变化:', msg.data);
      // 更新持仓 UI
      break;
    case 'account':
      console.log('账户余额变化:', msg.data);
      // 更新余额显示
      break;
  }
};

ws.onclose = (event) => {
  if (event.code === 4001) {
    console.error('Token 无效或已过期，请重新登录');
  } else {
    console.log('连接断开，尝试重连...');
    setTimeout(() => reconnect(), 3000);
  }
};
```

### 策略信号订阅示例（JavaScript）

```javascript
const ws = new WebSocket('wss://host/ws/strategy');

ws.onopen = () => {
  // 订阅指定策略的信号
  ws.send(JSON.stringify({
    action: 'subscribe',
    channels: ['strategy/alice__123456']
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  switch (msg.type) {
    case 'signal':
      const { action, symbol, price } = msg.data;
      console.log(`策略信号: ${symbol} ${action} @ ${price}`);
      break;
    case 'strategy_status':
      console.log('策略状态变化:', msg.data.state);
      break;
  }
};
```

---

## 断线重连建议

```javascript
class ReconnectingWebSocket {
  constructor(url, options = {}) {
    this.url = url;
    this.maxRetries = options.maxRetries || 5;
    this.retryDelay = options.retryDelay || 3000;
    this.retries = 0;
    this.connect();
  }

  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => {
      this.retries = 0;
      this.onopen?.();
    };
    this.ws.onmessage = (e) => this.onmessage?.(e);
    this.ws.onclose = (e) => {
      if (e.code === 4001) return; // Token 失效，不重连
      if (this.retries < this.maxRetries) {
        this.retries++;
        setTimeout(() => this.connect(), this.retryDelay * this.retries);
      }
    };
  }
}
```

---

## 注意事项

1. **心跳保活**：建议每 **30 秒**发送一次 `ping`，防止连接因空闲被网关断开。
2. **断线重连**：网络异常断开后应自动重连，重连后需重新发送订阅消息（行情/策略通道）；交易通道重连时需重新传入 Token。
3. **Token 刷新**：交易 WebSocket 的 Token 过期（关闭码 4001）时，需先通过 REST 接口刷新 Token，再重新建立连接。
4. **多频道订阅**：单次 `subscribe` 消息可同时订阅多个频道，减少消息往返次数。
5. **取消订阅**：不再需要的频道应及时取消订阅，减少服务端推送压力。
6. **消息顺序**：同一频道的消息按时间顺序推送，但不同频道之间不保证顺序。
