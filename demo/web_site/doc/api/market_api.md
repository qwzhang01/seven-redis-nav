# 行情 API 文档

## 概述

行情模块提供市场行情数据相关的 API 接口，支持行情订阅、K 线数据查询、实时 Tick 数据、市场深度等功能。同时提供管理员端的订阅配置管理和手动数据同步任务接口。

## 基础信息

- **C端基础URL**: `/api/v1/c/market`
- **Admin端基础URL**: `/api/v1/m/market`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

> **认证说明**：所有行情接口均需要在请求头中携带有效的 JWT 令牌：
> ```http
> Authorization: Bearer <token>
> ```

---

## 接口列表

### C端接口（普通用户）

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/c/market/subscribe` | 订阅行情数据 |
| POST | `/api/v1/c/market/unsubscribe` | 取消行情订阅 |
| GET | `/api/v1/c/market/kline/{symbol}` | 获取 K 线数据 |
| GET | `/api/v1/c/market/tick/{symbol}` | 获取最新 Tick 数据 |
| GET | `/api/v1/c/market/depth/{symbol}` | 获取市场深度数据 |
| GET | `/api/v1/c/market/symbols` | 获取已订阅的交易对列表 |
| GET | `/api/v1/c/market/stats` | 获取行情服务统计信息 |

### Admin端接口（管理员）

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/m/market/subscriptions` | 创建订阅配置 |
| GET | `/api/v1/m/market/subscriptions` | 获取订阅列表 |
| GET | `/api/v1/m/market/subscriptions/statistics` | 获取订阅统计信息 |
| GET | `/api/v1/m/market/subscriptions/{id}` | 获取订阅详情 |
| PUT | `/api/v1/m/market/subscriptions/{id}` | 更新订阅配置 |
| DELETE | `/api/v1/m/market/subscriptions/{id}` | 删除订阅 |
| POST | `/api/v1/m/market/subscriptions/{id}/start` | 启动订阅 |
| POST | `/api/v1/m/market/subscriptions/{id}/pause` | 暂停订阅 |
| POST | `/api/v1/m/market/subscriptions/{id}/stop` | 停止订阅 |
| POST | `/api/v1/m/market/sync-tasks` | 创建同步任务 |
| GET | `/api/v1/m/market/sync-tasks` | 获取同步任务列表 |
| GET | `/api/v1/m/market/sync-tasks/{id}` | 获取同步任务详情 |
| POST | `/api/v1/m/market/sync-tasks/{id}/cancel` | 取消同步任务 |

---

## C端接口详情

### 1. 订阅行情数据

**POST** `/api/v1/c/market/subscribe`

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

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 503 | 交易系统未启动 |

---

### 2. 取消行情订阅

**POST** `/api/v1/c/market/unsubscribe`

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

**GET** `/api/v1/c/market/kline/{symbol}`

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
GET /api/v1/c/market/kline/BTCUSDT?timeframe=1h&limit=50
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

**GET** `/api/v1/c/market/tick/{symbol}`

查询指定交易对的最新 Tick 行情数据。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symbol | string | 是 | 交易对符号，如 `BTCUSDT` |

#### 请求示例

```
GET /api/v1/c/market/tick/BTCUSDT
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

**GET** `/api/v1/c/market/depth/{symbol}`

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
GET /api/v1/c/market/depth/BTCUSDT?limit=10
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

**GET** `/api/v1/c/market/symbols`

查询指定交易所和市场类型下已订阅的交易对列表。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| exchange | string | 否 | `"binance"` | 交易所名称 |
| market_type | string | 否 | `"spot"` | 市场类型 |

#### 请求示例

```
GET /api/v1/c/market/symbols?exchange=binance&market_type=spot
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

**GET** `/api/v1/c/market/stats`

查询市场服务的运行统计数据和性能指标。

#### 请求示例

