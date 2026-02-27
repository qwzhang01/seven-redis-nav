# 实时行情 WebSocket 前端对接说明文档

> **版本**：v1.0  
> **最后更新**：2026-02-27  
> **后端框架**：FastAPI + WebSocket  
> **协议**：WebSocket (RFC 6455)

---

## 目录

1. [连接信息](#1-连接信息)
2. [消息协议总览](#2-消息协议总览)
3. [连接流程](#3-连接流程)
4. [客户端 → 服务端消息](#4-客户端--服务端消息)
5. [服务端 → 客户端消息](#5-服务端--客户端消息)
6. [频道说明](#6-频道说明)
7. [心跳保活机制](#7-心跳保活机制)
8. [错误处理](#8-错误处理)
9. [限制与约束](#9-限制与约束)
10. [完整前端接入示例（TypeScript）](#10-完整前端接入示例typescript)
11. [完整前端接入示例（JavaScript）](#11-完整前端接入示例javascript)
12. [常见问题 FAQ](#12-常见问题-faq)

---

## 1. 连接信息

### 连接地址

```
ws://{host}:{port}/api/v1/ws/market
wss://{host}:{port}/api/v1/ws/market   # 生产环境使用 wss
```

### 查询参数

| 参数    | 类型   | 必填 | 说明                                       |
|---------|--------|------|--------------------------------------------|
| `token` | string | 否   | JWT Token，用于身份识别。行情为公开数据，可不传 |

### 连接示例

```
ws://localhost:8000/api/v1/ws/market
ws://localhost:8000/api/v1/ws/market?token=eyJhbGciOiJIUzI1NiIs...
```

---

## 2. 消息协议总览

所有消息均使用 **JSON 格式**，通过 WebSocket **文本帧**（text frame）传输。

### 通信方向

```
┌──────────┐                      ┌──────────┐
│  前端     │ ── subscribe ──────► │  后端     │
│  客户端   │ ── unsubscribe ───► │  服务端   │
│          │ ── ping ───────────► │          │
│          │                      │          │
│          │ ◄── connected ────── │          │
│          │ ◄── subscribed ───── │          │
│          │ ◄── unsubscribed ─── │          │
│          │ ◄── pong ─────────── │          │
│          │ ◄── ticker ───────── │          │
│          │ ◄── kline ────────── │          │
│          │ ◄── depth ────────── │          │
│          │ ◄── error ────────── │          │
└──────────┘                      └──────────┘
```

---

## 3. 连接流程

```
1. 客户端发起 WebSocket 连接
       ↓
2. 服务端返回 "connected" 欢迎消息（确认连接成功）
       ↓
3. 客户端发送 "subscribe" 消息订阅感兴趣的频道
       ↓
4. 服务端返回 "subscribed" 确认消息
       ↓
5. 服务端开始推送该频道的实时行情数据
       ↓
6. 客户端定时发送 "ping" 保持连接活跃
       ↓
7. 不再需要时，发送 "unsubscribe" 取消订阅 或 直接关闭连接
```

### 连接成功后首条消息

连接建立成功后，服务端会**立即**推送一条欢迎消息：

```json
{
    "type": "connected",
    "message": "行情 WebSocket 连接成功",
    "timestamp": "2026-02-27T09:30:00.123456+00:00"
}
```

> **前端应在收到此消息后，再发送订阅请求。**

---

## 4. 客户端 → 服务端消息

### 4.1 订阅频道（subscribe）

```json
{
    "action": "subscribe",
    "channels": ["ticker/BTCUSDT", "kline/BTCUSDT/1m", "depth/ETHUSDT"]
}
```

| 字段       | 类型     | 必填 | 说明                     |
|------------|----------|------|--------------------------|
| `action`   | string   | 是   | 固定值 `"subscribe"`     |
| `channels` | string[] | 是   | 要订阅的频道列表（数组） |

**响应**（订阅成功）：

```json
{
    "type": "subscribed",
    "channels": ["ticker/BTCUSDT", "kline/BTCUSDT/1m", "depth/ETHUSDT"]
}
```

### 4.2 取消订阅（unsubscribe）

```json
{
    "action": "unsubscribe",
    "channels": ["ticker/BTCUSDT"]
}
```

| 字段       | 类型     | 必填 | 说明                       |
|------------|----------|------|----------------------------|
| `action`   | string   | 是   | 固定值 `"unsubscribe"`     |
| `channels` | string[] | 是   | 要取消订阅的频道列表（数组） |

**响应**（取消成功）：

```json
{
    "type": "unsubscribed",
    "channels": ["ticker/BTCUSDT"]
}
```

### 4.3 心跳 Ping

```json
{
    "action": "ping"
}
```

**响应**：

```json
{
    "type": "pong"
}
```

---

## 5. 服务端 → 客户端消息

所有服务端推送的行情数据消息都包含以下公共字段：

| 字段        | 类型   | 说明                              |
|-------------|--------|-----------------------------------|
| `type`      | string | 消息类型：`ticker` / `kline` / `depth` |
| `channel`   | string | 频道名称（与订阅时一致）           |
| `data`      | object | 行情数据主体                       |
| `timestamp` | string | 服务端推送时间（ISO 8601 UTC 格式） |

### 5.1 Ticker 行情数据

**频道**：`ticker/{symbol}`

```json
{
    "type": "ticker",
    "channel": "ticker/BTCUSDT",
    "data": {
        "symbol": "BTC/USDT",
        "exchange": "binance",
        "last_price": 65432.10,
        "bid_price": 65430.00,
        "ask_price": 65434.20,
        "volume": 12345.678,
        "turnover": 807654321.50,
        "timestamp": 1709020200.123
    },
    "timestamp": "2026-02-27T09:30:00.123456+00:00"
}
```

**data 字段说明**：

| 字段         | 类型   | 说明                        |
|--------------|--------|-----------------------------|
| `symbol`     | string | 交易对（原始格式如 BTC/USDT）|
| `exchange`   | string | 交易所名称                   |
| `last_price` | number | 最新成交价                   |
| `bid_price`  | number | 最优买一价                   |
| `ask_price`  | number | 最优卖一价                   |
| `volume`     | number | 24h 成交量                   |
| `turnover`   | number | 24h 成交额                   |
| `timestamp`  | number | 数据时间戳（Unix 秒，含小数） |

### 5.2 K 线数据

**频道**：`kline/{symbol}/{timeframe}`

```json
{
    "type": "kline",
    "channel": "kline/BTCUSDT/1m",
    "data": {
        "symbol": "BTC/USDT",
        "exchange": "binance",
        "timeframe": "1m",
        "timestamp": 1709020200.0,
        "open": 65400.00,
        "high": 65450.50,
        "low": 65380.00,
        "close": 65432.10,
        "volume": 123.456,
        "is_closed": false
    },
    "timestamp": "2026-02-27T09:30:00.123456+00:00"
}
```

**data 字段说明**：

| 字段        | 类型    | 说明                                        |
|-------------|---------|---------------------------------------------|
| `symbol`    | string  | 交易对（原始格式如 BTC/USDT）                |
| `exchange`  | string  | 交易所名称                                   |
| `timeframe` | string  | K 线周期（`1m`/`5m`/`15m`/`30m`/`1h`/`4h`/`1d`/`1w`） |
| `timestamp` | number  | K 线开盘时间戳（Unix 秒）                     |
| `open`      | number  | 开盘价                                       |
| `high`      | number  | 最高价                                       |
| `low`       | number  | 最低价                                       |
| `close`     | number  | 收盘价（未关闭时为最新价）                    |
| `volume`    | number  | 成交量                                       |
| `is_closed` | boolean | K 线是否已关闭。**⚠️ 重要**：见下方说明       |

> **`is_closed` 字段说明**：
> - `false`：该 K 线尚未关闭，数据会实时更新（OHLCV 会随新 Tick 变化）。前端应**更新**图表上当前最后一根 K 线。
> - `true`：该 K 线已关闭，数据为最终值。前端应**新增**一根 K 线到图表末尾。

### 5.3 市场深度（盘口）

**频道**：`depth/{symbol}`

```json
{
    "type": "depth",
    "channel": "depth/BTCUSDT",
    "data": {
        "symbol": "BTC/USDT",
        "exchange": "binance",
        "bids": [
            [65430.00, 1.234],
            [65429.50, 2.567],
            [65429.00, 0.890]
        ],
        "asks": [
            [65434.20, 0.456],
            [65434.70, 1.789],
            [65435.00, 3.012]
        ],
        "timestamp": "1709020200.123"
    },
    "timestamp": "2026-02-27T09:30:00.123456+00:00"
}
```

**data 字段说明**：

| 字段        | 类型          | 说明                                    |
|-------------|---------------|-----------------------------------------|
| `symbol`    | string        | 交易对                                   |
| `exchange`  | string        | 交易所名称                               |
| `bids`      | number[][]    | 买盘数组，每项 `[价格, 数量]`，按价格降序 |
| `asks`      | number[][]    | 卖盘数组，每项 `[价格, 数量]`，按价格升序 |
| `timestamp` | string        | 深度快照时间戳                            |

### 5.4 系统控制消息

| type           | 触发时机       | 示例                                                                    |
|----------------|----------------|-------------------------------------------------------------------------|
| `connected`    | 连接成功       | `{"type": "connected", "message": "行情 WebSocket 连接成功", "timestamp": "..."}` |
| `subscribed`   | 订阅成功       | `{"type": "subscribed", "channels": ["ticker/BTCUSDT"]}`                |
| `unsubscribed` | 取消订阅成功   | `{"type": "unsubscribed", "channels": ["ticker/BTCUSDT"]}`              |
| `pong`         | 响应心跳       | `{"type": "pong"}`                                                      |
| `error`        | 发生错误       | `{"type": "error", "message": "无效的频道名称: xxx"}`                    |

---

## 6. 频道说明

### 6.1 频道命名格式

| 频道类型 | 格式                            | 示例                    |
|----------|---------------------------------|-------------------------|
| Ticker   | `ticker/{symbol}`               | `ticker/BTCUSDT`        |
| K 线     | `kline/{symbol}/{timeframe}`    | `kline/BTCUSDT/1m`      |
| 深度     | `depth/{symbol}`                | `depth/ETHUSDT`         |

### 6.2 symbol 命名规则

频道中的 `{symbol}` 使用**去除分隔符**的交易对名称：

| 交易所原始名称 | 频道中的 symbol |
|---------------|----------------|
| `BTC/USDT`    | `BTCUSDT`      |
| `ETH-USDT`    | `ETHUSDT`      |
| `BTC_USDT`    | `BTC_USDT`     |

> **规则**：去掉 `/` 和 `-`，保留 `_`。只允许字母、数字、下划线 `[A-Za-z0-9_]`。

### 6.3 支持的 timeframe

| timeframe | 说明      |
|-----------|-----------|
| `1m`      | 1 分钟    |
| `5m`      | 5 分钟    |
| `15m`     | 15 分钟   |
| `30m`     | 30 分钟   |
| `1h`      | 1 小时    |
| `4h`      | 4 小时    |
| `1d`      | 1 天      |
| `1w`      | 1 周      |

### 6.4 频道校验

服务端会对订阅的频道名称进行**严格校验**，不符合以下正则的频道会被拒绝：

```
ticker:  ^ticker/[A-Za-z0-9_]+$
kline:   ^kline/[A-Za-z0-9_]+/(1m|5m|15m|30m|1h|4h|1d|1w)$
depth:   ^depth/[A-Za-z0-9_]+$
```

**错误示例**：

```json
// ❌ 频道名称非法
{"action": "subscribe", "channels": ["ticker/BTC/USDT"]}    // symbol 不能包含 /
{"action": "subscribe", "channels": ["kline/BTCUSDT/2m"]}   // 不支持 2m 周期
{"action": "subscribe", "channels": ["foo/BTCUSDT"]}        // 未知频道类型

// 服务端返回：
{"type": "error", "message": "无效的频道名称: ticker/BTC/USDT"}
```

---

## 7. 心跳保活机制

### 7.1 机制说明

- 服务端设置了 **120 秒心跳超时**检测
- 如果客户端在 120 秒内没有发送任何消息（包括 ping），服务端将**主动断开连接**
- 建议客户端每 **30~50 秒** 发送一次 ping

### 7.2 心跳流程

```
客户端                              服务端
  │                                    │
  │─── {"action": "ping"} ──────────►  │
  │                                    │
  │  ◄── {"type": "pong"} ───────────  │
  │                                    │
  │         ... 30~50 秒后 ...          │
  │                                    │
  │─── {"action": "ping"} ──────────►  │
  │                                    │
  │  ◄── {"type": "pong"} ───────────  │
  │                                    │
```

### 7.3 前端心跳实现要点

```javascript
// 推荐：每 30 秒发送一次 ping
const PING_INTERVAL = 30_000; // 30 秒

let pingTimer = null;

function startHeartbeat(ws) {
    pingTimer = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: "ping" }));
        }
    }, PING_INTERVAL);
}

function stopHeartbeat() {
    if (pingTimer) {
        clearInterval(pingTimer);
        pingTimer = null;
    }
}
```

---

## 8. 错误处理

### 8.1 错误消息格式

```json
{
    "type": "error",
    "message": "错误描述信息"
}
```

### 8.2 可能的错误场景

| 错误消息                                  | 原因                          | 处理方式                    |
|-------------------------------------------|-------------------------------|----------------------------|
| `"无效的 JSON 格式"`                      | 发送的消息不是合法 JSON        | 检查消息格式                |
| `"无效的频道名称: xxx"`                   | 频道名不符合命名规则           | 检查频道名格式              |
| `"订阅频道数超限，当前 N 个，最多 50 个"` | 订阅频道数超过上限             | 减少订阅或先取消无用订阅    |
| `"未知 action: xxx"`                      | action 不是 subscribe/unsubscribe/ping | 检查 action 拼写  |

### 8.3 连接关闭码

| 关闭码 | 说明              | 处理方式                |
|--------|-------------------|------------------------|
| `1000` | 正常关闭          | 正常处理                |
| `1001` | 服务端关闭        | 自动重连                |
| `1006` | 异常断开          | 自动重连                |
| `1013` | 服务器连接数已满  | 稍后重试（指数退避）    |

---

## 9. 限制与约束

| 限制项                   | 值     | 说明                                     |
|--------------------------|--------|------------------------------------------|
| 最大连接数               | 1000   | 全局最大 WebSocket 连接数                 |
| 每连接最大订阅频道数     | 50     | 单个连接最多订阅 50 个频道               |
| 心跳超时时间             | 120 秒 | 超过 120 秒无任何消息则自动断开          |
| 消息格式                 | JSON   | 仅接受 JSON 格式的文本帧                 |
| Token 认证               | 可选   | 行情数据为公开数据，Token 仅用于身份识别 |

---

## 10. 完整前端接入示例（TypeScript）

```typescript
/**
 * 量化交易系统 - 实时行情 WebSocket 客户端
 * 
 * 使用方式：
 *   const client = new MarketWebSocket('ws://localhost:8000/api/v1/ws/market');
 *   client.connect();
 *   client.subscribe(['ticker/BTCUSDT', 'kline/BTCUSDT/1m']);
 *   client.onTicker('BTCUSDT', (data) => { console.log(data); });
 *   client.onKline('BTCUSDT', '1m', (data) => { console.log(data); });
 */

// ===================== 类型定义 =====================

/** 服务端消息类型 */
type ServerMessageType = 'connected' | 'subscribed' | 'unsubscribed' | 'pong' | 'ticker' | 'kline' | 'depth' | 'error';

/** 服务端消息基础接口 */
interface ServerMessage {
    type: ServerMessageType;
    channel?: string;
    data?: any;
    message?: string;
    channels?: string[];
    timestamp?: string;
}

/** Ticker 数据 */
interface TickerData {
    symbol: string;
    exchange: string;
    last_price: number;
    bid_price: number;
    ask_price: number;
    volume: number;
    turnover: number;
    timestamp: number;
}

/** K 线数据 */
interface KlineData {
    symbol: string;
    exchange: string;
    timeframe: string;
    timestamp: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    is_closed: boolean;
}

/** 深度数据 */
interface DepthData {
    symbol: string;
    exchange: string;
    bids: [number, number][];
    asks: [number, number][];
    timestamp: string;
}

/** 支持的 K 线周期 */
type Timeframe = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w';

/** 连接状态 */
enum ConnectionState {
    DISCONNECTED = 'DISCONNECTED',
    CONNECTING = 'CONNECTING',
    CONNECTED = 'CONNECTED',
    RECONNECTING = 'RECONNECTING',
}

// ===================== WebSocket 客户端 =====================

class MarketWebSocket {
    private ws: WebSocket | null = null;
    private url: string;
    private token?: string;
    private state: ConnectionState = ConnectionState.DISCONNECTED;
    
    // 心跳
    private pingTimer: ReturnType<typeof setInterval> | null = null;
    private readonly PING_INTERVAL = 30_000; // 30 秒
    
    // 自动重连
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    private reconnectAttempts = 0;
    private readonly MAX_RECONNECT_ATTEMPTS = 10;
    private readonly RECONNECT_BASE_DELAY = 1000; // 1 秒起步
    private readonly RECONNECT_MAX_DELAY = 30_000; // 最大 30 秒
    
    // 订阅状态（重连后自动恢复）
    private subscribedChannels: Set<string> = new Set();
    
    // 回调
    private tickerCallbacks: Map<string, ((data: TickerData) => void)[]> = new Map();
    private klineCallbacks: Map<string, ((data: KlineData) => void)[]> = new Map();
    private depthCallbacks: Map<string, ((data: DepthData) => void)[]> = new Map();
    private connectCallback?: () => void;
    private disconnectCallback?: (event: CloseEvent) => void;
    private errorCallback?: (message: string) => void;

    constructor(url: string, token?: string) {
        this.url = url;
        this.token = token;
    }

    // ---- 连接管理 ----

    connect(): void {
        if (this.state === ConnectionState.CONNECTED || this.state === ConnectionState.CONNECTING) {
            return;
        }
        this.state = ConnectionState.CONNECTING;
        const fullUrl = this.token ? `${this.url}?token=${this.token}` : this.url;
        this.ws = new WebSocket(fullUrl);

        this.ws.onopen = () => {
            console.log('[MarketWS] WebSocket 连接已打开，等待服务端确认...');
        };

        this.ws.onmessage = (event: MessageEvent) => {
            this.handleMessage(event.data);
        };

        this.ws.onclose = (event: CloseEvent) => {
            console.log(`[MarketWS] 连接关闭 code=${event.code} reason=${event.reason}`);
            this.stopHeartbeat();
            this.state = ConnectionState.DISCONNECTED;
            this.disconnectCallback?.(event);
            
            // 非正常关闭时自动重连
            if (event.code !== 1000) {
                this.scheduleReconnect();
            }
        };

        this.ws.onerror = (event: Event) => {
            console.error('[MarketWS] WebSocket 错误', event);
        };
    }

    disconnect(): void {
        this.reconnectAttempts = this.MAX_RECONNECT_ATTEMPTS; // 阻止重连
        this.stopHeartbeat();
        this.clearReconnectTimer();
        if (this.ws) {
            this.ws.close(1000, '客户端主动断开');
            this.ws = null;
        }
        this.state = ConnectionState.DISCONNECTED;
    }

    // ---- 订阅管理 ----

    subscribe(channels: string[]): void {
        channels.forEach(ch => this.subscribedChannels.add(ch));
        this.send({ action: 'subscribe', channels });
    }

    unsubscribe(channels: string[]): void {
        channels.forEach(ch => this.subscribedChannels.delete(ch));
        this.send({ action: 'unsubscribe', channels });
    }

    // ---- 事件监听 ----

    /** 监听某个交易对的 Ticker 数据 */
    onTicker(symbol: string, callback: (data: TickerData) => void): void {
        const key = `ticker/${symbol}`;
        if (!this.tickerCallbacks.has(key)) {
            this.tickerCallbacks.set(key, []);
        }
        this.tickerCallbacks.get(key)!.push(callback);
    }

    /** 监听某个交易对某个周期的 K 线数据 */
    onKline(symbol: string, timeframe: Timeframe, callback: (data: KlineData) => void): void {
        const key = `kline/${symbol}/${timeframe}`;
        if (!this.klineCallbacks.has(key)) {
            this.klineCallbacks.set(key, []);
        }
        this.klineCallbacks.get(key)!.push(callback);
    }

    /** 监听某个交易对的深度数据 */
    onDepth(symbol: string, callback: (data: DepthData) => void): void {
        const key = `depth/${symbol}`;
        if (!this.depthCallbacks.has(key)) {
            this.depthCallbacks.set(key, []);
        }
        this.depthCallbacks.get(key)!.push(callback);
    }

    /** 监听连接成功事件 */
    onConnect(callback: () => void): void {
        this.connectCallback = callback;
    }

    /** 监听连接断开事件 */
    onDisconnect(callback: (event: CloseEvent) => void): void {
        this.disconnectCallback = callback;
    }

    /** 监听错误事件 */
    onError(callback: (message: string) => void): void {
        this.errorCallback = callback;
    }

    // ---- 状态查询 ----

    get connected(): boolean {
        return this.state === ConnectionState.CONNECTED;
    }

    get currentState(): ConnectionState {
        return this.state;
    }

    // ---- 内部方法 ----

    private handleMessage(raw: string): void {
        let msg: ServerMessage;
        try {
            msg = JSON.parse(raw);
        } catch {
            console.warn('[MarketWS] 收到非 JSON 消息:', raw);
            return;
        }

        switch (msg.type) {
            case 'connected':
                console.log('[MarketWS] 连接确认:', msg.message);
                this.state = ConnectionState.CONNECTED;
                this.reconnectAttempts = 0;
                this.startHeartbeat();
                // 重连时自动恢复订阅
                if (this.subscribedChannels.size > 0) {
                    this.send({ action: 'subscribe', channels: Array.from(this.subscribedChannels) });
                }
                this.connectCallback?.();
                break;

            case 'subscribed':
                console.log('[MarketWS] 订阅成功:', msg.channels);
                break;

            case 'unsubscribed':
                console.log('[MarketWS] 取消订阅:', msg.channels);
                break;

            case 'pong':
                // 心跳响应，无需处理
                break;

            case 'ticker':
                if (msg.channel && msg.data) {
                    const callbacks = this.tickerCallbacks.get(msg.channel);
                    callbacks?.forEach(cb => cb(msg.data as TickerData));
                }
                break;

            case 'kline':
                if (msg.channel && msg.data) {
                    const callbacks = this.klineCallbacks.get(msg.channel);
                    callbacks?.forEach(cb => cb(msg.data as KlineData));
                }
                break;

            case 'depth':
                if (msg.channel && msg.data) {
                    const callbacks = this.depthCallbacks.get(msg.channel);
                    callbacks?.forEach(cb => cb(msg.data as DepthData));
                }
                break;

            case 'error':
                console.error('[MarketWS] 服务端错误:', msg.message);
                this.errorCallback?.(msg.message || '未知错误');
                break;

            default:
                console.warn('[MarketWS] 未知消息类型:', msg.type);
        }
    }

    private send(data: object): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('[MarketWS] 连接未就绪，消息未发送:', data);
        }
    }

    private startHeartbeat(): void {
        this.stopHeartbeat();
        this.pingTimer = setInterval(() => {
            this.send({ action: 'ping' });
        }, this.PING_INTERVAL);
    }

    private stopHeartbeat(): void {
        if (this.pingTimer) {
            clearInterval(this.pingTimer);
            this.pingTimer = null;
        }
    }

    private scheduleReconnect(): void {
        if (this.reconnectAttempts >= this.MAX_RECONNECT_ATTEMPTS) {
            console.error('[MarketWS] 达到最大重连次数，停止重连');
            return;
        }
        this.state = ConnectionState.RECONNECTING;
        // 指数退避 + 随机抖动
        const delay = Math.min(
            this.RECONNECT_BASE_DELAY * Math.pow(2, this.reconnectAttempts) + Math.random() * 1000,
            this.RECONNECT_MAX_DELAY
        );
        this.reconnectAttempts++;
        console.log(`[MarketWS] 将在 ${Math.round(delay / 1000)}s 后重连（第 ${this.reconnectAttempts} 次）`);
        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, delay);
    }

    private clearReconnectTimer(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }
}

export { MarketWebSocket, ConnectionState };
export type { TickerData, KlineData, DepthData, Timeframe, ServerMessage };
```

### 使用示例

```typescript
// 创建客户端实例
const ws = new MarketWebSocket('ws://localhost:8000/api/v1/ws/market');

// 注册事件回调
ws.onConnect(() => {
    console.log('已连接到行情服务');
    // 连接成功后订阅频道
    ws.subscribe([
        'ticker/BTCUSDT',
        'ticker/ETHUSDT',
        'kline/BTCUSDT/1m',
        'kline/BTCUSDT/5m',
        'depth/BTCUSDT',
    ]);
});

ws.onDisconnect((event) => {
    console.log('行情连接已断开', event.code, event.reason);
});

ws.onError((msg) => {
    console.error('行情错误:', msg);
});

// 注册数据回调
ws.onTicker('BTCUSDT', (ticker) => {
    console.log(`BTC 最新价: ${ticker.last_price}`);
    // 更新页面上的价格显示
});

ws.onKline('BTCUSDT', '1m', (kline) => {
    if (kline.is_closed) {
        // K 线已关闭 → 图表新增一根 K 线
        console.log('新 K 线:', kline);
    } else {
        // K 线未关闭 → 更新图表最后一根 K 线
        console.log('K 线更新:', kline);
    }
});

ws.onDepth('BTCUSDT', (depth) => {
    console.log('买一:', depth.bids[0], '卖一:', depth.asks[0]);
});

// 发起连接
ws.connect();

// 页面销毁时断开连接
// ws.disconnect();
```

---

## 11. 完整前端接入示例（JavaScript）

适用于不使用 TypeScript 的项目：

```javascript
/**
 * 行情 WebSocket 客户端 - 简洁版
 */
class MarketWS {
    constructor(url, token = null) {
        this.url = token ? `${url}?token=${token}` : url;
        this.ws = null;
        this.channels = new Set();
        this.listeners = {};  // { channel: [callback, ...] }
        this.pingTimer = null;
        this.reconnectTimer = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.onmessage = (e) => {
            const msg = JSON.parse(e.data);
            
            switch (msg.type) {
                case 'connected':
                    console.log('[MarketWS] 已连接');
                    this.reconnectAttempts = 0;
                    this._startPing();
                    // 重连时恢复订阅
                    if (this.channels.size > 0) {
                        this._send({ action: 'subscribe', channels: [...this.channels] });
                    }
                    break;
                case 'ticker':
                case 'kline':
                case 'depth':
                    (this.listeners[msg.channel] || []).forEach(cb => cb(msg.data, msg));
                    break;
                case 'error':
                    console.error('[MarketWS] 错误:', msg.message);
                    break;
            }
        };

        this.ws.onclose = (e) => {
            this._stopPing();
            if (e.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 30000);
                this.reconnectAttempts++;
                console.log(`[MarketWS] ${delay / 1000}s 后重连...`);
                this.reconnectTimer = setTimeout(() => this.connect(), delay);
            }
        };
    }

    subscribe(channels) {
        channels.forEach(ch => this.channels.add(ch));
        this._send({ action: 'subscribe', channels });
    }

    unsubscribe(channels) {
        channels.forEach(ch => this.channels.delete(ch));
        this._send({ action: 'unsubscribe', channels });
    }

    /** 监听指定频道的数据 */
    on(channel, callback) {
        if (!this.listeners[channel]) this.listeners[channel] = [];
        this.listeners[channel].push(callback);
    }

    /** 移除指定频道的监听 */
    off(channel, callback) {
        if (!this.listeners[channel]) return;
        this.listeners[channel] = this.listeners[channel].filter(cb => cb !== callback);
    }

    disconnect() {
        this.maxReconnectAttempts = 0; // 阻止重连
        this._stopPing();
        clearTimeout(this.reconnectTimer);
        this.ws?.close(1000);
    }

    _send(data) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    _startPing() {
        this._stopPing();
        this.pingTimer = setInterval(() => this._send({ action: 'ping' }), 30000);
    }

    _stopPing() {
        clearInterval(this.pingTimer);
        this.pingTimer = null;
    }
}
```

### 使用示例

```javascript
const ws = new MarketWS('ws://localhost:8000/api/v1/ws/market');

// 监听 BTC Ticker
ws.on('ticker/BTCUSDT', (data) => {
    document.getElementById('btc-price').textContent = data.last_price;
});

// 监听 BTC 1分钟 K 线
ws.on('kline/BTCUSDT/1m', (data) => {
    if (data.is_closed) {
        chart.addKline(data);   // 新增 K 线
    } else {
        chart.updateKline(data); // 更新最后一根 K 线
    }
});

// 监听 BTC 深度
ws.on('depth/BTCUSDT', (data) => {
    renderOrderBook(data.bids, data.asks);
});

// 连接并订阅
ws.connect();
// 注意：连接成功后会自动恢复已添加的频道

// 延迟订阅也可以（内部会在连接成功后自动发送）
ws.subscribe(['ticker/BTCUSDT', 'kline/BTCUSDT/1m', 'depth/BTCUSDT']);
```

---

## 12. 常见问题 FAQ

### Q1：连接后没有收到任何行情数据？

**A**：请检查：
1. 是否收到了 `connected` 欢迎消息
2. 是否发送了 `subscribe` 消息
3. 频道名称是否正确（如 `ticker/BTCUSDT` 而非 `ticker/BTC/USDT`）
4. 后端行情服务是否正在运行并有真实数据流入

### Q2：频道中的 symbol 格式是什么？

**A**：去掉交易对中的 `/` 和 `-`，例如：
- `BTC/USDT` → `BTCUSDT`
- `ETH-USDT` → `ETHUSDT`

### Q3：K 线数据中 `is_closed` 有什么用？

**A**：
- `is_closed: false` 表示当前 K 线仍在形成中，数据会随新的 Tick 持续更新。前端应**更新图表最后一根 K 线**的 OHLCV 值。
- `is_closed: true` 表示该 K 线已结束，数据是最终值。前端应**在图表末尾新增一根 K 线**。

### Q4：连接断开后如何处理？

**A**：建议实现自动重连机制：
- 使用**指数退避**策略（1s → 2s → 4s → 8s → ... → 最大 30s）
- 重连成功后**自动恢复之前的订阅**（上面的示例代码已内置此功能）
- 设置最大重连次数（建议 10 次）

### Q5：收到 1013 关闭码是什么意思？

**A**：表示服务端连接数已满（上限 1000），请稍后重试。建议使用更长的退避时间。

### Q6：可以同时订阅多少个频道？

**A**：单个连接最多订阅 **50 个频道**。如果需要更多，可以建立多个 WebSocket 连接。

### Q7：需要认证才能接收行情数据吗？

**A**：不需要。行情数据是公开的，`token` 参数可选。传入 JWT Token 仅用于身份识别和日志追踪。

### Q8：数据推送频率是多少？

**A**：数据推送频率与交易所行情更新频率一致，通常：
- **Ticker**：每次有新的成交就推送（约 100ms~1s 一次，取决于交易活跃度）
- **K 线**：每次 Tick 更新都会推送当前 K 线的最新状态
- **深度**：每次深度变化时推送
