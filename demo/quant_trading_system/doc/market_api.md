# 行情 API 文档

## 概述

行情模块提供市场行情数据相关的 API 接口，支持行情订阅、K 线数据查询、实时 Tick 数据、市场深度等功能。

**Base URL**: `/market`

---

## 接口列表

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/market/subscribe` | 订阅行情数据 |
| POST | `/market/unsubscribe` | 取消行情订阅 |
| GET | `/market/kline/{symbol}` | 获取 K 线数据 |
| GET | `/market/tick/{symbol}` | 获取最新 Tick 数据 |
| GET | `/market/depth/{symbol}` | 获取市场深度数据 |
| GET | `/market/symbols` | 获取已订阅的交易对列表 |
| GET | `/market/stats` | 获取行情服务统计信息 |

---

## 接口详情

### 1. 订阅行情数据

**POST** `/market/subscribe`

向市场服务订阅指定交易对的实时行情数据。

#### 请求体

```json
{
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "exchange": "binance",
  "market_type": "spot"
}
```

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| symbols | array[string] | 是 | - | 要订阅的交易对列表 |
| exchange | string | 否 | `"binance"` | 交易所名称 |
| market_type | string | 否 | `"spot"` | 市场类型 |

#### 响应

```json
{
  "success": true,
  "message": "Subscribed to 2 symbols",
  "symbols": ["BTCUSDT", "ETHUSDT"]
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 操作是否成功 |
| message | string | 操作结果描述 |
| symbols | array[string] | 已订阅的交易对列表 |

---

### 2. 取消行情订阅

**POST** `/market/unsubscribe`

取消对指定交易对的行情数据订阅。

#### 请求体

```json
{
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "exchange": "binance",
  "market_type": "spot"
}
```

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| symbols | array[string] | 是 | - | 要取消订阅的交易对列表 |
| exchange | string | 否 | `"binance"` | 交易所名称 |
| market_type | string | 否 | `"spot"` | 市场类型 |

#### 响应

```json
{
  "success": true,
  "message": "Unsubscribed from 2 symbols",
  "symbols": ["BTCUSDT", "ETHUSDT"]
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 操作是否成功 |
| message | string | 操作结果描述 |
| symbols | array[string] | 已取消订阅的交易对列表 |

---

### 3. 获取 K 线数据

**GET** `/market/kline/{symbol}`

查询指定交易对和时间周期的历史 K 线数据。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symbol | string | 是 | 交易对符号，如 `BTCUSDT` |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| timeframe | string | 否 | `"1m"` | K 线时间周期，见下方枚举值 |
| limit | integer | 否 | `100` | 返回 K 线数量限制，范围 1~1000 |

**timeframe 枚举值：**

| 值 | 描述 |
|----|------|
| `1m` | 1 分钟 |
| `5m` | 5 分钟 |
| `15m` | 15 分钟 |
| `30m` | 30 分钟 |
| `1h` | 1 小时 |
| `4h` | 4 小时 |
| `1d` | 1 天 |
| `1w` | 1 周 |

#### 请求示例

```
GET /market/kline/BTCUSDT?timeframe=1h&limit=50
```

#### 响应

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "data": [
    {
      "timestamp": 1708300800000,
      "open": 52000.0,
      "high": 52500.0,
      "low": 51800.0,
      "close": 52300.0,
      "volume": 1234.56
    }
  ],
  "count": 1
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| symbol | string | 交易对符号 |
| timeframe | string | 时间周期 |
| data | array[object] | K 线数据列表 |
| data[].timestamp | integer | 时间戳（毫秒） |
| data[].open | float | 开盘价 |
| data[].high | float | 最高价 |
| data[].low | float | 最低价 |
| data[].close | float | 收盘价 |
| data[].volume | float | 成交量 |
| count | integer | 返回的 K 线数量 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 无效的时间周期参数 |
| 503 | 交易系统未启动 |

---

### 4. 获取最新 Tick 数据

**GET** `/market/tick/{symbol}`

查询指定交易对的最新 Tick 行情数据。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symbol | string | 是 | 交易对符号，如 `BTCUSDT` |

#### 请求示例

```
GET /market/tick/BTCUSDT
```

#### 响应

```json
{
  "symbol": "BTCUSDT",
  "last_price": 52300.0,
  "bid_price": 52298.0,
  "ask_price": 52302.0,
  "volume": 9876.54,
  "timestamp": 1708300800000
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| symbol | string | 交易对符号 |
| last_price | float | 最新成交价 |
| bid_price | float | 买一价 |
| ask_price | float | 卖一价 |
| volume | float | 成交量 |
| timestamp | integer | 时间戳（毫秒） |

> **注意**：若该交易对暂无 Tick 数据，所有价格和成交量字段将返回 `0`。

---

### 5. 获取市场深度数据

**GET** `/market/depth/{symbol}`

查询指定交易对的买卖盘深度数据。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symbol | string | 是 | 交易对符号，如 `BTCUSDT` |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| limit | integer | 否 | `20` | 深度档位数量限制 |

#### 请求示例

```
GET /market/depth/BTCUSDT?limit=10
```

#### 响应

```json
{
  "symbol": "BTCUSDT",
  "bids": [
    {"price": 52298.0, "size": 0.5},
    {"price": 52295.0, "size": 1.2}
  ],
  "asks": [
    {"price": 52302.0, "size": 0.3},
    {"price": 52305.0, "size": 0.8}
  ],
  "timestamp": 1708300800000
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| symbol | string | 交易对符号 |
| bids | array[object] | 买盘深度列表（价格从高到低排列） |
| bids[].price | float | 买盘价格 |
| bids[].size | float | 买盘数量 |
| asks | array[object] | 卖盘深度列表（价格从低到高排列） |
| asks[].price | float | 卖盘价格 |
| asks[].size | float | 卖盘数量 |
| timestamp | integer | 时间戳（毫秒） |

> **注意**：若该交易对暂无深度数据，`bids` 和 `asks` 将返回空数组，`timestamp` 返回 `0`。

---

### 6. 获取已订阅的交易对列表

**GET** `/market/symbols`

查询指定交易所和市场类型下已订阅的交易对列表。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| exchange | string | 否 | `"binance"` | 交易所名称 |
| market_type | string | 否 | `"spot"` | 市场类型 |

#### 请求示例

```
GET /market/symbols?exchange=binance&market_type=spot
```

#### 响应

```json
{
  "exchange": "binance",
  "market_type": "spot",
  "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| exchange | string | 交易所名称 |
| market_type | string | 市场类型 |
| symbols | array[string] | 已订阅的交易对列表 |

---

### 7. 获取行情服务统计信息

**GET** `/market/stats`

查询市场服务的运行统计数据和性能指标。

#### 请求示例

```
GET /market/stats
```

#### 响应

返回市场服务的统计信息字典，具体字段由服务运行状态决定。

```json
{
  "total_ticks": 100000,
  "total_bars": 5000,
  "connected_collectors": 2,
  "uptime_seconds": 3600
}
```

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误（如无效的时间周期） |
| 503 | 交易系统未启动，请先启动系统后再调用 |