```
GET /api/v1/c/market/stats
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

## Admin端接口详情

> **说明**：Admin端接口仅供管理员使用，用于管理行情订阅配置和手动数据同步任务。

### 订阅配置管理

#### 1. 创建订阅配置

**POST** `/api/v1/m/market/subscriptions`

创建新的数据订阅配置并持久化保存，初始状态为 `stopped`。

> 创建成功返回 HTTP **201 Created**。

##### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 是 | 订阅名称 |
| exchange | string | 是 | 交易所名称 |
| market_type | string | 否 | 市场类型，默认 `spot` |
| data_type | string | 是 | 数据类型（如 kline、tick） |
| symbols | array[string] | 是 | 订阅的交易对列表 |
| interval | string | 否 | K线周期（如 1m、1h），仅 kline 类型需要 |
| config | object | 否 | 高级配置 |

**config 字段说明：**

| 字段 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| auto_restart | boolean | true | 是否自动重启 |
| max_retries | integer | 3 | 最大重试次数 |
| batch_size | integer | 1000 | 批量处理大小 |
| sync_interval | integer | 60 | 同步间隔（秒） |

```json
{
  "name": "币安BTC现货K线订阅",
  "exchange": "binance",
  "market_type": "spot",
  "data_type": "kline",
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "interval": "1m",
  "config": {
    "auto_restart": true,
    "max_retries": 3,
    "batch_size": 1000,
    "sync_interval": 60
  }
}
```

##### 响应示例

```json
{
  "success": true,
  "message": "订阅创建成功",
  "data": {
    "id": "uuid",
    "name": "币安BTC现货K线订阅",
    "exchange": "binance",
    "market_type": "spot",
    "data_type": "kline",
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "interval": "1m",
    "status": "stopped",
    "created_at": "2026-02-14T10:00:00Z",
    "updated_at": "2026-02-14T10:00:00Z",
    "last_sync_time": null,
    "total_records": 0,
    "error_count": 0,
    "last_error": null,
    "config": {
      "auto_restart": true,
      "max_retries": 3,
      "batch_size": 1000,
      "sync_interval": 60
    }
  }
}
```

---

#### 2. 获取订阅列表

**GET** `/api/v1/m/market/subscriptions`

支持按交易所、数据类型、状态筛选，以及按名称模糊搜索，结果分页返回。

##### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| exchange | string | 否 | - | 按交易所筛选 |
| data_type | string | 否 | - | 按数据类型筛选 |
| status | string | 否 | - | 按状态筛选：running/paused/stopped |
| search | string | 否 | - | 按名称模糊搜索 |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（最大100） |

##### 请求示例

```
GET /api/v1/m/market/subscriptions?exchange=binance&status=running&page=1&page_size=20
```

##### 响应示例

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "币安BTC现货K线订阅",
        "exchange": "binance",
        "market_type": "spot",
        "data_type": "kline",
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "interval": "1m",
        "status": "running",
        "created_at": "2026-02-14T10:00:00Z",
        "updated_at": "2026-02-14T10:05:00Z",
        "last_sync_time": "2026-02-14T10:10:00Z",
        "total_records": 5000,
        "error_count": 0,
        "last_error": null,
        "config": {
          "auto_restart": true,
          "max_retries": 3,
          "batch_size": 1000,
          "sync_interval": 60
        }
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

---

#### 3. 获取订阅统计信息

**GET** `/api/v1/m/market/subscriptions/statistics`

返回各状态订阅数量、总记录数、错误数以及按交易所/数据类型的分布。

##### 响应示例

```json
{
  "success": true,
  "data": {
    "total_subscriptions": 5,
    "running_subscriptions": 3,
    "paused_subscriptions": 1,
    "stopped_subscriptions": 1,
    "total_records": 100000,
    "total_errors": 2,
    "by_exchange": {
      "binance": 3,
      "okx": 2
    },
    "by_data_type": {
      "kline": 4,
      "tick": 1
    }
  }
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| total_subscriptions | integer | 订阅总数 |
| running_subscriptions | integer | 运行中的订阅数 |
| paused_subscriptions | integer | 已暂停的订阅数 |
| stopped_subscriptions | integer | 已停止的订阅数 |
| total_records | integer | 总数据记录数 |
| total_errors | integer | 总错误次数 |
| by_exchange | object | 按交易所分布 |
| by_data_type | object | 按数据类型分布 |

---

#### 4. 获取订阅详情

**GET** `/api/v1/m/market/subscriptions/{subscription_id}`

根据订阅 ID 返回完整的订阅配置信息。

##### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| subscription_id | string | 是 | 订阅ID（UUID） |

##### 响应示例

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "币安BTC现货K线订阅",
    "exchange": "binance",
    "market_type": "spot",
    "data_type": "kline",
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "interval": "1m",
    "status": "running",
    "created_at": "2026-02-14T10:00:00Z",
    "updated_at": "2026-02-14T10:05:00Z",
    "last_sync_time": "2026-02-14T10:10:00Z",
    "total_records": 5000,
    "error_count": 0,
    "last_error": null,
    "config": {
      "auto_restart": true,
      "max_retries": 3,
      "batch_size": 1000,
      "sync_interval": 60
    }
  }
}
```

##### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 订阅不存在 |

---

#### 5. 更新订阅配置

**PUT** `/api/v1/m/market/subscriptions/{subscription_id}`

支持更新名称、交易对列表、K线周期和高级配置。

##### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| subscription_id | string | 是 | 订阅ID（UUID） |

##### 请求体

> **说明**：所有字段均为可选，仅传入需要修改的字段。config 字段采用合并更新，未传字段保留原值。

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 否 | 订阅名称 |
| symbols | array[string] | 否 | 交易对列表 |
| interval | string | 否 | K线周期 |
| config | object | 否 | 高级配置（合并更新） |

```json
{
  "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
  "config": {
    "sync_interval": 30
  }
}
```

##### 响应示例

```json
{
  "success": true,
  "message": "订阅更新成功",
  "data": { "...订阅完整信息..." }
}
```

##### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 订阅不存在 |

---

#### 6. 删除订阅

**DELETE** `/api/v1/m/market/subscriptions/{subscription_id}`

删除指定订阅配置，同时级联删除关联的同步任务。

##### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| subscription_id | string | 是 | 订阅ID（UUID） |

##### 响应示例

```json
{
  "success": true,
  "message": "订阅已删除"
}
```

##### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 订阅不存在 |

---

#### 7. 启动订阅

**POST** `/api/v1/m/market/subscriptions/{subscription_id}/start`

将 `stopped` 或 `paused` 状态的订阅切换为 `running`。

##### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| subscription_id | string | 是 | 订阅ID（UUID） |

##### 响应示例

```json
{
  "success": true,
  "message": "订阅已启动",
  "data": {
    "id": "uuid",
    "status": "running",
    "updated_at": "2026-02-14T10:05:00Z"
  }
}
```

##### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 当前状态不允许执行此操作（如已是 running 状态） |
| 404 | 订阅不存在 |

---

#### 8. 暂停订阅

**POST** `/api/v1/m/market/subscriptions/{subscription_id}/pause`

将 `running` 状态的订阅切换为 `paused`，保留配置和数据。

##### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| subscription_id | string | 是 | 订阅ID（UUID） |

##### 响应示例

```json
{
  "success": true,
  "message": "订阅已暂停",
  "data": {
    "id": "uuid",
    "status": "paused",
    "updated_at": "2026-02-14T10:06:00Z"
  }
}
```

##### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 当前状态不允许执行此操作（仅 running 状态可暂停） |
| 404 | 订阅不存在 |

---

#### 9. 停止订阅

**POST** `/api/v1/m/market/subscriptions/{subscription_id}/stop`

将 `running` 或 `paused` 状态的订阅切换为 `stopped`。

##### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| subscription_id | string | 是 | 订阅ID（UUID） |

##### 响应示例

```json
{
  "success": true,
  "message": "订阅已停止",
  "data": {
    "id": "uuid",
    "status": "stopped",
    "updated_at": "2026-02-14T10:07:00Z"
  }
}
```

##### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 当前状态不允许执行此操作（仅 running/paused 状态可停止） |
| 404 | 订阅不存在 |

---

### 手动同步任务管理

#### 1. 创建同步任务

**POST** `/api/v1/m/market/sync-tasks`

为指定订阅创建一个手动历史数据同步任务，任务初始状态为 `pending`。

> 创建成功返回 HTTP **201 Created**。

##### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| subscription_id | string | 是 | 关联的订阅ID |
| start_time | string | 是 | 同步开始时间（ISO 8601格式） |
| end_time | string | 是 | 同步结束时间（ISO 8601格式，必须晚于开始时间） |

```json
{
  "subscription_id": "uuid",
  "start_time": "2026-01-01T00:00:00Z",
  "end_time": "2026-02-01T00:00:00Z"
}
```

##### 响应示例

```json
{
  "success": true,
  "message": "同步任务已创建",
  "data": {
    "id": "task_uuid",
    "subscription_id": "uuid",
    "subscription_name": "币安BTC现货K线订阅",
    "exchange": "binance",
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "data_type": "kline",
    "start_time": "2026-01-01T00:00:00Z",
    "end_time": "2026-02-01T00:00:00Z",
    "status": "pending",
    "progress": 0,
    "total_records": 0,
    "synced_records": 0,
    "error_message": null,
    "created_at": "2026-02-14T10:00:00Z",
    "updated_at": "2026-02-14T10:00:00Z",
    "completed_at": null
  }
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 任务ID |
| subscription_id | string | 关联订阅ID |
| subscription_name | string | 关联订阅名称 |
| exchange | string | 交易所 |
| symbols | array[string] | 交易对列表 |
| data_type | string | 数据类型 |
| start_time | string | 同步开始时间 |
| end_time | string | 同步结束时间 |
| status | string | 任务状态：pending/running/completed/failed/cancelled |
| progress | integer | 进度（0-100） |
| total_records | integer | 总记录数 |
| synced_records | integer | 已同步记录数 |
| error_message | string\|null | 错误信息 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| completed_at | string\|null | 完成时间 |

##### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 结束时间必须晚于开始时间 |
| 404 | 订阅不存在 |

---

#### 2. 获取同步任务列表

**GET** `/api/v1/m/market/sync-tasks`

支持按订阅 ID 和状态筛选，结果按创建时间倒序分页返回。

##### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| subscription_id | string | 否 | - | 按订阅ID筛选 |
| status | string | 否 | - | 按状态筛选：pending/running/completed/failed/cancelled |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（最大100） |

##### 请求示例

```
GET /api/v1/m/market/sync-tasks?status=completed&page=1&page_size=20
```

##### 响应示例

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "task_uuid",
        "subscription_id": "uuid",
        "subscription_name": "币安BTC现货K线订阅",
        "exchange": "binance",
        "symbols": ["BTCUSDT"],
        "data_type": "kline",
        "start_time": "2026-01-01T00:00:00Z",
        "end_time": "2026-02-01T00:00:00Z",
        "status": "completed",
        "progress": 100,
        "total_records": 43200,
        "synced_records": 43200,
        "error_message": null,
        "created_at": "2026-02-14T10:00:00Z",
        "updated_at": "2026-02-14T11:00:00Z",
        "completed_at": "2026-02-14T11:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

---

#### 3. 获取同步任务详情

**GET** `/api/v1/m/market/sync-tasks/{task_id}`

根据任务 ID 返回完整的同步任务信息。

##### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| task_id | string | 是 | 同步任务ID（UUID） |

##### 响应示例

```json
{
  "success": true,
  "data": { "...同步任务完整信息..." }
}
```

##### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 同步任务不存在 |

---

#### 4. 取消同步任务

**POST** `/api/v1/m/market/sync-tasks/{task_id}/cancel`

取消处于 `pending` 或 `running` 状态的同步任务。

##### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| task_id | string | 是 | 同步任务ID（UUID） |

##### 响应示例

```json
{
  "success": true,
  "message": "同步任务已取消",
  "data": {
    "id": "task_uuid",
    "status": "cancelled",
    "updated_at": "2026-02-14T10:30:00Z"
  }
}
```

##### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 当前状态不允许取消（只有 pending/running 状态可取消） |
| 404 | 同步任务不存在 |

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误（如无效的时间周期、状态转换不合法等） |
| 401 | 未提供认证凭据或令牌无效/已过期 |
| 404 | 资源不存在（订阅、同步任务不存在） |
| 429 | 请求过于频繁（每 IP 每 60 秒最多 200 次） |
| 503 | 交易系统未启动，请先启动系统后再调用 |

## 订阅状态流转

```
stopped ──start──▶ running ──pause──▶ paused
   ▲                  │                  │
   └──────stop────────┘◀────stop─────────┘
```

| 当前状态 | 可执行操作 |
|----------|-----------|
| stopped | start |
| running | pause、stop |
| paused | start、stop |
